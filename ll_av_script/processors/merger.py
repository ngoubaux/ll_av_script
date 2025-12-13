"""
Media merging operations
"""

import os
import tempfile
import ffmpeg
from typing import List
from ..core.models import InputFile, ProcessingConfig
from ..core.constants import LANGUAGES, CHANNEL_LAYOUT, OUTPUT_EXTENSIONS
from ..core.language_manager import LanguageManager
from ..utils.ffmpeg_wrapper import FFmpegWrapper
from ..utils.output import print_substep
from .audio_processor import AudioProcessor
from .video_processor import VideoProcessor


class MediaMerger:
    """Handles merging of audio and video files"""

    def __init__(
        self,
        ffmpeg_wrapper: FFmpegWrapper,
        language_manager: LanguageManager,
        audio_processor: AudioProcessor,
        video_processor: VideoProcessor,
    ):
        self.ffmpeg = ffmpeg_wrapper
        self.lang_manager = language_manager
        self.audio_processor = audio_processor
        self.video_processor = video_processor

    def merge_files(
        self,
        input_files: List[InputFile],
        output_file: str,
        extra_seconds: int,
        extract_english: bool,
    ) -> bool:
        """Merge all input files into one video/audio file"""
        streams = []
        stream_offset = 0

        for item in input_files:
            item.ffmpeg_input = ffmpeg.input(item.file)

            # Add video track
            if item.has_video:
                video_stream = self.video_processor.pad_video(
                    item.ffmpeg_input["v"], extra_seconds
                )
                streams.append(video_stream)

            # Extract English track if needed
            if len(item.languages) > 0 and extract_english:
                english_stream, stream_offset = self.audio_processor.extract_english_track(
                    item, stream_offset
                )
                if english_stream is not None:
                    streams.append(english_stream)
                    extract_english = False

            # Add all audio tracks
            for language in item.languages.values():
                streams.append(item.ffmpeg_input[f"a:{language.audio_idx}"])
                track_idx = language.audio_idx + stream_offset
                LANGUAGES[language.lang]["track_idx"] = track_idx

            stream_offset += len(item.languages)

        print_substep("Video and Audio(s) merging...")
        metadata_langs = self.lang_manager.get_metadata_langs(input_files)

        output_ffmpeg = ffmpeg.output(
            *streams,
            output_file,
            acodec="aac",
            write_tmcd="0",
            **metadata_langs,
        )

        return self.ffmpeg.run(output_ffmpeg)

    def create_surround_track(
        self,
        input_filename: str,
        output_file: str,
        input_files: List[InputFile],
        languages_in_output: List[str],
        streamable: bool = False,
    ) -> bool:
        """Create surround sound track"""
        print_substep("Surround track creating...")

        surround_map = self.lang_manager.get_surround_map(input_files, languages_in_output)
        metadata_titles = self.lang_manager.get_metadata_titles(input_files)
        input_file = ffmpeg.input(input_filename)

        # Create streams for each language
        surround_streams = []
        for lang in LANGUAGES.values():
            if lang["name"] not in languages_in_output:
                # Create empty track
                track = ffmpeg.input(
                    "anullsrc=channel_layout=stereo:sample_rate=44100", f="lavfi"
                )
                surround_streams.append(track["a:0"])
            else:
                surround_streams.append(input_file[f"a:{lang['track_idx']}"])

        # Join channels
        surround_input = ffmpeg.filter_(
            tuple(surround_streams),
            "join",
            inputs=f"{len(LANGUAGES)}",
            channel_layout=CHANNEL_LAYOUT,
            map="|".join(surround_map),
        )

        # Build output options
        options = {"vcodec": "copy"}
        if streamable:
            options["movflags"] = "faststart"

        output_ffmpeg = ffmpeg.output(
            input_file,
            surround_input,
            output_file,
            **options,
            **{
                f"metadata:s:a:{len(metadata_titles)}": f"title='{'_'.join(languages_in_output)}'"
            },
            **metadata_titles,
        )

        return self.ffmpeg.run(output_ffmpeg)

    def process_new_workflow(
        self,
        input_files: List[InputFile],
        output_base: str,
        languages_in_output: List[str],
        extra_seconds: int,
        extract_english: bool,
        config: ProcessingConfig,
    ) -> bool:
        """Execute NEW workflow: explode -> merge -> AIF -> bundle with surround"""
        from ..utils.output import print_step

        output_file = f"{output_base}_{'_'.join(languages_in_output)}_Su{OUTPUT_EXTENSIONS}"

        try:
            # Step 1: Explode all audio tracks from the main video
            print_step("Step 1: Exploding audio tracks from video")
            if not self.audio_processor.explode_audio_tracks(
                input_files[0].file, output_base, input_files[0].languages
            ):
                return False

            # Step 2: Merge exploded tracks with newly provided ones
            print_step("Step 2: Merging with newly provided audio files")
            fd, output_file_tmp = tempfile.mkstemp(
                dir=os.path.dirname(output_file), suffix=OUTPUT_EXTENSIONS
            )

            if not self.merge_files(
                input_files, output_file_tmp, extra_seconds, extract_english
            ):
                os.remove(output_file_tmp)
                return False

            # Step 3: Convert all tracks to AIF
            print_step("Step 3: Converting all tracks to AIF")
            if not self.audio_processor.create_individual_aif_files(
                output_file_tmp, output_base, languages_in_output
            ):
                os.remove(output_file_tmp)
                return False

            # Step 4: Create bundle video with surround track
            print_step("Step 4: Creating bundle video with surround track")
            if not self.create_surround_track(
                output_file_tmp, output_file, input_files,
                languages_in_output, config.streamable
            ):
                os.remove(output_file_tmp)
                return False

            os.remove(output_file_tmp)

            # Step 5: Create individual language videos
            print_step("Step 5: Creating individual language videos")
            self.video_processor.create_individual_language_videos(
                output_file, output_base, languages_in_output
            )

            # Optional: Extract M4A if requested
            if config.extract_m4a:
                self.audio_processor.create_individual_m4a_files(
                    output_file, output_base, languages_in_output
                )

            return True

        except Exception as e:
            if 'output_file_tmp' in locals() and os.path.exists(output_file_tmp):
                os.remove(output_file_tmp)
            raise e

    def process_complete_workflow(
        self,
        input_files: List[InputFile],
        output_base: str,
        languages_in_output: List[str],
        extra_seconds: int,
        extract_english: bool,
        config: ProcessingConfig,
    ) -> bool:
        """Execute complete workflow: merge, surround, and extract individual files"""
        output_file = f"{output_base}_{'_'.join(languages_in_output)}_Su{OUTPUT_EXTENSIONS}"

        # Handle audio-only mode
        if config.only_audio:
            output_file = input_files[0].file
            for language in input_files[0].languages.values():
                LANGUAGES[language.lang]["track_idx"] = language.audio_idx

            if config.extract_aif:
                return self.audio_processor.create_individual_aif_files(
                    output_file, output_base, languages_in_output
                )
            else:
                return self.audio_processor.create_individual_m4a_files(
                    output_file, output_base, languages_in_output
                )

        # Handle explode mode
        if config.only_explode:
            output_file = input_files[0].file
            for language in input_files[0].languages.values():
                LANGUAGES[language.lang]["track_idx"] = language.audio_idx

            self.audio_processor.create_individual_m4a_files(
                output_file, output_base, languages_in_output
            )
            return self.video_processor.create_video_only(output_file, output_base)

        # Full workflow - NEW WORKFLOW
        return self.process_new_workflow(
            input_files,
            output_base,
            languages_in_output,
            extra_seconds,
            extract_english,
            config,
        )

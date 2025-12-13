"""
Audio processing operations
"""

import ffmpeg
from typing import List
from ..core.models import InputFile
from ..core.constants import LANGUAGES, OUTPUT_AIF_EXTENSIONS, AUDIO_EXTENSIONS
from ..utils.ffmpeg_wrapper import FFmpegWrapper
from ..utils.output import print_substep


class AudioProcessor:
    """Handles audio-specific processing operations"""

    def __init__(self, ffmpeg_wrapper: FFmpegWrapper):
        self.ffmpeg = ffmpeg_wrapper

    def create_individual_aif_files(
        self, input_filename: str, output_base: str, languages_in_output: List[str]
    ) -> bool:
        """Create individual AIF audio files for each language"""
        for lang in LANGUAGES.values():
            if lang["name"] not in languages_in_output:
                continue

            print_substep(f"{lang['desc']} aif audio generating...")

            input_file = ffmpeg.input(input_filename)
            suffix = lang["name"] if lang["name"] == "E" else f"E_{lang['name']}"
            output_file = f"{output_base}_{suffix}{OUTPUT_AIF_EXTENSIONS}"

            output_ffmpeg = ffmpeg.output(
                ffmpeg.filter(input_file[f"a:{lang['track_idx']}"], "pan", "mono|c0=c1"),
                output_file,
            )

            if not self.ffmpeg.run(output_ffmpeg):
                return False

        return True

    def create_individual_m4a_files(
        self, input_filename: str, output_base: str, languages_in_output: List[str]
    ) -> bool:
        """Create individual M4A audio files for each language"""
        for lang in LANGUAGES.values():
            if lang["name"] not in languages_in_output:
                continue

            print_substep(f"{lang['desc']} m4a audio generating...")

            input_file = ffmpeg.input(input_filename)
            suffix = lang["name"] if lang["name"] == "E" else f"E_{lang['name']}"
            output_file = f"{output_base}_{suffix}{AUDIO_EXTENSIONS}"

            output_ffmpeg = ffmpeg.output(
                input_file[f"a:{lang['track_idx']}"],
                output_file,
                acodec="copy",
                **{
                    "metadata:s:a:0": f"title='{lang['title']}'",
                    "disposition:a": "+default",
                },
            )

            if not self.ffmpeg.run(output_ffmpeg):
                return False

        return True

    def explode_audio_tracks(self, input_filename: str, output_base: str, languages: dict) -> bool:
        """Explode all audio tracks from video into individual M4A files"""
        print_substep("Exploding audio tracks from video...")

        for lang_key, lang_data in languages.items():
            print_substep(f"Extracting {LANGUAGES[lang_key]['desc']} track...")

            input_file = ffmpeg.input(input_filename)
            suffix = lang_key if lang_key == "E" else f"E_{lang_key}"
            output_file = f"{output_base}_{suffix}{AUDIO_EXTENSIONS}"

            output_ffmpeg = ffmpeg.output(
                input_file[f"a:{lang_data.audio_idx}"],
                output_file,
                acodec="copy",
                **{
                    "metadata:s:a:0": f"title='{lang_data.metadata_title}'",
                    "disposition:a": "+default",
                },
            )

            if not self.ffmpeg.run(output_ffmpeg):
                return False

        return True

    def extract_english_track(self, item: InputFile, stream_offset: int) -> tuple:
        """Extract English track from first audio track"""
        if len(item.languages) == 0:
            return None, stream_offset

        lang = next(iter(item.languages))
        print_substep(f"English track from {lang} extracting...")

        audio_stream = item.ffmpeg_input[f'a:{item.languages[lang].audio_idx}']
        english_stream = ffmpeg.filter(audio_stream, "pan", "stereo|c0=2*c0|c1=2*c0")

        LANGUAGES["E"]["track_idx"] = 0
        item.languages["E"] = type(item.languages[lang])(
            lang="E",
            audio_idx=0,
            metadata_lang=LANGUAGES["E"]["lang"],
            metadata_title="E",
            join_chan=LANGUAGES["E"]["channel"],
        )

        return english_stream, stream_offset + 1

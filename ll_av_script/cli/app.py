"""
Main application class
"""

import os
import sys
from typing import Optional
from ..core.models import ProcessingConfig, InputFile
from ..core.language_manager import LanguageManager
from ..core.constants import (
    BUDDLE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    AUDIO_EXTENSIONS,
)
from ..processors import (
    AudioProcessor,
    VideoProcessor,
    MediaMerger,
    FileAnalyzer,
)
from ..utils.ffmpeg_wrapper import FFmpegWrapper
from ..utils.output import print_step, print_desc, print_error, print_warning


class Application:
    """Main application class for audio/video processing"""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.ffmpeg = FFmpegWrapper(quiet=config.quiet_output)
        self.lang_manager = LanguageManager(no_interact=config.no_interact)
        self.audio_processor = AudioProcessor(self.ffmpeg)
        self.video_processor = VideoProcessor(self.ffmpeg)
        self.merger = MediaMerger(
            self.ffmpeg,
            self.lang_manager,
            self.audio_processor,
            self.video_processor,
        )
        self.file_analyzer = FileAnalyzer(self.ffmpeg)

    def run(self) -> int:
        """Main entry point for the application"""
        self._ensure_directories()

        # Handle cutting mode
        if self.config.start_time or self.config.end_time:
            return self._handle_cut_mode()

        # Handle file processing
        if self.config.filename:
            dirname = os.path.dirname(self.config.filename)
            filename = os.path.basename(self.config.filename)
            return self._process_file(filename, dirname)
        else:
            return self._process_directory()

    def _ensure_directories(self) -> None:
        """Ensure input and output directories exist"""
        if not os.path.exists(self.config.input_dir):
            os.mkdir(self.config.input_dir)
        if not os.path.exists(self.config.output_dir):
            os.mkdir(self.config.output_dir)

    def _handle_cut_mode(self) -> int:
        """Handle video cutting mode"""
        if (
            not self.config.start_time
            or not self.config.end_time
            or not self.config.filename
        ):
            print_error("You must specify all arguments: --start, --to, --file")
            return 1

        filename = os.path.basename(self.config.filename)
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(self.config.output_dir, f"{base_name}.mp4")

        success = self.video_processor.cut_video(
            self.config.filename,
            output_file,
            self.config.start_time,
            self.config.end_time,
        )
        return 0 if success else 1

    def _process_directory(self) -> int:
        """Process all files in input directory"""
        for file in os.listdir(self.config.input_dir):
            result = self._process_file(file, self.config.input_dir)
            if result != 0:
                return result
        return 0

    def _process_file(self, file: str, input_dir: str) -> int:
        """Process a single media file"""
        base_name, extension = os.path.splitext(file)

        if extension not in [BUDDLE_EXTENSIONS, VIDEO_EXTENSIONS]:
            return 0

        # Extract base name without language suffixes
        base_name = self.file_analyzer.extract_base_name(file)

        # Probe main file
        file_path = os.path.join(input_dir, file)
        probe = self.ffmpeg.probe(file_path)
        input_files = [self.file_analyzer.create_input_item(file_path, probe, True)]

        print_step(f"Process {input_files[0].file}")

        # Extract language tracks
        input_files[0].languages = self.lang_manager.extract_language_tracks(
            input_files[0].file, probe
        )

        # Calculate audio/video duration padding
        audio_duration = self.file_analyzer.get_max_audio_duration(probe)
        video_duration = self.file_analyzer.get_video_duration(probe)

        # Find additional audio files
        additional_files = self.file_analyzer.find_additional_audio_files(
            base_name, input_dir, input_files[0].languages
        )
        input_files.extend(additional_files)

        # Update audio duration
        for item in additional_files:
            item_probe = self.ffmpeg.probe(item.file)
            audio_duration = self.file_analyzer.get_max_audio_duration(
                item_probe, audio_duration
            )

        extra_seconds = max(0, audio_duration - video_duration)

        # Collect all languages
        languages_in_output = []
        for item in input_files:
            languages_in_output.extend(item.languages.keys())

        if not languages_in_output:
            print_warning(
                f"No language found: Specify languages in {input_files[0].file}.yml"
            )
            return 1

        output_base = os.path.join(self.config.output_dir, base_name)

        print_desc(f"\t Name: {base_name}")
        print_desc(f"\t Language: {' '.join(languages_in_output)}")
        print_desc(f"\t Video padding: {extra_seconds}s")

        # Check if English needs to be extracted
        extract_english = "E" not in languages_in_output
        if extract_english:
            languages_in_output.insert(0, "E")

        # Process the files
        success = self.merger.process_complete_workflow(
            input_files,
            output_base,
            languages_in_output,
            extra_seconds,
            extract_english,
            self.config,
        )

        return 0 if success else 1

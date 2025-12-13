"""
File analysis utilities
"""

import os
import re
from typing import Tuple, List
from ..core.models import InputFile
from ..core.constants import LANGUAGES, AUDIO_EXTENSIONS
from ..utils.output import print_adding_file
from ..utils.ffmpeg_wrapper import FFmpegWrapper


class FileAnalyzer:
    """Analyzes media files and extracts metadata"""

    def __init__(self, ffmpeg_wrapper: FFmpegWrapper):
        self.ffmpeg = ffmpeg_wrapper

    def get_audio_count(self, probe: dict) -> int:
        """Get number of audio tracks in file"""
        return sum(1 for stream in probe["streams"] if stream["codec_type"] == "audio")

    def get_max_audio_duration(self, probe: dict, audio_duration: int = 0) -> int:
        """Get maximum audio duration from all audio tracks"""
        for stream in probe["streams"]:
            if stream["codec_type"] != "audio":
                continue
            duration = round(float(stream["duration"]))
            if duration > audio_duration:
                audio_duration = duration
        return audio_duration

    def get_video_duration(self, probe: dict) -> int:
        """Get video duration"""
        for stream in probe["streams"]:
            if stream["codec_type"] != "video":
                continue
            return round(float(stream["duration"]))
        return 0

    def get_video_resolution(self, probe: dict) -> Tuple[int, int, str, str, str]:
        """Get video resolution and codec information"""
        for stream in probe["streams"]:
            if stream["codec_type"] != "video":
                continue

            aspect_ratio = (
                stream["sample_aspect_ratio"].replace(":", "/")
                if "sample_aspect_ratio" in stream
                else f"{stream['height']}/{stream['width']}"
            )

            return (
                stream["width"],
                stream["height"],
                stream["r_frame_rate"],
                stream["codec_name"],
                aspect_ratio,
            )
        return 0, 0, "0", "", "0"

    def create_input_item(self, file: str, probe: dict, has_video: bool) -> InputFile:
        """Create InputFile object from probe data"""
        width, height, frame_rate, codec, sar = self.get_video_resolution(probe)
        return InputFile(
            file=file,
            has_video=has_video,
            languages={},
            audio_count=0,
            width=width,
            height=height,
            frame_rate=frame_rate,
            video_codec=codec,
            sar=sar,
        )

    def find_additional_audio_files(
        self, base_name: str, input_dir: str, master_file_languages: dict
    ) -> List[InputFile]:
        """Find additional audio files matching the base name"""
        additional_files = []

        for language in LANGUAGES:
            suffix = language if language == "E" else f"E_{language}"
            filename = f"{base_name}_{suffix}{AUDIO_EXTENSIONS}"
            input_file = os.path.join(input_dir, filename)

            if os.path.exists(input_file):
                probe = self.ffmpeg.probe(input_file)
                item = self.create_input_item(input_file, probe, False)
                item.languages[language] = {
                    "lang": language,
                    "audio_idx": 0,
                    "metadata_lang": LANGUAGES[language]["lang"],
                    "metadata_title": suffix,
                    "join_chan": LANGUAGES[language]["channel"],
                }
                print_adding_file(f"Adding file {item.file}")
                additional_files.append(item)

                # Remove language from master file if present
                if language in master_file_languages:
                    del master_file_languages[language]

        return additional_files

    def extract_base_name(self, filename: str) -> str:
        """Extract base name from filename with language suffixes"""
        pattern = "((_[" + "".join(list(LANGUAGES.keys())) + "])(?![0-9A-Za-z]))+"
        matches = re.search(pattern, filename)
        if matches:
            pos = matches.start()
            return filename[0:pos]
        return os.path.splitext(filename)[0]

"""
Video processing operations
"""

import ffmpeg
from typing import List
from ..core.models import InputFile
from ..core.constants import LANGUAGES, OUTPUT_EXTENSIONS
from ..utils.ffmpeg_wrapper import FFmpegWrapper
from ..utils.output import print_substep


class VideoProcessor:
    """Handles video-specific processing operations"""

    def __init__(self, ffmpeg_wrapper: FFmpegWrapper):
        self.ffmpeg = ffmpeg_wrapper

    def create_individual_language_videos(
        self, input_filename: str, output_base: str, languages_in_output: List[str]
    ) -> bool:
        """Create individual video files for each language"""
        for lang in LANGUAGES.values():
            if lang["name"] not in languages_in_output:
                continue

            print_substep(f"{lang['desc']} video generating...")

            input_file = ffmpeg.input(input_filename)
            suffix = lang["title"]
            output_file = f"{output_base}_{suffix}{OUTPUT_EXTENSIONS}"

            output_ffmpeg = ffmpeg.output(
                input_file.video,
                input_file[f"a:{lang['track_idx']}"],
                output_file,
                vcodec="copy",
                acodec="copy",
                **{
                    "metadata:s:a:0": f"title='{lang['title']}'",
                    "disposition:a": "+default",
                    "movflags": "faststart",
                },
            )

            if not self.ffmpeg.run(output_ffmpeg):
                return False

        return True

    def create_video_only(self, input_filename: str, output_base: str) -> bool:
        """Create video-only file (no audio)"""
        print_substep("video generating...")

        input_file = ffmpeg.input(input_filename)
        output_file = f"{output_base}{OUTPUT_EXTENSIONS}"

        output_ffmpeg = ffmpeg.output(
            input_file.video,
            output_file,
            vcodec="copy",
            **{
                "disposition:a": "+default",
                "movflags": "faststart",
            },
        )

        return self.ffmpeg.run(output_ffmpeg)

    def cut_video(
        self, input_file: str, output_file: str, start_time: str, end_time: str
    ) -> bool:
        """Cut video from start to end time"""
        print_substep(f"Cutting video from {start_time} to {end_time}")

        input_stream = ffmpeg.input(input_file)
        output_ffmpeg = ffmpeg.output(
            input_stream,
            output_file,
            to=end_time,
            ss=start_time,
            vcodec="copy",
            acodec="copy",
            **{"map": 0},
        )

        return self.ffmpeg.run(output_ffmpeg)

    def pad_video(self, video_stream, extra_seconds: int):
        """Add padding to video"""
        if extra_seconds > 0:
            return ffmpeg.filter(video_stream, "tpad", f"stop_duration={extra_seconds}")
        return video_stream

"""
FFmpeg wrapper for simplified command execution
"""

import subprocess
from typing import List, Tuple, Optional
import ffmpeg


class FFmpegWrapper:
    """Wrapper class for FFmpeg operations"""

    def __init__(self, quiet: bool = True):
        self.quiet = quiet

    def run_cmdline_async(self, args: List[str]) -> subprocess.Popen:
        """Run FFmpeg command asynchronously"""
        stdin_stream = None
        stdout_stream = subprocess.PIPE
        stderr_stream = subprocess.PIPE
        if self.quiet:
            stderr_stream = subprocess.STDOUT
            stdout_stream = subprocess.PIPE
        return subprocess.Popen(
            args,
            stdin=stdin_stream,
            stdout=stdout_stream,
            stderr=stderr_stream,
            cwd=None,
            text=True,
        )

    def run_cmdline(self, cmdline: List[str], input_data: Optional[str] = None) -> Tuple[str, str]:
        """Run FFmpeg command synchronously"""
        process = self.run_cmdline_async(cmdline)
        out, err = process.communicate(input_data)
        retcode = process.poll()
        if retcode:
            raise ffmpeg.Error("ffmpeg", out, err)
        return out, err

    def run(self, output_ffmpeg, force_args: bool = False) -> bool:
        """Execute FFmpeg command from ffmpeg-python object"""
        _args = ffmpeg.compile(output_ffmpeg, overwrite_output=True)
        args = [arg.replace("\\\\\\\\\\\\=", "=") for arg in _args]

        if not self.quiet or force_args:
            print(args)

        try:
            out, err = self.run_cmdline(args)
            if not self.quiet:
                print(out)
                print(err)
        except ffmpeg.Error as e:
            from .output import print_error
            print_error("ffmpeg run cmdline failed")
            print(" ".join(args))
            if e.stdout:
                print(e.stdout)
            if e.stderr:
                print(e.stderr)
            return False
        return True

    @staticmethod
    def probe(file: str) -> dict:
        """Probe media file for information"""
        return ffmpeg.probe(file)

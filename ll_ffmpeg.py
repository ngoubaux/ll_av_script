import ffmpeg
import subprocess
from ll_print import *

def ffmpeg_run_cmdline_async(args):
    stdin_stream = None
    stdout_stream = subprocess.PIPE
    stderr_stream = subprocess.PIPE
    if quiet_output:
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


def ffmpeg_run_cmdline(cmdline):
    process = ffmpeg_run_cmdline_async(cmdline)
    out, err = process.communicate(input)
    retcode = process.poll()
    if retcode:
        raise ffmpeg.Error("ffmpeg", out, err)
    return out, err


def ffmpeg_run(output_ffmpeg, force_args=0):
    global quiet_output
    # output_ffmpeg = ffmpeg.overwrite_output(output_ffmpeg)

    # output_ffmpeg.get_args()
    _args = ffmpeg.compile(output_ffmpeg, overwrite_output=True)
    args = [arg.replace("\\\\\\\\\\\\=", "=") for arg in _args]

    if not quiet_output or force_args:
        print(args)
        # print(ffmpeg.compile(output_ffmpeg))

    try:
        out, err = ffmpeg_run_cmdline(args)
        if not quiet_output:
            print(out)
            print(err)

    except ffmpeg.Error as e:
        print_error("ffmpeg run cmdline failed")
        print(" ".join(args))
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False
    return True

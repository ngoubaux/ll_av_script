#!/usr/bin/env python3

import textwrap
from enum import Enum
import ffmpeg
import os
import argparse
from colorama import Fore, Back, Style, init as colorama_init
import subprocess
from pathlib import Path

colorama_init()

prog_version = "0.0.1"
prog_name = "ll_audiofix"

quiet_output = False
no_interact = False
fix_type = "voiceRec"
volume_db = 0


class ModelType(Enum):
    generic = "Generic"
    voice = "Voice"
    genericRec = "Generic recording"
    voiceRec = "Voice recording"
    speechRec = "Speech recording"

    def file(self):
        return {
            ModelType.generic: "rnnoise-models/marathon-prescription-2018-08-29/mp.rnnn",
            ModelType.voice: "rnnoise-models/leavened-quisling-2018-08-31/lq.rnnn",
            ModelType.genericRec: "rnnoise-models/conjoined-burgers-2018-08-28/cb.rnnn",
            ModelType.voiceRec: "rnnoise-models/beguiling-drafter-2018-08-30/bd.rnnn",
            ModelType.speechRec: "rnnoise-models/somnolent-hogwash-2018-09-01/sh.rnnn",
        }.get(self)

    def describe(self):
        return {
            ModelType.generic: "Generic",
            ModelType.voice: "Voice",
            ModelType.genericRec: "Recording (Generic)",
            ModelType.voiceRec: "Voice Recording",
            ModelType.speechRec: "Speech Recording",
        }.get(self)

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        try:
            return ModelType[s]
        except KeyError:
            return s


def print_step(str):
    print(Fore.BLUE + "==> " + Style.RESET_ALL + Style.BRIGHT + str + Style.RESET_ALL)


def print_substep(str):
    print(Fore.GREEN + "==> " + Style.RESET_ALL + str + Style.RESET_ALL)


def print_error(str):
    print(
        Fore.RED
        + Style.BRIGHT
        + "X"
        + Style.NORMAL
        + Fore.RED
        + " Error: "
        + Style.RESET_ALL
        + str
    )


def print_warning(str):
    print(
        Fore.YELLOW
        + Style.BRIGHT
        + "<!>"
        + Style.NORMAL
        + Fore.YELLOW
        + " Warning: "
        + Style.RESET_ALL
        + str
    )


def print_desc(str):
    print(Style.DIM + str + Style.RESET_ALL)


def print_addingg_file(str):
    print(Style.DIM + "==>" + Style.RESET_ALL + str)


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


def main():
    global quiet_output
    global no_interact
    global fix_type
    global volume_db

    parser = argparse.ArgumentParser(
        prog=prog_name,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            f"""\
        Audio enhancement
        --------------------
            Reduce noise and increase sound level

        """
        ),
    )
    parser.add_argument(
        "-v", "--verbose", help="Make output more verbose", action="store_false"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s: {prog_version}"
    )
    parser.add_argument(
        "--db",
        help="Change audio volume (Db)",
        dest="db",
        action="store",
    )
    parser.add_argument(
        "-t",
        "--type",
        type=ModelType.argparse,
        choices=list(ModelType),
        help="Type of enhancement",
        dest="model",
        action="store",
    )
    parser.add_argument("filename")

    args = parser.parse_args()
    quiet_output = args.verbose

    if args.model is not None:
        fix_type = args.model

    if args.db is not None:
        volume_db = args.db

    filename = os.path.abspath(args.filename)

    print(f"{prog_name} v.{prog_version}")
    print(f"Process file: {filename}")

    fetch_volume_db(filename)
    process_file(filename)


def fetch_volume_db(file):
    global volume_db

    process = subprocess.Popen(
        f"ffmpeg -i {file}  -af volumedetect -vn -sn -dn -f null - 2>&1 | grep histogram_ | cut -d ' ' -f 4 | head -n 1 | cut -d '_' -f 2 | sed s/':'//",
        shell=True,
        stdout=subprocess.PIPE,
    )
    stdout_list = process.communicate()[0].decode().split("\n")
    if volume_db == 0:
        print_substep(f"Volume increased by {stdout_list[0]}")
        volume_db = stdout_list[0].replace('b', 'B')
    else:
        print_substep(f"Volume increased by {volume_db} forced (detected: {stdout_list[0]})")
        volume_db = f"{volume_db}dB"

def process_file(file):
    """
    Process the file
    """
    global quiet_output
    global fix_type
    global volume_db

    base_name, extension = os.path.splitext(file)
    print_substep(f"  Audio Fix using {fix_type.describe()} model...")

    script_dir = Path(__file__).resolve().parent
    model_file = f"{script_dir}/{fix_type.file()}"
    # print(f"model {model_file}")
    input_file = ffmpeg.input(file)
    output_file = f"{base_name}_audiofix{extension}"
    # Create the final command
    output_ffmpeg = ffmpeg.output(
        input_file,
        output_file,
        vcodec="copy",
        af=f"arnndn=m={model_file},volume=volume={volume_db}", #,volume=volume={volume_db}
    )

    if not ffmpeg_run(output_ffmpeg):
        return False

    return True


if __name__ == "__main__":
    main()

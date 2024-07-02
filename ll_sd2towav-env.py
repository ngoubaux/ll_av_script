#!/usr/bin/env python3

import json
import textwrap
import ffmpeg
import os
import glob
import argparse
import subprocess
from pathlib import Patht
import pandas as pd
from ll_print import *



colorama_init()

prog_version = "0.0.2"
prog_name = "ll_sd2towav"

output_extension = ".aif"

quiet_output = False
no_interact = False
df = None
source_path = Path().absolute()
file_db_path = "sound-designer_files.xlsx"
file_template_db = {
    "file": [],
    "rsrc": [],
    "channels": [],
    "sample-rate": [],
    "sample-size": [],
    "verified": [],
    "need_sound_fix": [],
}
custom_header = [
    "file",
    "rsrc",
    "channels",
    "sample-rate",
    "sample-size",
    "verified",
    'need_sound_fix',
]


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
    global source_path
    global file_db
    global df
    global custom_header

    parser = argparse.ArgumentParser(
        prog=prog_name,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            f"""\
        Sound Designer II to {{output_extension}} convert
        --------------------
            Convert Sound Designer II audio to {{output_extension}} audio
            Can recover file without resource fork

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
        "-f",
        "--filter",
        help="path to config file with list of file to convert",
        dest="file_list",
        action="store",
    )
    parser.add_argument("path", nargs="?")
    # parser.add_argument("-aif-only", "--extract-only-audio-aif", help="Extra only mono aif audio for each language", dest="only_extract_aif", action='store_true')
    args = parser.parse_args()
    quiet_output = args.verbose

    if args.path is not None:
        source_path = os.path.abspath(args.path)
    # no_interact = args.no_interact

    print(f"{prog_name} v.{prog_version}")
    print(f"Path: {source_path}")

    if os.path.exists(file_db_path):
        df = pd.read_excel(file_db_path)
        if 'need_sound_fix' not in df.columns:
            df.insert(6, "need_sound_fix", [0] * len(df), False)

    else:
        df = pd.DataFrame(file_template_db)

    df.astype(
        {
            "file": str,
            "rsrc": int,
            "channels": int,
            "sample-rate": int,
            "sample-size": int,
            "verified": int,
            "need_sound_fix": int,
        }
    )

    ##
    # Full workflow
    ##
    if args.file_list is not None:
        dirname = os.path.dirname(args.filename)
        filename = os.path.basename(args.filename)

    # Parcourir le dossier d'entrée
    for filename in glob.iglob(str(source_path) + "**/**", recursive=True):
        if os.path.isfile(filename):
            file_df = df.loc[(df["file"] == filename)]
            if file_df.empty or file_df["verified"].item() == 0:
                process_file(filename, file_df)
            else:
                if not quiet_output:
                    print_substep(f"{filename} already verifed...")

    df.to_excel(file_db_path, header=custom_header, index_label="file", index=False)


def process_file(file, file_df):
    """
    Process the full workflow (Merge audio, Extract Audio, Update metadata, create Surround)
    """
    global quiet_output
    global output_dir

    base_name, extension = os.path.splitext(file)
    if extension == "" or extension == ".sd2":
        print_step(f"Processing: {file}")
        convert_audio_file(file, file_df)
    # rf = rsrcfork.open(file)


def convert_audio_file(input_filename, file_df):
    """
    Purpose: arg
    """
    global df

    input_folder = os.path.dirname(input_filename)
    input_json = f"{input_filename}.json"
    has_rsrc = 0

    print_substep("  Getting Audio setting...")
    if file_df.empty:
        return_code = subprocess.call(
            f"rsrcdump -i STR --extract '{input_filename}/..namedfork/rsrc'",
            shell=True,
            stdout=subprocess.DEVNULL,
            cwd=input_folder,
            stderr=subprocess.DEVNULL,
        )
        if return_code == 0:
            print_desc("\t source: resource fork")
            has_rsrc = 1
            with open(input_json) as fd:
                json_data = json.load(fd)
                # 1000 = "sample-size"
                sample_size = int(json_data["STR "]["1000"]["obj"]) * 8
                # 1000 = "sample-rate"
                sample_rate = int(json_data["STR "]["1001"]["obj"])
                # 1000 = "channels"
                channels = int(json_data["STR "]["1002"]["obj"])
        else:
            print_desc("\t source: default")
            sample_size = 16
            sample_rate = 44100
            channels = 1
    else:
        print_desc("\t source: SpreadSheet")
        sample_size = file_df["sample-size"].item()
        sample_rate = file_df["sample-rate"].item()
        channels = file_df["channels"].item()

    print_desc(f"\t channel(s): {channels}")
    print_desc(f"\t sample-rate: {sample_rate}")
    print_desc(f"\t sample-size: {sample_size}")

    if file_df.empty:
        file_df = pd.DataFrame(
            {
                "file": [input_filename],
                "rsrc": [has_rsrc],
                "channels": [channels],
                "sample-rate": [sample_rate],
                "sample-size": [sample_size],
                "verified": [0],
                "need_sound_fix": [0],
            },
            index=[len(df.index)],
        )
        df = pd.concat([df, file_df])

    print_substep("  Audio conversion...")

    input_file = ffmpeg.input(
        input_filename, f=f"s{sample_size}be", ar=f"{sample_rate}", ac=f"{channels}"
    )
    output_file = f"{input_filename}{output_extension}"
    # Create the final command
    output_ffmpeg = ffmpeg.output(
        input_file,
        output_file,
    )

    if not ffmpeg_run(output_ffmpeg):
        return False

    return True


if __name__ == "__main__":
    main()

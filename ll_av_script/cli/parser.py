"""
Command-line argument parser
"""

import argparse
import textwrap
from ..core.constants import CHANNEL_LAYOUT, LANGUAGES


def create_argument_parser(prog_version: str) -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
    lang_keys = " ".join(
        "{0: <5}".format(o["name"].replace("_", "-")) for o in LANGUAGES.values()
    )
    lang_channel = " ".join("{0: <5}".format(o["channel"]) for o in LANGUAGES.values())
    lang_count = " ".join("{0: <5}".format(i) for i in range(1, 9))

    parser = argparse.ArgumentParser(
        prog="ll_av_script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            f"""\
        Audio / Video Mixer
        --------------------
            Merge Audio and video file to one single file.
            Then create a Surround ({CHANNEL_LAYOUT}) track with all languages

            Layout
            ------
            {lang_count}
            {lang_keys}
            {lang_channel}

        """
        ),
    )

    parser.add_argument(
        "-v",
        "--verbose",
        help="Make output more verbose",
        dest="verbose",
        action="store_false",
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s: {prog_version}"
    )

    parser.add_argument(
        "--streaming",
        help="Make the video streamable",
        dest="streamable",
        action="store_true",
    )

    parser.add_argument(
        "-ss",
        "--start",
        help="Cut the video from this time",
        dest="start_time",
        action="store",
    )

    parser.add_argument(
        "-to",
        "--to",
        help="Cut the video until this time",
        dest="end_time",
        action="store",
    )

    parser.add_argument(
        "-f", "--file", help="Process this file", dest="filename", action="store"
    )

    parser.add_argument(
        "-aif",
        "--extra-audio-aif",
        help="Extra mono aif audio for each language",
        dest="extract_aif",
        action="store_true",
    )

    parser.add_argument(
        "-m4a",
        "--extra-audio-m4a",
        help="Extra stereo audio for each language",
        dest="extract_m4a",
        action="store_true",
    )

    parser.add_argument(
        "--no-interact",
        help="No user interaction",
        dest="no_interact",
        action="store_true",
    )

    parser.add_argument(
        "-e",
        "--edit",
        help="Edit the video by remove parts (<timecode_start>,<second_remove>)",
        dest="edit",
        action="append",
    )

    parser.add_argument(
        "-audio-only",
        "--extract-only-audio",
        help="Extract only audio for each language",
        dest="only_extract_audios",
        action="store_true",
    )

    parser.add_argument(
        "--explode",
        help="Explode the video into multiple files by language",
        dest="explode_only",
        action="store_true",
    )

    return parser

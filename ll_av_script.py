#!/usr/bin/env python3

import json
import textwrap
import ffmpeg
import re
import os
import yaml
import tempfile
import exiftool
import sys
import argparse
from colorama import Fore, Back, Style, init as colorama_init
import subprocess

colorama_init()

prog_version="1.0.4"

# Liste des extensions de fichiers vidéo et audio
buddle_extensions = ".mov"
video_extensions = ".mp4"
audio_extensions = ".m4a"
output_extensions = ".mp4"


quiet_output = True
# Liste des langues
# FFMPEG is using ISO 639-2 language table
# https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes
#
# Channel Layout
# http://underpop.online.fr/f/ffmpeg/help/channel-layout.htm.gz
# https://trac.ffmpeg.org/wiki/AudioChannelManipulation
#
channel_layout="7.1"
languages = {
    "E": {
        "name": "E",
        "lang": "eng",
        "title": "E",
        "channel": "FL",
        "track_idx": -1,
        "desc": "English",
        "old_name": "Eng",
    },
    "F": {
        "name": "F",
        "lang": "fra",
        "title": "E_F",
        "channel": "FR",
        "track_idx": -1,
        "desc": "French",
        "old_name": "Fre",
    },
    "G": {
        "name": "G",
        "lang": "ger",
        "title": "E_G",
        "channel": "FC",
        "track_idx": -1,
        "desc": "German",
        "old_name": "Ger",
    },
    "-": {
        "name": "-",
        "lang": "und",
        "title": "und",
        "channel": "LFE",
        "track_idx": -1,
        "desc": "Unused",
        "old_name": "und",
    },
    "S": {
        "name": "S",
        "lang": "spa",
        "title": "E_S",
        "channel": "BL",
        "track_idx": -1,
        "desc": "Spanish",
        "old_name": "Spa",
    },
    "I": {
        "name": "I",
        "lang": "ita",
        "title": "E_I",
        "channel": "BR",
        "track_idx": -1,
        "desc": "Italian",
        "old_name": "Ita",
    },
    "C": {
        "name": "C",
        "lang": "chi",
        "title": "E_C",
        "channel": "SL",
        "track_idx": -1,
        "desc": "Chinese",
        "old_name": "Chi",
    },
    "$": {
        "name": "-",
        "lang": "und",
        "title": "und",
        "channel": "SR",
        "track_idx": -1,
        "desc": "Unused",
        "old_name": "und",
    },
}


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
        + "Extracting ffmpeg error output..."
    )
    print(str)
    print(
        Fore.RED
        + Style.BRIGHT
        + "X"
        + Style.NORMAL
        + Fore.RED
        + " Error: "
        + Style.RESET_ALL
        + "Please watch log message behove..."
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


def search_lang_by_md(lang_md):
    for lang in languages:
        if languages[lang]["lang"] == lang_md:
            return lang

    return ""


def search_lang_by_title(lang_title):
    for lang in languages:
        title = re.sub("[_-]", "", languages[lang]["title"])
        lang_title = re.sub("[_-]", "", lang_title)
        if title == lang_title:
            return lang

    return ""


def extract_language_tracks(file, probe):
    # Open Config file if present
    yml = None
    yml_path = f"{file}.yml"
    if os.path.isfile(yml_path):
        if stream := open(yml_path):
            yml = yaml.safe_load(stream)

    with exiftool.ExifToolHelper() as et:
        metadata = et.get_metadata(file)[0]

    language_tracks = {}
    audio_idx = 0
    for elt in probe["streams"]:
        lang = ""

        # Get Track language with Metadata
        if elt["codec_type"] != "audio" or elt["channels"] > 2:
            continue

        # Get Track language with Yml file
        if yml and yml[f"track_{audio_idx+1}"] and yml[f"track_{audio_idx+1}"]["lang"]:
            lang = yml[f"track_{audio_idx+1}"]["lang"]
            md_lang = languages[lang]["lang"]

        title_key = f"QuickTime:Track{elt['index']+1}Name"
        if lang == "" and title_key in metadata:
            key_name = metadata[title_key].replace("'", "")
            lang = search_lang_by_title(key_name)
            if lang != "":
                md_lang = languages[lang]["lang"]

        if lang == "" and "language" in elt["tags"]:
            md_lang = elt["tags"]["language"]
            lang = search_lang_by_md(md_lang)

        if lang != "":
            language_tracks[lang] = {
                "lang": lang,
                "audio_idx": audio_idx,
                "metadata_lang": md_lang,
                "metadata_title": languages[lang]["title"],
                "join_chan": languages[lang]["channel"],
            }
        else:
            print_warning(f"Audio track_{audio_idx} is skipped")

        audio_idx += 1

    return language_tracks


def get_audio_count(probe):
    audio_idx = 0
    for elt in probe["streams"]:
        # Get Track language with Metadata
        if elt["codec_type"] != "audio":
            continue

        audio_idx += 1

    return audio_idx


def get_max_audio_duration(probe, audio_duration=0):
    for elt in probe["streams"]:
        # Get Track language with Metadata
        if elt["codec_type"] != "audio":
            continue

        duration = round(float(elt["duration"]))
        if duration > audio_duration:
            audio_duration = duration

    return audio_duration


def get_video_duration(probe):
    duration = 0
    for elt in probe["streams"]:
        # Get Track language with Metadata
        if elt["codec_type"] != "video":
            continue

        duration = round(float(elt["duration"]))
        break

    return duration


def ffmpeg_run_cmdline_async(
    args
):    
    stdin_stream = None
    stdout_stream = None
    stderr_stream = subprocess.PIPE
    if quiet_output:
        stderr_stream = subprocess.STDOUT
        stdout_stream = subprocess.DEVNULL
    return subprocess.Popen(
        args,
        stdin=stdin_stream,
        stdout=stdout_stream,
        stderr=stderr_stream,
        cwd=None,
    )
    
def ffmpeg_run_cmdline(    
    cmdline    
):
    
    process = ffmpeg_run_cmdline_async(
       cmdline
    )
    out, err = process.communicate(input)
    retcode = process.poll()
    if retcode:
        raise ffmpeg.Error('ffmpeg', out, err)
    return out, err

def ffmpeg_run(output_ffmpeg, force_args=0):
    # output_ffmpeg = ffmpeg.overwrite_output(output_ffmpeg)

    # output_ffmpeg.get_args()
    _args = ffmpeg.compile(output_ffmpeg, overwrite_output=True)
    
    args = [arg.replace('\\\\\\\\\\\\=', '=') for arg in _args]
    
    if not quiet_output or force_args:
        print(args)
        # print(ffmpeg.compile(output_ffmpeg))

    try:
        out, err = ffmpeg_run_cmdline(args)
    except ffmpeg.Error as e:
        print_error(e.stderr.decode("utf-8"))
        return False
    return True


def get_video_resolution(probe):
    for elt in probe["streams"]:
        # Get Track language with Metadata
        if elt["codec_type"] != "video":
            continue

        return (
            elt["width"],
            elt["height"],
            elt["r_frame_rate"],
            elt["codec_name"],
            elt["sample_aspect_ratio"].replace(":", "/"),
        )

    return 0, 0, 0, 0, 0


def create_input_item(file, probe, has_video):
    width, height, frame_rate, codec, sar = get_video_resolution(probe)
    return {
        "file": file,
        "has_video": has_video,
        "languages": {},
        "audio_count": 0,
        "width": width,
        "height": height,
        "frame_rate": frame_rate,
        "video_codec": codec,
        "sar": sar,
    }


def main():
    global quiet_output
    # Chemin du dossier contenant les fichiers d'entrée
    input_dir = "inputs"
    output_dir = "outputs"

    # lang_keys = "   ".join(languages.keys());
    lang_keys = " ".join('{0: <5}'.format(o["name"].replace('_', '-')) for o in languages.values())
    lang_channel = " ".join('{0: <5}'.format(o["channel"]) for o in languages.values())
    lang_count = " ".join('{0: <5}'.format(i) for i in range(1, 9))
    # lang_channel = "  ".join(o["channel"] for o in languages.values())
    
    parser = argparse.ArgumentParser(
        prog="ll_av_script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(f'''\
        Audio / Video Mixer
        --------------------
            Merge Audio and video file to one single file.
            Then create a Surround ({channel_layout}) track with all languages
            
            Layout
            ------
            {lang_count}
            {lang_keys}
            {lang_channel}
                    
        '''))    
    parser.add_argument("-v", "--verbose", help="Make output more verbose", action="store_false")
    parser.add_argument('--version', action='version', version=f"%(prog)s: {prog_version}")
    args = parser.parse_args()
    quiet_output = args.verbose
    
         
    # Parcourir le dossier d'entrée
    for file in os.listdir(input_dir):
        base_name, extension = os.path.splitext(file)
        input_files = []

        if extension == buddle_extensions or extension == video_extensions:
            # Extract basename + Language
            pattern = (
                "((_["
                + "".join(list(languages.keys()))
                + "])(?![0-9A-Za-z]))+"
            )
            matches = re.search(pattern, file)
            if matches:
                pos = matches.start()
                base_name = file[0:pos]

            probe = ffmpeg.probe(os.path.join(input_dir, file))
            input_files.append(
                create_input_item(os.path.join(input_dir, file), probe, True)
            )

            print_step(f"Process {input_files[0]['file']}")
            input_files[0]["languages"] = extract_language_tracks(
                input_files[0]["file"], probe
            )
            audio_duration = get_max_audio_duration(probe)
            video_duration = get_video_duration(probe)

            # Rechercher les fichiers audio manquants
            for language in languages:
                suffix = language
                if suffix != "E":
                    suffix = f"E_{suffix}"
                filename = f"{base_name}_{suffix}{audio_extensions}"
                input_file = os.path.join(input_dir, filename)

                if os.path.exists(input_file):
                    probe = ffmpeg.probe(input_file)
                    audio_duration = get_max_audio_duration(probe, audio_duration)
                    item = create_input_item(input_file, probe, False)
                    item["languages"][language] = {
                        "lang": language,
                        "audio_idx": 0,
                        "metadata_lang": languages[language]["lang"],
                        "metadata_title": suffix,
                        "join_chan": languages[language]["channel"],
                    }
                    print_addingg_file(f"Adding file {item['file']}")
                    input_files.append(item)
                    # Remove lang from the master file                    
                    if language in input_files[0]["languages"].keys():
                        del input_files[0]["languages"][language]

            extra_second = 0
            if video_duration < audio_duration:
                extra_second = audio_duration - video_duration

            # Construct output filename
            languages_in_ouput_file = []
            for item in input_files:
                languages_in_ouput_file += item["languages"].keys()

            output_base_file = os.path.join(output_dir, f"{base_name}")

            if len(languages_in_ouput_file) == 0:
                print_warning(
                    f"No language found: Specify languages in {input_files[0]['file']}.yml"
                )
                sys.exit(1)

            print_desc(f"\t Name: {base_name}")
            print_desc(f"\t Language: {' '.join(languages_in_ouput_file)}")
            print_desc(f"\t Video padding: {extra_second}s")
            
            extract_english = False
            if not "E" in languages_in_ouput_file:
                languages_in_ouput_file.insert(0, "E")
                extract_english = True

            # Créer un nouveau fichier vidéo avec les pistes audio et vidéo des fichiers d'entrée
            create_output_file(
                input_files,
                output_base_file,
                languages_in_ouput_file,
                extra_second,
                extract_english,
            )


def get_lang_metadata(input_files):
    """
    Create lang metadata
    """

    metadata_langs = {}
    for item in input_files:
        for language in item["languages"].values():
            metadata_langs[
                f"metadata:s:a:{len(metadata_langs)}"
            ] = f"language={language['metadata_lang']}"

    return metadata_langs


def get_title_metadata(input_files):
    """
    Create title metadata
    """

    metadata_titles = {}
    for item in input_files:
        for language in item["languages"].values():
            metadata_titles[
                f"metadata:s:a:{len(metadata_titles)}"
            ] = f"title='{language['metadata_title']}'"

    return metadata_titles


# end def


def get_surround_map(input_files, languages_in_ouput_file):
    """
    Purpose: arg
    """

    stream_offset = 0
    for item in input_files:
        stream_offset += len(item["languages"])

    surround_map = []
    # Add the surround map
    track_idx = stream_offset
    chan_idx = 0
    for language_key, lang in languages.items():
        if language_key not in languages_in_ouput_file:
            lang["track_idx"] = track_idx
            track_idx += 1
        surround_map.append(f'{chan_idx}.FR-{lang["channel"]}')
        chan_idx += 1

    return surround_map


# end def


def create_output_file_merge_files(
    input_files, output_file, extra_second, extract_english
):
    """
    Merge all input files to one video/audio file
    """

    streams = []
    stream_offset = 0

    for item in input_files:
        item["ffmpeg_input"] = ffmpeg.input(item["file"])
        # Add video track to the stream
        if item["has_video"]:
            if extra_second > 0:
                video_codec = item["video_codec"]
                streams.append(
                    ffmpeg.concat(
                        item["ffmpeg_input"]["v"],
                        ffmpeg.input(
                            f"color=c=black:s={item['width']}x{item['height']}:d={extra_second}:r={item['frame_rate']}:sar={item['sar']}",
                            f="lavfi",
                        ),
                    )
                )
            else:
                streams.append(item["ffmpeg_input"]["v"])

        #  Extract English track from the first audio track
        if len(item["languages"]) > 0 and extract_english:
            lang = next(iter(item["languages"]))
            print_substep(f"English track From {lang} Extracting...")
            streams.append(
                ffmpeg.filter(
                    (
                        item["ffmpeg_input"][
                            f'a:{item["languages"][lang]["audio_idx"]}'
                        ],
                    ),
                    "pan",
                    "stereo|c0=2*c0|c1=2*c0",
                )
            )
            languages["E"]["track_idx"] = 0
            stream_offset = 1
            extract_english = False
            input_files[0]["languages"]["E"] = {
                "lang": "E",
                "audio_idx": 0,
                "metadata_lang": languages["E"]["lang"],
                "metadata_title": "E",
                "join_chan": languages["E"]["channel"],
            }

        for language in item["languages"].values():
            streams.append(item["ffmpeg_input"][f'a:{language["audio_idx"]}'])
            track_idx = language["audio_idx"] + stream_offset
            languages[language["lang"]]["track_idx"] = track_idx
        stream_offset += len(item["languages"])

    print_substep(f"Video and Audio(s) Merging...")
    metadata_langs = get_lang_metadata(input_files)
    # 1 - Create one files with all audio tracks
    output_ffmpeg = ffmpeg.output(
        *streams,
        output_file,
        vcodec="libx264",
        acodec="aac",
        pix_fmt="yuv420p",
        **metadata_langs,
    )

    return ffmpeg_run(output_ffmpeg)


def create_output_file_create_surround_track(
    input_files, merged_file_tmp, output_file, languages_in_ouput_file
):
    """
    Purpose: one
    """
    # 2 - Create Sourrond track + title metadata
    print_substep(f"Surround track creating...")
    surround_map = get_surround_map(input_files, languages_in_ouput_file)
    metadata_titles = get_title_metadata(input_files)
    input_file = ffmpeg.input(merged_file_tmp)

    # Create empty track
    surround_streams = []
    for lang in languages.values():
        # No translation to export
        if lang["name"] not in languages_in_ouput_file:
            track = ffmpeg.input(
                "anullsrc=channel_layout=stereo:sample_rate=44100", f="lavfi"
            )
            surround_streams.append(track["a:0"])
        else:
            surround_streams.append(input_file[f"a:{lang['track_idx']}"])

    # Extract channel and join them
    surround_input = ffmpeg.filter_(
        (
            surround_streams[0],
            surround_streams[1],
            surround_streams[2],
            surround_streams[3],
            surround_streams[4],
            surround_streams[5],
            surround_streams[6],
            surround_streams[7],
        ),
        "join",
        inputs=f"{len(languages)}",
        channel_layout=channel_layout,
        map="|".join(surround_map),
    )
    # Create the final command
    output_ffmpeg = ffmpeg.output(
        input_file,
        surround_input,
        output_file,
        vcodec="copy",
        **{
            f"metadata:s:a:{len(metadata_titles)}": f"title='{'_'.join(languages_in_ouput_file)}'"
        },
        **metadata_titles,
    )

    return ffmpeg_run(output_ffmpeg)


# end def


def create_output_file_create_individual_language(
    input_filename, output_base_file, languages_in_ouput_file
):
    """
    Purpose: arg
    """
    # Create one mov file for each lang
    for lang in languages.values():
        # No translation to export
        if lang['name'] not in languages_in_ouput_file:
            continue

        # 2 - Create individual file
        print_substep(f"{lang['desc']} video generating...")

        input_file = ffmpeg.input(input_filename)
        suffix = lang["title"]
        output_single_file = f"{output_base_file}_{suffix}{output_extensions}"
        # Create the final command
        output_ffmpeg = ffmpeg.output(
            input_file.video,
            input_file[f"a:{lang['track_idx']}"],
            output_single_file,
            vcodec="copy",
            acodec="copy",
            **{f"metadata:s:a:0": f"title='{lang['title']}'",
            "disposition:a":  "+default",},
        )

        if not ffmpeg_run(output_ffmpeg):
            return False

    return True

    # end def

    """_summary_
    """


def create_output_file(
    input_files,
    output_base_file,
    languages_in_ouput_file,
    extra_second,
    extract_english,
):
    output_file = f"{output_base_file}_{'_'.join(languages_in_ouput_file)}_Su{output_extensions}"
    fd, output_file_tmp = tempfile.mkstemp(
        dir=os.path.dirname(output_file), suffix=output_extensions
    )

    if not create_output_file_merge_files(
        input_files, output_file_tmp, extra_second, extract_english
    ):
        os.remove(output_file_tmp)
        return False

    if not create_output_file_create_surround_track(
        input_files, output_file_tmp, output_file, languages_in_ouput_file
    ):
        os.remove(output_file_tmp)
        return False

    os.remove(output_file_tmp)
    create_output_file_create_individual_language(
        output_file, output_base_file, languages_in_ouput_file
    )


if __name__ == "__main__":
    main()

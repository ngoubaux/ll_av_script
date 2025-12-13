"""
Application constants and configuration
"""

# File extensions
BUDDLE_EXTENSIONS = ".mov"
VIDEO_EXTENSIONS = ".mp4"
AUDIO_EXTENSIONS = ".m4a"
OUTPUT_EXTENSIONS = ".mp4"
OUTPUT_AIF_EXTENSIONS = ".aif"

# Audio configuration
CHANNEL_LAYOUT = "7.1"

# Language definitions
# FFMPEG is using ISO 639-2 language table
# https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes
#
# Channel Layout
# http://underpop.online.fr/f/ffmpeg/help/channel-layout.htm.gz
# https://trac.ffmpeg.org/wiki/AudioChannelManipulation
LANGUAGES = {
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

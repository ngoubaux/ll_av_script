# Installation 
The script needs extra tools:
 mediainfo: brew install mediainfo
 ffmpeg: brew install ffmpeg" 
 realpath: brew install coreutils

# Run
Put all mov files into "inputs" folder
Run the script ./convert_mov_mutlichan_to60.sh

The modified mov file are going to be in 'outputs' folder with "_6.0" suffix.

# Configuration file 
Each mov file can have a config file (<filename>.cfg) with label or/and index of each audio tracks next to it.
When a track index is set to -1 or it is not present in the file, the English Channel is used.
So the output is always in 6.0.

If no English Channel the script exits.

Config file example: 
TRACK_ENGLISH="E"
TRACK_FRENCH="E-F"
TRACK_GERMAN="E-G"
TRACK_SPANISH="E-S"
TRACK_ITALIAN="E-I"
TRACK_CHINESE="E-C"

TRACK_ENGLISH_IDX=0
TRACK_FRENCH_IDX=1
TRACK_GERMAN_IDX=2
TRACK_SPANISH_IDX=3
TRACK_ITALIAN_IDX=4
TRACK_CHINESE_IDX=-1

The audio mapping used is 6.0 (Standard)
Better than using LFE for a classic audio voice

English: FL (Front Left)
French: FR (Front RIght)
German: FC (Front Center)
Spanish: SL (Left Surround)
Italian:  SR (Right Surround)
Chinese: BC (Back Center)

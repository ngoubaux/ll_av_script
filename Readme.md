# Installation 
Inside a terminal , execute this command.
/bin/bash -c "$(curl -fsSL https://bitbucket.org/goubsi/ll_av_script/raw/main/bootstrap.sh)"

This script will install:
homebrew
python3
pip3
git
ffmpeg
exiftool
Python modules

And fetch last version of the source in a new folder named ll_av_script if the bootstrap.sh script is not current from the ll_av_script folder.
If the bootstrap.sh is called from the ll_av_script it will update the current folder and update python module requirements.

# Usage 
Copy files into the folder inputs
Run the script ./ll_av_script.py
Get files from the folder outputs


# Today we have:
- Scenario1: edit video (mp4) with x audio files of translations (m4a)
- Scenario2: Adding x new translations (m4a) to an already produced video with y audiotracks of translations already on (without surround)
- Scenario3: Adding x new translations to an already produced video with y audiotracks of translations and a surround audio track already on)

# Changelog:
- Support Scenario 1 
- Support Scenario 2
- Support Scenario 3
- Add config file (aml) to indicate language of Audiotracks if there is no metadata
- Add metadata lang and title for each audio tracks
- Add silence audio channel when translation is missing
- Look in inputs folder for job
  - Can have several video files and audio to convert.
    One job by video file (.mov or .mp4)
- Store outputs in outputs folder 
   - One Video with surround track (xxx_6.0.mov)
   - One video for each language (E(_X).mov) - where x is the lang letter.

# Known bug:
For some ffmpeg reason, the surround channel ordre is not correct.
But at least you can test it.

# Input files
## Video inputs are:
- 20230701LN1030MJK_20231112AP.mp4 (Video only)
- 20230701LN1030MJK_20231112AP_E_F_G_S_I.mov (Without surround track)
- 20230701LN1030MJK_20231112AP_E_F_G_S_I_6.0.mov (With surround track)

## Audio inputs are:
- 20230701LN1030MJK_20231112AP_E.m4a (English only)
- 20230701LN1030MJK_20231112AP_E_<translation_letter>.m4a (English left and translation on right)
- 20230701LN1030MJK_20231112AP_E_F_G_S_I.mov (Without surround track)
- 20230701LN1030MJK_20231112AP_E_F_G_S_I_6.0.mov (With surround track)

## Config file: 
If audio track has no lang metadata, the script needs a configuration file (.yml) that describe each track:

For exemple: 
```
track_1: 
  lang: E
track_2: 
  lang: F
track_3: 
  lang: G
track_4:
  lang: S
track_5: 
  lang: I
```
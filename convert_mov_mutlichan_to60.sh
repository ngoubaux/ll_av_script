#!/bin/bash

command -v mediainfo >/dev/null 2>&1 || { 
	echo >&2 "WARNING: mediainfo is required but it's not installed."
	echo "$> brew install mediainfo"  
	echo "Aborting..."
	exit 1; 
}

command -v ffmpeg >/dev/null 2>&1 || { 
	echo >&2 "WARNING: ffmpeg is required but it's not installed."
	echo "$> brew install ffmpeg"  
	echo "Aborting..."
	exit 1; 
}

command -v realpath >/dev/null 2>&1 || { 
	echo >&2 "WARNING: realpath is required but it's not installed."
	echo "$> brew install coreutils"  
	echo "Aborting..."
	exit 1; 
}

#
# realpath on MacOS
# brew install coreutils
#
test -x /usr/bin/realpath || realpath () {
	f=$@;                                                                                                                                                                                     
	if [ -d "$f" ]; then                                                                                                                                                                      
		base="";                                                                                                                                                                              
		dir="$f";                                                                                                                                                                             
	else                                                                                                                                                                                      
		base="/$(basename "$f")";                                                                                                                                                             
		dir=$(dirname "$f");                                                                                                                                                                  
	fi;                                                                                                                                                                                       
	dir=$(cd "$dir" && /bin/pwd);                                                                                                                                                             
	echo "$dir$base"   
}

SCRIPT=$0
SCRIPT_PATH=$(dirname $(realpath $0))
ROOT_PATH=$(realpath $SCRIPT_PATH/..)
INPUTS_PATH=${SCRIPT_PATH}/inputs
OUTPUTS_PATH=${SCRIPT_PATH}/outputs

# Include Configuration file
. ${SCRIPT_PATH}/output_audio_mapping.cfg
. ${SCRIPT_PATH}/functions.inc

if [ ! -d "${INPUTS_PATH}" ]; then
  echo "use 'inputs' folder to put movie to convert"
  mkdir "${INPUTS_PATH}"
  exit 1;
fi

if [ ! -d "${OUTPUTS_PATH}" ]; then
  echo "Converted movies are stored in 'outputs' folder."
  mkdir "${OUTPUTS_PATH}"
fi

MOVFILES="$(ls ${INPUTS_PATH}/*.mov)"

for file in ${MOVFILES}; do
  process_movfile "${file}" "${OUTPUTS_PATH}"
done

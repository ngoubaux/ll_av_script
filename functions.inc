# FFMPEG is using ISO 639-2 language table
# https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes

dump_input_tracks() {
  echo -n "Input Tracks:"
  echo -n "  E:${TRACK_ENGLISH_IDX}"
  echo -n "  F:${TRACK_FRENCH_IDX}"
  echo -n "  G:${TRACK_GERMAN_IDX}"
  echo -n "  S:${TRACK_SPANISH_IDX}"
  echo -n "  I:${TRACK_ITALIAN_IDX}"
  echo -n "  C:${TRACK_CHINESE_IDX}"
  echo
}

process_movfile() {
  local file="$1"
  local out_folder="$2"
  local filename="$(basename $file)"
  local filebasename="${filename%%.*}"
  local extension="${filename##*.}"
  local track_count=0	
  local track_found_count=0
  local output_filename="${out_folder}/${filebasename}_6.0.${extension}"

  #mediainfo --Info-Parameters
  echo "Processing: ${filename}..."
  local TRACKS_INFO=$(mediainfo --Output='Audio;%AlternateGroup%:%ID%:%Title%:%ChannelLayout%\n'  ${file})
  local track_count=$( echo "${TRACKS_INFO}" | wc -l  )

  echo "${file}.cfg"
  if [ -f "${file}.cfg" ]; then
    . "${file}.cfg"
  fi

  # Get Track index for English (Default: Left)
  if [ "${TRACK_ENGLISH_IDX}" == "" ]; then
    TRACK_ENGLISH_IDX=$(( $(echo "${TRACKS_INFO}" | grep ":${TRACK_ENGLISH}:" | cut -d ':' -f 1) - 1))
    TRACK_FRENCH_IDX=$(( $(echo "${TRACKS_INFO}" | grep ":${TRACK_FRENCH}:" | cut -d ':' -f 1) - 1))
    TRACK_GERMAN_IDX=$(( $(echo "${TRACKS_INFO}" | grep ":${TRACK_GERMAN}:" | cut -d ':' -f 1) - 1))
    TRACK_SPANISH_IDX=$(( $(echo "${TRACKS_INFO}" | grep ":${TRACK_SPANISH}:" | cut -d ':' -f 1) - 1))
    TRACK_ITALIAN_IDX=$(( $(echo "${TRACKS_INFO}" | grep ":${TRACK_ITALIAN}:" | cut -d ':' -f 1) - 1))
    TRACK_CHINESE_IDX=$(( $(echo "${TRACKS_INFO}" | grep ":${TRACK_CHINESE}:" | cut -d ':' -f 1) - 1))
  fi
  dump_input_tracks

  [ "${TRACK_ENGLISH_IDX}" -gt "-1" ] && track_found_count=$(( ${track_found_count} + 1 ))
  [ "${TRACK_FRENCH_IDX}" -gt "-1" ] && track_found_count=$(( ${track_found_count} + 1 ))
  [ "${TRACK_GERMAN_IDX}" -gt "-1" ] && track_found_count=$(( ${track_found_count} + 1 ))
  [ "${TRACK_SPANISH_IDX}" -gt "-1" ] && track_found_count=$(( ${track_found_count} + 1 ))
  [ "${TRACK_ITALIAN_IDX}" -gt "-1" ] && track_found_count=$(( ${track_found_count} + 1 ))
  [ "${TRACK_CHINESE_IDX}" -gt "-1" ] && track_found_count=$(( ${track_found_count} + 1 ))

  ffmpeg_audio_count=0
  ffmpeg_audio_chan_idx=$(( 6 - ${track_found_count} ))
  ffmpeg_audio_missing_count=0
  ffmpeg_audio_in_chansplit=""
  ffmpeg_audio_in_join=""
  ffmpeg_audio_in_asplit=""
  ffmpeg_audio_out=""
  ffmpeg_video_opt="-vcodec copy"
  ffmpeg_md_opt=""
  chan6_title=""

  # Split each input audio stereo stream into one ouput mono channel and save it
  if [ "${TRACK_ENGLISH_IDX}" == "-1" ]; then
    echo "Error: English track not found: exit"
    exit 1
  fi
  ffmpeg_md_opt=" -metadata:s:a:${TRACK_ENGLISH_IDX} language=eng"
  ffmpeg_md_opt+=" -metadata:s:a:${TRACK_ENGLISH_IDX} title=E-E"
  TRACK_ENGLISH_IDX=$((${TRACK_ENGLISH_IDX} + ${ffmpeg_audio_chan_idx} ))  
  ffmpeg_audio_count=$(( ${ffmpeg_audio_count} + 1 ))
  ffmpeg_audio_in_join="${TRACK_ENGLISH_IDX}.0-${CHAN_ENGLISH_NAME}"
  ffmpeg_audio_out="[${CHAN_ENGLISH_NAME}]"
  chan6_title="E"
  
  if [ "${TRACK_FRENCH_IDX}" == "-1" ]; then
    echo "Warning: French track not found: Insert english channel."
    ffmpeg_audio_french_join="${ffmpeg_audio_missing_count}.0-${CHAN_FRENCH_NAME}"
    ffmpeg_audio_in_join="${ffmpeg_audio_in_join}|${ffmpeg_audio_french_join}"
    ffmpeg_audio_missing_count=$(( ${ffmpeg_audio_missing_count} + 1 ))
  else
    ffmpeg_md_opt+=" -metadata:s:a:${TRACK_FRENCH_IDX} language=fra"
    ffmpeg_md_opt+=" -metadata:s:a:${TRACK_FRENCH_IDX} title=E-F"
    chan6_title="${chan6_title}-F"
    TRACK_FRENCH_IDX=$((${TRACK_FRENCH_IDX} + ffmpeg_audio_chan_idx))
    ffmpeg_audio_count=$(( ${ffmpeg_audio_count} + 1 ))

    ffmpeg_audio_french_join="${TRACK_FRENCH_IDX}.1-${CHAN_FRENCH_NAME}"
    ffmpeg_audio_in_join="${ffmpeg_audio_in_join}|${ffmpeg_audio_french_join}"
  fi

  if [ "${TRACK_GERMAN_IDX}" == "-1" ]; then
    echo "Warning: German track not found: Insert english channel."
    ffmpeg_audio_german_join="${ffmpeg_audio_missing_count}.0-${CHAN_GERMAN_NAME}"
    ffmpeg_audio_in_join="${ffmpeg_audio_in_join}|${ffmpeg_audio_german_join}"
    ffmpeg_audio_missing_count=$(( ${ffmpeg_audio_missing_count} + 1 ))
  else 
    ffmpeg_md_opt+=" -metadata:s:a:${TRACK_GERMAN_IDX} language=gre"
    ffmpeg_md_opt+=" -metadata:s:a:${TRACK_GERMAN_IDX} title=E-G"
    chan6_title="${chan6_title}-G"
    TRACK_GERMAN_IDX=$((${TRACK_GERMAN_IDX} + ffmpeg_audio_chan_idx))
    ffmpeg_audio_count=$(( ${ffmpeg_audio_count} + 1 ))

    ffmpeg_audio_german_join="${TRACK_GERMAN_IDX}.1-${CHAN_GERMAN_NAME}"
    ffmpeg_audio_in_join="${ffmpeg_audio_in_join}|${ffmpeg_audio_german_join}"
  fi

  if [ "${TRACK_SPANISH_IDX}" == "-1" ]; then
    echo "Warning: Spanish track not found: Insert english channel."
    ffmpeg_audio_spanish_join="${ffmpeg_audio_missing_count}.0-${CHAN_SPANISH_NAME}"
    ffmpeg_audio_in_join="${ffmpeg_audio_in_join}|${ffmpeg_audio_spanish_join}"
    ffmpeg_audio_missing_count=$(( ${ffmpeg_audio_missing_count} + 1 ))
  else 
    ffmpeg_md_opt+=" -metadata:s:a:${TRACK_SPANISH_IDX} language=spa"
    ffmpeg_md_opt+=" -metadata:s:a:${TRACK_SPANISH_IDX} title=E-S"
    chan6_title="${chan6_title}-S"
    TRACK_SPANISH_IDX=$(( ${TRACK_SPANISH_IDX} + ffmpeg_audio_chan_idx))
    ffmpeg_audio_count=$(( ${ffmpeg_audio_count} + 1 ))

    ffmpeg_audio_spanish_join="${TRACK_SPANISH_IDX}.1-${CHAN_SPANISH_NAME}"
    ffmpeg_audio_in_join="${ffmpeg_audio_in_join}|${ffmpeg_audio_spanish_join}"
  fi

  if [ "${TRACK_ITALIAN_IDX}" == "-1" ]; then
    echo "Warning: Italian track not found: Insert english channel."
    ffmpeg_audio_italian_join="${ffmpeg_audio_missing_count}.0-${CHAN_ITALIAN_NAME}"
    ffmpeg_audio_in_join="${ffmpeg_audio_in_join}|${ffmpeg_audio_italian_join}"
    ffmpeg_audio_missing_count=$(( ${ffmpeg_audio_missing_count} + 1 ))
  else 
    ffmpeg_md_opt+=" -metadata:s:a:${TRACK_ITALIAN_IDX} language=ita"
    ffmpeg_md_opt+=" -metadata:s:a:${TRACK_ITALIAN_IDX} title=E-I"
    chan6_title="${chan6_title}-I"
    TRACK_ITALIAN_IDX=$(( ${TRACK_ITALIAN_IDX} + ffmpeg_audio_chan_idx))
    ffmpeg_audio_count=$(( ${ffmpeg_audio_count} + 1 ))

    ffmpeg_audio_italian_join="${TRACK_ITALIAN_IDX}.1-${CHAN_ITALIAN_NAME}"
    ffmpeg_audio_in_join="${ffmpeg_audio_in_join}|${ffmpeg_audio_italian_join}"
  fi

  if [ "${TRACK_CHINESE_IDX}" == "-1" ]; then
    echo "Warning: Chinese track not found: Insert english channel."
    ffmpeg_audio_chinese_join="${ffmpeg_audio_missing_count}.0-${CHAN_CHINESE_NAME}"
    ffmpeg_audio_in_join="${ffmpeg_audio_in_join}|${ffmpeg_audio_chinese_join}"
    ffmpeg_audio_missing_count=$(( ${ffmpeg_audio_missing_count} + 1 ))
  else 
    ffmpeg_md_opt+=" -metadata:s:a:${TRACK_CHINESE_IDX} language=chi"
    ffmpeg_md_opt+=" -metadata:s:a:${TRACK_CHINESE_IDX} title=E-C"
    chan6_title="${chan6_title}-C"
    TRACK_CHINESE_IDX=$(( ${TRACK_CHINESE_IDX} + ffmpeg_audio_chan_idx))
    ffmpeg_audio_count=$(( ${ffmpeg_audio_count} + 1 ))

    ffmpeg_audio_chinese_join="${TRACK_CHINESE_IDX}.1-${CHAN_CHINESE_NAME}"
    ffmpeg_audio_in_join="${ffmpeg_audio_in_join}|${ffmpeg_audio_chinese_join}"
  fi
  
  ffmpeg_md_opt="${ffmpeg_md_opt} -metadata:s:a:${ffmpeg_audio_count} title=${chan6_title}"

  ffmpeg_audio_out=""
  if [ "${ffmpeg_audio_missing_count}" -gt 0 ]; then
    for nb in `seq 1 ${ffmpeg_audio_missing_count}`; do
      ffmpeg_audio_out="${ffmpeg_audio_out}[0:a:0]"
    done
    ffmpeg_audio_out="${ffmpeg_audio_out}[0:a]"
    ffmpeg_audio_count=6
  fi
  
  local input_stream_count=$(( ${track_count} + ${ffmpeg_audio_missing_count} ))

  ffmpeg_audio_out="${ffmpeg_audio_out}join=inputs=${input_stream_count}:channel_layout=${ffmpeg_audio_count}.0:map=${ffmpeg_audio_in_join}[ch6]" 
  ffmpeg_audio_opt="${ffmpeg_audio_in};${ffmpeg_audio_out}"
  ffmpeg_audio_opt="${ffmpeg_audio_out}"
    
  ffmpeg  -hide_banner -loglevel error -i "${file}" -filter_complex "${ffmpeg_audio_opt}" ${ffmpeg_video_opt} ${ffmpeg_md_opt} -map 0 -map "[ch6]" "${output_filename}"
}
import json
import ffmpeg
import re
import os
import yaml
import tempfile

# Liste des langues
languages = {
    'E' : { 'name':'E', 'lang': 'eng', 'title' : 'E',   'channel': 'FL'},
    'F' : { 'name':'F', 'lang': 'fra', 'title' : 'E_F', 'channel': 'FR'},
    'G' : { 'name':'G', 'lang': 'gre', 'title' : 'E_G', 'channel': 'FC'},
    'S' : { 'name':'S', 'lang': 'spa', 'title' : 'E_S', 'channel': 'SL'}, 
    'I' : { 'name':'I', 'lang': 'ita', 'title' : 'E_I', 'channel': 'SR'},
    'C' : { 'name':'C', 'lang': 'chi', 'title' : 'E_C', 'channel': 'BC'},
}

def search_lang_by_md(lang_md):
    for lang in languages:
        if languages[lang]['lang'] == lang_md:
            return lang
        
    return ""

def extract_language_tracks(file, probe):
    # Open Config file if present
    yml         = None 
    yml_path    = f"{file}.yml"
    if os.path.isfile(yml_path):
        if stream := open(yml_path):
            yml = yaml.safe_load(stream);
    
    language_tracks = {}
    audio_idx       = 0
    for elt in probe["streams"]:
        lang = ""

        # Get Track language with Metadata
        if elt['codec_type'] != 'audio':
            continue

        if 'language' in elt['tags']:
            md_lang = elt["tags"]['language']
            lang = search_lang_by_md(md_lang)

        # Get Track language with Yml file
        if lang == "" and yml and yml[f'track_{audio_idx+1}'] and yml[f'track_{audio_idx+1}']['lang']: 
            lang = yml[f'track_{audio_idx+1}']['lang']
            md_lang =  languages[lang]['lang']

        if lang != "":
            language_tracks[lang] = {
                'lang' : lang,
                'audio_idx' : audio_idx,
                'metadata_lang': md_lang,
                'metadata_title': languages[lang]['title'],
                'join_chan' : languages[lang]['channel']
            }
        else:
            print (f"Audio track_{audio_idx} is skipt") 
        
        audio_idx+=1

    return language_tracks

def get_audio_count(probe):
    audio_idx       = 0
    for elt in probe["streams"]:
    
        # Get Track language with Metadata
        if elt['codec_type'] != 'audio':
            continue 
        audio_idx+=1

    return audio_idx

def create_input_item(file, probe, has_video):
    return {
                'file': file,
                'has_video': has_video,
                'languages': {},
                'audio_count': get_audio_count(probe)
            }
    
def main():
    # Chemin du dossier contenant les fichiers d'entrée
    input_dir = "inputs"
    output_dir = "outputs"

    # Liste des extensions de fichiers vidéo et audio
    buddle_extensions   = ".mov"
    video_extensions    = ".mp4"
    audio_extensions    = ".m4a"

    # Parcourir le dossier d'entrée
    for file in os.listdir(input_dir):
        base_name, extension = os.path.splitext(file)
        languages_in_file   = []
        languages_missing   = []
        input_files         = []

        if extension == buddle_extensions:
            # Extract basename + Language
            pattern = "(\w*?)((_["+"".join(list(languages.keys()))+"])+).mov"
            matches   = re.match(pattern, file)
            if not matches:
                return
            base_name = matches.group(1)
            probe = ffmpeg.probe(os.path.join(input_dir, file))
            input_files.append(create_input_item(
                os.path.join(input_dir, file),
                probe,
                True
            ));

            print(f"Process file {input_files[0]['file']}")
            input_files[0]['languages'] = extract_language_tracks(input_files[0]['file'], probe)
            
            # Rechercher les fichiers audio manquants
            for language in languages:
                if language not in input_files[0]['languages'].keys():
                    suffix = language
                    if suffix != 'E':
                        suffix = f"E_{suffix}" 
                    filename = f"{base_name}_{suffix}.m4a"
                    input_file = os.path.join(input_dir, filename)

                    if os.path.exists(input_file):
                        probe = ffmpeg.probe(input_file)
                        item = create_input_item(input_file, probe, False) 
                        item['languages'][language] = {
                            'lang' : language,
                            'audio_idx' : 0,
                            'metadata_lang': languages[language]['lang'],
                            'metadata_title': suffix,
                            'join_chan' : languages[language]['channel']
                        }
                        print(f"\t Add file {item['file']}")
                        languages_missing.append(language)
                        input_files.append(item) 

            # Construct output filename
            languages_in_ouput_file = []
            for item in input_files:
                languages_in_ouput_file += item['languages'].keys()

            output_file = os.path.join(output_dir, f"{base_name}_{'_'.join(languages_in_ouput_file)}_6.0.mov")
            # Créer un nouveau fichier vidéo avec les pistes audio et vidéo des fichiers d'entrée
            create_output_file(
                input_files,
                output_file,
                languages_in_ouput_file,
            )


def create_output_file(
    input_files,
    output_file,
    languages_in_ouput_file):

    fd, output_file_tmp = tempfile.mkstemp(dir=os.path.dirname(output_file), suffix = '.mov')
    fd, output_file_60_tmp = tempfile.mkstemp(dir=os.path.dirname(output_file), suffix = '.mov')
    # Load all input files 
    # Add Video & Audio Stream 
    # Create metadata
    streams = []
    metadatas_lang = {}
    surround_map = []
    metadatas_title = {}
    stream_offset = 0
    for item in input_files:
        item['ffmpeg_input'] = ffmpeg.input(item['file'])
        if item['has_video']:
            streams.append(item['ffmpeg_input']['v'])
        for language in item['languages'].values():
            streams.append(item['ffmpeg_input'][f'a:{language["audio_idx"]}'])
            metadatas_lang[f'metadata:s:a:{len(metadatas_lang)}'] = f"language={language['metadata_lang']}"
            metadatas_title[f'metadata:s:a:{len(metadatas_title)}'] = f"title='{language['metadata_title']}'"
            surround_map.append(f'{language["audio_idx"]+stream_offset}.1-{language["join_chan"]}')
        stream_offset += item['audio_count']

    # '[0:a:0][0:a]join=inputs=6:channel_layout=6.0:map=1.0-FL|2.1-FR|3.1-FC|4.1-SL|5.1-SR|0.0-BC[ch6]' 
    #stream6_0 = ffmpeg.filter_(*surround_stream, 'join', inputs='6', channel_layout='6.0', map='|'.join(surround_map)+"[ch6]")
    # 1 - Create one files with all audio tracks
    output_ffmpeg = ffmpeg.output(*streams, output_file_tmp, vcodec='copy', acodec='copy', **metadatas_lang)
    output_ffmpeg = ffmpeg.overwrite_output(output_ffmpeg)
    print(output_ffmpeg.get_args())

    print(ffmpeg.compile(output_ffmpeg))
    ffmpeg.run(
        output_ffmpeg,
        quiet=True
    )

    # 2 - Set Audio track title metadata
    input = ffmpeg.input(output_file_tmp)
    output_ffmpeg = ffmpeg.output(
        input['v'], 
        input['a'], 
        output_file_60_tmp, 
        vcodec='copy', 
        acodec='copy', 
        **metadatas_title
    )
    output_ffmpeg = ffmpeg.overwrite_output(output_ffmpeg)
    print(output_ffmpeg.get_args())
    ffmpeg.run(
        output_ffmpeg,
        quiet=True
    )
    os.remove(output_file_tmp)

    # 3 - Create Sourrond track
    input_file = ffmpeg.input(output_file_60_tmp)
    surround_input = input_file.audio.filter(
        'join', 
        inputs='6', 
        channel_layout='6.0', 
        map='|'.join(surround_map)
    )
    output_ffmpeg = ffmpeg.output(
        input_file,
        surround_input,
        output_file,
        vcodec='copy', 
         **{f'metadata:s:a:{len(metadatas_title)}': f"title='{'_'.join(languages_in_ouput_file)}'"},
    )

    # Write the output video
    output_ffmpeg = ffmpeg.overwrite_output(output_ffmpeg)
    print(output_ffmpeg.get_args())
    output_ffmpeg.run(
        quiet=True
    )
    os.remove(output_file_60_tmp)

    #probe = ffmpeg.probe(output_file)
    #print(json.dumps(probe,indent=2))



if __name__ == "__main__":
    main()
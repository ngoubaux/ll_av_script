import json
import ffmpeg
import re
import os
import yaml
import tempfile

# Liste des langues
languages = {
    'E' : { 'lang': 'eng', 'title' : 'E'},
    'F' : { 'lang': 'fra', 'title' : 'E_F'},
    'G' : { 'lang': 'gre', 'title' : 'E_G'},
    'S' : { 'lang': 'spa', 'title' : 'E_S'}, 
    'I' : { 'lang': 'ita', 'title' : 'E_I'},
    'C' : { 'lang': 'chi', 'title' : 'E_C'},
}

def search_lang_by_md(lang_md):
    for lang in languages:
        if languages[lang]['lang'] == lang_md:
            return lang
        
    return ""

def extract_language_tracks(file):
    # Open Config file if present
    yml         = None 
    yml_path    = f"{file}.yml"
    if os.path.isfile(yml_path):
        if stream := open(yml_path):
            yml = yaml.safe_load(stream);
    
    probe           = ffmpeg.probe(file)
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
            }
        else:
            print (f"Audio track_{audio_idx} is skipt") 
        
        audio_idx+=1

    return language_tracks

def create_input_item(file, has_video):
    return {
                'file': file,
                'has_video': has_video,
                'languages': {}
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

            input_files.append(create_input_item(
                os.path.join(input_dir, file),
                True
            ));
            input_files[0]['languages'] = extract_language_tracks(input_files[0]['file']);

            # Rechercher les fichiers audio manquants
            for language in languages:
                if language not in input_files[0]['languages'].keys():
                    suffix = language
                    if suffix != 'E':
                        suffix = f"E_{suffix}" 
                    filename = f"{base_name}_{suffix}.m4a"
                    input_file = os.path.join(input_dir, filename)

                    if os.path.exists(input_file):
                        item = create_input_item(input_file, False) 
                        item['languages'][language] = {
                            'lang' : language,
                            'audio_idx' : 0,
                            'metadata_lang': languages[language]['lang'],
                            'metadata_title': suffix
                        }
                        
                        languages_missing.append(language)
                        input_files.append(item) 

            # Construct output filename
            languages_in_ouput_file = []
            for item in input_files:
                languages_in_ouput_file += item['languages'].keys()

            output_file = os.path.join(output_dir, f"{base_name}_{'_'.join(languages_in_ouput_file)}.mov")
            # Créer un nouveau fichier vidéo avec les pistes audio et vidéo des fichiers d'entrée
            create_output_file(
                input_files,
                output_file
            )


def create_output_file(
    input_files,
    output_file ):

    fd, output_file_tmp = tempfile.mkstemp(dir=os.path.dirname(output_file), suffix = '.mov')
    # Load all input files 
    # Add Video & Audio Stream 
    # Create metadata
    streams = []
    metadatas_lang = {}
    metadatas_title = {}
    for item in input_files:
        item['ffmpeg_input'] = ffmpeg.input(item['file'])
        if item['has_video']:
            streams.append(item['ffmpeg_input']['v'])
        for language in item['languages'].values():
            streams.append(item['ffmpeg_input'][f'a:{language["audio_idx"]}'])        
            metadatas_lang[f'metadata:s:a:{len(metadatas_lang)}'] = f"language={language['metadata_lang']}"
            metadatas_title[f'metadata:s:a:{len(metadatas_title)}'] = f"title='{language['metadata_title']}'"
    
    output_ffmpeg = ffmpeg.output(*streams, output_file_tmp, vcodec='copy', acodec='copy', **metadatas_lang)
    output_ffmpeg = ffmpeg.overwrite_output(output_ffmpeg)
    print(output_ffmpeg.get_args())

    print(ffmpeg.compile(output_ffmpeg))
    ffmpeg.run(output_ffmpeg)

    # Second round: Set Audio track title metadata
    input = ffmpeg.input(output_file_tmp)
    output_ffmpeg = ffmpeg.output(input['v'], input['a'], output_file, vcodec='copy', acodec='copy', **metadatas_title)
    output_ffmpeg = ffmpeg.overwrite_output(output_ffmpeg)
    print(output_ffmpeg.get_args())
    ffmpeg.run(output_ffmpeg)
    os.remove(output_file_tmp)

    probe = ffmpeg.probe(output_file)
    print(json.dumps(probe,indent=2))

    # Créer un objet `AVFormatContext` pour le fichier audio surround
    # if len(languages_in_file) + len(languages_missing) < len(languages):
    #     null_input = ffmpeg.input('anullsrc=r=44100:cl=stereo', f='lavfi')
    #     out_format_context.add_stream(null_input)

    # Ajouter les pistes audio stéréo du fichier vidéo d'entrée
    # for language in languages_in_file:
    #     # Extraire le canal droit de la piste audio stéréo
    #     audio_stream = in_format_context.streams[f"{language}_L"]
    #     audio_data = audio_stream.decode().audio
    #     audio_data = audio_data[:, 1]

    #     # Ajouter la piste audio à la sortie
    #     out_format_context.add_stream(
    #         ffmpeg.input(audio_data, format="s16le", channels=1)
    #     )

    # # Ajouter les pistes audio mono des fichiers audio manquants
    # for language in languages_missing:
    #     # Charger le fichier audio mono
    #     audio_stream = ffmpeg.input(
    #         os.path.join(input_dir, f"{base_name}_{language}.m4a")
    #     )

    #     # Ajouter la piste audio à la sortie
    #     out_format_context.add_stream(audio_stream)

    # Créer le fichier de sortie
    # ffmpeg.output(out_format_context.streams, out_format_context.filename)


if __name__ == "__main__":
    main()
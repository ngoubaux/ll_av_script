import json
import ffmpeg
import re
import os
import yaml

# Liste des langues
languages = {
    'E' : 'eng', 
    'F': 'fra', 
    'G': 'gre', 
    'S': 'spa', 
    'I': 'ita',
    'C': 'chi'
}

def extract_language_tracks(file):
    # Open Config file if present
    yml         = None 
    yml_path    = f"{file}.yml"
    if os.path.isfile(yml_path):
        if stream := open(yml_path):
            yml = yaml.safe_load(stream);
    
    probe           = ffmpeg.probe(file)
    language_tracks = {}
    audio_idx       = 1
    for elt in probe["streams"]:
        lang = ""

        # Get Track language with Metadata
        if elt['codec_type'] != 'audio':
            continue

        if 'language' in elt['tags']:
            md_lang = elt["tags"]['language']
            if (lang_ix := languages.items.index(md_lang)):
                lang = languages.keys()[lang_ix];
        
        # Get Track language with Yml file
        if lang == "" and yml and yml[f'track_{audio_idx}'] and yml[f'track_{audio_idx}']['lang']: 
            lang = yml[f'track_{audio_idx}']['lang']
            md_lang =  languages[lang]

        if lang != "":
            language_tracks[lang] = {
                'lang' : lang,
                'audio_idx' : audio_idx,
                'metadata_lang': md_lang
            }
        else:
            print (f"Audio track_{audio_idx} is skipt") 
        
        audio_idx+=1

    return language_tracks


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

        item = {
            'file': os.path.join(input_dir, file),
            'languages': []
        }
        input_files.append( item);
        
        if extension == buddle_extensions:
            # Extraire les langues du suffixe
            pattern = "(\w*?)((_["+"".join(list(languages.keys()))+"])+).mov"
            matches   = re.match(pattern, file)
            if not matches:
                continue
            
            input_files[0]['languages'] = extract_language_tracks(input_files[0]['file']);
            base_name = matches.group(1)
            languages_in_file = matches.group(2).split("_")
            languages_in_file.pop(0)
            for lang in languages_in_file:
                languages[lang] = 1

            # Rechercher les fichiers audio manquants
            for language in languages.keys():
                if language not in languages_in_file:
                    suffix = language
                    if suffix != 'E':
                        suffix = f"E_{suffix}" 
                    filename = f"{base_name}_{suffix}.m4a"
                    input_file = os.path.join(input_dir, filename)
                    if os.path.exists(input_file):
                        languages_missing.append(language)
                        input_files.append(input_file)
                        languages[language] = len(input_files)

            languages_in_ouput_file = [language for language in languages if language not in languages_in_file or language not in languages_missing]
            output_file = os.path.join(output_dir, f"{base_name}_{'_'.join(languages_in_ouput_file)}.mov")
            # Créer un nouveau fichier vidéo avec les pistes audio et vidéo des fichiers d'entrée
            create_output_file(
                input_files,
                output_file,
                languages_in_file,
                languages_missing,
            )


def create_output_file(
    input_files,
    output_file,
    languages_in_file,
    languages_missing,
):
    # Load all input files
    inputs = []
    for input_file in input_files:
        inputs.append(ffmpeg.input(input_file))

    # Select and ordre video and audio
    streams = []
    streams.append(inputs[0]['v'])
    streams.append(inputs[0]['a:2'])
    
    metadatas = {}
    metadatas['metadata:s:a:0'] = "language=eng"

    
    output_ffmpeg = ffmpeg.output(*streams, output_file, vcodec='copy', acodec='copy', **metadatas)
    output_ffmpeg = ffmpeg.overwrite_output(output_ffmpeg)
    print(output_ffmpeg.get_args())

    print(ffmpeg.compile(output_ffmpeg))
    ffmpeg.run(output_ffmpeg)
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
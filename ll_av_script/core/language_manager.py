"""
Language and metadata management
"""

import os
import re
from typing import Dict, Optional
import yaml
import exiftool

from ..core.constants import LANGUAGES
from ..core.models import Language
from ..utils.output import print_warning


class LanguageManager:
    """Manages language detection and metadata for audio tracks"""

    def __init__(self, no_interact: bool = False):
        self.no_interact = no_interact
        self.languages = LANGUAGES.copy()

    def search_lang_by_md(self, lang_md: str) -> str:
        """Search language by metadata language code"""
        for lang in self.languages:
            if self.languages[lang]["lang"] == lang_md:
                return lang
        return ""

    def search_lang_by_title(self, lang_title: str) -> str:
        """Search language by title"""
        for lang in self.languages:
            title = re.sub("[_-]", "", self.languages[lang]["title"])
            lang_title_clean = re.sub("[_-]", "", lang_title)
            if title == lang_title_clean:
                return lang
        return ""

    def create_language_entry(self, lang: str, audio_idx: int, md_lang: str) -> Language:
        """Create a Language object"""
        return Language(
            lang=lang,
            audio_idx=audio_idx,
            metadata_lang=md_lang,
            metadata_title=self.languages[lang]["title"],
            join_chan=self.languages[lang]["channel"],
        )

    def extract_language_tracks(self, file: str, probe: dict) -> Dict[str, Language]:
        """Extract language tracks from media file"""
        yml = self._load_yaml_config(file)
        metadata = self._get_file_metadata(file)

        language_tracks = {}
        audio_idx = 0

        for elt in probe["streams"]:
            if not self._is_valid_audio_stream(elt):
                if elt["codec_type"] == "audio":
                    print_warning(f"Audio track_{elt['index']} is not stereo")
                continue

            # Skip 7.1 tracks
            if elt["channels"] == 8:
                continue

            lang, md_lang = self._detect_language(
                elt, audio_idx, yml, metadata
            )

            if lang:
                language_tracks[lang] = self.create_language_entry(lang, audio_idx, md_lang)
            else:
                self._handle_unknown_language(
                    file, audio_idx, elt, yml, language_tracks
                )

            audio_idx += 1

        return language_tracks

    def _load_yaml_config(self, file: str) -> Optional[dict]:
        """Load YAML configuration if present"""
        yml_path = f"{file}.yml"
        try:
            if os.path.isfile(yml_path):
                with open(yml_path) as stream:
                    return yaml.safe_load(stream)
        except yaml.YAMLError:
            print_warning(f"Error while parsing YAML file: {yml_path}")
        return None

    def _get_file_metadata(self, file: str) -> dict:
        """Get file metadata using exiftool"""
        with exiftool.ExifToolHelper() as et:
            return et.get_metadata(file)[0]

    def _is_valid_audio_stream(self, stream: dict) -> bool:
        """Check if stream is valid audio"""
        return stream["codec_type"] == "audio" and stream.get("channels", 0) >= 2

    def _detect_language(
        self, stream: dict, audio_idx: int, yml: Optional[dict], metadata: dict
    ) -> tuple:
        """Detect language from various sources"""
        lang = ""
        md_lang = ""

        # Check YAML config first
        if yml and f"track_{audio_idx + 1}" in yml:
            track_config = yml[f"track_{audio_idx + 1}"]
            if track_config and track_config.get("lang"):
                lang = track_config["lang"]
                md_lang = self.languages[lang]["lang"]
                return lang, md_lang

        # Check QuickTime metadata
        title_key = f"QuickTime:Track{stream['index'] + 1}Name"
        if title_key in metadata:
            key_name = metadata[title_key].replace("'", "")
            lang = self.search_lang_by_title(key_name)
            if lang:
                md_lang = self.languages[lang]["lang"]
                return lang, md_lang

        # Check stream tags
        if "language" in stream.get("tags", {}):
            md_lang = stream["tags"]["language"]
            lang = self.search_lang_by_md(md_lang)
            if lang:
                return lang, md_lang

        return "", md_lang

    def _handle_unknown_language(
        self, file: str, audio_idx: int, stream: dict, yml: Optional[dict],
        language_tracks: Dict[str, Language]
    ) -> None:
        """Handle audio tracks with unknown language"""
        md_lang = stream.get("tags", {}).get("language", "")
        key_name = ""

        print_warning(f"No mapped language found for Audio track_{audio_idx + 1}")
        print_warning("   => Please add either a tag, a QuickTime setting or yml config file")
        print_warning(f"   => current tag: {md_lang}")
        print_warning(f"   => current QuickTime desc: {key_name}")

        if not self.no_interact:
            lang = self._prompt_for_language()
            if lang:
                self._save_language_to_yaml(file, audio_idx, lang, md_lang, key_name)
                md_lang = self.languages[lang]["lang"]
                language_tracks[lang] = self.create_language_entry(lang, audio_idx, md_lang)

    def _prompt_for_language(self) -> Optional[str]:
        """Prompt user to select language"""
        choice_lang = [s for s in self.languages.keys() if s not in ["-", "$"]]
        while True:
            ask = input(f"Fix the audio track language? ({','.join(choice_lang)}/n)\n")
            if ask.upper() in choice_lang or ask.lower() == "n":
                break

        return ask.upper() if ask.lower() != "n" else None

    def _save_language_to_yaml(
        self, file: str, audio_idx: int, lang: str, md_lang: str, key_name: str
    ) -> None:
        """Save language mapping to YAML file"""
        yml_path = f"{file}.yml"
        with open(yml_path, "a") as yml_file:
            yml_file.write(
                f"\n# tag: {md_lang}, QuickTime desc: {key_name}\n"
                f"track_{audio_idx + 1}:\n  lang: {lang}"
            )

    def get_metadata_langs(self, input_files: list) -> dict:
        """Create language metadata for FFmpeg"""
        metadata_langs = {}
        for item in input_files:
            for language in item.languages.values():
                metadata_langs[f"metadata:s:a:{len(metadata_langs)}"] = (
                    f"language={language.metadata_lang}"
                )
        return metadata_langs

    def get_metadata_titles(self, input_files: list) -> dict:
        """Create title metadata for FFmpeg"""
        metadata_titles = {}
        for item in input_files:
            for language in item.languages.values():
                metadata_titles[f"metadata:s:a:{len(metadata_titles)}"] = (
                    f"title='{language.metadata_title}'"
                )
        return metadata_titles

    def get_surround_map(self, input_files: list, languages_in_output: list) -> list:
        """Generate surround sound channel mapping"""
        stream_offset = sum(len(item.languages) for item in input_files)

        surround_map = []
        track_idx = stream_offset
        chan_idx = 0

        for language_key, lang in self.languages.items():
            if language_key not in languages_in_output:
                lang["track_idx"] = track_idx
                track_idx += 1
            surround_map.append(f'{chan_idx}.FR-{lang["channel"]}')
            chan_idx += 1

        return surround_map

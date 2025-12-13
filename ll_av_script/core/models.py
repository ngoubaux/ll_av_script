"""
Data models for the application
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Language:
    """Represents a language track"""
    lang: str
    audio_idx: int
    metadata_lang: str
    metadata_title: str
    join_chan: str


@dataclass
class InputFile:
    """Represents an input media file"""
    file: str
    has_video: bool
    languages: Dict[str, Language] = field(default_factory=dict)
    audio_count: int = 0
    width: int = 0
    height: int = 0
    frame_rate: str = "0"
    video_codec: str = ""
    sar: str = "0"
    ffmpeg_input: Optional[object] = None


@dataclass
class ProcessingConfig:
    """Configuration for media processing"""
    quiet_output: bool = True
    streamable: bool = False
    extract_aif: bool = False
    extract_m4a: bool = False
    only_audio: bool = False
    only_explode: bool = False
    no_interact: bool = False
    output_dir: str = "outputs"
    input_dir: str = "inputs"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    filename: Optional[str] = None
    edit_segments: Optional[List[str]] = None

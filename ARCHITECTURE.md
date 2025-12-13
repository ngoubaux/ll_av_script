# ll_av_script - Refactored Application

A modular Python application for audio/video processing and mixing with support for multiple languages and surround sound.

## Architecture

The application has been refactored into a modular structure:

```
ll_av_script/
├── __init__.py              # Package initialization
├── core/                    # Core models and configuration
│   ├── __init__.py
│   ├── constants.py         # Application constants
│   ├── models.py            # Data models (Language, InputFile, ProcessingConfig)
│   └── language_manager.py  # Language detection and metadata management
├── processors/              # Media processing modules
│   ├── __init__.py
│   ├── audio_processor.py   # Audio-specific operations
│   ├── video_processor.py   # Video-specific operations
│   ├── merger.py            # Media merging operations
│   └── file_analyzer.py     # File analysis utilities
├── utils/                   # Utility modules
│   ├── __init__.py
│   ├── output.py            # Console output formatting
│   ├── ffmpeg_wrapper.py    # FFmpeg command wrapper
│   └── time_utils.py        # Time conversion utilities
└── cli/                     # Command-line interface
    ├── __init__.py
    ├── parser.py            # Argument parser
    └── app.py               # Main application class
```

## Benefits of Refactoring

### 1. **Modularity**
- Each module has a single, well-defined responsibility
- Easy to test individual components
- Easier to understand and maintain

### 2. **Flexibility**
- Components can be used independently
- Easy to extend with new features
- Can create custom workflows by combining processors

### 3. **Testability**
- Each module can be unit tested separately
- Dependencies can be mocked easily
- Better code coverage

### 4. **Reusability**
- Processors can be reused in different contexts
- Core models can be imported and used by other tools
- Language manager can be used independently

### 5. **Maintainability**
- Changes are localized to specific modules
- Clear separation of concerns
- Better code organization

## Installation

### Development Installation

```bash
pip install -e .
```

### Production Installation

```bash
pip install .
```

## Usage

### Command Line

The refactored script maintains the same CLI interface:

```bash
./ll_av_script.py -f files/SF9_3_20070508PA1110SR_E_F_G_S_I.mov -m4a
```

### Programmatic Usage

You can now use the modules programmatically:

```python
from ll_av_script.core.models import ProcessingConfig
from ll_av_script.cli import Application

# Create configuration
config = ProcessingConfig(
    quiet_output=False,
    extract_m4a=True,
    filename="input.mov"
)

# Run application
app = Application(config)
result = app.run()
```

### Custom Workflows

Create custom workflows using individual processors:

```python
from ll_av_script.utils.ffmpeg_wrapper import FFmpegWrapper
from ll_av_script.processors import AudioProcessor, VideoProcessor

# Initialize components
ffmpeg = FFmpegWrapper(quiet=True)
audio_proc = AudioProcessor(ffmpeg)
video_proc = VideoProcessor(ffmpeg)

# Use processors
video_proc.cut_video("input.mp4", "output.mp4", "00:00:10", "00:01:00")
audio_proc.create_individual_m4a_files("input.mov", "output_base", ["E", "F", "G"])
```

## Module Details

### Core Modules

- **models.py**: Data classes for Language, InputFile, and ProcessingConfig
- **constants.py**: Application-wide constants (file extensions, channel layouts, language definitions)
- **language_manager.py**: Handles language detection, metadata extraction, and YAML config management

### Processor Modules

- **audio_processor.py**: Audio extraction (AIF, M4A), English track extraction
- **video_processor.py**: Video cutting, padding, individual language video creation
- **merger.py**: Orchestrates the complete workflow, merges audio/video, creates surround tracks
- **file_analyzer.py**: Analyzes media files, extracts metadata, finds related files

### Utility Modules

- **ffmpeg_wrapper.py**: Simplified FFmpeg command execution
- **output.py**: Colored console output
- **time_utils.py**: Time format conversion

### CLI Modules

- **parser.py**: Command-line argument parsing
- **app.py**: Main application orchestration

## Migration from Old Script

The old monolithic script (`ll_av_script-env.py`) has been preserved for reference. The new modular version provides:

1. **Same functionality** - All features have been migrated
2. **Better error handling** - More specific error messages
3. **Improved code organization** - Easier to understand
4. **Extensibility** - Easy to add new features

## Testing

The modular structure enables comprehensive testing:

```python
# Example test
from ll_av_script.utils.time_utils import get_sec

def test_time_conversion():
    assert get_sec("00:01:30") == 90
    assert get_sec("01:00:00") == 3600
```

## Contributing

With the new modular structure, contributions are easier:

1. Identify the appropriate module for your change
2. Make changes in isolation
3. Add tests for new functionality
4. Submit a pull request

## License

[Your License Here]

## Version History

- **2.0.0** - Complete refactoring into modular architecture
- **1.0.18** - Original monolithic version (preserved as ll_av_script-env.py)

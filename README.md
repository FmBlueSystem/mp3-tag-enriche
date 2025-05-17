# MP3 Tag Enricher

A Python application built with PySide6 that helps enrich MP3 file metadata tags using MusicBrainz database.

## Features

- Drag and drop support for MP3 files and directories
- Recursive directory scanning for MP3 files
- Batch processing of multiple files
- Integration with MusicBrainz for metadata lookup
- Material Design-inspired user interface
- Real-time progress tracking
- Analysis mode for preview before changes

## Requirements

- Python 3.6+
- PySide6
- Additional dependencies listed in requirements.txt

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/FmBlueSystem/mp3-tag-enriche.git
   cd mp3-tag-enricher
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python -m src
```

The application provides several ways to work with MP3 files:

1. Drag and drop MP3 files or directories into the application window
2. Use "Browse for MP3 Files" to select individual files
3. Use "Browse for Directory" to select entire folders for processing

After loading files:
- Select files from the list to view/edit their current tags
- Enable "Analysis Mode" to preview changes without modifying files
- Click "Process All Files" to begin processing

## License

MIT License

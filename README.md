# Genre Detector App

## Usage

The main application can be run using:

```bash
# Basic usage
python3 -m src <path_to_mp3_or_directory>

# Full options
python3 -m src <path> [options]
  --recursive, -r        Process directories recursively
  --analyze-only        Only analyze without modifying files
  --backup-dir DIR      Directory for file backups
  --confidence FLOAT    Minimum confidence threshold (default: 0.3)
  --max-genres INT      Maximum number of genres to write (default: 3)
  --output, -o FILE     Output JSON file for results
  --quiet, -q          Disable verbose output

# Examples

# Analyze single file
python3 -m src "path/to/song.mp3" --analyze-only

# Process directory with backups
python3 -m src "path/to/music/folder" --backup-dir backups

# Process directory with custom confidence
python3 -m src "path/to/music/folder" --confidence 0.2

# Save analysis results to JSON
python3 -m src "path/to/music" --analyze-only -o results.json
```

The app will:
1. Analyze MP3 files using multiple music APIs
2. Detect and normalize genres with confidence scores
3. Update genre tags in CamelCase format
4. Create backups of modified files
5. Generate detailed analysis reports

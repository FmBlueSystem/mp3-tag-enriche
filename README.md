# Genre Detector - Dark AI

A Material Design-compliant application for detecting and normalizing music genres in MP3 files.

## Features

- Material Design dark theme with full accessibility support
- Multiple API support for genre detection (MusicBrainz, LastFM)
- Drag-and-drop file handling
- Keyboard navigation and screen reader support
- Automatic file backups
- Genre normalization and filtering
- Batch processing capabilities

## Installation

1. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
python -m pip install -r requirements.txt
```

## Running the Application

```bash
python run_gui.py
```

## Running Tests

The project uses pytest for testing. Run the tests with:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Generate HTML coverage report
pytest --cov=src --cov-report=html tests/

# Run specific test categories
pytest tests/test_file_handler.py
pytest tests/test_genre_detection.py
pytest tests/test_gui.py
```

## Accessibility Features

- Full keyboard navigation (Tab/Shift+Tab)
- Screen reader support with ARIA labels
- High contrast color scheme following Material Design
- Focus indicators for all interactive elements
- Keyboard shortcuts:
  - Ctrl+O: Add Files
  - Ctrl+Shift+O: Add Folder
  - Ctrl+P: Process Files

## Material Design Implementation

The application follows Material Design guidelines:

- Color system using Material Dark theme palette
- Elevation with shadows and overlays
- Typography using Roboto/Segoe UI
- Component spacing following 8dp grid
- Interactive states (hover, focus, pressed)
- Motion and transitions

## Development

### Code Style

The project uses several tools to maintain code quality:

- black: Code formatting
- isort: Import sorting
- flake8: Linting
- mypy: Type checking

Run them with:
```bash
black src tests
isort src tests
flake8 src tests
mypy src
```

### Documentation

Generate documentation with:
```bash
cd docs
make html
```

## Project Structure

```
├── src/
│   ├── core/           # Core business logic
│   │   ├── file_handler.py
│   │   ├── genre_detector.py
│   │   ├── genre_normalizer.py
│   │   └── music_apis.py
│   └── gui/            # User interface
│       ├── main_window.py
│       └── style.py
├── tests/              # Test suite
│   ├── test_file_handler.py
│   ├── test_genre_detection.py
│   └── test_gui.py
├── .coveragerc         # Coverage configuration
├── pytest.ini         # Pytest configuration
└── requirements.txt    # Project dependencies
```

## Contributing

1. Ensure all tests pass before submitting changes
2. Follow Material Design guidelines for UI changes
3. Maintain accessibility compliance
4. Update documentation as needed

## License

MIT License - See LICENSE file for details

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Crear directorio temporal para tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_music_files(temp_dir):
    """Crear archivos de música de ejemplo para tests."""
    music_dir = temp_dir / "music"
    music_dir.mkdir()
    
    # Crear archivos de ejemplo (vacíos para tests)
    files = [
        "artist1 - song1.mp3",
        "artist2 - song2.flac",
        "artist1 - song3.ogg",
    ]
    
    for file in files:
        (music_dir / file).touch()
    
    return music_dir


@pytest.fixture
def mock_config():
    """Configuración mock para tests."""
    return {
        "database": {"path": ":memory:"},
        "library": {"scan_paths": [], "supported_formats": ["mp3", "flac", "ogg"]},
        "logging": {"level": "DEBUG"},
    }

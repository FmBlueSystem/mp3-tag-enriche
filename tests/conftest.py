"""Shared test fixtures."""
import os
import shutil
import pytest
import tempfile
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TCON

SAMPLE_MP3_PATH = "/Volumes/My Passport/Dj compilation 2025/DMS/Mayo25/X-MIX CLUB CLASSICS BEST OF 320 (Seperated Tracks)"

@pytest.fixture(scope="session")
def sample_mp3():
    """Get a real MP3 file for testing."""
    # Get first MP3 file from the directory
    for file in Path(SAMPLE_MP3_PATH).glob("*.mp3"):
        if file.is_file():
            return str(file)
    raise RuntimeError("No MP3 files found in sample directory")

@pytest.fixture
def valid_mp3(tmp_path, sample_mp3):
    """Create a copy of the sample MP3 file for individual test use."""
    test_file = tmp_path / "test.mp3"
    shutil.copy2(sample_mp3, test_file)
    return str(test_file)

@pytest.fixture
def backup_dir(tmp_path):
    """Create a backup directory."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    return str(backup_dir)

@pytest.fixture
def mock_musicbrainz_api(monkeypatch):
    """Mock MusicBrainz API responses."""
    def mock_get_genres(self, artist, track):
        return {
            "Rock": 0.9,
            "Alternative": 0.7,
            "Pop": 0.5
        }
    
    from src.core.music_apis import MusicBrainzAPI
    monkeypatch.setattr(MusicBrainzAPI, "get_genres", mock_get_genres)
    return mock_get_genres

@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data that persists across tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mp3_collection(test_data_dir, valid_mp3):
    """Create a collection of test MP3 files."""
    collection_dir = Path(test_data_dir) / "collection"
    collection_dir.mkdir(exist_ok=True)
    
    # Create multiple files with different tags
    files = []
    for i in range(3):
        dest = collection_dir / f"test_{i}.mp3"
        shutil.copy(valid_mp3, dest)
        
        # Modify tags for each file
        tags = ID3(dest)
        tags.add(TIT2(encoding=3, text=f"Song {i}"))
        tags.add(TPE1(encoding=3, text=f"Artist {i}"))
        tags.add(TCON(encoding=3, text=f"Genre {i}"))
        tags.save()
        
        files.append(str(dest))
    
    return files

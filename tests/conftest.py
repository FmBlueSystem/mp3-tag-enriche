"""Shared test fixtures."""
import os
import shutil
import pytest
import tempfile
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TCON

@pytest.fixture(scope="session")
def sample_mp3():
    """Use an existing MP3 file for testing."""
    test_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "mp3_backups",
        "BORN TO BE ALIVEPATRIC HERNANDEZX-MIX CLASSICS320kbps_20250517_142020.mp3"
    )
    if not os.path.exists(test_file):
        raise RuntimeError(f"Test MP3 file not found: {test_file}")
    return test_file

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
    def mock_get_track_info(self, artist, track):
        return {
            "genres": ["Rock", "Alternative Rock", "Progressive Rock"],
            "year": "2025",
            "album": "Test Album"
        }
    
    from src.core.music_apis import MusicBrainzAPI
    monkeypatch.setattr(MusicBrainzAPI, "get_track_info", mock_get_track_info)
    return mock_get_track_info

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

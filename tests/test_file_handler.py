"""Tests for file handling operations."""
import os
import shutil
import pytest
from pathlib import Path
from src.core.file_handler import Mp3FileHandler


class TestMp3FileHandler:
    @pytest.fixture
    def handler(self):
        """Create a test file handler with the specified backup directory."""
        fixed_backup_dir = "/Volumes/My Passport/Dj compilation 2025/Respados mp3"
        # Asegurarse de que el directorio de backup exista o se pueda crear por Mp3FileHandler
        # Mp3FileHandler ya intenta crearlo en su __init__
        return Mp3FileHandler(backup_dir=fixed_backup_dir)

    def test_backup_creation(self, handler, valid_mp3):
        """Test backup file creation."""
        assert handler.backup_dir is not None, "Backup directory must be set for this test"
        initial_backup_files = list(Path(handler.backup_dir).glob('*'))

        success = handler._create_backup(valid_mp3)
        assert success, "Backup creation should succeed"
        
        current_backup_files = list(Path(handler.backup_dir).glob('*'))
        new_backup_files = [f for f in current_backup_files if f not in initial_backup_files]

        assert len(new_backup_files) == 1, "One new backup file should be created"
        backup_path = new_backup_files[0]
        
        assert backup_path.exists(), "Backup file should exist"
        assert backup_path.stat().st_size > 0, "Backup file should not be empty"

    def test_invalid_mp3_detection(self, handler, tmp_path):
        """Test detection of invalid MP3 files."""
        invalid_file = tmp_path / "invalid.mp3"
        invalid_file.write_text("Not an MP3 file")
        
        assert not handler.is_valid_mp3(str(invalid_file)), "Should detect invalid MP3"

    def test_valid_mp3_detection(self, handler, valid_mp3):
        """Test detection of valid MP3 files."""
        assert handler.is_valid_mp3(valid_mp3), "Should recognize valid MP3"

    def test_write_genre(self, handler, valid_mp3):
        """Test writing genre tags."""
        genres = ["Rock", "Pop"]
        success = handler.write_genre(valid_mp3, genres, backup=True)
        assert success, "Genre writing should succeed"
        
        # Verify genre was written
        info = handler.get_file_info(valid_mp3)
        assert "current_genre" in info, "Genre info should be readable"
        assert any(genre in info["current_genre"] for genre in genres), "Written genres should be present"

    def test_file_permission_handling(self, handler, valid_mp3):
        """Test handling of file permission issues."""
        # Make file read-only
        os.chmod(valid_mp3, 0o444)
        try:
            success = handler.write_genre(valid_mp3, ["Rock"], backup=True)
            assert not success, "Should fail on read-only file"
        finally:
            # Restore permissions for cleanup
            os.chmod(valid_mp3, 0o666)

    def test_genre_normalization(self, handler, valid_mp3):
        """Test genre name normalization."""
        genres = ["rock and roll", "R&B", "hip-hop"]
        success = handler.write_genre(valid_mp3, genres)
        assert success, "Genre writing should succeed"
        
        info = handler.get_file_info(valid_mp3)
        written_genres = info.get("current_genre", "").split(";")
        
        # Verify proper capitalization
        assert any("Rock" in g for g in written_genres), "Genre should be properly capitalized"
        assert "R&B" in written_genres, "Should preserve certain abbreviations"
        assert "Hip-Hop" in written_genres, "Should properly capitalize hyphenated genres"

    def test_backup_restoration(self, handler, valid_mp3):
        """Test backup restoration functionality."""
        assert handler.backup_dir is not None, "Backup directory must be set for this test"
        original_content = Path(valid_mp3).read_bytes()
        
        initial_backup_files = list(Path(handler.backup_dir).glob('*'))
        success = handler._create_backup(valid_mp3)
        assert success, "Backup creation should succeed"
        
        current_backup_files = list(Path(handler.backup_dir).glob('*'))
        new_backup_files = [f for f in current_backup_files if f not in initial_backup_files]
        assert len(new_backup_files) == 1, "One new backup file should be created for restoration test"
        backup_path = new_backup_files[0]
        
        assert backup_path.exists(), "Backup should exist for restoration test"
        
        # Modify file
        handler.write_genre(valid_mp3, ["Test Genre"], backup=False) # Ensure no new backup is made here for this step
        
        # Verify backup content matches original
        backup_content = backup_path.read_bytes()
        assert backup_content == original_content, "Backup should preserve original content"

    def test_file_renaming(self, handler, valid_mp3):
        """Test file renaming functionality."""
        # First write a genre
        handler.write_genre(valid_mp3, ["Rock"])
        
        # Then try to rename
        result = handler.rename_file_by_genre(valid_mp3)
        
        assert result["success"], "File renaming should succeed"
        assert "[Rock]" in result["new_path"], "New filename should include genre"
        assert Path(result["new_path"]).exists(), "New file should exist"

    def test_concurrent_access(self, handler, valid_mp3):
        """Test handling of concurrent file access."""
        with open(valid_mp3, "rb") as f:
            # Should still be able to read file info
            info = handler.get_file_info(valid_mp3)
            assert info is not None, "Should read info from open file"
            assert "current_genre" in info, "Should read genre from open file"

    def test_backup_on_write(self, handler, valid_mp3):
        """Test automatic backup creation during write."""
        assert handler.backup_dir is not None, "Backup directory must be set for this test"
        original_content = Path(valid_mp3).read_bytes()
        initial_backup_files = list(Path(handler.backup_dir).glob('*'))
        
        handler.write_genre(valid_mp3, ["Test Genre"], backup=True)
        
        current_backup_files = list(Path(handler.backup_dir).glob('*'))
        new_backup_files = [f for f in current_backup_files if f not in initial_backup_files]

        assert len(new_backup_files) == 1, "One new backup file should be created by write_genre"
        backup_path = new_backup_files[0]
        
        assert backup_path.exists(), "Backup should be created by write_genre"
        assert backup_path.read_bytes() == original_content, "Backup should match original"

    def test_multiple_genre_handling(self, handler, valid_mp3):
        """Test handling multiple genres."""
        test_genres = ["Rock", "Alternative", "Indie"]
        
        success = handler.write_genre(valid_mp3, test_genres)
        assert success, "Writing multiple genres should succeed"
        
        info = handler.get_file_info(valid_mp3)
        written_genres = info.get("current_genre", "").split(";")
        
        assert len(written_genres) == len(test_genres), "All genres should be written"
        assert all(g in written_genres for g in test_genres), "All genres should be present"

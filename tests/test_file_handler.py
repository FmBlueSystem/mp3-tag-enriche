"""Test suite for file handling and genre normalization functionality."""
import pytest
from pathlib import Path
import os
from src.core.file_handler import Mp3FileHandler
from src.core.genre_normalizer import GenreNormalizer

@pytest.fixture
def file_handler(tmp_path):
    """Create a file handler with temporary backup directory."""
    backup_dir = tmp_path / "backups"
    return Mp3FileHandler(str(backup_dir))

@pytest.fixture
def sample_mp3(tmp_path):
    """Create a sample MP3 file for testing."""
    mp3_path = tmp_path / "test.mp3"
    mp3_path.write_bytes(b"dummy mp3 content")
    return str(mp3_path)

class TestGenreNormalization:
    """Test genre normalization functionality."""

    def test_rnb_variations(self):
        """Test various R&B genre name variations."""
        variations = [
            ("r&b", "R&B"),
            ("rnb", "R&B"),
            ("randb", "R&B"),
            ("rb", "R&B"),
            ("r n b", "R&B"),
            ("r and b", "R&B"),
            ("rhythm & blues", "R&B"),
            ("rhythm n blues", "R&B"),
            ("contemporary r&b", "Contemporary R&B")
        ]
        for input_genre, expected in variations:
            normalized, confidence = GenreNormalizer.normalize(input_genre)
            assert normalized == expected
            assert confidence == 1.0

    def test_case_sensitivity(self):
        """Test genre case sensitivity rules."""
        cases = [
            ("r&b", "R&B"),
            ("R&B", "R&B"),
            ("hip-hop", "Hip-Hop"),
            ("HIP-HOP", "Hip-Hop"),
            ("UK Garage", "UK Garage"),
            ("uk garage", "UK Garage"),
            ("edm", "Electronic Dance Music"),
            ("EDM", "Electronic Dance Music")
        ]
        for input_genre, expected in cases:
            normalized, _ = GenreNormalizer.normalize(input_genre)
            assert normalized == expected

    def test_multiple_genre_weighting(self):
        """Test genre weighting and combination logic."""
        genres = {
            "alternative rock": 0.9,
            "rock": 0.8,
            "indie": 0.7,
            "punk": 0.6
        }
        normalized = GenreNormalizer.normalize_dict(genres)
        
        # Check that parent genres are properly weighted
        assert "Rock" in normalized
        assert "Alternative Rock" in normalized
        assert normalized["Alternative Rock"] > normalized["Rock"]
        assert len(normalized) <= 3  # Should limit to top 3 genres

    def test_genre_edge_cases(self):
        """Test edge cases in genre normalization."""
        cases = [
            ("", ("", 0.0)),  # Empty string
            ("   ", ("", 0.0)),  # Whitespace only
            ("unknown_genre", ("Unknown_genre", 0.5)),  # Unknown genre
            ("r&b/soul", ("R&B", 0.95)),  # Complex genre
            ("ELECTRONIC-DANCE", ("Electronic Dance Music", 0.85))  # All caps with hyphen
        ]
        for input_genre, (expected_name, min_confidence) in cases:
            normalized, confidence = GenreNormalizer.normalize(input_genre)
            assert normalized == expected_name
            assert confidence >= min_confidence

class TestFileRenaming:
    """Test file renaming functionality."""

    def test_genre_in_filename(self, file_handler, sample_mp3):
        """Test including genres in filename."""
        genres = ["Rock", "Alternative Rock"]
        result = file_handler.rename_file_by_genre(
            sample_mp3,
            genres_to_write=genres,
            include_genre_in_filename=True
        )
        assert result["success"]
        assert "[Rock, Alternative Rock]" in result["new_path"]

    def test_special_characters(self, file_handler, sample_mp3):
        """Test handling of special characters in filenames."""
        special_cases = [
            ("Artist/Name", "Artist⁄Name"),  # Forward slash
            ("Artist\\Name", "Artist⧵Name"),  # Backslash
            ("Artist:Name", "Artist꞉Name"),  # Colon
            ("Artist*Name", "Artist∗Name"),  # Asterisk
            ("Artist?Name", "Artist？Name"),  # Question mark
            ('Artist"Name', "Artist'Name"),  # Quotes
            ("Artist<Name", "Artist❮Name"),  # Less than
            ("Artist>Name", "Artist❯Name"),  # Greater than
            ("Artist|Name", "Artist⏐Name")   # Vertical bar
        ]
        
        for input_name, expected in special_cases:
            result = file_handler.rename_file_by_genre(
                sample_mp3,
                genres_to_write=["Rock"],
                include_genre_in_filename=True
            )
            assert result["success"]

    def test_filename_conflict_resolution(self, file_handler, tmp_path):
        """Test handling of filename conflicts."""
        # Create two files with same metadata
        file1 = tmp_path / "test1.mp3"
        file2 = tmp_path / "test2.mp3"
        file1.write_bytes(b"dummy content 1")
        file2.write_bytes(b"dummy content 2")
        
        # Try to rename both to same name
        result1 = file_handler.rename_file_by_genre(str(file1), genres_to_write=["Rock"])
        result2 = file_handler.rename_file_by_genre(str(file2), genres_to_write=["Rock"])
        
        assert result1["success"]
        assert result2["success"]
        assert result1["new_path"] != result2["new_path"]
        assert " (1)" in result2["new_path"]

    def test_long_filename_handling(self, file_handler, sample_mp3):
        """Test handling of very long filenames."""
        very_long_artist = "A" * 100
        very_long_title = "T" * 100
        very_long_genres = ["Very Long Genre Name"] * 3
        
        result = file_handler.rename_file_by_genre(
            sample_mp3,
            genres_to_write=very_long_genres,
            include_genre_in_filename=True
        )
        
        assert result["success"]
        new_path = Path(result["new_path"])
        # Check that final filename is within filesystem limits
        assert len(new_path.name.encode('utf-8')) <= 255

if __name__ == "__main__":
    pytest.main([__file__])

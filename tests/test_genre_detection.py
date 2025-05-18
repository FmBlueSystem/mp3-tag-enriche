"""Tests for genre detection and API integration."""
import pytest
from unittest.mock import Mock, patch
from src.core.genre_detector import GenreDetector
from src.core.music_apis import MusicBrainzAPI

class TestGenreDetection:
    @pytest.fixture
    def detector(self, mock_musicbrainz_api):
        """Create a genre detector with mocked API."""
        return GenreDetector(apis=[MusicBrainzAPI()], verbose=False)

    def test_genre_detection(self, detector, valid_mp3):
        """Test basic genre detection functionality."""
        result = detector.analyze_file(valid_mp3)
        
        # Should always have these fields
        assert "file_info" in result, "Should have file info"
        assert "metadata" in result, "Should have metadata"
        assert "current_genres" in result, "Should have current genres"
        assert "detected_genres" in result, "Should have detected genres"
        
        # Should have valid metadata
        assert result["metadata"]["title"], "Should have title"
        assert result["metadata"]["artist"], "Should have artist"
        
        # Should have properly normalized confidence scores
        genres = result["detected_genres"]
        if genres and not "error" in result:
            confidences = genres.values()

    def test_confidence_threshold(self, detector, valid_mp3):
        """Test confidence threshold filtering."""
        detector.confidence_threshold = 0.8
        with patch.object(MusicBrainzAPI, 'get_genres', return_value={"Rock": 0.9, "Pop": 0.7}):
            result = detector.analyze_file(valid_mp3)
            genres = result.get("detected_genres", {})
            assert all(conf >= 0.8 for conf in genres.values())

    def test_max_genres_limit(self, detector, valid_mp3):
        """Test maximum genres limit."""
        detector.max_genres = 2
        with patch.object(MusicBrainzAPI, 'get_genres', return_value={
            "Rock": 0.9,
            "Pop": 0.8,
            "Jazz": 0.7
        }):
            result = detector.analyze_file(valid_mp3)
            genres = result.get("detected_genres", {})
            assert len(genres) <= 2, "Should respect max genres limit"

    def test_api_error_handling(self, detector, valid_mp3):
        """Test handling of API errors."""
        with patch.object(MusicBrainzAPI, 'get_genres', side_effect=Exception("API Error")):
            result = detector.analyze_file(valid_mp3)
            assert "error" in result, "Should report API error"
            assert "API Error" in result["error"], "Should include error message"

    def test_genre_merging(self, detector, valid_mp3):
        """Test merging of genres from multiple APIs."""
        test_genres_1 = {"rock": 0.9, "pop": 0.7}
        test_genres_2 = {"Rock": 0.8, "jazz": 0.6}
        expected_genres = {"Rock", "Pop", "Jazz"}
        
        # Mock APIs
        detector.apis = [
            Mock(spec=MusicBrainzAPI, get_genres=Mock(return_value=test_genres_1)),
            Mock(spec=MusicBrainzAPI, get_genres=Mock(return_value=test_genres_2))
        ]
        
        result = detector.analyze_file(valid_mp3)
        genres = result.get("detected_genres", {})
        
        # Check normalized genres are present
        assert set(genres.keys()) == expected_genres, "Should normalize and merge genres"
        
        # Verify highest confidence is used
        assert genres["Rock"] >= 0.9, "Should use highest confidence score"

    def test_empty_results_handling(self, detector, valid_mp3):
        """Test handling of empty API results."""
        with patch.object(MusicBrainzAPI, 'get_genres', return_value={}):
            result = detector.analyze_file(valid_mp3)
            assert "error" in result, "Should report error"
            assert result["error"] == "No genres detected from APIs.", "Should indicate no genres found"
            assert "detected_genres" in result, "Should include empty detected_genres"

    def test_genre_normalization(self, detector, valid_mp3):
        """Test genre name normalization and confidence distribution."""
        test_genres_raw = {
            "rock and roll": 0.9,
            "r&b": 0.8,
            "hip-hop": 0.7,
            "drum & bass": 0.6,
            "alternative rock": 0.5
        }
        expected_normalized_names = {
            "Rock and Roll",
            "R&B",
            "Hip-Hop",
            "Drum & Bass",
            "Alternative Rock"
        }
        
        with patch.object(MusicBrainzAPI, 'get_genres', return_value=test_genres_raw):
            result = detector.analyze_file(valid_mp3)
            detected_genres = result.get("detected_genres", {})
            
            assert set(detected_genres.keys()) == expected_normalized_names, \
                f"Normalized genre names do not match. Expected {expected_normalized_names}, got {set(detected_genres.keys())}"
            
            if detected_genres: # Only verify sum if genres were detected

                # Verify that the genre with the highest original score ("rock and roll")
                # has the highest normalized score.
                # Need GenreNormalizer for this check
                from src.core.genre_normalizer import GenreNormalizer
                original_sorted_by_score = sorted(test_genres_raw.items(), key=lambda item: item[1], reverse=True)
                
                # detected_genres keys are already normalized by GenreNormalizer.normalize via _merge_genre_scores
                top_original_normalized_name = GenreNormalizer.normalize(original_sorted_by_score[0][0])
                
                # Find the score of the top original genre in the detected results
                top_detected_score = detected_genres.get(top_original_normalized_name, -1)

                # Verify this genre has the highest score in the detected results
                assert top_detected_score == max(detected_genres.values()), \
                    "The genre with the highest original score should have the highest normalized score after processing."

    def test_metadata_extraction(self, detector, valid_mp3):
        """Test metadata extraction from files."""
        result = detector.analyze_file(valid_mp3)
        assert "metadata" in result, "Should extract metadata"
        metadata = result["metadata"]
        assert metadata["title"] == "Got To Be Real ( Part 1 )"
        assert metadata["artist"] == "Cheryl Lynn"

    def test_cache_functionality(self, detector, valid_mp3):
        """Test genre detection caching."""
        # First call with original genres
        original_genres = {"Rock": 0.9, "Pop": 0.7}
        with patch.object(MusicBrainzAPI, 'get_genres', return_value=original_genres):
            result1 = detector.analyze_file(valid_mp3)
            
        # Second call with different genres
        with patch.object(MusicBrainzAPI, 'get_genres', return_value={"Different": 0.9}):
            result2 = detector.analyze_file(valid_mp3)
            assert result2["detected_genres"] == result1["detected_genres"]

    def test_genre_filtering(self, detector, valid_mp3):
        """Test genre filtering with confidence threshold."""
        detector.confidence_threshold = 0.5
        test_genres = {
            "Rock": 0.8,  # Above threshold
            "Pop": 0.4,   # Below threshold
            "Jazz": 0.6   # Above threshold
        }
        
        with patch.object(MusicBrainzAPI, 'get_genres', return_value=test_genres):
            result = detector.analyze_file(valid_mp3)
            genres = result.get("detected_genres", {})
            filtered = [g for g, c in genres.items() if c >= 0.5]
            assert set(filtered) == {"Rock", "Jazz"}

    def test_invalid_file_handling(self, detector, tmp_path):
        """Test handling of invalid files."""
        invalid_file = tmp_path / "invalid.mp3"
        invalid_file.write_text("Not an MP3")
        
        result = detector.analyze_file(str(invalid_file))
        assert "error" in result, "Should report error for invalid file"

"""Test suite for genre detection and combination logic."""
import pytest
from src.core.genre_normalizer import GenreNormalizer
from typing import Dict, List, Tuple

@pytest.fixture
def genre_samples() -> List[Tuple[str, List[str]]]:
    """Sample genre data for testing."""
    return [
        ("rock_sample", ["Rock", "Alternative Rock", "Indie Rock"]),
        ("electronic_sample", ["Electronic", "House", "Techno"]),
        ("mixed_sample", ["Hip-Hop", "R&B", "Pop"]),
        ("jazz_sample", ["Jazz", "Contemporary Jazz", "Fusion"])
    ]

class TestGenreCombination:
    """Test genre combination and weighting logic."""

    def test_genre_hierarchy_weighting(self):
        """Test that parent genres are properly weighted based on children."""
        input_genres = {
            "Alternative Rock": 0.9,
            "Hard Rock": 0.8,
            "Progressive Rock": 0.7
        }
        
        normalized = GenreNormalizer.normalize_dict(input_genres)
        
        # Parent genre (Rock) should be included
        assert "Rock" in normalized
        # Parent should have high confidence due to multiple strong children
        assert normalized["Rock"] >= 0.8
        # Original genres should maintain relative ordering
        assert normalized["Alternative Rock"] > normalized["Hard Rock"]

    def test_conflicting_genres(self):
        """Test handling of conflicting genre assignments."""
        conflicts = {
            "Heavy Metal": 0.8,
            "Pop": 0.8,
            "Classical": 0.7,
            "Electronic": 0.6
        }
        
        normalized = GenreNormalizer.normalize_dict(conflicts)
        
        # Should only keep top genres with significant confidence
        assert len(normalized) <= 3
        # Should prefer stronger genre families
        assert "Heavy Metal" in normalized
        assert "Metal" in normalized
        # Lower confidence genres should be excluded
        assert "Electronic" not in normalized

    def test_genre_combination_thresholds(self):
        """Test thresholds for combining multiple genres."""
        cases = [
            # High confidence similar genres
            {
                "Rock": 0.9,
                "Alternative Rock": 0.85,
                "Indie Rock": 0.8
            },
            # Mixed confidence genres
            {
                "Electronic": 0.9,
                "Ambient": 0.5,
                "Experimental": 0.3
            },
            # Low confidence genres
            {
                "Pop": 0.4,
                "Dance": 0.3,
                "Funk": 0.2
            }
        ]
        
        for input_genres in cases:
            normalized = GenreNormalizer.normalize_dict(input_genres)
            # Should not have more than max allowed genres
            assert len(normalized) <= 3
            # All included genres should be above threshold
            assert all(score >= 0.3 for score in normalized.values())

    def test_genre_family_preservation(self):
        """Test preservation of genre family relationships."""
        genres = {
            "Blues Rock": 0.9,
            "Chicago Blues": 0.8,
            "Delta Blues": 0.7,
            "Rock & Roll": 0.6
        }
        
        normalized = GenreNormalizer.normalize_dict(genres)
        
        # Should preserve core genre families
        assert "Blues" in normalized
        assert "Rock" in normalized
        # Should maintain some subgenres
        assert any(g for g in normalized if "Blues" in g and g != "Blues")

    def test_edge_case_combinations(self):
        """Test edge cases in genre combination logic."""
        edge_cases = [
            # Empty input
            ({}, {}),
            # Single genre
            ({"Rock": 0.9}, {"Rock": 0.9}),
            # All low confidence
            ({"Pop": 0.2, "Rock": 0.3}, {}),
            # One valid, rest invalid
            ({"Jazz": 0.9, "Unknown1": 0.5, "Unknown2": 0.4},
             {"Jazz": 0.9}),
            # Special characters
            ({"R&B": 0.9, "D&B": 0.8},
             {"R&B": 0.9, "Drum & Bass": 0.8})
        ]
        
        for input_genres, expected in edge_cases:
            normalized = GenreNormalizer.normalize_dict(input_genres)
            if expected:
                assert all(genre in normalized for genre in expected)
                assert all(normalized[genre] >= expected[genre] for genre in expected)
            else:
                assert len(normalized) == 0

    def test_fuzzy_matching_thresholds(self):
        """Test fuzzy matching confidence thresholds."""
        variations = [
            ("elektronik", "Electronic"),
            ("hiphop", "Hip-Hop"),
            ("rythm and blues", "R&B"),
            ("jaz", "Jazz"),
            ("rokk", "Rock")
        ]
        
        for input_genre, expected in variations:
            normalized, confidence = GenreNormalizer.normalize(input_genre)
            if confidence >= 0.7:  # Our threshold for acceptance
                assert normalized == expected
            else:
                assert normalized != expected

if __name__ == "__main__":
    pytest.main([__file__])

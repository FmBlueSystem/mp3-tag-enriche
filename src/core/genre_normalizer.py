"""Genre normalization and mapping module."""
from typing import Dict, List, Set
import re

class GenreNormalizer:
    """Normalizes and maps music genres."""
    
    def __init__(self):
        """Initialize genre mappings."""
        # Core genre categories
        self.genre_map = {
            # Hip Hop variants
            'hip hop': 'HipHop',
            'hip-hop': 'HipHop',
            'rap': 'HipHop',
            'gangsta rap': 'HipHop',
            'boom bap': 'HipHop',
            
            # Rock variants
            'rock': 'Rock',
            'hard rock': 'Rock',
            'classic rock': 'Rock',
            'soft rock': 'Rock',
            'rock and indie': 'Rock',
            
            # Electronic variants
            'electronic': 'Electronic',
            'electronica': 'Electronic',
            'edm': 'Electronic',
            'dance': 'Electronic',
            'techno': 'Electronic',
            
            # Pop variants
            'pop': 'Pop',
            'pop rock': 'Pop',
            'synth pop': 'Pop',
            'power pop': 'Pop',
            'dance pop': 'Pop',
            
            # R&B variants
            'r&b': 'RAndB',
            'rnb': 'RAndB',
            'rhythm & blues': 'RAndB',
            'soul': 'RAndB',
            'funk': 'RAndB',
            
            # Jazz variants
            'jazz': 'Jazz',
            'fusion': 'Jazz',
            'smooth jazz': 'Jazz',
            'big band': 'Jazz',
            'swing': 'Jazz'
        }
        
    def normalize_genre(self, genre: str) -> str:
        """Normalize a single genre string.
        
        Args:
            genre: Raw genre string
            
        Returns:
            Normalized genre string
        """
        # Convert to lowercase for matching
        genre = genre.lower().strip()
        
        # Look up in mapping
        if genre in self.genre_map:
            return self.genre_map[genre]
            
        # If not found, convert to CamelCase
        words = re.findall(r'[a-z]+', genre)
        if words:
            return ''.join(w.capitalize() for w in words)
            
        return genre.capitalize()
        
    def get_confidence_score(self, genres: List[str]) -> Dict[str, float]:
        """Calculate confidence scores for normalized genres.
        
        Args:
            genres: List of raw genre strings
            
        Returns:
            Dictionary of normalized genres to confidence scores
        """
        if not genres:
            return {}
            
        # Count occurrences of normalized genres
        counts: Dict[str, int] = {}
        total = 0
        
        for genre in genres:
            norm = self.normalize_genre(genre)
            counts[norm] = counts.get(norm, 0) + 1
            total += 1
            
        # Calculate confidence scores
        return {
            genre: count / total 
            for genre, count in counts.items()
        }

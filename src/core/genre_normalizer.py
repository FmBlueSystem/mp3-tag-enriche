"""Genre name normalization utilities."""
from typing import Dict, List

class GenreNormalizer:
    """Handle genre name normalization and standardization."""
    
    # Special cases that should be preserved
    SPECIAL_CASES = {
        'r&b': 'R&B',
        'rnb': 'R&B',
        'r n b': 'R&B',
        'r and b': 'R&B',
        'rhythm & blues': 'R&B',
        'rhythm n blues': 'R&B',
        'rhythm and blues': 'R&B',
        'hip-hop': 'Hip-Hop',
        'hip hop': 'Hip-Hop',
        'drum & bass': 'Drum & Bass',
        'drum n bass': 'Drum & Bass',
        'dnb': 'Drum & Bass',
        'rock n roll': 'Rock & Roll',
        'rock and roll': 'Rock and Roll',
        'rock & roll': 'Rock & Roll',
        'house music': 'House',
        'edm': 'Electronic Dance Music',
        'alt rock': 'Alternative Rock',
        'alt': 'Alternative',
        'pop rock': 'Pop/Rock'
    }
    
    @classmethod
    def normalize(cls, genre: str) -> str:
        """Normalize a genre name.
        
        Args:
            genre: Raw genre name
            
        Returns:
            Normalized genre name
        """
        if not genre:
            return ""
            
        # Convert to lowercase for comparison
        lower_genre = genre.lower().strip()
        
        # Check special cases first
        if lower_genre in cls.SPECIAL_CASES:
            return cls.SPECIAL_CASES[lower_genre]
            
        # Split into words while preserving certain symbols
        words = lower_genre.replace('-', ' - ').replace('&', ' & ').replace('/', ' / ').split()
        
        # List of words to keep lowercase when they're not at the start
        small_words = {'and', 'or', 'the', 'in', 'of', 'a', 'an', 'but', 'for', 'on', 'to', 'with'}
        
        # Capitalize each word unless it's a small word not at the start
        result = []
        for i, word in enumerate(words):
            # Special symbols should be preserved as-is
            if word in {'-', '&', '/'}:
                result.append(word)
            # First word or not a small word: capitalize
            elif i == 0 or word not in small_words:
                result.append(word.capitalize())
            # Small word not at start: keep lowercase
            else:
                result.append(word)
                
        return ' '.join(result)
        
    @classmethod
    def normalize_list(cls, genres: List[str]) -> List[str]:
        """Normalize a list of genres.
        
        Args:
            genres: List of raw genre names
            
        Returns:
            List of normalized genre names
        """
        return [cls.normalize(g) for g in genres if g]
        
    @classmethod
    def normalize_dict(cls, genres: Dict[str, float]) -> Dict[str, float]:
        """Normalize genre names in a confidence score dictionary.
        
        Args:
            genres: Dictionary of genre names to confidence scores
            
        Returns:
            Dictionary with normalized genre names
        """
        normalized = {}
        for genre, score in genres.items():
            norm_name = cls.normalize(genre)
            if norm_name in normalized:
                normalized[norm_name] = max(normalized[norm_name], score)
            else:
                normalized[norm_name] = score
                
        return normalized

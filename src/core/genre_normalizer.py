"""Genre name normalization utilities."""
from typing import Dict, List, Optional, Set, Tuple
from difflib import SequenceMatcher

class GenreNormalizer:
    """Handle genre name normalization and standardization."""
    
    # Special cases that should be preserved
    SPECIAL_CASES = {
        # R&B variations
        'r&b': 'R&B',
        'rnb': 'R&B',
        'randb': 'R&B',
        'rb': 'R&B',
        'r n b': 'R&B',
        'r and b': 'R&B',
        'r & b': 'R&B',
        'rhythm & blues': 'R&B',
        'rhythm n blues': 'R&B',
        'rhythm and blues': 'R&B',
        'rythm and blues': 'R&B',
        'rythm & blues': 'R&B',
        'rythem and blues': 'R&B',
        'contemporary r&b': 'Contemporary R&B',
        'modern r&b': 'Contemporary R&B',
        
        # Hip-Hop variations
        'hip-hop': 'Hip-Hop',
        'hip hop': 'Hip-Hop',
        'hiphop': 'Hip-Hop',
        'hip hop music': 'Hip-Hop',
        'rap': 'Hip-Hop',
        'rap music': 'Hip-Hop',
        
        # Electronic music variations
        'drum & bass': 'Drum & Bass',
        'drum n bass': 'Drum & Bass',
        'drum and bass': 'Drum & Bass',
        'dnb': 'Drum & Bass',
        'd&b': 'Drum & Bass',
        'house music': 'House',
        'edm': 'Electronic Dance Music',
        'electronic': 'Electronic',
        'electronica': 'Electronic',
        'techno music': 'Techno',
        
        # Rock variations
        'rock n roll': 'Rock & Roll',
        'rock and roll': 'Rock & Roll',
        'rock & roll': 'Rock & Roll',
        'alt rock': 'Alternative Rock',
        'alt': 'Alternative Rock',
        'alternative': 'Alternative Rock',
        'pop rock': 'Pop/Rock',
        'pop/rock': 'Pop/Rock',
        
        # Jazz variations
        'jazz music': 'Jazz',
        'modern jazz': 'Contemporary Jazz',
        'contemp jazz': 'Contemporary Jazz',
        
        # Classical variations
        'classical music': 'Classical',
        'classic': 'Classical',
        'classics': 'Classical',
        
        # Soul/Funk variations
        'soul music': 'Soul',
        'funk music': 'Funk',
        'funky': 'Funk',
        
        # Blues variations
        'blues music': 'Blues',
        'rhythm and blues': 'R&B',  # Mapping to R&B as it's more common in modern context
        
        # Pop variations
        'popular': 'Pop',
        'pop music': 'Pop',
    }

    # Genre hierarchy relationships
    GENRE_HIERARCHY = {
        'Rock': {'Alternative Rock', 'Hard Rock', 'Progressive Rock', 'Punk Rock', 'Rock & Roll'},
        'Electronic': {'House', 'Techno', 'Trance', 'Drum & Bass', 'Ambient', 'Electronic Dance Music'},
        'Hip-Hop': {'Trap', 'Rap', 'Old School Hip-Hop'},
        'R&B': {'Soul', 'Funk', 'Contemporary R&B'},
        'Jazz': {'Bebop', 'Swing', 'Fusion', 'Latin Jazz'},
        'Pop': {'Synth Pop', 'Pop/Rock', 'Dance Pop'},
        'Metal': {'Heavy Metal', 'Death Metal', 'Black Metal', 'Thrash Metal'},
        'Folk': {'Traditional Folk', 'Contemporary Folk', 'Folk Rock'},
        'Classical': {'Baroque', 'Romantic', 'Contemporary Classical'},
        'Blues': {'Delta Blues', 'Chicago Blues', 'Blues Rock'}
    }

    # Validated genre whitelist (includes both parent and child genres)
    VALID_GENRES = set()
    for parent, children in GENRE_HIERARCHY.items():
        VALID_GENRES.add(parent)
        VALID_GENRES.update(children)
        
    # Add special cases to valid genres
    VALID_GENRES.update(set(SPECIAL_CASES.values()))

    @classmethod
    def normalize(cls, genre: str, fuzzy_match: bool = True) -> Tuple[str, float]:
        """Normalize a genre name with confidence score.
        
        Args:
            genre: Raw genre name
            fuzzy_match: Whether to attempt fuzzy matching for unknown genres
            
        Returns:
            Tuple of (normalized genre name, confidence score)
        """
        if not genre:
            return "", 0.0
            
        # Remove extra whitespace and convert to lowercase for comparison
        cleaned_genre = ' '.join(genre.strip().split())
        lower_genre = cleaned_genre.lower()
        
        # Check special cases first (including common misspellings)
        if lower_genre in cls.SPECIAL_CASES:
            return cls.SPECIAL_CASES[lower_genre], 1.0
            
        # Split and normalize words
        words = lower_genre.replace('-', ' - ').replace('&', ' & ').replace('/', ' / ').split()
        
        # Words to keep lowercase when not at start
        small_words = {'and', 'or', 'the', 'in', 'of', 'a', 'an', 'but', 'for', 'on', 'to', 'with', 'n', 'feat', 'ft'}
        
        # Special words that should always be capitalized
        force_capitalize = {'R&B', 'DJ', 'UK', 'USA', 'MTV', 'EP', 'LP', 'CD'}
        
        # Capitalize each word with special rules
        result = []
        for i, word in enumerate(words):
            if word.upper() in force_capitalize:
                result.append(word.upper())
            elif word in {'-', '&', '/'}:
                result.append(word)
            elif i == 0 or word not in small_words:
                result.append(word.capitalize())
            else:
                result.append(word)
                
        normalized = ' '.join(result)

        # If normalized genre is in whitelist, return with full confidence
        if normalized in cls.VALID_GENRES:
            return normalized, 1.0

        # Try fuzzy matching if enabled
        if fuzzy_match:
            # First check if it's a parent genre
            if normalized in cls.GENRE_HIERARCHY:
                return normalized, 1.0
                
            # Then try exact substring matches with parent genres first
            for valid_genre in cls.GENRE_HIERARCHY.keys():
                if lower_genre in valid_genre.lower() or valid_genre.lower() in lower_genre:
                    return valid_genre, 0.95
                    
            # Then try other exact substring matches
            for valid_genre in cls.VALID_GENRES:
                if lower_genre in valid_genre.lower() or valid_genre.lower() in lower_genre:
                    return valid_genre, 0.9

            # Try fuzzy matching against parent genres first
            parent_match, parent_score = cls._find_best_match(normalized, cls.GENRE_HIERARCHY.keys())
            if parent_score >= 0.85:
                return parent_match, parent_score

            # Then try special cases
            special_match, special_score = cls._find_best_match(normalized, cls.SPECIAL_CASES.values())
            if special_score >= 0.9:
                return special_match, special_score

            # Finally try all valid genres
            valid_match, valid_score = cls._find_best_match(normalized, cls.VALID_GENRES)
            if valid_score >= 0.85:
                return valid_match, valid_score * 0.95  # Slightly reduce confidence for non-parent matches

            # Return empty for low confidence matches
            if valid_score < 0.7:
                return "", 0.0
                
        # Return empty for unmatched genres to prevent false positives
        return "", 0.0

    @classmethod
    def _find_best_match(cls, genre: str, candidates: Set[str]) -> Tuple[str, float]:
        """Find the best matching genre from a set of candidates.
        
        Args:
            genre: The genre to find a match for
            candidates: Set of candidate genres to match against
            
        Returns:
            Tuple of (best matching genre, similarity score)
        """
        best_score = 0
        best_match = genre

        for candidate in candidates:
            # Calculate base similarity score
            score = SequenceMatcher(None, genre.lower(), candidate.lower()).ratio()
            
            # Apply bonuses for partial matches
            if genre.lower() in candidate.lower() or candidate.lower() in genre.lower():
                score += 0.1
                
            # Bonus for matching first word
            genre_first = genre.lower().split()[0]
            candidate_first = candidate.lower().split()[0]
            if genre_first == candidate_first:
                score += 0.1
                
            score = min(score, 1.0)  # Cap at 1.0
            
            if score > best_score:
                best_score = score
                best_match = candidate

        return best_match, best_score

    @classmethod
    def get_parent_genre(cls, genre: str) -> Optional[str]:
        """Get the parent genre for a given genre.
        
        Args:
            genre: The genre to find the parent for
            
        Returns:
            Parent genre name or None if no parent found
        """
        normalized, _ = cls.normalize(genre)
        for parent, children in cls.GENRE_HIERARCHY.items():
            if normalized in children:
                return parent
        return None

    @classmethod
    def normalize_list(cls, genres: List[str]) -> List[Tuple[str, float]]:
        """Normalize a list of genres with confidence scores.
        
        Args:
            genres: List of raw genre names
            
        Returns:
            List of tuples (normalized genre, confidence score)
        """
        return [cls.normalize(g) for g in genres if g]
        
    @classmethod
    def normalize_dict(cls, genres: Dict[str, float]) -> Dict[str, float]:
        """Normalize genre names in a confidence score dictionary with intelligent weighting.
        
        Args:
            genres: Dictionary of genre names to confidence scores
            
        Returns:
            Dictionary with normalized genre names and adjusted confidence scores
        """
        if not genres:
            return {}

        THRESHOLD = 0.4

        # First pass: Normalize and filter based on threshold
        intermediate = {}
        
        for genre, score in genres.items():
            if score < THRESHOLD:
                continue
            
            # Check special cases first
            lower_genre = genre.lower()
            if lower_genre in cls.SPECIAL_CASES:
                norm_name = cls.SPECIAL_CASES[lower_genre]
                intermediate[norm_name] = score
                continue
                
            # Keep valid genres as-is
            if genre in cls.VALID_GENRES:
                intermediate[genre] = score
                continue
                
            # Try normalizing unknown genres
            norm_name, norm_score = cls.normalize(genre)
            if norm_name and norm_score * score >= THRESHOLD:
                intermediate[norm_name] = score # Keep original score for consistency
                
        if not intermediate:
            return {}
            
        # Second pass: Add parent and base genres with derived scores
        all_genres = {}  # Start fresh to control order of addition
        
        # Add parent genres first (they get priority)
        for genre, score in intermediate.items():
            parent = cls.get_parent_genre(genre)
            if parent:
                parent_score = score * 0.95
                if parent not in all_genres or parent_score > all_genres[parent]:
                    all_genres[parent] = parent_score
                    
        # Add original genres next (preserving their scores)
        for genre, score in intermediate.items():
            if score >= THRESHOLD:
                all_genres[genre] = score
                    
        # Finally add base genres from compounds
        for genre, score in intermediate.items():
            if " " in genre:
                parts = genre.split()
                for part in parts:
                    if part in cls.GENRE_HIERARCHY:
                        base_score = score * 0.95
                        if part not in all_genres or base_score > all_genres[part]:
                            all_genres[part] = base_score
                            
        # Sort by confidence (descending) then name (ascending)
        sorted_genres = sorted(all_genres.items(), key=lambda x: (-x[1], x[0]))
        
        # Build final result with top 3 genres
        final = {}
        for genre, score in sorted_genres:
            if score >= THRESHOLD:
                final[genre] = score
                if len(final) >= 3:
                    break

        return final

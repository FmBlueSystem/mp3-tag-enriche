"""Genre detection and analysis module."""
from typing import Dict, List, Optional
from pathlib import Path
import json
import os
from .music_apis import MusicAPI
from .file_handler import Mp3FileHandler
from .genre_normalizer import GenreNormalizer

# Import all available API classes for convenience
try:
    from .spotify_api import SpotifyAPI
except ImportError:
    SpotifyAPI = None

class GenreDetector:
    """Detect and normalize music genres from various sources."""
    
    def __init__(self, apis: Optional[List[MusicAPI]] = None, file_handler: Optional[Mp3FileHandler] = None):
        """Initialize genre detector.
        
        Args:
            apis: List of music APIs to use for genre detection
            file_handler: Mp3FileHandler instance to use (will create new one if None)
        """
        self.apis = apis or []
        self.file_handler = file_handler if file_handler else Mp3FileHandler()
        self.confidence_threshold = 0.5
        self.max_genres = 5
        self._genre_cache = {}
        
    def _merge_genre_scores(self, genre_scores: List[Dict[str, float]]) -> Dict[str, float]:
        """Merge and normalize genre confidence scores."""
        # First pass: normalize names and find highest scores
        max_scores = {}
        for scores in genre_scores:
            for genre, score in scores.items():
                norm_genre, norm_conf = GenreNormalizer.normalize(genre)
                combined_score = score * norm_conf  # Combine API score with normalization confidence
                if norm_genre not in max_scores or combined_score > max_scores[norm_genre]:
                    max_scores[norm_genre] = combined_score
                    
        if not max_scores:
            return {}
            
        # Apply confidence threshold
        filtered = {g: s for g, s in max_scores.items() if s >= self.confidence_threshold}
        
        # If nothing passes threshold, take top scoring genres
        if not filtered:
            sorted_items = sorted(max_scores.items(), key=lambda x: x[1], reverse=True)
            top_genres = sorted_items[:self.max_genres]
            if top_genres:  # Only keep if we found any genres
                filtered = dict(top_genres)
            
        # Apply max genres limit
        if len(filtered) > self.max_genres:
            sorted_items = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
            filtered = dict(sorted_items[:self.max_genres])
            
        # Keep original scores but ensure they sum to 1.0
        total = sum(filtered.values())
        if total > 0:
            result = {g: s/total for g, s in filtered.items()}
            return result
            
        return {}
        
    def analyze_file(self, file_path: str, chunk_size: int = 8192) -> Dict:
        """Analyze an MP3 file to detect genres.
        
        Args:
            file_path: Ruta al archivo MP3
            chunk_size: Tamaño del chunk para lectura en bytes (default: 8KB)
        """
        result = {
            "file_info": {},
            "metadata": {},
            "current_genres": [],
            "detected_genres": {},
            "year": None,  # Initialize year field
            "api_results": {}  # Store individual API results
        }
        
        # Get file info usando chunks
        file_info = self.file_handler.get_file_info(file_path, chunk_size=chunk_size)
        if not file_info:
            result["error"] = "No se pudo leer la información del archivo"
            return result
            
        result["file_info"] = file_info
        
        # Extract and normalize current genres
        current_genres = file_info.get('current_genre', '').split(';')
        current_genres = [g.strip() for g in current_genres if g.strip()]
        result["current_genres"] = GenreNormalizer.normalize_list(current_genres)
        
        # Get metadata usando tags leídos previamente
        metadata = {
            'title': file_info.get('title'),
            'artist': file_info.get('artist'),
            'album': file_info.get('album')
        }
        
        # Liberar recursos explícitamente
        if hasattr(file_info, 'clear'):
            file_info.clear()
        result["metadata"] = metadata
        
        print(f"\nProcessing: {metadata['artist']} - {metadata['title']}")
        
        # Check cache first - only use cache for valid artist/title combinations
        if metadata['artist'] and metadata['title'] and metadata['artist'] != "None" and metadata['title'] != "None":
            cache_key = f"{metadata['artist']}_{metadata['title']}"
            if cache_key in self._genre_cache:
                cached_data = self._genre_cache[cache_key]
                result["detected_genres"] = cached_data.get("detected_genres", {})
                result["year"] = cached_data.get("year")
                result["source"] = "cache"
                return result
            
        # Query APIs
        api_results = []
        api_errors = []
        
        for api in self.apis:
            try:
                print(f"Querying {api.__class__.__name__}...")
                track_info = api.get_track_info(metadata['artist'], metadata['title'])
                
                # Store complete API result for later access
                result["api_results"][api.__class__.__name__] = track_info
                
                # Extract year information if available
                if not result["year"] and track_info.get("year"):
                    result["year"] = track_info["year"]
                
                genres = track_info.get('genres', [])
                # Convert list of genres to dict with confidence scores (1.0 for each)
                genre_scores = {genre: 1.0 for genre in genres}
                print(f"Found genres: {genre_scores}")
                if genre_scores:
                    api_results.append(genre_scores)
            except Exception as e:
                error_msg = f"Error with {api.__class__.__name__}: {e}"
                print(error_msg)
                api_errors.append(error_msg)
                
        if not api_results:
            # En lugar de error, continuamos con géneros vacíos
            result["detected_genres"] = {}
            result["warning"] = "API Error" if api_errors else "No genres detected from APIs"
            return result
            
        # Merge and normalize results
        merged_genres = self._merge_genre_scores(api_results)
        if not merged_genres:
            # En lugar de error, continuamos con géneros vacíos
            result["detected_genres"] = {}
            result["warning"] = "No genres met confidence threshold"
            return result
            
        # Store original scores and year in the result
        result["detected_genres"] = merged_genres
        
        # Create a cache entry with more comprehensive information
        cache_entry = {
            "detected_genres": merged_genres,
            "year": result.get("year")
        }
        
        # Only cache results for valid metadata
        if metadata['artist'] and metadata['title'] and metadata['artist'] != "None" and metadata['title'] != "None":
            cache_key = f"{metadata['artist']}_{metadata['title']}"
            self._genre_cache[cache_key] = cache_entry
            
        return result
        
    def analyze_files(self, file_paths: List[str], chunk_size: int = 8192) -> Dict[str, Dict]:
        """Analyze multiple files.
        
        Args:
            file_paths: Lista de rutas de archivos MP3
            chunk_size: Tamaño del chunk para lectura en bytes (default: 8KB)
        """
        results = {}
        for path in file_paths:
            try:
                results[path] = self.analyze_file(path, chunk_size=chunk_size)
            except Exception as e:
                results[path] = {"error": f"Error al analizar {path}: {str(e)}"}
        return results

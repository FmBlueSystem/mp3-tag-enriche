"""Genre detection and analysis module."""
from typing import Dict, List, Optional
from pathlib import Path
import json
import os
import logging # Importar logging
from .music_apis import MusicAPI
from .file_handler import Mp3FileHandler
from .genre_normalizer import GenreNormalizer

# Configurar un logger básico para el módulo
logger = logging.getLogger(__name__)

class GenreDetector:
    """Detect and normalize music genres from various sources."""
    
    def __init__(self, apis: Optional[List[MusicAPI]] = None, verbose: bool = False, file_handler: Optional[Mp3FileHandler] = None): # MODIFICADO
        """Initialize genre detector."""
        self.apis = apis or []
        if file_handler:
            self.file_handler = file_handler
        else:
            logger.info("GenreDetector: No Mp3FileHandler provided, creating a default one.")
            self.file_handler = Mp3FileHandler() # Crea uno por defecto si no se proporciona
        self.confidence_threshold = 0.5
        self.max_genres = 5
        self._genre_cache = {}
        self.verbose = verbose # Almacenar verbose
        if self.verbose:
            logger.setLevel(logging.INFO) # O logging.DEBUG para más detalle
        else:
            logger.setLevel(logging.WARNING) # O superior para menos detalle
        
    def _merge_genre_scores(self, genre_scores: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Merge genre confidence scores from multiple API results.
        Normalizes genre names, takes the highest score for each normalized genre,
        applies a confidence threshold, and then limits by max_genres.
        The returned scores are the direct scores that passed the threshold and limits,
        and do not necessarily sum to 1.0.
        """
        # First pass: normalize names and find highest scores
        max_scores = {}
        for scores in genre_scores:
            for genre, score in scores.items():
                norm_genre = GenreNormalizer.normalize(genre)
                if norm_genre not in max_scores or score > max_scores[norm_genre]:
                    max_scores[norm_genre] = score
                    
        if not max_scores:
            return {}
            
        # Apply confidence threshold
        filtered = {g: s for g, s in max_scores.items() if s >= self.confidence_threshold}
        
        # If nothing passes threshold, take top scoring genres from original max_scores
        # (before applying the initial confidence threshold)
        if not filtered and max_scores: # Check max_scores to ensure it's not empty
            logger.info("No genres met the initial confidence threshold. Considering top genres before threshold.")
            sorted_items_before_threshold = sorted(max_scores.items(), key=lambda x: x[1], reverse=True)
            top_genres = sorted_items_before_threshold[:self.max_genres]
            if top_genres:
                filtered = dict(top_genres)
            
        # Apply max genres limit
        if len(filtered) > self.max_genres:
            logger.info(f"Limiting {len(filtered)} genres to {self.max_genres} based on score.")
            sorted_items = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
            filtered = dict(sorted_items[:self.max_genres])
            
        # Scores are returned as they are after filtering; they do not necessarily sum to 1.0.
        return filtered
        
    def analyze_file(self, file_path: str) -> Dict:
        """Analyze an MP3 file to detect genres."""
        logger.info(f"Starting analysis for file: {file_path}")
        result = {
            "file_info": {},
            "metadata": {},
            "current_genres": [],
            "detected_genres": {}
        }
        
        # Get file info
        file_info = self.file_handler.get_file_info(file_path)
        if not file_info:
            logger.error(f"Could not read file info for {file_path}")
            result["error"] = "Could not read file info"
            return result
            
        result["file_info"] = file_info
        
        # Extract and normalize current genres
        current_genres_str = file_info.get('current_genre', '')
        current_genres_list = [g.strip() for g in current_genres_str.split(';') if g.strip()]
        result["current_genres"] = GenreNormalizer.normalize_list(current_genres_list)
        logger.info(f"Current genres for {file_path}: {result['current_genres']}")
        
        # Get metadata
        metadata = {
            'title': file_info.get('title'),
            'artist': file_info.get('artist'),
            'album': file_info.get('album')
        }
        result["metadata"] = metadata
        
        logger.info(f"Processing: Artist - {metadata.get('artist', 'N/A')}, Title - {metadata.get('title', 'N/A')}")
        
        # Check cache first
        cache_key = f"{metadata.get('artist', '')}_{metadata.get('title', '')}"
        if cache_key in self._genre_cache:
            logger.info(f"Found in cache for {cache_key}")
            result["detected_genres"] = self._genre_cache[cache_key]
            result["source"] = "cache"
            return result
            
        # Query APIs
        api_results = []
        api_errors = []
        
        for api in self.apis:
            try:
                logger.info(f"Querying {api.__class__.__name__}...")
                genres = api.get_genres(metadata['artist'], metadata['title'])
                logger.info(f"Found genres from {api.__class__.__name__}: {genres}")
                if genres:
                    api_results.append(genres)
            except Exception as e:
                error_msg = f"Error with {api.__class__.__name__}: {e}"
                logger.error(error_msg)
                api_errors.append(error_msg)
                
        if not api_results:
            err_msg = "API Error during processing." if api_errors else "No genres detected from APIs."
            logger.warning(f"{err_msg} For Artist: {metadata.get('artist', 'N/A')}, Title: {metadata.get('title', 'N/A')}")
            result["error"] = err_msg
            return result
            
        # Merge and normalize results
        merged_genres = self._merge_genre_scores(api_results)
        if not merged_genres:
            logger.warning(f"No genres met confidence/ranking criteria for Artist: {metadata.get('artist', 'N/A')}, Title: {metadata.get('title', 'N/A')}")
            result["error"] = "No genres met confidence threshold or ranking criteria" # Mensaje actualizado
            return result
            
        logger.info(f"Detected genres for {cache_key}: {merged_genres}")
        result["detected_genres"] = merged_genres
        self._genre_cache[cache_key] = merged_genres
        return result
        
    def analyze_files(self, file_paths: List[str]) -> Dict[str, Dict]:
        """Analyze multiple files."""
        return {path: self.analyze_file(path) for path in file_paths}

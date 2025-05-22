"""Spotify API integration for genre detection."""
from typing import Dict, List, Optional, Any
import logging
import re
import time
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from .rate_limiter import RateLimiter
from .persistent_cache import PersistentCache
from .api_metrics import MetricsTracker
from .genre_normalizer import GenreNormalizer
from .music_apis import MusicAPI

# Configure logging
logger = logging.getLogger(__name__)

# Get shared instances of rate limiter, metrics tracker
from .music_apis import _rate_limiter, _metrics, CACHE_DIR

class SpotifyAPI(MusicAPI):
    """Spotify API integration with rate limiting and metrics."""
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, cache_ttl: int = 3600):
        """Initialize Spotify API client.
        
        Args:
            client_id: Spotify API client ID (optional, will use SPOTIPY_CLIENT_ID env var if not provided)
            client_secret: Spotify API client secret (optional, will use SPOTIPY_CLIENT_SECRET env var if not provided)
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        super().__init__(cache_ttl=cache_ttl)
        
        try:
            # Use provided credentials or environment variables
            # The SpotifyClientCredentials will automatically check for environment variables
            # SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET if not explicitly provided
            auth_manager = SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            logger.info("Successfully initialized Spotify API client")
        except Exception as e:
            logger.error(f"Failed to initialize Spotify API client: {e}")
            self.sp = None
    
    def _setup_rate_limits(self):
        """Configure Spotify-specific rate limits."""
        # Spotify allows ~1 request per second for search endpoints
        _rate_limiter.create_limit(
            f"{self.api_name}_search",
            capacity=5,     # Allow burst of 5 requests
            fill_rate=1.0   # 1 token per second
        )
        
        # Separate limit for artist/track/album lookups
        _rate_limiter.create_limit(
            f"{self.api_name}_lookup",
            capacity=5,     # Allow burst of 5 requests
            fill_rate=1.0   # 1 token per second
        )
    
    def get_track_info(self, artist: str, track: str) -> Dict[str, Any]:
        """Get track information from Spotify.
        
        Args:
            artist: Artist name
            track: Track title
            
        Returns:
            Dict with track information
            
        Raises:
            RuntimeError: If rate limit is exceeded or API is not initialized
        """
        # Initialize result with empty values
        result = {
            "genres": [],
            "year": None,
            "album": None,
            "source_api": "Spotify"
        }
        
        # Handle None or empty values
        if artist is None or track is None or artist == "None" or track == "None" or not artist.strip() or not track.strip():
            return result
            
        cache_key = f"spotify_info:{artist}:{track}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for Spotify info: {artist} - {track}")
            return cached

        start_time = time.time()

        if not self.sp:
            logger.warning("Spotify client not initialized. Skipping Spotify query.")
            self._track_api_call(start_time, success=False)
            return result

        # Enforce rate limit before API call
        self._enforce_rate_limit("search")
        
        try:
            # Search for track
            search_query = f"artist:{artist} track:{track}"
            search_results = self.sp.search(q=search_query, type='track', limit=5)
            
            if not search_results.get('tracks', {}).get('items'):
                # Try a more general search if specific one fails
                search_query = f"{artist} {track}"
                search_results = self.sp.search(q=search_query, type='track', limit=5)
                
            if not search_results.get('tracks', {}).get('items'):
                logger.info(f"No tracks found on Spotify for {artist} - {track}")
                self._track_api_call(start_time, success=True)
                return result
            
            # Get the most relevant track
            track_data = search_results['tracks']['items'][0]
            
            # Get album info
            if track_data.get('album'):
                result['album'] = track_data['album'].get('name')
                
                # Get release year from release date
                if track_data['album'].get('release_date'):
                    match_y = re.search(r'(\d{4})', track_data['album']['release_date'])
                    if match_y:
                        extracted_year = int(match_y.group(1))
                        if 1900 <= extracted_year <= 2030:
                            result['year'] = str(extracted_year)
                        else:
                            logger.warning(
                                f"Invalid year {extracted_year} in album release date for"
                                f" {artist} - {track}"
                            )
            
            # Get artist genres
            if track_data.get('artists') and len(track_data['artists']) > 0:
                # Get primary artist ID for genre lookup
                artist_id = track_data['artists'][0]['id']
                
                # Enforce rate limit for artist lookup
                self._enforce_rate_limit("lookup")
                
                # Get detailed artist info for genre data
                artist_data = self.sp.artist(artist_id)
                if artist_data.get('genres'):
                    # Format genres with title case
                    result['genres'] = [genre.title() for genre in artist_data['genres']]
            
            # Limit to top 5 genres
            result['genres'] = result['genres'][:5]
            
        except Exception as e:
            logger.error(f"Error getting Spotify data for {artist} - {track}: {e}")
            self._track_api_call(start_time, success=False)
            return result
        
        # Record successful API call
        self._track_api_call(start_time, success=True)
        
        # Cache successful results
        self.cache.set(cache_key, result)
        return result
    
    def search_by_year_and_genre(self, year: Optional[str] = None, genre: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search for tracks by year and/or genre.
        
        Args:
            year: Release year (optional)
            genre: Genre name (optional)
            limit: Maximum number of results to return (default: 10)
            
        Returns:
            List of track data dictionaries
        """
        if not self.sp:
            logger.warning("Spotify client not initialized. Skipping search.")
            return []
            
        if not year and not genre:
            logger.warning("No search criteria provided (year or genre required)")
            return []
        
        # Build search query
        query_parts = []
        if year:
            query_parts.append(f"year:{year}")
        if genre:
            query_parts.append(f"genre:{genre}")
        
        query = " ".join(query_parts)
        
        # Enforce rate limit
        self._enforce_rate_limit("search")
        
        try:
            # Execute search
            results = self.sp.search(q=query, type='track', limit=limit)
            
            # Process results
            tracks = []
            for item in results['tracks']['items']:
                track_info = {
                    'name': item['name'],
                    'artist': item['artists'][0]['name'],
                    'album': item['album']['name'],
                    'release_date': item['album']['release_date'],
                    'popularity': item['popularity'],
                    'preview_url': item['preview_url'],
                    'external_url': item['external_urls']['spotify']
                }
                tracks.append(track_info)
                
            return tracks
            
        except Exception as e:
            logger.error(f"Error searching Spotify by year/genre: {e}")
            return []

"""Music API integrations for genre detection."""
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, List, Optional
import requests
import musicbrainzngs
import pylast
from bs4 import BeautifulSoup
import time
import logging
import re
import os
from pathlib import Path

from .rate_limiter import RateLimiter
from .persistent_cache import PersistentCache
from .api_metrics import MetricsTracker
from .genre_normalizer import GenreNormalizer
from .http_client import HTTPClient, CircuitBreakerConfig

# Claves API (idealmente se pasarían en el constructor o se leerían de config)
# Por ahora, para Discogs, si es necesario, se puede definir aquí temporalmente o asumir que se pasa.
DISCOGS_API_TOKEN_MUSIC_APIS = "pTWfxAgLTSTbXzbNFvAvqXNKawGiDVELrBLnfoNv" # Reutilizar el token
DISCOGS_BASE_URL_MUSIC_APIS = "https://api.discogs.com/"
LASTFM_API_KEY_MUSIC_APIS = "b7651b3758d74bd0f47df535a5ddf45d"
LASTFM_API_SECRET_MUSIC_APIS = "eb38d3f09f394d652c93d948972a3285" # Necesitarás el secret si no está ya

# Configure logging
logger = logging.getLogger(__name__)

# Global rate limiter, cache, and metrics instances
_rate_limiter = RateLimiter()
_metrics = MetricsTracker()

# Ensure cache directory exists
CACHE_DIR = Path("cache/music_apis")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class MusicAPI(ABC):
    """Base class for music API integrations."""
    
    def __init__(self, cache_ttl: int = 3600):
        """Initialize the API client.
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.api_name = self.__class__.__name__
        
        # Initialize persistent cache for this API
        cache_path = CACHE_DIR / self.api_name.lower()
        self.cache = PersistentCache(cache_path, cache_ttl)
        
        # Configure rate limiting for this API
        self._setup_rate_limits()
        
    def _setup_rate_limits(self):
        """Configure API-specific rate limits. Override in subclasses."""
        # Default conservative limits
        _rate_limiter.create_limit(
            f"{self.api_name}_default",
            capacity=10,   # burst capacity
            fill_rate=1.0  # tokens per second
        )
    
    def _enforce_rate_limit(self, limit_key: str = None):
        """Enforce rate limiting using token bucket.
        
        Args:
            limit_key: Specific rate limit key, or None for default
        """
        key = f"{self.api_name}_{limit_key or 'default'}"
        start_time = time.time()
        
        # Try to acquire token
        if not _rate_limiter.acquire(key, wait=True):
            _metrics.record_api_call(
                self.api_name,
                success=False,
                latency=time.time() - start_time,
                rate_limited=True
            )
            raise RuntimeError(f"Rate limit exceeded for {self.api_name}")

    def _track_api_call(self, start_time: float, success: bool, rate_limited: bool = False):
        """Record API call metrics.
        
        Args:
            start_time: Call start timestamp
            success: Whether call succeeded
            rate_limited: Whether call was rate limited
        """
        _metrics.record_api_call(
            self.api_name,
            success=success,
            latency=time.time() - start_time,
            rate_limited=rate_limited
        )

    def get_metrics(self) -> Mapping[str, float]:
        """Get current metrics for this API."""
        return _metrics.get_metrics(self.api_name)

    @abstractmethod
    def get_track_info(self, artist: str, track: str) -> Mapping[str, Any]:
        """Get track information (genres, year, album).
        
        Args:
            artist: Artist name
            track: Track title
            
        Returns:
            Dict with track information
        """
        # Handle None or empty values
        if not artist or not track or artist == "None" or track == "None":
            return {
                "genres": [],
                "year": None,
                "album": None,
                "source_api": "None",
                "error": "Missing artist or track"
            }
        # Implementation provided by subclasses
        pass

    def get_genres(self, artist: str, track: str) -> Mapping[str, float]:
        """Get genres with confidence scores for a track.
        
        Args:
            artist: Artist name
            track: Track title
            
        Returns:
            Dict mapping genre names to confidence scores
        """
        # Handle None or empty values
        if artist is None or track is None or artist == "None" or track == "None" or not artist.strip() or not track.strip():
            return {}
            
        track_info = self.get_track_info(artist, track)
        genres = track_info.get("genres", [])
        
        # Assign confidence scores based on position
        result = {}
        for i, genre in enumerate(genres):
            # Decrease confidence score as position increases
            confidence = 1.0 - (i * 0.1)
            if confidence < 0.5:  # Set minimum confidence threshold
                confidence = 0.5
            result[genre] = confidence
            
        # Normalize the genre names using GenreNormalizer
        normalized_genres = {}
        for genre, score in result.items():
            norm_genre = GenreNormalizer.normalize(genre)[0]  # Solo tomamos el nombre normalizado
            if norm_genre in normalized_genres:
                normalized_genres[norm_genre] = max(normalized_genres[norm_genre], score)
            else:
                normalized_genres[norm_genre] = score
                
        return normalized_genres
    # Por ahora lo comentamos para enfocarnos en get_track_info.
    # @abstractmethod
    # def get_genres(self, artist: str, track: str) -> Dict[str, float]:
    #     pass

class MusicBrainzAPI(MusicAPI):
    """MusicBrainz API integration with rate limiting and metrics."""
    
    def __init__(self, app_name: str = "GenreDetector", version: str = "0.1.0", email: str = ""):
        """Initialize MusicBrainz API client.
        
        Args:
            app_name: Application name for user agent
            version: Application version
            email: Email for user agent
        """
        super().__init__()
        musicbrainzngs.set_useragent(app_name, version, email)
    
    def _setup_rate_limits(self):
        """Configure MusicBrainz-specific rate limits."""
        # Main search rate limit (1 request/sec)
        _rate_limiter.create_limit(
            f"{self.api_name}_search",
            capacity=2,     # Allow burst of 2 requests
            fill_rate=1.0   # 1 token per second
        )
        
        # Release lookup rate limit
        _rate_limiter.create_limit(
            f"{self.api_name}_lookup",
            capacity=2,     # Allow burst of 2 requests
            fill_rate=1.0   # 1 token per second
        )
        
    def get_track_info(self, artist: str, track: str) -> Mapping[str, Any]:
        """Get track information from MusicBrainz.
        
        Args:
            artist: Artist name
            track: Track title
            
        Returns:
            Dict with track information
            
        Raises:
            RuntimeError: If rate limit is exceeded
            ValueError: If input validation fails
        """
        # Initialize result with empty values
        result = {
            "genres": [],
            "year": None,
            "album": None,
            "source_api": "MusicBrainz"
        }
        
        # Handle None or empty values
        if artist is None or track is None or artist == "None" or track == "None" or not artist.strip() or not track.strip():
            return result
            
        cache_key = f"mb_info:{artist}:{track}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for MusicBrainz info: {artist} - {track}")
            return cached

        start_time = time.time()
        genres: List[str] = []
        year: Optional[str] = None
        album: Optional[str] = None

        try:
            # Input validation
            if not artist.strip() or not track.strip():
                raise ValueError(f"Empty artist or track name: {artist} - {track}")

            # Search for recording with rate limiting
            self._enforce_rate_limit("search")
            try:
                rec_result = musicbrainzngs.search_recordings(artist=artist, recording=track, limit=5)
            except ValueError as e:
                raise ValueError(f"Invalid search query for MusicBrainz: {e}")
            except musicbrainzngs.WebServiceError as e:
                raise RuntimeError(f"MusicBrainz search failed: {e}")
                
            if not rec_result.get("recording-list"):
                logger.info(f"No recordings found for {artist} - {track}")
                self._track_api_call(start_time, success=True)
                return result
                
            recording = rec_result["recording-list"][0]
            
            # Extract genres from recording tags
            if "tag-list" in recording:
                genres.extend(tag["name"].title() for tag in recording["tag-list"] if tag.get("name"))

            # Get release details if available
            if recording.get("release-list"):
                for release_item in recording["release-list"][:1]:
                    try:
                        self._enforce_rate_limit("lookup")
                        release_details = musicbrainzngs.get_release_by_id(
                            release_item["id"],
                            includes=["media", "release-groups"]
                        )
                        
                        if release_details.get("release"):
                            release_data = release_details["release"]
                            
                            # Get album title
                            if not album and release_data.get("title"):
                                album = str(release_data["title"]).strip()
                            
                            # Try to get year from release date
                            if not year and release_data.get("date"):
                                match_y = re.search(r'(\d{4})', release_data["date"])
                                if match_y:
                                    extracted_year = int(match_y.group(1))
                                    if 1900 <= extracted_year <= 2030:
                                        year = str(extracted_year)
                                    else:
                                        logger.warning(
                                            f"Invalid year {extracted_year} in release date for"
                                            f" {artist} - {track}"
                                        )
                            
                            # Try release group date as fallback
                            if not year and release_data.get("release-group", {}).get("first-release-date"):
                                match_y = re.search(
                                    r'(\d{4})',
                                    release_data["release-group"]["first-release-date"]
                                )
                                if match_y:
                                    extracted_year = int(match_y.group(1))
                                    if 1900 <= extracted_year <= 2030:
                                        year = str(extracted_year)
                                    else:
                                        logger.warning(
                                            f"Invalid year {extracted_year} in release group for"
                                            f" {artist} - {track}"
                                        )
                                        
                    except musicbrainzngs.WebServiceError as e:
                        logger.warning(f"Failed to get release details: {e}")
                        continue
            
            # Get additional genres from artist if needed
            if not genres or len(genres) < 3:
                try:
                    self._enforce_rate_limit("search")
                    artist_result = musicbrainzngs.search_artists(artist=artist, limit=1)
                    
                    if artist_result.get("artist-list"):
                        artist_data = artist_result["artist-list"][0]
                        if "tag-list" in artist_data:
                            genres.extend(
                                tag["name"].title()
                                for tag in artist_data["tag-list"]
                                if tag.get("name") and tag["name"].title() not in genres
                            )
                except musicbrainzngs.WebServiceError as e:
                    logger.warning(f"Failed to get artist details: {e}")

            # Remove duplicates and limit genres
            unique_genres = []
            seen = set()
            for genre in genres:
                if genre.lower() not in seen:
                    unique_genres.append(genre)
                    seen.add(genre.lower())
            genres = unique_genres[:5]

        except (ValueError, RuntimeError) as e:
            logger.error(str(e))
            self._track_api_call(start_time, success=False)
            return result
        except Exception as e:
            logger.error(
                f"Unexpected error with MusicBrainz for {artist} - {track}: {e}",
                exc_info=True
            )
            self._track_api_call(start_time, success=False)
            return result

        # Record successful API call
        self._track_api_call(start_time, success=True)

        # Update result with found data
        result.update({
            "genres": genres,
            "year": year if year and 1900 <= int(year) <= 2030 else None,
            "album": album if album and album.strip() else None
        })
        
        # Cache successful results
        self.cache.set(cache_key, result)
        return result

class LastFmAPI(MusicAPI):
    """Last.fm API integration with rate limiting and metrics."""
    
    def __init__(self, api_key: str = LASTFM_API_KEY_MUSIC_APIS, api_secret: str = LASTFM_API_SECRET_MUSIC_APIS):
        """Initialize Last.fm API client.
        
        Args:
            api_key: Last.fm API key
            api_secret: Last.fm API secret
        """
        super().__init__()
        try:
            self.network = pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret)
        except Exception as e:
            logger.error(f"Failed to initialize LastFMNetwork: {e}")
            self.network = None
            
    def _setup_rate_limits(self):
        """Configure Last.fm-specific rate limits."""
        # Last.fm allows 5 requests per second
        _rate_limiter.create_limit(
            f"{self.api_name}_default",
            capacity=10,    # Allow burst of 10 requests
            fill_rate=5.0   # 5 tokens per second
        )
        
    def get_track_info(self, artist: str, track: str) -> Mapping[str, Any]:
        """Get track information from Last.fm.
        
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
            "source_api": "Last.fm"
        }
        
        # Handle None or empty values
        if artist is None or track is None or artist == "None" or track == "None" or not artist.strip() or not track.strip():
            return result
            
        cache_key = f"lastfm_info:{artist}:{track}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for Last.fm info: {artist} - {track}")
            return cached

        start_time = time.time()

        if not self.network:
            logger.warning("LastFMNetwork not initialized. Skipping Last.fm query.")
            self._track_api_call(start_time, success=False)
            return result

        # Enforce rate limit before API call
        self._enforce_rate_limit()

        try:
            track_obj = self.network.get_track(artist, track)
            if not track_obj:
                logger.info(f"No track found on Last.fm for {artist} - {track}")
                self._track_api_call(start_time, success=True)
                return result
                
            try:
                # Get track tags
                top_tags = track_obj.get_top_tags(limit=5)
                result["genres"].extend(
                    tag.item.get_name().title()
                    for tag in top_tags
                    if tag.item.get_name()
                )
            except pylast.WSError as e:
                logger.warning(f"Failed to get track tags: {e}")

            try:
                # Get album info and year
                track_album = track_obj.get_album()
                if track_album:
                    result["album"] = track_album.get_title().strip()
                    
                    # Try to get year from album release date
                    if hasattr(track_album, 'get_release_date'):
                        release_date = track_album.get_release_date()
                        if release_date:
                            match_y = re.search(r'(\d{4})', release_date)
                            if match_y:
                                extracted_year = int(match_y.group(1))
                                if 1900 <= extracted_year <= 2030:
                                    result["year"] = str(extracted_year)
                                else:
                                    logger.warning(
                                        f"Invalid year {extracted_year} in album release date for"
                                        f" {artist} - {track}"
                                    )
            except pylast.WSError as e:
                logger.warning(f"Failed to get album info: {e}")

            # Try wiki date as fallback for year
            if not result["year"]:
                try:
                    if (hasattr(track_obj, 'get_wiki_published_date') and
                        track_obj.get_wiki_published_date()):
                        wiki_date = track_obj.get_wiki_published_date()
                        match_y = re.search(r'(\d{4})', wiki_date)
                        if match_y:
                            extracted_year = int(match_y.group(1))
                            if 1900 <= extracted_year <= 2030:
                                result["year"] = str(extracted_year)
                            else:
                                logger.warning(
                                    f"Invalid year {extracted_year} in wiki date for"
                                    f" {artist} - {track}"
                                )
                except pylast.WSError as e:
                    logger.warning(f"Failed to get wiki date: {e}")

            # Remove genre duplicates
            unique_genres = []
            seen = set()
            for genre in result["genres"]:
                if genre.lower() not in seen:
                    unique_genres.append(genre)
                    seen.add(genre.lower())
            result["genres"] = unique_genres  # Already limited to 5 by API call
            
        except pylast.WSError as e:
            logger.error(f"Last.fm API error for {artist} - {track}: {e}")
            self._track_api_call(start_time, success=False)
            return result
        except Exception as e:
            logger.error(
                f"Unexpected error with Last.fm for {artist} - {track}: {e}",
                exc_info=True
            )
            self._track_api_call(start_time, success=False)
            return result

        # Record successful API call
        self._track_api_call(start_time, success=True)
        
        # Cache successful results
        self.cache.set(cache_key, result)
        return result

class DiscogsAPI(MusicAPI):
    """Discogs API integration with rate limiting and metrics."""
    
    def __init__(self, api_token: str = DISCOGS_API_TOKEN_MUSIC_APIS):
        """Initialize Discogs API client.
        
        Args:
            api_token: Discogs API token
        """
        super().__init__()
        self.api_token = api_token
        self.base_url = DISCOGS_BASE_URL_MUSIC_APIS
        
        # Initialize HTTP client with connection pooling and circuit breaker
        self.http_client = HTTPClient(
            base_url=self.base_url,
            pool_connections=5,
            pool_maxsize=10,
            max_retries=3,
            timeout=15,
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=5,
                reset_timeout=60.0,
                half_open_timeout=30.0
            )
        )
    
    def _setup_rate_limits(self):
        """Configure Discogs-specific rate limits."""
        # Discogs allows 60 requests per minute for authenticated users
        _rate_limiter.create_limit(
            f"{self.api_name}_search",
            capacity=5,     # Allow burst of 5 requests
            fill_rate=1.0   # 1 token per second (60/minute)
        )
        
        # Separate limit for release lookups
        _rate_limiter.create_limit(
            f"{self.api_name}_lookup",
            capacity=5,     # Allow burst of 5 requests
            fill_rate=1.0   # 1 token per second
        )
        
    def _request_discogs(self, endpoint: str, params: Optional[Mapping[str, Any]] = None) -> Optional[Mapping[str, Any]]:
        """Make a request to the Discogs API using connection pooling and circuit breaker.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            Response JSON data or None if request failed
            
        Raises:
            RuntimeError: If rate limit is exceeded or circuit breaker is open
        """
        if not self.api_token:
            logger.warning("Discogs API token not configured. Skipping Discogs query.")
            return None
            
        start_time = time.time()
        
        # Determine rate limit key based on endpoint
        limit_key = "lookup" if any(x in endpoint for x in ["masters/", "releases/"]) else "search"
        self._enforce_rate_limit(limit_key)
        
        headers = {
            "Authorization": f"Discogs token={self.api_token}",
            "User-Agent": "GenreDetectorApp/0.2 (+http://example.com)"
        }
        
        response = self.http_client.request(
            method="GET",
            endpoint=endpoint,
            headers=headers,
            params=params
        )
        
        if response is not None:
            try:
                data = response.json()
                self._track_api_call(start_time, success=True)
                return data
            except ValueError as e:
                logger.error(f"Invalid JSON response from Discogs: {e}")
                self._track_api_call(start_time, success=False)
                return None
        
        self._track_api_call(start_time, success=False)
        return None

    def get_track_info(self, artist: str, track: str) -> Mapping[str, Any]:
        """Get track information from Discogs.
        
        Args:
            artist: Artist name
            track: Track title
            
        Returns:
            Dict with track information
            
        Raises:
            RuntimeError: If rate limit is exceeded
        """
        # Initialize result with empty values
        result = {
            "genres": [],
            "year": None,
            "album": None,
            "source_api": "Discogs"
        }
        
        # Handle None or empty values
        if artist is None or track is None or artist == "None" or track == "None" or not artist.strip() or not track.strip():
            return result
            
        cache_key = f"discogs_info:{artist}:{track}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for Discogs info: {artist} - {track}")
            return cached

        start_time = time.time()

        # Search for release
        search_params = {
            "q": f"{artist} - {track}",
            "type": "release",
            "artist": artist,
            "track": track,
            "per_page": 5
        }
        
        search_data = self._request_discogs("database/search", params=search_params)
        if not search_data:
            self._track_api_call(start_time, success=False)
            return result

        # Find best matching release
        release_id = None
        release_type = None
        
        if search_data.get("results"):
            # Try to find master release first
            for item in search_data["results"]:
                if item.get("type") == "master":
                    title = item.get("title", "").lower()
                    if artist.lower() in title and track.lower() in title:
                        release_id = item.get("id")
                        release_type = "masters"
                        break
            
            # Fall back to regular release if no master found
            if not release_id:
                for item in search_data["results"]:
                    if item.get("type") == "release":
                        release_id = item.get("id")
                        release_type = "releases"
                        break
        else:
            logger.info(f"No results found on Discogs for {artist} - {track}")
        
        # Get release details if we found a match
        if release_id and release_type:
            release_data = self._request_discogs(f"{release_type}/{release_id}")
            
            if release_data:
                # Get genres and styles
                if release_data.get("genres"):
                    result["genres"].extend(g.title() for g in release_data["genres"])
                if release_data.get("styles"):
                    result["genres"].extend(s.title() for s in release_data["styles"])

                # Get year from either direct year field or release date
                if release_data.get("year"):
                    year = str(release_data["year"])
                    if 1900 <= int(year) <= 2030:
                        result["year"] = year
                    else:
                        logger.warning(
                            f"Invalid year {year} in release data for {artist} - {track}"
                        )
                elif release_data.get("released"):
                    match_y = re.search(r'(\d{4})', str(release_data["released"]))
                    if match_y:
                        year = match_y.group(1)
                        if 1900 <= int(year) <= 2030:
                            result["year"] = year
                        else:
                            logger.warning(
                                f"Invalid year {year} from release date for {artist} - {track}"
                            )

                # Get album title
                if release_data.get("title"):
                    result["album"] = release_data["title"].strip()

                # Remove genre duplicates
                unique_genres = []
                seen = set()
                for genre in result["genres"]:
                    if genre.lower() not in seen:
                        unique_genres.append(genre)
                        seen.add(genre.lower())
                result["genres"] = unique_genres[:5]  # Limit to 5 genres

        # Record successful API call and cache result
        self._track_api_call(start_time, success=True)
        self.cache.set(cache_key, result)
        return result

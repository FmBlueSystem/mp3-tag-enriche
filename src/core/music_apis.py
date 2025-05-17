"""Music API integrations for genre detection."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from cachetools import TTLCache
from ratelimit import limits
import requests
import musicbrainzngs
import pylast
from bs4 import BeautifulSoup
import time

class MusicAPI(ABC):
    """Base class for music API integrations."""
    
    def __init__(self, cache_ttl: int = 3600):
        """Initialize the API client with caching.
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.cache = TTLCache(maxsize=100, ttl=cache_ttl)
        
    @abstractmethod
    def get_genres(self, artist: str, track: str) -> List[str]:
        """Get genres for a track.
        
        Args:
            artist: Artist name
            track: Track title
            
        Returns:
            List of genre strings
        """
        pass

class MusicBrainzAPI(MusicAPI):
    """MusicBrainz API integration."""
    
    def __init__(self, app_name: str = "GenreDetector", version: str = "0.1.0"):
        """Initialize MusicBrainz API client.
        
        Args:
            app_name: Application name for user agent
            version: Application version
        """
        super().__init__()
        musicbrainzngs.set_useragent(app_name, version)
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Enforce rate limiting with sleep."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < 2:  # Ensure 2 seconds between requests
            time.sleep(2 - elapsed)
        self.last_request_time = time.time()
        
    def get_genres(self, artist: str, track: str) -> List[str]:
        """Get genres from MusicBrainz."""
        cache_key = f"mb:{artist}:{track}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        self._rate_limit()  # Apply rate limiting
            
        try:
            result = musicbrainzngs.search_recordings(
                artist=artist,
                recording=track,
                limit=1
            )
            if result["recording-list"]:
                recording = result["recording-list"][0]
                genres = []
                if "tag-list" in recording:
                    genres.extend(tag["name"] for tag in recording["tag-list"]
                                if tag["name"].lower() != "seen live")
                
                # Also search for artist tags
                time.sleep(1)  # Wait before artist query
                artist_result = musicbrainzngs.search_artists(artist, limit=1)
                if artist_result.get("artist-list"):
                    artist_data = artist_result["artist-list"][0]
                    if "tag-list" in artist_data:
                        genres.extend(tag["name"] for tag in artist_data["tag-list"])
                
                genres = list(set(genres))  # Remove duplicates
                self.cache[cache_key] = genres
                return genres
                
        except Exception as e:
            print(f"MusicBrainz API error: {e}")
            return []
            
        return []

class LastFmAPI(MusicAPI):
    """Last.fm API integration."""
    
    def __init__(self, api_key: str, api_secret: str):
        """Initialize Last.fm API client.
        
        Args:
            api_key: Last.fm API key
            api_secret: Last.fm API secret
        """
        super().__init__()
        self.network = pylast.LastFMNetwork(
            api_key=api_key,
            api_secret=api_secret
        )
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Enforce rate limiting with sleep."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < 1:  # Ensure 1 second between requests
            time.sleep(1 - elapsed)
        self.last_request_time = time.time()
        
    def get_genres(self, artist: str, track: str) -> List[str]:
        """Get genres from Last.fm tags."""
        cache_key = f"lastfm:{artist}:{track}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        self._rate_limit()  # Apply rate limiting
            
        try:
            track_obj = self.network.get_track(artist, track)
            tags = track_obj.get_top_tags(limit=10)
            genres = [tag.item.get_name() for tag in tags]
            
            time.sleep(1)  # Wait before artist query
            # Also get artist genres
            artist_obj = self.network.get_artist(artist)
            artist_tags = artist_obj.get_top_tags(limit=10)
            genres.extend(tag.item.get_name() for tag in artist_tags)
            
            genres = list(set(genres))  # Remove duplicates
            self.cache[cache_key] = genres
            return genres
            
        except Exception as e:
            print(f"Last.fm API error: {e}")
            return []

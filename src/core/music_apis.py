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
    def get_genres(self, artist: str, track: str) -> Dict[str, float]:
        """Get genres for a track.
        
        Args:
            artist: Artist name
            track: Track title
            
        Returns:
            Dict of genre strings and their scores
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
        
    def get_genres(self, artist: str, track: str) -> Dict[str, float]:
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
            raw_genres_list = []
            if result["recording-list"]:
                recording = result["recording-list"][0]
                if "tag-list" in recording:
                    # Guardar tuplas (nombre, cuenta) si está disponible, sino (nombre, 1)
                    raw_genres_list.extend([(tag["name"], tag.get("count", 1)) 
                                            for tag in recording["tag-list"] 
                                            if tag["name"].lower() != "seen live"])
                
                time.sleep(1)  # Wait before artist query
                artist_result = musicbrainzngs.search_artists(artist, limit=1)
                if artist_result.get("artist-list"):
                    artist_data = artist_result["artist-list"][0]
                    if "tag-list" in artist_data:
                        raw_genres_list.extend([(tag["name"], tag.get("count", 1)) 
                                                for tag in artist_data["tag-list"]])
                
            # Convertir lista de tuplas (genre, count) a Dict[str, float]
            # Si hay duplicados, tomar el count más alto. Normalizar counts si es necesario.
            # Por ahora, sumaremos counts para géneros duplicados (después de normalizar nombre de género)
            # y luego normalizaremos todos los counts para que sumen 1.0, o simplemente los usaremos como están.
            # Para simplificar, asignaremos 1.0 a cada género único por ahora.
            # TODO: Implementar una mejor lógica de puntuación basada en "count"
            
            # Primero obtener todos los nombres de género únicos
            unique_genre_names = list(set([g_tuple[0] for g_tuple in raw_genres_list]))
            
            # Crear el diccionario con una puntuación predeterminada (p.ej. 1.0)
            # O, si queremos usar counts, necesitaríamos una normalización más sofisticada.
            # Usaremos 1.0 por ahora para asegurar que sea un diccionario.
            genres_with_scores = {genre: 1.0 for genre in unique_genre_names} 

            self.cache[cache_key] = genres_with_scores
            return genres_with_scores
                
        except Exception as e:
            print(f"MusicBrainz API error: {e}")
            return {}
            
        return {}

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
        
    def get_genres(self, artist: str, track: str) -> Dict[str, float]:
        """Get genres from Last.fm tags."""
        cache_key = f"lastfm:{artist}:{track}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        self._rate_limit()  # Apply rate limiting
        raw_genres_list = []
        try:
            track_obj = self.network.get_track(artist, track)
            tags = track_obj.get_top_tags(limit=10)
            # pylast tags tienen .item.name y .weight (que es un count)
            raw_genres_list.extend([(tag.item.get_name(), float(tag.weight)) for tag in tags])
            
            time.sleep(1)  # Wait before artist query
            artist_obj = self.network.get_artist(artist)
            artist_tags = artist_obj.get_top_tags(limit=10)
            raw_genres_list.extend([(tag.item.get_name(), float(tag.weight)) for tag in artist_tags])
            
            # Similar a MusicBrainz, por ahora convertimos a Dict[str, float] con 1.0
            # TODO: Mejorar la lógica de puntuación usando los weights/counts.
            unique_genre_names = list(set([g_tuple[0] for g_tuple in raw_genres_list]))
            genres_with_scores = {genre: 1.0 for genre in unique_genre_names}

            self.cache[cache_key] = genres_with_scores
            return genres_with_scores
            
        except Exception as e:
            print(f"Last.fm API error: {e}")
            return {}

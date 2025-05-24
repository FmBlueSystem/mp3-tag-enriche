"""
Define los modelos de datos para la base de datos SQLite.
Cada clase representa una tabla en la base de datos.
"""

import json
from typing import Optional, List, Dict, Any
import sqlite3

class Track:
    """
    Representa un track musical en la base de datos.
    Corresponde a la tabla 'tracks'.
    """
    def __init__(self,
                 filepath: str,
                 title: Optional[str] = None,
                 artist: Optional[str] = None,
                 album: Optional[str] = None,
                 genre: Optional[str] = None,
                 year: Optional[int] = None,
                 bpm: Optional[float] = None,
                 key: Optional[str] = None,
                 energy_level: Optional[int] = None,
                 rating: Optional[int] = None,
                 play_count: Optional[int] = None,
                 last_played: Optional[str] = None,
                 date_added: Optional[str] = None,
                 checksum: Optional[str] = None,
                 id: Optional[int] = None):
        self.id = id
        self.filepath = filepath
        self.title = title
        self.artist = artist
        self.album = album
        self.genre = genre
        self.year = year
        self.bpm = bpm
        self.key = key
        self.energy_level = energy_level
        self.rating = rating
        self.play_count = play_count
        self.last_played = last_played
        self.date_added = date_added
        self.checksum = checksum

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto Track a un diccionario."""
        return {
            "id": self.id,
            "filepath": self.filepath,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "genre": self.genre,
            "year": self.year,
            "bpm": self.bpm,
            "key": self.key,
            "energy_level": self.energy_level,
            "rating": self.rating,
            "play_count": self.play_count,
            "last_played": self.last_played,
            "date_added": self.date_added,
            "checksum": self.checksum
        }

    @staticmethod
    def from_row(row: sqlite3.Row) -> 'Track':
        """Crea un objeto Track desde una fila de la base de datos."""
        return Track(
            id=row['id'],
            filepath=row['filepath'],
            title=row['title'],
            artist=row['artist'],
            album=row['album'],
            genre=row['genre'],
            year=row['year'],
            bpm=row['bpm'],
            key=row['key'],
            energy_level=row['energy_level'],
            rating=row['rating'],
            play_count=row['play_count'],
            last_played=row['last_played'],
            date_added=row['date_added'],
            checksum=row['checksum']
        )

class SmartPlaylist:
    """
    Representa una playlist inteligente en la base de datos.
    Corresponde a la tabla 'smart_playlists'.
    """
    def __init__(self,
                 name: str,
                 rules: Dict[str, Any], # Las reglas se almacenarán como JSON string
                 description: Optional[str] = None,
                 created_at: Optional[str] = None,
                 updated_at: Optional[str] = None,
                 id: Optional[int] = None):
        self.id = id
        self.name = name
        self.rules = rules
        self.description = description
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto SmartPlaylist a un diccionario."""
        return {
            "id": self.id,
            "name": self.name,
            "rules": self.rules,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @staticmethod
    def from_row(row: sqlite3.Row) -> 'SmartPlaylist':
        """Crea un objeto SmartPlaylist desde una fila de la base de datos."""
        return SmartPlaylist(
            id=row['id'],
            name=row['name'],
            rules=json.loads(row['rules']), # Cargar reglas desde JSON string
            description=row['description'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

class SyncHistory:
    """
    Representa un evento en el historial de sincronización.
    Corresponde a la tabla 'sync_history'.
    """
    def __init__(self,
                 event_type: str,
                 details: Optional[Dict[str, Any]] = None, # Detalles como JSON string
                 timestamp: Optional[str] = None,
                 id: Optional[int] = None):
        self.id = id
        self.event_type = event_type
        self.details = details
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto SyncHistory a un diccionario."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "details": self.details,
            "timestamp": self.timestamp
        }

    @staticmethod
    def from_row(row: sqlite3.Row) -> 'SyncHistory':
        """Crea un objeto SyncHistory desde una fila de la base de datos."""
        return SyncHistory(
            id=row['id'],
            event_type=row['event_type'],
            details=json.loads(row['details']) if row['details'] else None, # Cargar detalles desde JSON string
            timestamp=row['timestamp']
        )

class Config:
    """
    Representa una entrada de configuración de la aplicación.
    Corresponde a la tabla 'config'.
    """
    def __init__(self,
                 key: str,
                 value: str):
        self.key = key
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto Config a un diccionario."""
        return {
            "key": self.key,
            "value": self.value
        }

    @staticmethod
    def from_row(row: sqlite3.Row) -> 'Config':
        """Crea un objeto Config desde una fila de la base de datos."""
        return Config(
            key=row['key'],
            value=row['value']
        )

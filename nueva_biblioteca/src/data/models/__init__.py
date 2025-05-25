"""
Modelos de datos para Nueva Biblioteca.
"""

from .base import Base, engine, SessionLocal, get_db, create_tables, drop_tables
from .music import Artist, Album, Genre, Track, track_genres, track_artists

__all__ = [
    # Base
    'Base',
    'engine', 
    'SessionLocal',
    'get_db',
    'create_tables',
    'drop_tables',
    
    # Modelos
    'Artist',
    'Album', 
    'Genre',
    'Track',
    
    # Tablas de asociación
    'track_genres',
    'track_artists',
]
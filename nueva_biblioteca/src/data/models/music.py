"""
Modelos de datos para la gestión musical.
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text,
    ForeignKey, Table, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List
from .base import Base

# Tabla de asociación para géneros de tracks (many-to-many)
track_genres = Table(
    'track_genres',
    Base.metadata,
    Column('track_id', Integer, ForeignKey('tracks.id'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genres.id'), primary_key=True)
)

# Tabla de asociación para artistas de tracks (many-to-many)
track_artists = Table(
    'track_artists',
    Base.metadata,
    Column('track_id', Integer, ForeignKey('tracks.id'), primary_key=True),
    Column('artist_id', Integer, ForeignKey('artists.id'), primary_key=True)
)

class Artist(Base):
    """
    Modelo para artistas musicales.
    """
    __tablename__ = 'artists'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    normalized_name = Column(String(255), nullable=False, index=True)  # Para búsquedas
    sort_name = Column(String(255), nullable=True)  # Nombre para ordenamiento
    
    # Metadatos adicionales
    mbid = Column(String(36), nullable=True, unique=True)  # MusicBrainz ID
    spotify_id = Column(String(255), nullable=True, unique=True)
    lastfm_url = Column(String(255), nullable=True)
    
    # Información adicional
    country = Column(String(2), nullable=True)  # Código ISO del país
    begin_date = Column(DateTime, nullable=True)  # Fecha de inicio
    end_date = Column(DateTime, nullable=True)    # Fecha de fin
    biography = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relaciones
    albums = relationship("Album", back_populates="artist")
    tracks = relationship("Track", secondary=track_artists, back_populates="artists")
    
    # Índices
    __table_args__ = (
        Index('idx_artist_normalized_name', 'normalized_name'),
        Index('idx_artist_mbid', 'mbid'),
        UniqueConstraint('normalized_name', name='uq_artist_normalized_name'),
    )
    
    def __repr__(self):
        return f"<Artist(id={self.id}, name='{self.name}')>"

class Album(Base):
    """
    Modelo para álbumes musicales.
    """
    __tablename__ = 'albums'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    normalized_title = Column(String(255), nullable=False, index=True)
    sort_title = Column(String(255), nullable=True)
    
    # Relaciones con artista
    artist_id = Column(Integer, ForeignKey('artists.id'), nullable=False, index=True)
    
    # Metadatos del álbum
    release_date = Column(DateTime, nullable=True)
    year = Column(Integer, nullable=True, index=True)
    total_tracks = Column(Integer, nullable=True)
    total_discs = Column(Integer, nullable=True, default=1)
    
    # Metadatos adicionales
    mbid = Column(String(36), nullable=True, unique=True)
    spotify_id = Column(String(255), nullable=True, unique=True)
    catalog_number = Column(String(100), nullable=True)
    label = Column(String(255), nullable=True)
    
    # Información adicional
    album_type = Column(String(50), nullable=True)  # album, single, ep, compilation
    cover_art_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relaciones
    artist = relationship("Artist", back_populates="albums")
    tracks = relationship("Track", back_populates="album")
    
    # Índices
    __table_args__ = (
        Index('idx_album_artist_title', 'artist_id', 'normalized_title'),
        Index('idx_album_year', 'year'),
        Index('idx_album_mbid', 'mbid'),
    )
    
    def __repr__(self):
        return f"<Album(id={self.id}, title='{self.title}', artist_id={self.artist_id})>"

class Genre(Base):
    """
    Modelo para géneros musicales.
    """
    __tablename__ = 'genres'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    normalized_name = Column(String(100), nullable=False, unique=True, index=True)
    
    # Jerarquía de géneros
    parent_id = Column(Integer, ForeignKey('genres.id'), nullable=True)
    
    # Información adicional
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Color hex para UI
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relaciones
    parent = relationship("Genre", remote_side=[id], backref="children")
    tracks = relationship("Track", secondary=track_genres, back_populates="genres")
    
    def __repr__(self):
        return f"<Genre(id={self.id}, name='{self.name}')>"

class Track(Base):
    """
    Modelo principal para tracks musicales.
    """
    __tablename__ = 'tracks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Información básica del archivo
    file_path = Column(String(500), nullable=False, unique=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    file_size = Column(Integer, nullable=True)  # Tamaño en bytes
    file_format = Column(String(10), nullable=True)  # mp3, flac, etc.
    file_modified = Column(DateTime, nullable=True)  # Última modificación del archivo
    
    # Metadatos básicos
    title = Column(String(255), nullable=False, index=True)
    normalized_title = Column(String(255), nullable=False, index=True)
    
    # Relaciones
    album_id = Column(Integer, ForeignKey('albums.id'), nullable=True, index=True)
    
    # Información del track
    track_number = Column(Integer, nullable=True)
    disc_number = Column(Integer, nullable=True, default=1)
    duration = Column(Float, nullable=True)  # Duración en segundos
    
    # Metadatos técnicos de audio
    bitrate = Column(Integer, nullable=True)  # kbps
    sample_rate = Column(Integer, nullable=True)  # Hz
    channels = Column(Integer, nullable=True)  # 1=mono, 2=estéreo
    
    # Análisis musical
    bpm = Column(Float, nullable=True)  # Beats per minute
    key = Column(String(10), nullable=True)  # Clave musical
    camelot_key = Column(String(3), nullable=True)  # Notación Camelot
    energy = Column(Float, nullable=True)  # 0.0 - 1.0
    danceability = Column(Float, nullable=True)  # 0.0 - 1.0
    valence = Column(Float, nullable=True)  # 0.0 - 1.0 (positividad)
    loudness = Column(Float, nullable=True)  # dB
    
    # Metadatos adicionales
    isrc = Column(String(12), nullable=True, unique=True)  # International Standard Recording Code
    spotify_id = Column(String(255), nullable=True, unique=True)
    mbid = Column(String(36), nullable=True, unique=True)  # MusicBrainz ID
    
    # Información de reproducción
    play_count = Column(Integer, nullable=False, default=0)
    last_played = Column(DateTime, nullable=True)
    date_added = Column(DateTime, default=func.now(), nullable=False)
    
    # Flags de estado
    is_favorite = Column(Boolean, nullable=False, default=False)
    is_analyzed = Column(Boolean, nullable=False, default=False)  # Si se analizó el audio
    has_metadata = Column(Boolean, nullable=False, default=False)  # Si tiene metadatos completos
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relaciones
    album = relationship("Album", back_populates="tracks")
    artists = relationship("Artist", secondary=track_artists, back_populates="tracks")
    genres = relationship("Genre", secondary=track_genres, back_populates="tracks")
    
    # Índices para optimizar búsquedas
    __table_args__ = (
        Index('idx_track_normalized_title', 'normalized_title'),
        Index('idx_track_album_track_number', 'album_id', 'track_number'),
        Index('idx_track_file_path', 'file_path'),
        Index('idx_track_duration', 'duration'),
        Index('idx_track_bpm', 'bpm'),
        Index('idx_track_key', 'key'),
        Index('idx_track_play_count', 'play_count'),
        Index('idx_track_date_added', 'date_added'),
        Index('idx_track_is_favorite', 'is_favorite'),
    )
    
    def __repr__(self):
        return f"<Track(id={self.id}, title='{self.title}', file_path='{self.file_path}')>"
    
    @property
    def duration_formatted(self) -> str:
        """
        Retorna la duración formateada como MM:SS.
        """
        if not self.duration:
            return "0:00"
        
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        return f"{minutes}:{seconds:02d}"
    
    @property
    def primary_artist(self) -> Optional['Artist']:
        """
        Retorna el artista principal del track.
        """
        return self.artists[0] if self.artists else None
    
    @property
    def artist_names(self) -> List[str]:
        """
        Retorna una lista con los nombres de todos los artistas.
        """
        return [artist.name for artist in self.artists]
    
    @property
    def genre_names(self) -> List[str]:
        """
        Retorna una lista con los nombres de todos los géneros.
        """
        return [genre.name for genre in self.genres]
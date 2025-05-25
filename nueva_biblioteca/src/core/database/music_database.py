"""
Capa de persistencia para la gestión de música en Nueva Biblioteca.
Integra con los modelos SQLAlchemy existentes.
"""

from typing import List, Dict, Any, Optional
import logging
import uuid
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, func

from src.data.models.base import SessionLocal, create_tables, engine
from src.data.models.music import Track, Artist, Album, Genre
from src.data.models.playlist import SmartPlaylist, PlaylistRule, PlaylistTrack


class TrackMetadata:
    """
    Clase para manejar metadatos de tracks de manera compatible
    con el formato esperado por MusicService.
    """
    
    def __init__(self, **kwargs):
        """
        Inicializa los metadatos del track.
        
        Args:
            **kwargs: Metadatos del track
        """
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.title = kwargs.get('title', '')
        self.artist = kwargs.get('artist', '')
        self.album = kwargs.get('album', '')
        self.genre = kwargs.get('genre', '')
        self.year = kwargs.get('year')
        self.path = kwargs.get('path', '')
        self.duration = kwargs.get('duration')
        self.bpm = kwargs.get('bpm')
        self.key = kwargs.get('key')
        self.energy = kwargs.get('energy')
        self.danceability = kwargs.get('danceability')
        self.valence = kwargs.get('valence')
        self.bitrate = kwargs.get('bitrate')
        self.sample_rate = kwargs.get('sample_rate')
        self.file_size = kwargs.get('file_size')
        self.file_format = kwargs.get('file_format')
        self.track_number = kwargs.get('track_number')
        self.disc_number = kwargs.get('disc_number', 1)
        self.play_count = kwargs.get('play_count', 0)
        self.is_favorite = kwargs.get('is_favorite', False)
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())


class MusicDatabase:
    """
    Gestor principal de base de datos para la biblioteca musical.
    Proporciona una interfaz unificada para interactuar con los modelos SQLAlchemy.
    """
    
    def __init__(self, db_path: str = None):
        """
        Inicializa la base de datos.
        
        Args:
            db_path: Ruta a la base de datos (para compatibilidad, usa SQLAlchemy config)
        """
        self._logger = logging.getLogger(__name__)
        self._session: Optional[Session] = None
        self._connected = False
        
    def connect(self) -> bool:
        """
        Establece conexión con la base de datos.
        
        Returns:
            True si la conexión es exitosa
        """
        try:
            # Crear las tablas si no existen
            create_tables()
            
            # Crear una sesión
            self._session = SessionLocal()
            self._connected = True
            
            self._logger.info("Conexión a base de datos establecida")
            return True
            
        except Exception as e:
            self._logger.error(f"Error conectando a base de datos: {e}")
            return False
    
    def disconnect(self):
        """Cierra la conexión con la base de datos."""
        if self._session:
            self._session.close()
            self._session = None
        self._connected = False
        self._logger.info("Conexión a base de datos cerrada")
    
    def is_connected(self) -> bool:
        """Verifica si hay conexión activa."""
        return self._connected and self._session is not None
    
    def get_track(self, track_id: str) -> Optional[TrackMetadata]:
        """
        Obtiene un track por su ID.
        
        Args:
            track_id: ID del track
            
        Returns:
            TrackMetadata o None si no existe
        """
        if not self.is_connected():
            return None
            
        try:
            # Buscar por ID numérico o por file_path como string ID
            track = None
            if track_id.isdigit():
                track = self._session.query(Track).filter(Track.id == int(track_id)).first()
            else:
                # Buscar por file_path si no es un ID numérico
                track = self._session.query(Track).filter(Track.file_path.contains(track_id)).first()
            
            if track:
                return self._track_to_metadata(track)
            return None
            
        except Exception as e:
            self._logger.error(f"Error obteniendo track {track_id}: {e}")
            return None
    
    def get_tracks(self, filters: Optional[Dict[str, Any]] = None) -> List[TrackMetadata]:
        """
        Obtiene todos los tracks con filtros opcionales.
        
        Args:
            filters: Filtros a aplicar (opcional)
            
        Returns:
            Lista de TrackMetadata
        """
        if not self.is_connected():
            return []
            
        try:
            query = self._session.query(Track)
            
            # Aplicar filtros si se proporcionan
            if filters:
                for field, value in filters.items():
                    if hasattr(Track, field):
                        if isinstance(value, str):
                            query = query.filter(getattr(Track, field).ilike(f"%{value}%"))
                        else:
                            query = query.filter(getattr(Track, field) == value)
            
            tracks = query.all()
            return [self._track_to_metadata(track) for track in tracks]
            
        except Exception as e:
            self._logger.error(f"Error obteniendo tracks: {e}")
            return []
    
    def update_track(self, track_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Actualiza o crea un track.
        
        Args:
            track_id: ID del track
            metadata: Metadatos a actualizar
            
        Returns:
            True si la operación fue exitosa
        """
        if not self.is_connected():
            return False
            
        try:
            # Buscar track existente
            track = None
            if track_id.isdigit():
                track = self._session.query(Track).filter(Track.id == int(track_id)).first()
            
            if track:
                # Actualizar track existente
                self._update_track_from_metadata(track, metadata)
            else:
                # Crear nuevo track
                track = self._create_track_from_metadata(metadata)
                self._session.add(track)
            
            self._session.commit()
            return True
            
        except Exception as e:
            self._logger.error(f"Error actualizando track {track_id}: {e}")
            self._session.rollback()
            return False
    
    def search_tracks(self, query: str, fields: List[str] = None) -> List[TrackMetadata]:
        """
        Busca tracks por texto en múltiples campos.
        
        Args:
            query: Texto a buscar
            fields: Campos donde buscar (por defecto: title, artist, album)
            
        Returns:
            Lista de TrackMetadata que coinciden
        """
        if not self.is_connected():
            return []
            
        if not fields:
            fields = ['title', 'normalized_title']
            
        try:
            # Construir consulta de búsqueda
            search_query = self._session.query(Track)
            
            # Crear condiciones OR para cada campo
            conditions = []
            for field in fields:
                if hasattr(Track, field):
                    conditions.append(getattr(Track, field).ilike(f"%{query}%"))
            
            # También buscar en artistas y álbumes relacionados
            conditions.append(
                Track.artists.any(Artist.name.ilike(f"%{query}%"))
            )
            conditions.append(
                Track.album.has(Album.title.ilike(f"%{query}%"))
            )
            
            if conditions:
                search_query = search_query.filter(or_(*conditions))
            
            tracks = search_query.all()
            return [self._track_to_metadata(track) for track in tracks]
            
        except Exception as e:
            self._logger.error(f"Error buscando tracks: {e}")
            return []
    
    def _track_to_metadata(self, track: Track) -> TrackMetadata:
        """
        Convierte un objeto Track SQLAlchemy a TrackMetadata.
        
        Args:
            track: Objeto Track de SQLAlchemy
            
        Returns:
            TrackMetadata equivalente
        """
        # Obtener artista principal
        artist_name = track.primary_artist.name if track.primary_artist else ""
        
        # Obtener álbum
        album_title = track.album.title if track.album else ""
        
        # Obtener géneros
        genre_name = track.genre_names[0] if track.genre_names else ""
        
        return TrackMetadata(
            id=str(track.id),
            title=track.title,
            artist=artist_name,
            album=album_title,
            genre=genre_name,
            year=track.album.year if track.album else None,
            path=track.file_path,
            duration=track.duration,
            bpm=track.bpm,
            key=track.key,
            energy=track.energy,
            danceability=track.danceability,
            valence=track.valence,
            bitrate=track.bitrate,
            sample_rate=track.sample_rate,
            file_size=track.file_size,
            file_format=track.file_format,
            track_number=track.track_number,
            disc_number=track.disc_number,
            play_count=track.play_count,
            is_favorite=track.is_favorite,
            created_at=track.created_at,
            updated_at=track.updated_at
        )
    
    def _update_track_from_metadata(self, track: Track, metadata: Dict[str, Any]):
        """
        Actualiza un objeto Track con metadatos.
        
        Args:
            track: Objeto Track a actualizar
            metadata: Diccionario con metadatos
        """
        # Mapear campos directos
        direct_fields = [
            'title', 'file_path', 'filename', 'file_size', 'file_format',
            'track_number', 'disc_number', 'duration', 'bitrate', 'sample_rate',
            'channels', 'bpm', 'key', 'energy', 'danceability', 'valence',
            'loudness', 'play_count', 'is_favorite'
        ]
        
        for field in direct_fields:
            if field in metadata:
                if field == 'file_path' and hasattr(track, 'file_path'):
                    track.file_path = metadata[field]
                elif hasattr(track, field):
                    setattr(track, field, metadata[field])
        
        # Actualizar título normalizado
        if 'title' in metadata:
            track.normalized_title = metadata['title'].lower().strip()
        
        # Actualizar timestamp
        track.updated_at = datetime.now()
    
    def _create_track_from_metadata(self, metadata: Dict[str, Any]) -> Track:
        """
        Crea un nuevo objeto Track desde metadatos.
        
        Args:
            metadata: Diccionario con metadatos
            
        Returns:
            Nuevo objeto Track
        """
        track = Track(
            title=metadata.get('title', ''),
            normalized_title=metadata.get('title', '').lower().strip(),
            file_path=metadata.get('path', ''),
            filename=Path(metadata.get('path', '')).name if metadata.get('path') else '',
            file_size=metadata.get('file_size'),
            file_format=metadata.get('file_format'),
            track_number=metadata.get('track_number'),
            disc_number=metadata.get('disc_number', 1),
            duration=metadata.get('duration'),
            bitrate=metadata.get('bitrate'),
            sample_rate=metadata.get('sample_rate'),
            channels=metadata.get('channels'),
            bpm=metadata.get('bpm'),
            key=metadata.get('key'),
            energy=metadata.get('energy'),
            danceability=metadata.get('danceability'),
            valence=metadata.get('valence'),
            loudness=metadata.get('loudness'),
            play_count=metadata.get('play_count', 0),
            is_favorite=metadata.get('is_favorite', False),
            has_metadata=True
        )
        
        return track


class DatabaseFactory:
    """
    Factory para crear instancias de base de datos.
    Proporciona compatibilidad con diferentes tipos de almacenamiento.
    """
    
    @staticmethod
    def create(db_type: str = 'sqlite', db_path: str = 'music.db') -> MusicDatabase:
        """
        Crea una instancia de base de datos.
        
        Args:
            db_type: Tipo de base de datos ('sqlite' principalmente)
            db_path: Ruta al archivo de base de datos
            
        Returns:
            Instancia de MusicDatabase
        """
        if db_type == 'sqlite':
            return MusicDatabase(db_path)
        elif db_type == 'json':
            # Para compatibilidad, devuelve SQLite de todas formas
            return MusicDatabase(db_path)
        else:
            raise ValueError(f"Tipo de base de datos no soportado: {db_type}")
    
    @staticmethod
    def get_supported_types() -> List[str]:
        """
        Obtiene los tipos de base de datos soportados.
        
        Returns:
            Lista de tipos soportados
        """
        return ['sqlite', 'json']
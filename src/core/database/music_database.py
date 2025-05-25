"""
Sistema de integración con bases de datos de música.
Soporta múltiples fuentes de datos y formatos.
"""

from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import sqlite3
import json
import logging
from pathlib import Path
from dataclasses import dataclass

@dataclass
class TrackMetadata:
    """Metadata de un track musical."""
    id: str
    title: str
    artist: str
    album: str
    key: Optional[str] = None
    bpm: Optional[float] = None
    energy: Optional[float] = None
    danceability: Optional[float] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    path: Optional[str] = None

class MusicDatabase(ABC):
    """Clase base para bases de datos de música."""
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establece conexión con la base de datos.
        
        Returns:
            bool: True si la conexión fue exitosa
        """
        pass
        
    @abstractmethod
    def disconnect(self):
        """Cierra la conexión con la base de datos."""
        pass
        
    @abstractmethod
    def get_track(self, track_id: str) -> Optional[TrackMetadata]:
        """
        Obtiene metadata de un track.
        
        Args:
            track_id: ID del track
            
        Returns:
            TrackMetadata si existe, None si no
        """
        pass
        
    @abstractmethod
    def get_tracks(self, filters: Dict[str, Any] = None) -> List[TrackMetadata]:
        """
        Obtiene tracks que cumplen los filtros.
        
        Args:
            filters: Diccionario de filtros
            
        Returns:
            Lista de tracks que cumplen los filtros
        """
        pass
        
    @abstractmethod
    def update_track(self, track_id: str, data: Dict[str, Any]) -> bool:
        """
        Actualiza metadata de un track.
        
        Args:
            track_id: ID del track
            data: Datos a actualizar
            
        Returns:
            bool: True si la actualización fue exitosa
        """
        pass

class SQLiteDatabase(MusicDatabase):
    """Implementación de base de datos SQLite."""
    
    def __init__(self, path: str):
        self.path = path
        self.conn = None
        self.cursor = None
        self._logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        try:
            self.conn = sqlite3.connect(self.path)
            self.cursor = self.conn.cursor()
            
            # Crear tablas si no existen
            self._create_tables()
            
            return True
            
        except Exception as e:
            self._logger.error(f"Error conectando a SQLite: {str(e)}")
            return False
            
    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            
    def get_track(self, track_id: str) -> Optional[TrackMetadata]:
        if not self.conn:
            raise RuntimeError("No hay conexión a la base de datos")
            
        try:
            self.cursor.execute(
                """
                SELECT id, title, artist, album, key, bpm, 
                       energy, danceability, year, genre, path
                FROM tracks 
                WHERE id = ?
                """,
                (track_id,)
            )
            
            row = self.cursor.fetchone()
            if row:
                return TrackMetadata(*row)
                
            return None
            
        except Exception as e:
            self._logger.error(f"Error obteniendo track {track_id}: {str(e)}")
            return None
            
    def get_tracks(self, filters: Dict[str, Any] = None) -> List[TrackMetadata]:
        if not self.conn:
            raise RuntimeError("No hay conexión a la base de datos")
            
        try:
            query = """
                SELECT id, title, artist, album, key, bpm,
                       energy, danceability, year, genre, path
                FROM tracks
            """
            
            params = []
            if filters:
                conditions = []
                for field, value in filters.items():
                    if isinstance(value, (list, tuple)):
                        conditions.append(f"{field} IN ({','.join('?' * len(value))})")
                        params.extend(value)
                    else:
                        conditions.append(f"{field} = ?")
                        params.append(value)
                        
                query += " WHERE " + " AND ".join(conditions)
                
            self.cursor.execute(query, params)
            return [TrackMetadata(*row) for row in self.cursor.fetchall()]
            
        except Exception as e:
            self._logger.error(f"Error obteniendo tracks: {str(e)}")
            return []
            
    def update_track(self, track_id: str, data: Dict[str, Any]) -> bool:
        if not self.conn:
            raise RuntimeError("No hay conexión a la base de datos")
            
        try:
            fields = []
            values = []
            
            for field, value in data.items():
                fields.append(f"{field} = ?")
                values.append(value)
                
            values.append(track_id)
            
            query = f"""
                UPDATE tracks 
                SET {', '.join(fields)}
                WHERE id = ?
            """
            
            self.cursor.execute(query, values)
            self.conn.commit()
            
            return True
            
        except Exception as e:
            self._logger.error(f"Error actualizando track {track_id}: {str(e)}")
            return False
            
    def _create_tables(self):
        """Crea las tablas necesarias si no existen."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                album TEXT NOT NULL,
                key TEXT,
                bpm REAL,
                energy REAL,
                danceability REAL,
                year INTEGER,
                genre TEXT,
                path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()

class JSONDatabase(MusicDatabase):
    """Implementación de base de datos JSON."""
    
    def __init__(self, path: str):
        self.path = Path(path)
        self.data = {}
        self._logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        try:
            if self.path.exists():
                with open(self.path, 'r') as f:
                    self.data = json.load(f)
            else:
                self.data = {'tracks': {}}
                self._save()
                
            return True
            
        except Exception as e:
            self._logger.error(f"Error conectando a JSON: {str(e)}")
            return False
            
    def disconnect(self):
        self._save()
        self.data = {}
        
    def get_track(self, track_id: str) -> Optional[TrackMetadata]:
        try:
            if track_id in self.data['tracks']:
                return TrackMetadata(**self.data['tracks'][track_id])
            return None
            
        except Exception as e:
            self._logger.error(f"Error obteniendo track {track_id}: {str(e)}")
            return None
            
    def get_tracks(self, filters: Dict[str, Any] = None) -> List[TrackMetadata]:
        try:
            tracks = []
            
            for track_data in self.data['tracks'].values():
                if self._matches_filters(track_data, filters):
                    tracks.append(TrackMetadata(**track_data))
                    
            return tracks
            
        except Exception as e:
            self._logger.error(f"Error obteniendo tracks: {str(e)}")
            return []
            
    def update_track(self, track_id: str, data: Dict[str, Any]) -> bool:
        try:
            if track_id in self.data['tracks']:
                self.data['tracks'][track_id].update(data)
                self._save()
                return True
                
            return False
            
        except Exception as e:
            self._logger.error(f"Error actualizando track {track_id}: {str(e)}")
            return False
            
    def _save(self):
        """Guarda los datos en el archivo JSON."""
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=4)
            
    def _matches_filters(self, track: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Verifica si un track cumple con los filtros.
        
        Args:
            track: Datos del track
            filters: Filtros a aplicar
            
        Returns:
            bool: True si el track cumple los filtros
        """
        if not filters:
            return True
            
        for field, value in filters.items():
            if field not in track:
                return False
                
            if isinstance(value, (list, tuple)):
                if track[field] not in value:
                    return False
            elif track[field] != value:
                return False
                
        return True

class DatabaseFactory:
    """Factory para crear instancias de bases de datos."""
    
    @staticmethod
    def create(db_type: str, path: str) -> MusicDatabase:
        """
        Crea una instancia de base de datos.
        
        Args:
            db_type: Tipo de base de datos ('sqlite' o 'json')
            path: Ruta al archivo de base de datos
            
        Returns:
            Instancia de MusicDatabase
            
        Raises:
            ValueError: Si el tipo es inválido
        """
        if db_type == 'sqlite':
            return SQLiteDatabase(path)
        elif db_type == 'json':
            return JSONDatabase(path)
        else:
            raise ValueError(f"Tipo de base de datos no soportado: {db_type}")

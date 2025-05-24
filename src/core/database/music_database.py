"""
Sistema de base de datos SQLite robusto para la organización musical.
Maneja tracks, playlists, reglas y metadatos de manera eficiente.
"""
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class Track:
    """Modelo de datos para un track musical."""
    id: Optional[int] = None
    filepath: str = ""
    title: str = ""
    artist: str = ""
    album: str = ""
    genre: str = ""
    year: Optional[int] = None
    duration: Optional[float] = None
    bpm: Optional[float] = None
    key: str = ""
    camelot_key: str = ""
    energy: Optional[float] = None
    danceability: Optional[float] = None
    valence: Optional[float] = None
    acousticness: Optional[float] = None
    instrumentalness: Optional[float] = None
    metadata_json: str = "{}"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Track':
        """Crea una instancia Track desde una fila de la base de datos."""
        return cls(**dict(row))

@dataclass
class Playlist:
    """Modelo de datos para una playlist."""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    rules_json: str = "{}"
    is_dynamic: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class PlaylistTrack:
    """Relación entre playlist y track."""
    id: Optional[int] = None
    playlist_id: int = 0
    track_id: int = 0
    position: int = 0
    added_at: Optional[str] = None

@dataclass
class Rule:
    """Modelo para reglas de filtrado inteligente."""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    conditions_json: str = "{}"
    actions_json: str = "{}"
    is_active: bool = True
    created_at: Optional[str] = None

class MusicDatabase:
    """Gestor principal de la base de datos musical."""

    def __init__(self, db_path: str = "music_library.db"):
        """
        Inicializa la conexión a la base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = Path(db_path)
        self.connection = None
        self._ensure_database()

    def _ensure_database(self):
        """Asegura que la base de datos y tablas existan."""
        try:
            self.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0
            )
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.execute("PRAGMA journal_mode = WAL")
            self._create_tables()
            logger.info(f"Base de datos inicializada: {self.db_path}")
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}")
            raise

    def _create_tables(self):
        """Crea todas las tablas necesarias."""
        tables = {
            'tracks': '''
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filepath TEXT UNIQUE NOT NULL,
                    title TEXT DEFAULT '',
                    artist TEXT DEFAULT '',
                    album TEXT DEFAULT '',
                    genre TEXT DEFAULT '',
                    year INTEGER,
                    duration REAL,
                    bpm REAL,
                    key TEXT DEFAULT '',
                    camelot_key TEXT DEFAULT '',
                    energy REAL,
                    danceability REAL,
                    valence REAL,
                    acousticness REAL,
                    instrumentalness REAL,
                    metadata_json TEXT DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'playlists': '''
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT DEFAULT '',
                    rules_json TEXT DEFAULT '{}',
                    is_dynamic BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'playlist_tracks': '''
                CREATE TABLE IF NOT EXISTS playlist_tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER NOT NULL,
                    track_id INTEGER NOT NULL,
                    position INTEGER DEFAULT 0,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (playlist_id) REFERENCES playlists (id) ON DELETE CASCADE,
                    FOREIGN KEY (track_id) REFERENCES tracks (id) ON DELETE CASCADE,
                    UNIQUE (playlist_id, track_id)
                )
            ''',
            'rules': '''
                CREATE TABLE IF NOT EXISTS rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT DEFAULT '',
                    conditions_json TEXT DEFAULT '{}',
                    actions_json TEXT DEFAULT '{}',
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'camelot_transitions': '''
                CREATE TABLE IF NOT EXISTS camelot_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_key TEXT NOT NULL,
                    to_key TEXT NOT NULL,
                    transition_type TEXT NOT NULL,
                    energy_change REAL DEFAULT 0,
                    compatibility_score REAL DEFAULT 1.0
                )
            '''
        }

        # Crear índices para optimizar consultas
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_tracks_genre ON tracks(genre)',
            'CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist)',
            'CREATE INDEX IF NOT EXISTS idx_tracks_year ON tracks(year)',
            'CREATE INDEX IF NOT EXISTS idx_tracks_bpm ON tracks(bpm)',
            'CREATE INDEX IF NOT EXISTS idx_tracks_energy ON tracks(energy)',
            'CREATE INDEX IF NOT EXISTS idx_tracks_camelot ON tracks(camelot_key)',
            'CREATE INDEX IF NOT EXISTS idx_playlist_tracks_playlist ON playlist_tracks(playlist_id)',
            'CREATE INDEX IF NOT EXISTS idx_playlist_tracks_position ON playlist_tracks(position)',
        ]

        try:
            for table_name, sql in tables.items():
                self.connection.execute(sql)
                logger.debug(f"Tabla '{table_name}' verificada/creada")

            for index_sql in indexes:
                self.connection.execute(index_sql)

            self._populate_camelot_data()
            self.connection.commit()
            logger.info("Todas las tablas e índices creados correctamente")

        except Exception as e:
            logger.error(f"Error creando tablas: {e}")
            self.connection.rollback()
            raise

    def _populate_camelot_data(self):
        """Pobla la tabla de transiciones Camelot si está vacía."""
        cursor = self.connection.execute("SELECT COUNT(*) FROM camelot_transitions")
        if cursor.fetchone()[0] > 0:
            return  # Ya hay datos

        # Datos de transiciones armónicas Camelot
        camelot_data = [
            # Transiciones perfectas (misma clave)
            ('1A', '1A', 'perfect', 0, 1.0),
            ('1B', '1B', 'perfect', 0, 1.0),
            # Transiciones compatibles (+/-1 semitono)
            ('1A', '2A', 'compatible', 0.1, 0.9),
            ('1A', '12A', 'compatible', -0.1, 0.9),
            ('1B', '2B', 'compatible', 0.1, 0.9),
            ('1B', '12B', 'compatible', -0.1, 0.9),
            # Transiciones de energía (+/-7 semitonos, relativa menor/mayor)
            ('1A', '1B', 'energy', 0.2, 0.8),
            ('1B', '1A', 'energy', -0.2, 0.8),
            # Agregar todas las 24 claves...
        ]

        # Generar todas las transiciones para las 12 claves
        all_transitions = []
        for i in range(1, 13):
            for key_type in ['A', 'B']:
                current_key = f"{i}{key_type}"
                
                # Misma clave (perfecta)
                all_transitions.append((current_key, current_key, 'perfect', 0, 1.0))
                
                # Clave siguiente
                next_i = (i % 12) + 1
                next_key = f"{next_i}{key_type}"
                all_transitions.append((current_key, next_key, 'compatible', 0.1, 0.9))
                
                # Clave anterior  
                prev_i = ((i - 2) % 12) + 1
                prev_key = f"{prev_i}{key_type}"
                all_transitions.append((current_key, prev_key, 'compatible', -0.1, 0.9))
                
                # Relativa menor/mayor
                other_type = 'B' if key_type == 'A' else 'A'
                relative_key = f"{i}{other_type}"
                energy_change = 0.2 if key_type == 'A' else -0.2
                all_transitions.append((current_key, relative_key, 'energy', energy_change, 0.8))

        self.connection.executemany(
            'INSERT INTO camelot_transitions (from_key, to_key, transition_type, energy_change, compatibility_score) VALUES (?, ?, ?, ?, ?)',
            all_transitions
        )
        logger.info(f"Datos de transiciones Camelot insertados: {len(all_transitions)} registros")

    def add_track(self, track: Track) -> int:
        """
        Añade un track a la base de datos.
        
        Args:
            track: Objeto Track a insertar
            
        Returns:
            ID del track insertado
        """
        try:
            track.updated_at = datetime.now().isoformat()
            if track.created_at is None:
                track.created_at = track.updated_at

            cursor = self.connection.execute('''
                INSERT OR REPLACE INTO tracks 
                (filepath, title, artist, album, genre, year, duration, bpm, key, camelot_key,
                 energy, danceability, valence, acousticness, instrumentalness, 
                 metadata_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                track.filepath, track.title, track.artist, track.album, track.genre,
                track.year, track.duration, track.bpm, track.key, track.camelot_key,
                track.energy, track.danceability, track.valence, track.acousticness,
                track.instrumentalness, track.metadata_json, track.created_at, track.updated_at
            ))
            
            self.connection.commit()
            track_id = cursor.lastrowid
            logger.debug(f"Track añadido: {track.title} (ID: {track_id})")
            return track_id

        except Exception as e:
            logger.error(f"Error añadiendo track: {e}")
            self.connection.rollback()
            raise

    def get_track_by_filepath(self, filepath: str) -> Optional[Track]:
        """Obtiene un track por su ruta de archivo."""
        try:
            cursor = self.connection.execute(
                "SELECT * FROM tracks WHERE filepath = ?", (filepath,)
            )
            row = cursor.fetchone()
            return Track.from_row(row) if row else None
        except Exception as e:
            logger.error(f"Error obteniendo track por filepath: {e}")
            return None

    def search_tracks(self, query: str, field: str = "title") -> List[Track]:
        """
        Busca tracks por un campo específico.
        
        Args:
            query: Texto a buscar
            field: Campo donde buscar (title, artist, album, genre)
            
        Returns:
            Lista de tracks que coinciden
        """
        try:
            valid_fields = ["title", "artist", "album", "genre"]
            if field not in valid_fields:
                field = "title"

            cursor = self.connection.execute(
                f"SELECT * FROM tracks WHERE {field} LIKE ? ORDER BY {field}",
                (f"%{query}%",)
            )
            return [Track.from_row(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error buscando tracks: {e}")
            return []

    def create_playlist(self, playlist: Playlist) -> int:
        """Crea una nueva playlist."""
        try:
            playlist.updated_at = datetime.now().isoformat()
            if playlist.created_at is None:
                playlist.created_at = playlist.updated_at

            cursor = self.connection.execute('''
                INSERT INTO playlists (name, description, rules_json, is_dynamic, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                playlist.name, playlist.description, playlist.rules_json,
                playlist.is_dynamic, playlist.created_at, playlist.updated_at
            ))

            self.connection.commit()
            playlist_id = cursor.lastrowid
            logger.info(f"Playlist creada: {playlist.name} (ID: {playlist_id})")
            return playlist_id

        except Exception as e:
            logger.error(f"Error creando playlist: {e}")
            self.connection.rollback()
            raise

    def add_track_to_playlist(self, playlist_id: int, track_id: int, position: Optional[int] = None) -> bool:
        """Añade un track a una playlist."""
        try:
            if position is None:
                # Obtener la próxima posición
                cursor = self.connection.execute(
                    "SELECT COALESCE(MAX(position), 0) + 1 FROM playlist_tracks WHERE playlist_id = ?",
                    (playlist_id,)
                )
                position = cursor.fetchone()[0]

            self.connection.execute('''
                INSERT OR REPLACE INTO playlist_tracks (playlist_id, track_id, position)
                VALUES (?, ?, ?)
            ''', (playlist_id, track_id, position))

            self.connection.commit()
            logger.debug(f"Track {track_id} añadido a playlist {playlist_id} en posición {position}")
            return True

        except Exception as e:
            logger.error(f"Error añadiendo track a playlist: {e}")
            self.connection.rollback()
            return False

    def get_compatible_tracks(self, current_track_id: int, max_results: int = 10) -> List[Tuple[Track, float]]:
        """
        Obtiene tracks compatibles armónicamente con el track actual.
        
        Args:
            current_track_id: ID del track actual
            max_results: Máximo número de resultados
            
        Returns:
            Lista de tuplas (Track, compatibility_score)
        """
        try:
            # Obtener el track actual
            current_track = self.get_track_by_id(current_track_id)
            if not current_track or not current_track.camelot_key:
                return []

            # Buscar tracks compatibles
            cursor = self.connection.execute('''
                SELECT t.*, ct.compatibility_score
                FROM tracks t
                JOIN camelot_transitions ct ON t.camelot_key = ct.to_key
                WHERE ct.from_key = ? AND t.id != ?
                ORDER BY ct.compatibility_score DESC, t.energy ASC
                LIMIT ?
            ''', (current_track.camelot_key, current_track_id, max_results))

            results = []
            for row in cursor.fetchall():
                track_data = dict(row)
                compatibility_score = track_data.pop('compatibility_score')
                track = Track(**track_data)
                results.append((track, compatibility_score))

            logger.debug(f"Encontrados {len(results)} tracks compatibles con {current_track.camelot_key}")
            return results

        except Exception as e:
            logger.error(f"Error obteniendo tracks compatibles: {e}")
            return []

    def get_track_by_id(self, track_id: int) -> Optional[Track]:
        """Obtiene un track por su ID."""
        try:
            cursor = self.connection.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
            row = cursor.fetchone()
            return Track.from_row(row) if row else None
        except Exception as e:
            logger.error(f"Error obteniendo track por ID: {e}")
            return None

    def close(self):
        """Cierra la conexión a la base de datos."""
        if self.connection:
            self.connection.close()
            logger.info("Conexión a base de datos cerrada")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

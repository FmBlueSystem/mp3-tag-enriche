"""
Gestor de importación que coordina el escaneo, extracción de metadatos y almacenamiento.
"""

import os
import threading
import time
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any, Generator
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session
import logging

from .file_scanner import MusicFileScanner, ScanResult
from ..metadata.extractor import MetadataExtractor, TrackMetadata
from ..data.models import get_db, Track, Artist, Album, Genre
from ..data.repositories import TrackRepository

@dataclass
class ImportProgress:
    """
    Información de progreso de importación.
    """
    total_files: int = 0
    processed_files: int = 0
    successful_imports: int = 0
    failed_imports: int = 0
    duplicate_files: int = 0
    current_file: str = ""
    start_time: Optional[datetime] = None
    estimated_time_remaining: Optional[float] = None
    
    @property
    def completion_percentage(self) -> float:
        """Porcentaje de completitud."""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100
    
    @property
    def processing_rate(self) -> float:
        """Archivos por segundo."""
        if not self.start_time or self.processed_files == 0:
            return 0.0
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return self.processed_files / elapsed if elapsed > 0 else 0.0

@dataclass
class ImportResult:
    """
    Resultado de una importación.
    """
    total_processed: int
    successful_imports: int
    failed_imports: int
    duplicate_files: int
    errors: List[str]
    duration_seconds: float
    new_tracks: List[int]  # IDs de tracks importados

class ImportManager:
    """
    Gestor principal de importación de archivos musicales.
    Coordina el escaneo, extracción de metadatos y almacenamiento en base de datos.
    """
    
    def __init__(self, max_workers: int = 4):
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        
        # Componentes
        self.scanner = MusicFileScanner(max_workers=max_workers)
        self.metadata_extractor = MetadataExtractor()
        
        # Estado de importación
        self._is_importing = False
        self._import_cancelled = threading.Event()
        self._progress = ImportProgress()
        
        # Callbacks para progreso
        self._progress_callbacks: List[Callable[[ImportProgress], None]] = []
        self._completion_callbacks: List[Callable[[ImportResult], None]] = []
        self._error_callbacks: List[Callable[[str], None]] = []
    
    def add_progress_callback(self, callback: Callable[[ImportProgress], None]):
        """Añade callback para updates de progreso."""
        self._progress_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable[[ImportResult], None]):
        """Añade callback para completar importación."""
        self._completion_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str], None]):
        """Añade callback para errores."""
        self._error_callbacks.append(callback)
    
    def _notify_progress(self):
        """Notifica progreso a los callbacks."""
        for callback in self._progress_callbacks:
            try:
                callback(self._progress)
            except Exception as e:
                self.logger.error(f"Error en callback de progreso: {e}")
    
    def _notify_completion(self, result: ImportResult):
        """Notifica completar a los callbacks."""
        for callback in self._completion_callbacks:
            try:
                callback(result)
            except Exception as e:
                self.logger.error(f"Error en callback de completar: {e}")
    
    def _notify_error(self, error_message: str):
        """Notifica errores a los callbacks."""
        for callback in self._error_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                self.logger.error(f"Error en callback de error: {e}")
    
    @property
    def is_importing(self) -> bool:
        """Retorna True si hay una importación en progreso."""
        return self._is_importing
    
    @property
    def progress(self) -> ImportProgress:
        """Retorna el progreso actual de importación."""
        return self._progress
    
    def cancel_import(self):
        """Cancela la importación en progreso."""
        if self._is_importing:
            self.logger.info("Cancelando importación...")
            self._import_cancelled.set()
            self.scanner.stop_scan()
    
    def import_directory(
        self, 
        directory_path: str,
        recursive: bool = True,
        check_duplicates: bool = True,
        extract_metadata: bool = True
    ) -> ImportResult:
        """
        Importa archivos musicales de un directorio.
        
        Args:
            directory_path: Ruta del directorio a importar
            recursive: Si buscar recursivamente en subdirectorios
            check_duplicates: Si verificar archivos duplicados
            extract_metadata: Si extraer metadatos de archivos
        
        Returns:
            ImportResult con estadísticas de la importación
        """
        if self._is_importing:
            raise RuntimeError("Ya hay una importación en progreso")
        
        self._is_importing = True
        self._import_cancelled.clear()
        
        # Inicializar progreso
        self._progress = ImportProgress(start_time=datetime.now())
        start_time = time.time()
        
        try:
            # Fase 1: Escaneo de archivos
            self.logger.info(f"Iniciando importación de: {directory_path}")
            self._progress.current_file = "Escaneando archivos..."
            self._notify_progress()
            
            scan_results = list(self.scanner.scan_directory(directory_path, recursive))
            
            if self._import_cancelled.is_set():
                return self._create_cancelled_result(start_time)
            
            valid_files = [r for r in scan_results if r.is_valid]
            self._progress.total_files = len(valid_files)
            self._notify_progress()
            
            self.logger.info(f"Encontrados {len(valid_files)} archivos válidos")
            
            # Fase 2: Importación con metadatos
            new_track_ids = []
            errors = []
            
            with next(get_db()) as db:
                track_repo = TrackRepository(db)
                
                for scan_result in valid_files:
                    if self._import_cancelled.is_set():
                        break
                    
                    try:
                        # Actualizar progreso
                        self._progress.current_file = Path(scan_result.file_path).name
                        self._notify_progress()
                        
                        # Verificar duplicados
                        if check_duplicates:
                            existing_track = track_repo.get_by_file_path(scan_result.file_path)
                            if existing_track:
                                self._progress.duplicate_files += 1
                                self._progress.processed_files += 1
                                continue
                        
                        # Extraer metadatos
                        metadata = None
                        if extract_metadata:
                            metadata = self.metadata_extractor.extract_metadata(scan_result.file_path)
                        
                        # Crear track en base de datos
                        track_id = self._create_track_from_metadata(
                            db, scan_result, metadata
                        )
                        
                        if track_id:
                            new_track_ids.append(track_id)
                            self._progress.successful_imports += 1
                        else:
                            self._progress.failed_imports += 1
                            errors.append(f"Error creando track: {scan_result.file_path}")
                        
                    except Exception as e:
                        error_msg = f"Error procesando {scan_result.file_path}: {e}"
                        self.logger.error(error_msg)
                        errors.append(error_msg)
                        self._progress.failed_imports += 1
                        self._notify_error(error_msg)
                    
                    finally:
                        self._progress.processed_files += 1
                        
                        # Calcular tiempo estimado restante
                        if self._progress.processing_rate > 0:
                            remaining_files = self._progress.total_files - self._progress.processed_files
                            self._progress.estimated_time_remaining = remaining_files / self._progress.processing_rate
                        
                        self._notify_progress()
            
            # Crear resultado final
            duration = time.time() - start_time
            result = ImportResult(
                total_processed=self._progress.processed_files,
                successful_imports=self._progress.successful_imports,
                failed_imports=self._progress.failed_imports,
                duplicate_files=self._progress.duplicate_files,
                errors=errors,
                duration_seconds=duration,
                new_tracks=new_track_ids
            )
            
            self.logger.info(
                f"Importación completada: {result.successful_imports} éxitos, "
                f"{result.failed_imports} fallos, {result.duplicate_files} duplicados "
                f"en {duration:.2f}s"
            )
            
            self._notify_completion(result)
            return result
            
        except Exception as e:
            error_msg = f"Error en importación: {e}"
            self.logger.error(error_msg)
            self._notify_error(error_msg)
            
            return ImportResult(
                total_processed=self._progress.processed_files,
                successful_imports=self._progress.successful_imports,
                failed_imports=self._progress.failed_imports + 1,
                duplicate_files=self._progress.duplicate_files,
                errors=[error_msg],
                duration_seconds=time.time() - start_time,
                new_tracks=[]
            )
        
        finally:
            self._is_importing = False
    
    def import_files(
        self, 
        file_paths: List[str],
        check_duplicates: bool = True,
        extract_metadata: bool = True
    ) -> ImportResult:
        """
        Importa una lista específica de archivos.
        
        Args:
            file_paths: Lista de rutas de archivos a importar
            check_duplicates: Si verificar archivos duplicados
            extract_metadata: Si extraer metadatos de archivos
        
        Returns:
            ImportResult con estadísticas de la importación
        """
        if self._is_importing:
            raise RuntimeError("Ya hay una importación en progreso")
        
        self._is_importing = True
        self._import_cancelled.clear()
        
        # Inicializar progreso
        self._progress = ImportProgress(
            total_files=len(file_paths),
            start_time=datetime.now()
        )
        start_time = time.time()
        
        try:
            new_track_ids = []
            errors = []
            
            with next(get_db()) as db:
                track_repo = TrackRepository(db)
                
                for file_path in file_paths:
                    if self._import_cancelled.is_set():
                        break
                    
                    try:
                        # Actualizar progreso
                        self._progress.current_file = Path(file_path).name
                        self._notify_progress()
                        
                        # Escanear archivo
                        scan_result = self.scanner.scan_file(Path(file_path))
                        if not scan_result.is_valid:
                            self._progress.failed_imports += 1
                            errors.append(f"Archivo inválido: {file_path}")
                            continue
                        
                        # Verificar duplicados
                        if check_duplicates:
                            existing_track = track_repo.get_by_file_path(file_path)
                            if existing_track:
                                self._progress.duplicate_files += 1
                                continue
                        
                        # Extraer metadatos
                        metadata = None
                        if extract_metadata:
                            metadata = self.metadata_extractor.extract_metadata(file_path)
                        
                        # Crear track
                        track_id = self._create_track_from_metadata(
                            db, scan_result, metadata
                        )
                        
                        if track_id:
                            new_track_ids.append(track_id)
                            self._progress.successful_imports += 1
                        else:
                            self._progress.failed_imports += 1
                            errors.append(f"Error creando track: {file_path}")
                    
                    except Exception as e:
                        error_msg = f"Error procesando {file_path}: {e}"
                        self.logger.error(error_msg)
                        errors.append(error_msg)
                        self._progress.failed_imports += 1
                        self._notify_error(error_msg)
                    
                    finally:
                        self._progress.processed_files += 1
                        self._notify_progress()
            
            # Crear resultado
            duration = time.time() - start_time
            result = ImportResult(
                total_processed=self._progress.processed_files,
                successful_imports=self._progress.successful_imports,
                failed_imports=self._progress.failed_imports,
                duplicate_files=self._progress.duplicate_files,
                errors=errors,
                duration_seconds=duration,
                new_tracks=new_track_ids
            )
            
            self._notify_completion(result)
            return result
            
        finally:
            self._is_importing = False
    
    def _create_track_from_metadata(
        self, 
        db: Session, 
        scan_result: ScanResult, 
        metadata: Optional[TrackMetadata]
    ) -> Optional[int]:
        """
        Crea un track en la base de datos a partir de los metadatos.
        
        Returns:
            ID del track creado o None si falló
        """
        try:
            # Preparar datos del track
            track_data = {
                'file_path': scan_result.file_path,
                'filename': Path(scan_result.file_path).name,
                'file_size': scan_result.file_size,
                'file_format': scan_result.file_format,
                'file_modified': datetime.fromtimestamp(scan_result.last_modified),
            }
            
            # Usar metadatos si están disponibles
            if metadata and metadata.extraction_success:
                track_data.update({
                    'title': metadata.title or Path(scan_result.file_path).stem,
                    'normalized_title': (metadata.title or Path(scan_result.file_path).stem).lower(),
                    'track_number': metadata.track_number,
                    'disc_number': metadata.disc_number or 1,
                    'duration': metadata.duration,
                    'bitrate': metadata.bitrate,
                    'sample_rate': metadata.sample_rate,
                    'channels': metadata.channels,
                    'bpm': metadata.bpm,
                    'key': metadata.key,
                    'isrc': metadata.isrc,
                    'has_metadata': True,
                    'is_analyzed': metadata.bpm is not None,
                })
                
                # Crear/obtener artista si existe
                if metadata.artist:
                    artist = self._get_or_create_artist(db, metadata.artist)
                    if artist and metadata.album:
                        album = self._get_or_create_album(db, metadata.album, artist.id, metadata.year)
                        if album:
                            track_data['album_id'] = album.id
            else:
                # Datos mínimos sin metadatos
                track_data.update({
                    'title': Path(scan_result.file_path).stem,
                    'normalized_title': Path(scan_result.file_path).stem.lower(),
                    'disc_number': 1,
                    'has_metadata': False,
                    'is_analyzed': False,
                })
            
            # Crear track
            track = Track(**track_data)
            db.add(track)
            db.flush()  # Para obtener el ID
            
            # Asociar artistas si existen metadatos
            if metadata and metadata.artist:
                artist = self._get_or_create_artist(db, metadata.artist)
                if artist:
                    track.artists.append(artist)
            
            # Asociar géneros si existen
            if metadata and metadata.genre:
                genres = self._get_or_create_genres(db, metadata.genre)
                track.genres.extend(genres)
            
            db.commit()
            return track.id
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creando track en BD: {e}")
            return None
    
    def _get_or_create_artist(self, db: Session, artist_name: str) -> Optional[Artist]:
        """Obtiene o crea un artista."""
        try:
            normalized_name = artist_name.lower().strip()
            
            # Buscar artista existente
            artist = db.query(Artist).filter(
                Artist.normalized_name == normalized_name
            ).first()
            
            if not artist:
                # Crear nuevo artista
                artist = Artist(
                    name=artist_name.strip(),
                    normalized_name=normalized_name
                )
                db.add(artist)
                db.flush()
            
            return artist
            
        except Exception as e:
            self.logger.error(f"Error con artista {artist_name}: {e}")
            return None
    
    def _get_or_create_album(
        self, 
        db: Session, 
        album_title: str, 
        artist_id: int, 
        year: Optional[int] = None
    ) -> Optional[Album]:
        """Obtiene o crea un álbum."""
        try:
            normalized_title = album_title.lower().strip()
            
            # Buscar álbum existente del mismo artista
            album = db.query(Album).filter(
                Album.normalized_title == normalized_title,
                Album.artist_id == artist_id
            ).first()
            
            if not album:
                # Crear nuevo álbum
                album = Album(
                    title=album_title.strip(),
                    normalized_title=normalized_title,
                    artist_id=artist_id,
                    year=year
                )
                db.add(album)
                db.flush()
            
            return album
            
        except Exception as e:
            self.logger.error(f"Error con álbum {album_title}: {e}")
            return None
    
    def _get_or_create_genres(self, db: Session, genre_string: str) -> List[Genre]:
        """Obtiene o crea géneros a partir de una cadena."""
        genres = []
        
        try:
            # Separar por comas y limpiar
            genre_names = [g.strip() for g in genre_string.split(',') if g.strip()]
            
            for genre_name in genre_names:
                normalized_name = genre_name.lower()
                
                # Buscar género existente
                genre = db.query(Genre).filter(
                    Genre.normalized_name == normalized_name
                ).first()
                
                if not genre:
                    # Crear nuevo género
                    genre = Genre(
                        name=genre_name,
                        normalized_name=normalized_name
                    )
                    db.add(genre)
                    db.flush()
                
                genres.append(genre)
            
        except Exception as e:
            self.logger.error(f"Error con géneros {genre_string}: {e}")
        
        return genres
    
    def _create_cancelled_result(self, start_time: float) -> ImportResult:
        """Crea un resultado para importación cancelada."""
        return ImportResult(
            total_processed=self._progress.processed_files,
            successful_imports=self._progress.successful_imports,
            failed_imports=self._progress.failed_imports,
            duplicate_files=self._progress.duplicate_files,
            errors=["Importación cancelada por el usuario"],
            duration_seconds=time.time() - start_time,
            new_tracks=[]
        )
    
    def get_import_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas de importación."""
        return {
            'is_importing': self.is_importing,
            'progress': self._progress,
            'scanner_supported_formats': self.scanner.SUPPORTED_FORMATS,
            'extractor_supported_formats': self.metadata_extractor.get_supported_formats(),
        }
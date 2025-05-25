#!/usr/bin/env python3
"""
🏷️ EXTRACTOR DE METADATOS MUSICALES - NUEVA BIBLIOTECA v2.0
==========================================================
Extrae metadatos de archivos de audio usando mutagen y los enriquece con APIs musicales
"""

import os
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict, field
import time
import hashlib
import logging

try:
    from mutagen import File as MutagenFile
    from mutagen.id3 import ID3NoHeaderError
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

# Importar sistema de enriquecimiento
try:
    from ..core.metadata_enricher import MetadataEnricher, EnrichmentResult
    ENRICHMENT_AVAILABLE = True
except ImportError:
    ENRICHMENT_AVAILABLE = False
    
logger = logging.getLogger(__name__)

@dataclass
class TrackMetadata:
    """Metadatos completos de un track musical."""
    # Información básica del archivo
    file_path: str
    file_name: str
    file_size: int
    file_extension: str
    file_hash: Optional[str] = None
    last_modified: float = 0.0
    
    # Metadatos musicales básicos
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    album_artist: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    track_number: Optional[int] = None
    total_tracks: Optional[int] = None
    disc_number: Optional[int] = None
    total_discs: Optional[int] = None
    
    # Información técnica
    duration: Optional[float] = None  # en segundos
    bitrate: Optional[int] = None     # en kbps
    sample_rate: Optional[int] = None # en Hz
    channels: Optional[int] = None
    
    # Metadatos adicionales
    composer: Optional[str] = None
    comment: Optional[str] = None
    bpm: Optional[int] = None
    key: Optional[str] = None
    
    # Análisis de audio (para futuro)
    energy: Optional[float] = None
    valence: Optional[float] = None
    danceability: Optional[float] = None
    
    # Estadísticas de uso
    play_count: int = 0
    rating: Optional[int] = None
    last_played: Optional[float] = None
    date_added: float = 0.0
    
    # Metadatos enriquecidos (nuevos campos)
    enriched_genres: Dict[str, float] = field(default_factory=dict)
    enrichment_confidence: float = 0.0
    enrichment_sources: List[str] = field(default_factory=list)
    enrichment_timestamp: Optional[float] = None
    
    def __post_init__(self):
        """Inicialización post-creación."""
        if self.date_added == 0.0:
            self.date_added = time.time()

class MetadataExtractor:
    """
    Extractor de metadatos de archivos musicales con enriquecimiento automático.
    """
    
    def __init__(self, enable_enrichment: bool = True):
        """
        Inicializar el extractor.
        
        Args:
            enable_enrichment: Si habilitar enriquecimiento automático de metadatos
        """
        if not MUTAGEN_AVAILABLE:
            raise ImportError(
                "mutagen no está disponible. Instala con: pip install mutagen"
            )
        
        self.extraction_errors = []
        self.enable_enrichment = enable_enrichment and ENRICHMENT_AVAILABLE
        
        # Inicializar enriquecedor si está disponible
        if self.enable_enrichment:
            try:
                self.enricher = MetadataEnricher()
                logger.info("MetadataExtractor initialized with enrichment enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize enricher: {e}")
                self.enable_enrichment = False
                self.enricher = None
        else:
            self.enricher = None
            if not ENRICHMENT_AVAILABLE:
                logger.info("MetadataExtractor initialized without enrichment (not available)")
            else:
                logger.info("MetadataExtractor initialized with enrichment disabled")
        
    def extract_metadata(self, file_path: str, calculate_hash: bool = False, 
                        enrich_metadata: bool = True) -> Optional[TrackMetadata]:
        """
        Extraer metadatos de un archivo de audio.
        
        Args:
            file_path: Ruta del archivo
            calculate_hash: Si calcular hash MD5 del archivo
            enrich_metadata: Si enriquecer metadatos con APIs musicales
            
        Returns:
            TrackMetadata o None si hay error
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.extraction_errors.append(f"Archivo no encontrado: {file_path}")
                return None
                
            # Información básica del archivo
            stat = path.stat()
            
            # Crear objeto base de metadatos
            metadata = TrackMetadata(
                file_path=str(path.absolute()),
                file_name=path.name,
                file_size=stat.st_size,
                file_extension=path.suffix.lower(),
                last_modified=stat.st_mtime
            )
            
            # Calcular hash si se solicita
            if calculate_hash:
                metadata.file_hash = self._calculate_file_hash(file_path)
            
            # Extraer metadatos del archivo de audio
            try:
                audio_file = MutagenFile(file_path)
                if audio_file is None:
                    self.extraction_errors.append(f"No se pudo leer el archivo de audio: {file_path}")
                    return metadata
                    
                # Extraer metadatos según el formato
                self._extract_common_metadata(audio_file, metadata)
                self._extract_technical_metadata(audio_file, metadata)
                
            except Exception as e:
                self.extraction_errors.append(f"Error extrayendo metadatos de {file_path}: {e}")
            
            # Enriquecer metadatos si está habilitado y tenemos artista/título
            if (enrich_metadata and self.enable_enrichment and 
                metadata.artist and metadata.title):
                try:
                    self._enrich_metadata(metadata)
                except Exception as e:
                    logger.warning(f"Error enriching metadata for {file_path}: {e}")
                    self.extraction_errors.append(f"Error enriqueciendo metadatos de {file_path}: {e}")
                
            return metadata
            
        except Exception as e:
            self.extraction_errors.append(f"Error procesando {file_path}: {e}")
            return None
            
    def _extract_common_metadata(self, audio_file: Any, metadata: TrackMetadata) -> None:
        """Extraer metadatos comunes de cualquier formato."""
        # Mapeo de tags comunes
        tag_mappings = {
            'title': ['TIT2', 'TITLE', '\xa9nam', 'TITLE'],
            'artist': ['TPE1', 'ARTIST', '\xa9ART', 'ARTIST'],
            'album': ['TALB', 'ALBUM', '\xa9alb', 'ALBUM'],
            'album_artist': ['TPE2', 'ALBUMARTIST', 'aART', 'ALBUMARTIST'],
            'genre': ['TCON', 'GENRE', '\xa9gen', 'GENRE'],
            'year': ['TDRC', 'DATE', '\xa9day', 'DATE'],
            'track_number': ['TRCK', 'TRACKNUMBER', 'trkn', 'TRACKNUMBER'],
            'disc_number': ['TPOS', 'DISCNUMBER', 'disk', 'DISCNUMBER'],
            'composer': ['TCOM', 'COMPOSER', '\xa9wrt', 'COMPOSER'],
            'comment': ['COMM::eng', 'COMMENT', '\xa9cmt', 'COMMENT'],
            'bpm': ['TBPM', 'BPM', 'tmpo', 'BPM']
        }
        
        for field, possible_tags in tag_mappings.items():
            value = self._get_tag_value(audio_file, possible_tags)
            if value:
                if field in ['year', 'track_number', 'disc_number', 'bpm']:
                    try:
                        # Extraer número de strings como "2023" o "1/12"
                        if isinstance(value, str) and '/' in value:
                            value = int(value.split('/')[0])
                        else:
                            value = int(str(value)[:4])  # Limitar año a 4 dígitos
                        setattr(metadata, field, value)
                    except (ValueError, TypeError):
                        pass
                else:
                    setattr(metadata, field, str(value))
                    
    def _extract_technical_metadata(self, audio_file: Any, metadata: TrackMetadata) -> None:
        """Extraer metadatos técnicos del archivo."""
        try:
            # Duración
            if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'length'):
                metadata.duration = float(audio_file.info.length)
                
            # Bitrate
            if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'bitrate'):
                metadata.bitrate = int(audio_file.info.bitrate)
                
            # Sample rate
            if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'sample_rate'):
                metadata.sample_rate = int(audio_file.info.sample_rate)
                
            # Canales
            if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'channels'):
                metadata.channels = int(audio_file.info.channels)
                
        except (AttributeError, ValueError, TypeError):
            pass
            
    def _get_tag_value(self, audio_file: Any, possible_tags: List[str]) -> Optional[str]:
        """Obtener valor de tag probando múltiples nombres."""
        for tag in possible_tags:
            try:
                if tag in audio_file:
                    value = audio_file[tag]
                    if isinstance(value, list) and value:
                        return str(value[0])
                    elif value:
                        return str(value)
            except (KeyError, TypeError):
                continue
        return None
        
    def _enrich_metadata(self, metadata: TrackMetadata) -> None:
        """
        Enriquecer metadatos usando APIs musicales.
        
        Args:
            metadata: Metadatos a enriquecer (se modifica in-place)
        """
        if not self.enricher or not metadata.artist or not metadata.title:
            return
            
        logger.debug(f"Enriching metadata for: {metadata.artist} - {metadata.title}")
        
        # Obtener enriquecimiento
        enrichment = self.enricher.enrich_metadata(metadata.artist, metadata.title)
        
        # Aplicar resultados del enriquecimiento
        if enrichment.genres:
            metadata.enriched_genres = enrichment.genres
            
            # Si no hay género original, usar el género más confiable del enriquecimiento
            if not metadata.genre and enrichment.genres:
                best_genre = max(enrichment.genres.items(), key=lambda x: x[1])
                metadata.genre = best_genre[0]
                
        # Enriquecer año si no existe
        if not metadata.year and enrichment.year:
            try:
                metadata.year = int(enrichment.year)
            except (ValueError, TypeError):
                pass
                
        # Enriquecer álbum si no existe
        if not metadata.album and enrichment.album:
            metadata.album = enrichment.album
            
        # Guardar información del enriquecimiento
        metadata.enrichment_confidence = enrichment.confidence_score
        metadata.enrichment_sources = enrichment.sources_used
        metadata.enrichment_timestamp = time.time()
        
        logger.debug(
            f"Enrichment completed: {len(enrichment.genres)} genres, "
            f"confidence: {enrichment.confidence_score:.2f}, "
            f"sources: {enrichment.sources_used}"
        )
            
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calcular hash MD5 del archivo."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
            
    def extract_batch(self, file_paths: List[str], calculate_hash: bool = False,
                     enrich_metadata: bool = True) -> List[TrackMetadata]:
        """
        Extraer metadatos de múltiples archivos.
        
        Args:
            file_paths: Lista de rutas de archivos
            calculate_hash: Si calcular hash de archivos
            enrich_metadata: Si enriquecer metadatos con APIs musicales
            
        Returns:
            Lista de metadatos extraídos
        """
        results = []
        self.extraction_errors.clear()
        
        logger.info(f"Starting batch extraction for {len(file_paths)} files")
        
        for i, file_path in enumerate(file_paths, 1):
            logger.debug(f"Processing file {i}/{len(file_paths)}: {file_path}")
            
            metadata = self.extract_metadata(file_path, calculate_hash, enrich_metadata)
            if metadata:
                results.append(metadata)
                
        logger.info(f"Batch extraction completed: {len(results)} files processed successfully")
        return results
        
    def get_extraction_errors(self) -> List[str]:
        """Obtener lista de errores de extracción."""
        return self.extraction_errors.copy()
        
    def clear_errors(self) -> None:
        """Limpiar lista de errores."""
        self.extraction_errors.clear()
        
    @staticmethod
    def metadata_to_dict(metadata: TrackMetadata) -> Dict[str, Any]:
        """Convertir metadatos a diccionario."""
        return asdict(metadata)
        
    @staticmethod
    def dict_to_metadata(data: Dict[str, Any]) -> TrackMetadata:
        """Crear metadatos desde diccionario."""
        return TrackMetadata(**data)
        
    def validate_metadata(self, metadata: TrackMetadata) -> Dict[str, List[str]]:
        """
        Validar metadatos y retornar problemas encontrados.
        
        Args:
            metadata: Metadatos a validar
            
        Returns:
            Diccionario con categorías de problemas
        """
        issues = {
            'missing_basic': [],
            'missing_technical': [],
            'invalid_values': [],
            'warnings': []
        }
        
        # Verificar metadatos básicos faltantes
        if not metadata.title:
            issues['missing_basic'].append('Título faltante')
        if not metadata.artist:
            issues['missing_basic'].append('Artista faltante')
        if not metadata.album:
            issues['missing_basic'].append('Álbum faltante')
        if not metadata.genre:
            issues['missing_basic'].append('Género faltante')
            
        # Verificar metadatos técnicos
        if not metadata.duration:
            issues['missing_technical'].append('Duración faltante')
        if not metadata.bitrate:
            issues['missing_technical'].append('Bitrate faltante')
            
        # Verificar valores inválidos
        if metadata.year and (metadata.year < 1900 or metadata.year > 2030):
            issues['invalid_values'].append(f'Año inválido: {metadata.year}')
        if metadata.track_number and metadata.track_number < 1:
            issues['invalid_values'].append(f'Número de track inválido: {metadata.track_number}')
        if metadata.duration and metadata.duration < 0:
            issues['invalid_values'].append(f'Duración inválida: {metadata.duration}')
            
        # Advertencias
        if metadata.file_size < 1024 * 1024:  # < 1MB
            issues['warnings'].append('Archivo muy pequeño (< 1MB)')
        if metadata.bitrate and metadata.bitrate < 128:
            issues['warnings'].append(f'Bitrate bajo: {metadata.bitrate} kbps')
            
        return issues
        
    def get_metadata_completeness(self, metadata: TrackMetadata) -> Dict[str, float]:
        """
        Calcular completitud de metadatos.
        
        Args:
            metadata: Metadatos a analizar
            
        Returns:
            Diccionario con porcentajes de completitud
        """
        basic_fields = ['title', 'artist', 'album', 'genre', 'year']
        technical_fields = ['duration', 'bitrate', 'sample_rate', 'channels']
        extended_fields = ['album_artist', 'composer', 'track_number', 'bpm', 'key']
        
        def calculate_completeness(fields: List[str]) -> float:
            filled = sum(1 for field in fields if getattr(metadata, field) is not None)
            return (filled / len(fields)) * 100 if fields else 0
            
        return {
            'basic': calculate_completeness(basic_fields),
            'technical': calculate_completeness(technical_fields),
            'extended': calculate_completeness(extended_fields),
            'overall': calculate_completeness(basic_fields + technical_fields + extended_fields)
        }
        
    def get_enrichment_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del sistema de enriquecimiento.
        
        Returns:
            Diccionario con estadísticas del enriquecimiento
        """
        if not self.enable_enrichment or not self.enricher:
            return {
                'enrichment_enabled': False,
                'enrichment_available': ENRICHMENT_AVAILABLE
            }
            
        stats = self.enricher.get_stats()
        stats['enrichment_enabled'] = True
        stats['enrichment_available'] = ENRICHMENT_AVAILABLE
        
        return stats
        
    def enrich_existing_metadata(self, metadata: TrackMetadata, 
                                force_refresh: bool = False) -> bool:
        """
        Enriquecer metadatos existentes.
        
        Args:
            metadata: Metadatos a enriquecer
            force_refresh: Si forzar re-enriquecimiento aunque ya exista
            
        Returns:
            True si se enriqueció exitosamente, False si no
        """
        if not self.enable_enrichment or not self.enricher:
            return False
            
        # Verificar si ya está enriquecido y no se fuerza refresh
        if (not force_refresh and metadata.enrichment_timestamp and 
            metadata.enriched_genres):
            logger.debug("Metadata already enriched, skipping")
            return True
            
        if not metadata.artist or not metadata.title:
            logger.debug("Missing artist or title, cannot enrich")
            return False
            
        try:
            self._enrich_metadata(metadata)
            return True
        except Exception as e:
            logger.error(f"Error enriching metadata: {e}")
            return False
            
    def get_best_genres(self, metadata: TrackMetadata, 
                       max_genres: int = 3) -> List[str]:
        """
        Obtener los mejores géneros para un track.
        
        Args:
            metadata: Metadatos del track
            max_genres: Número máximo de géneros a retornar
            
        Returns:
            Lista de géneros ordenados por confianza
        """
        genres = []
        
        # Usar géneros enriquecidos si están disponibles
        if metadata.enriched_genres:
            sorted_genres = sorted(
                metadata.enriched_genres.items(),
                key=lambda x: x[1],
                reverse=True
            )
            genres = [genre for genre, _ in sorted_genres[:max_genres]]
        
        # Fallback al género original si no hay enriquecidos
        elif metadata.genre:
            genres = [metadata.genre]
            
        return genres
        
    def close(self):
        """Cerrar recursos del extractor."""
        if self.enricher:
            self.enricher.close()
            logger.info("MetadataExtractor resources closed") 
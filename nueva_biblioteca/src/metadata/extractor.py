"""
Extractor de metadatos locales de archivos musicales.
"""

import os
from pathlib import Path
from typing import Dict, Optional, List, Union, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

try:
    from mutagen import File as MutagenFile
    from mutagen.id3 import ID3NoHeaderError
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
    from mutagen.wave import WAVE
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

@dataclass
class TrackMetadata:
    """
    Estructura de metadatos extraídos de un archivo musical.
    """
    # Información del archivo
    file_path: str
    file_size: int
    file_format: str
    last_modified: datetime
    
    # Metadatos básicos
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    album_artist: Optional[str] = None
    date: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    
    # Información del track
    track_number: Optional[int] = None
    track_total: Optional[int] = None
    disc_number: Optional[int] = None
    disc_total: Optional[int] = None
    
    # Metadatos técnicos
    duration: Optional[float] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    
    # Metadatos adicionales
    composer: Optional[str] = None
    comment: Optional[str] = None
    lyrics: Optional[str] = None
    isrc: Optional[str] = None
    catalog_number: Optional[str] = None
    label: Optional[str] = None
    
    # Análisis musical (si está disponible en el archivo)
    bpm: Optional[float] = None
    key: Optional[str] = None
    
    # Flags de estado
    has_cover_art: bool = False
    extraction_success: bool = True
    extraction_errors: List[str] = None
    
    def __post_init__(self):
        if self.extraction_errors is None:
            self.extraction_errors = []

class MetadataExtractor:
    """
    Extractor de metadatos locales de archivos musicales usando Mutagen.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if not MUTAGEN_AVAILABLE:
            self.logger.warning("Mutagen no está disponible. Funcionalidad limitada.")
    
    def extract_metadata(self, file_path: Union[str, Path]) -> TrackMetadata:
        """
        Extrae metadatos de un archivo musical.
        """
        path = Path(file_path)
        
        # Información básica del archivo
        try:
            stat = path.stat()
            file_size = stat.st_size
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            file_format = path.suffix.lower().lstrip('.')
        except Exception as e:
            return TrackMetadata(
                file_path=str(path),
                file_size=0,
                file_format="",
                last_modified=datetime.now(),
                extraction_success=False,
                extraction_errors=[f"Error accediendo al archivo: {e}"]
            )
        
        metadata = TrackMetadata(
            file_path=str(path.resolve()),
            file_size=file_size,
            file_format=file_format,
            last_modified=last_modified
        )
        
        if not MUTAGEN_AVAILABLE:
            metadata.extraction_success = False
            metadata.extraction_errors.append("Mutagen no está instalado")
            return metadata
        
        try:
            # Cargar archivo con Mutagen
            audio_file = MutagenFile(str(path))
            
            if audio_file is None:
                metadata.extraction_success = False
                metadata.extraction_errors.append("Archivo no reconocido por Mutagen")
                return metadata
            
            # Extraer metadatos según el formato
            if isinstance(audio_file, MP3):
                self._extract_mp3_metadata(audio_file, metadata)
            elif isinstance(audio_file, FLAC):
                self._extract_flac_metadata(audio_file, metadata)
            elif isinstance(audio_file, MP4):
                self._extract_mp4_metadata(audio_file, metadata)
            elif isinstance(audio_file, OggVorbis):
                self._extract_ogg_metadata(audio_file, metadata)
            elif isinstance(audio_file, WAVE):
                self._extract_wave_metadata(audio_file, metadata)
            else:
                self._extract_generic_metadata(audio_file, metadata)
            
            # Información técnica común
            if hasattr(audio_file, 'info'):
                info = audio_file.info
                metadata.duration = getattr(info, 'length', None)
                metadata.bitrate = getattr(info, 'bitrate', None)
                metadata.sample_rate = getattr(info, 'sample_rate', None)
                metadata.channels = getattr(info, 'channels', None)
            
            # Verificar si tiene artwork
            metadata.has_cover_art = self._has_cover_art(audio_file)
            
        except ID3NoHeaderError:
            metadata.extraction_errors.append("Archivo MP3 sin headers ID3")
        except Exception as e:
            metadata.extraction_success = False
            metadata.extraction_errors.append(f"Error extrayendo metadatos: {e}")
            self.logger.error(f"Error extrayendo metadatos de {path}: {e}")
        
        # Limpiar y normalizar metadatos
        self._normalize_metadata(metadata)
        
        return metadata
    
    def _extract_mp3_metadata(self, audio_file: MP3, metadata: TrackMetadata):
        """
        Extrae metadatos específicos de archivos MP3.
        """
        tags = audio_file.tags
        if not tags:
            return
        
        # Metadatos básicos
        metadata.title = self._get_tag_value(tags, ['TIT2', 'TITLE'])
        metadata.artist = self._get_tag_value(tags, ['TPE1', 'ARTIST'])
        metadata.album = self._get_tag_value(tags, ['TALB', 'ALBUM'])
        metadata.album_artist = self._get_tag_value(tags, ['TPE2', 'ALBUMARTIST'])
        metadata.date = self._get_tag_value(tags, ['TDRC', 'DATE'])
        metadata.genre = self._get_tag_value(tags, ['TCON', 'GENRE'])
        
        # Información del track
        track_info = self._get_tag_value(tags, ['TRCK', 'TRACKNUMBER'])
        if track_info:
            parts = str(track_info).split('/')
            metadata.track_number = self._safe_int(parts[0])
            if len(parts) > 1:
                metadata.track_total = self._safe_int(parts[1])
        
        disc_info = self._get_tag_value(tags, ['TPOS', 'DISCNUMBER'])
        if disc_info:
            parts = str(disc_info).split('/')
            metadata.disc_number = self._safe_int(parts[0])
            if len(parts) > 1:
                metadata.disc_total = self._safe_int(parts[1])
        
        # Metadatos adicionales
        metadata.composer = self._get_tag_value(tags, ['TCOM', 'COMPOSER'])
        metadata.comment = self._get_tag_value(tags, ['COMM', 'COMMENT'])
        metadata.isrc = self._get_tag_value(tags, ['TSRC', 'ISRC'])
        metadata.bpm = self._safe_float(self._get_tag_value(tags, ['TBPM', 'BPM']))
        metadata.key = self._get_tag_value(tags, ['TKEY', 'KEY'])
        
        # Año del campo de fecha
        if metadata.date:
            metadata.year = self._extract_year_from_date(metadata.date)
    
    def _extract_flac_metadata(self, audio_file: FLAC, metadata: TrackMetadata):
        """
        Extrae metadatos específicos de archivos FLAC.
        """
        tags = audio_file.tags
        if not tags:
            return
        
        # FLAC usa Vorbis Comments
        metadata.title = self._get_vorbis_tag(tags, 'TITLE')
        metadata.artist = self._get_vorbis_tag(tags, 'ARTIST')
        metadata.album = self._get_vorbis_tag(tags, 'ALBUM')
        metadata.album_artist = self._get_vorbis_tag(tags, 'ALBUMARTIST')
        metadata.date = self._get_vorbis_tag(tags, 'DATE')
        metadata.genre = self._get_vorbis_tag(tags, 'GENRE')
        
        metadata.track_number = self._safe_int(self._get_vorbis_tag(tags, 'TRACKNUMBER'))
        metadata.track_total = self._safe_int(self._get_vorbis_tag(tags, 'TRACKTOTAL'))
        metadata.disc_number = self._safe_int(self._get_vorbis_tag(tags, 'DISCNUMBER'))
        metadata.disc_total = self._safe_int(self._get_vorbis_tag(tags, 'DISCTOTAL'))
        
        metadata.composer = self._get_vorbis_tag(tags, 'COMPOSER')
        metadata.comment = self._get_vorbis_tag(tags, 'COMMENT')
        metadata.isrc = self._get_vorbis_tag(tags, 'ISRC')
        metadata.bpm = self._safe_float(self._get_vorbis_tag(tags, 'BPM'))
        metadata.key = self._get_vorbis_tag(tags, 'KEY')
        
        if metadata.date:
            metadata.year = self._extract_year_from_date(metadata.date)
    
    def _extract_mp4_metadata(self, audio_file: MP4, metadata: TrackMetadata):
        """
        Extrae metadatos específicos de archivos MP4/M4A.
        """
        tags = audio_file.tags
        if not tags:
            return
        
        # MP4 usa diferentes códigos de tag
        metadata.title = self._get_mp4_tag(tags, '\xa9nam')
        metadata.artist = self._get_mp4_tag(tags, '\xa9ART')
        metadata.album = self._get_mp4_tag(tags, '\xa9alb')
        metadata.album_artist = self._get_mp4_tag(tags, 'aART')
        metadata.date = self._get_mp4_tag(tags, '\xa9day')
        metadata.genre = self._get_mp4_tag(tags, '\xa9gen')
        
        # Track number en MP4 es una tupla (track, total)
        track_info = tags.get('trkn')
        if track_info and len(track_info) > 0:
            track_tuple = track_info[0]
            metadata.track_number = track_tuple[0] if len(track_tuple) > 0 else None
            metadata.track_total = track_tuple[1] if len(track_tuple) > 1 else None
        
        # Disc number también es una tupla
        disc_info = tags.get('disk')
        if disc_info and len(disc_info) > 0:
            disc_tuple = disc_info[0]
            metadata.disc_number = disc_tuple[0] if len(disc_tuple) > 0 else None
            metadata.disc_total = disc_tuple[1] if len(disc_tuple) > 1 else None
        
        metadata.composer = self._get_mp4_tag(tags, '\xa9wrt')
        metadata.comment = self._get_mp4_tag(tags, '\xa9cmt')
        
        # BPM en MP4
        bpm_tag = tags.get('tmpo')
        if bpm_tag:
            metadata.bpm = float(bpm_tag[0])
        
        if metadata.date:
            metadata.year = self._extract_year_from_date(metadata.date)
    
    def _extract_ogg_metadata(self, audio_file: OggVorbis, metadata: TrackMetadata):
        """
        Extrae metadatos específicos de archivos OGG Vorbis.
        """
        # OGG Vorbis usa el mismo sistema que FLAC
        self._extract_flac_metadata(audio_file, metadata)
    
    def _extract_wave_metadata(self, audio_file: WAVE, metadata: TrackMetadata):
        """
        Extrae metadatos específicos de archivos WAV.
        """
        # WAV puede tener tags ID3
        if hasattr(audio_file, 'tags') and audio_file.tags:
            self._extract_mp3_metadata(audio_file, metadata)
    
    def _extract_generic_metadata(self, audio_file, metadata: TrackMetadata):
        """
        Extrae metadatos de formatos genéricos.
        """
        try:
            tags = audio_file.tags
            if tags:
                # Intentar campos comunes
                for key, value in tags.items():
                    if isinstance(value, list) and value:
                        value = value[0]
                    
                    key_lower = str(key).lower()
                    if 'title' in key_lower and not metadata.title:
                        metadata.title = str(value)
                    elif 'artist' in key_lower and not metadata.artist:
                        metadata.artist = str(value)
                    elif 'album' in key_lower and not metadata.album:
                        metadata.album = str(value)
        except Exception as e:
            metadata.extraction_errors.append(f"Error en extracción genérica: {e}")
    
    def _get_tag_value(self, tags, tag_names: List[str]) -> Optional[str]:
        """
        Obtiene el valor de un tag probando múltiples nombres.
        """
        for tag_name in tag_names:
            if tag_name in tags:
                value = tags[tag_name]
                if isinstance(value, list) and value:
                    return str(value[0])
                elif value:
                    return str(value)
        return None
    
    def _get_vorbis_tag(self, tags, tag_name: str) -> Optional[str]:
        """
        Obtiene un tag de Vorbis Comment.
        """
        values = tags.get(tag_name, [])
        return str(values[0]) if values else None
    
    def _get_mp4_tag(self, tags, tag_name: str) -> Optional[str]:
        """
        Obtiene un tag de MP4.
        """
        values = tags.get(tag_name, [])
        return str(values[0]) if values else None
    
    def _has_cover_art(self, audio_file) -> bool:
        """
        Verifica si el archivo tiene artwork/cover art.
        """
        try:
            if isinstance(audio_file, MP3):
                return any(key.startswith('APIC') for key in audio_file.tags.keys()) if audio_file.tags else False
            elif isinstance(audio_file, FLAC):
                return len(audio_file.pictures) > 0
            elif isinstance(audio_file, MP4):
                return 'covr' in audio_file.tags if audio_file.tags else False
            return False
        except:
            return False
    
    def _safe_int(self, value) -> Optional[int]:
        """
        Convierte un valor a entero de forma segura.
        """
        if value is None:
            return None
        try:
            return int(str(value).split('/')[0])  # Por si hay formato "1/10"
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value) -> Optional[float]:
        """
        Convierte un valor a float de forma segura.
        """
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _extract_year_from_date(self, date_string: str) -> Optional[int]:
        """
        Extrae el año de una cadena de fecha.
        """
        if not date_string:
            return None
        
        try:
            # Intentar diferentes formatos
            for fmt in ['%Y', '%Y-%m-%d', '%Y-%m', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    return datetime.strptime(str(date_string)[:10], fmt).year
                except ValueError:
                    continue
            
            # Si no funciona, intentar extraer solo números
            year_str = ''.join(filter(str.isdigit, str(date_string)))[:4]
            if len(year_str) == 4:
                year = int(year_str)
                if 1900 <= year <= 2100:  # Rango razonable
                    return year
        except:
            pass
        
        return None
    
    def _normalize_metadata(self, metadata: TrackMetadata):
        """
        Normaliza y limpia los metadatos extraídos.
        """
        # Limpiar strings vacíos
        string_fields = [
            'title', 'artist', 'album', 'album_artist', 'date', 'genre',
            'composer', 'comment', 'lyrics', 'isrc', 'catalog_number', 
            'label', 'key'
        ]
        
        for field in string_fields:
            value = getattr(metadata, field)
            if value:
                # Limpiar whitespace y strings vacíos
                cleaned = str(value).strip()
                setattr(metadata, field, cleaned if cleaned else None)
        
        # Usar título del filename si no hay título
        if not metadata.title:
            filename = Path(metadata.file_path).stem
            metadata.title = filename
        
        # Valores por defecto para números de disco/track
        if metadata.disc_number is None:
            metadata.disc_number = 1
    
    def extract_batch(self, file_paths: List[Union[str, Path]]) -> List[TrackMetadata]:
        """
        Extrae metadatos de múltiples archivos de forma eficiente.
        """
        results = []
        for file_path in file_paths:
            try:
                metadata = self.extract_metadata(file_path)
                results.append(metadata)
            except Exception as e:
                # Crear metadata con error
                error_metadata = TrackMetadata(
                    file_path=str(file_path),
                    file_size=0,
                    file_format="",
                    last_modified=datetime.now(),
                    extraction_success=False,
                    extraction_errors=[f"Error: {e}"]
                )
                results.append(error_metadata)
        
        return results
    
    def to_dict(self, metadata: TrackMetadata) -> Dict[str, Any]:
        """
        Convierte metadatos a diccionario.
        """
        return asdict(metadata)
    
    def get_supported_formats(self) -> List[str]:
        """
        Retorna la lista de formatos soportados.
        """
        return ['.mp3', '.flac', '.m4a', '.aac', '.wav', '.ogg', '.wma', '.aiff', '.ape', '.opus']
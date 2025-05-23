"""Módulo de integración para el extractor mejorado de metadatos."""
from typing import Dict, List, Optional, Tuple, Any
import os
import re
import logging
from pathlib import Path

# 🔧 PARCHE: Suprimir logs verbosos que causan congelamiento
import logging
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('musicbrainzngs').setLevel(logging.ERROR)
logging.getLogger('musicbrainzngs.musicbrainzngs').setLevel(logging.ERROR)
logging.getLogger('mutagen').setLevel(logging.WARNING)
logging.getLogger('spotipy').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('pylast').setLevel(logging.WARNING)

import mutagen
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TCOM, TCOP, TENC, TLEN, TMOO, TPE2, TPUB, TLAN, TRCK, TPOS, TSRC, TXXX

# Importar la clase original Mp3FileHandler
from src.core.file_handler import Mp3FileHandler
# Importar las funciones mejoradas
from src.core.improved_file_handler import (
    extract_artist_title_improved,
    post_process_artist,
    post_process_title,
    extract_and_clean_metadata
)

logger = logging.getLogger(__name__)

class EnhancedMp3FileHandler(Mp3FileHandler):
    """Versión mejorada del manejador de archivos MP3 con extracción avanzada de metadatos."""
    
    def __init__(self, backup_dir: Optional[str] = None, verbose: bool = False):
        """Constructor de la clase mejorada.
        
        Args:
            backup_dir: Directorio para backups (opcional)
            verbose: Modo verboso para logging detallado
        """
        super().__init__(backup_dir, verbose)
        # Map de IDs de frame ID3 a nombres amigables
        self.tag_fields = {
            'TIT2': {'name': 'title', 'create': lambda t: TIT2(encoding=3, text=t)},
            'TPE1': {'name': 'artist', 'create': lambda t: TPE1(encoding=3, text=t)},
            'TALB': {'name': 'album', 'create': lambda t: TALB(encoding=3, text=t)},
            'TCON': {'name': 'genre', 'create': lambda t: TCON(encoding=3, text=t)},
            'TCOM': {'name': 'composer', 'create': lambda t: TCOM(encoding=3, text=t)},
            'TCOP': {'name': 'copyright', 'create': lambda t: TCOP(encoding=3, text=t)},
            'TENC': {'name': 'encodedby', 'create': lambda t: TENC(encoding=3, text=t)},
            'TLEN': {'name': 'length', 'create': lambda t: TLEN(encoding=3, text=t)},
            'TMOO': {'name': 'mood', 'create': lambda t: TMOO(encoding=3, text=t)},
            'TPE2': {'name': 'albumartist', 'create': lambda t: TPE2(encoding=3, text=t)},
            'TPUB': {'name': 'organization', 'create': lambda t: TPUB(encoding=3, text=t)},
            'TLAN': {'name': 'language', 'create': lambda t: TLAN(encoding=3, text=t)},
            'TRCK': {'name': 'tracknumber', 'create': lambda t: TRCK(encoding=3, text=t)},
            'TPOS': {'name': 'discnumber', 'create': lambda t: TPOS(encoding=3, text=t)},
            'TSRC': {'name': 'isrc', 'create': lambda t: TSRC(encoding=3, text=t)},
        }
        logger.debug("EnhancedMp3FileHandler inicializado")
    
    # PARCHE: Timeout y gestión de memoria
    # timeout_patch_applied
    def get_file_info_with_timeout(self, file_path: str, chunk_size: int = 8192, timeout: float = 30.0) -> Dict[str, str]:
        """Versión con timeout del get_file_info."""
        import signal
        import gc
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Timeout procesando {file_path}")
        
        # Configurar timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout))
        
        try:
            result = self.get_file_info_original(file_path, chunk_size)
            # Limpiar memoria después de cada archivo
            gc.collect()
            return result
        except TimeoutError as e:
            logger.warning(f"Timeout en {file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error en {file_path}: {e}")
            return {}
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    # Aplicar parche si no existe
    if not hasattr(self, 'get_file_info_original'):
        self.get_file_info_original = self.get_file_info
        self.get_file_info = self.get_file_info_with_timeout

    def extract_artist_title_from_filename(self, filename: str, fallback_artist: str = "", fallback_title: str = "") -> Tuple[str, str]:
        """Versión mejorada que reemplaza la función original.
        
        Args:
            filename: Nombre del archivo (sin extensión) a analizar
            fallback_artist: Artista por defecto si no se puede extraer
            fallback_title: Título por defecto si no se puede extraer
            
        Returns:
            Tupla (artista, título)
        """
        # Usar la implementación mejorada
        artist, title = extract_artist_title_improved(filename, fallback_artist, fallback_title)
        
        # Procesar y formatear los resultados
        processed_artist = post_process_artist(artist)
        processed_title = post_process_title(title)
        
        logger.debug(f"Extracción mejorada: Artist='{processed_artist}', Title='{processed_title}'")
        return processed_artist, processed_title
    
    def get_file_info(self, file_path: str, chunk_size: int = 8192) -> Dict[str, str]:
        """Versión mejorada de get_file_info con extracción más robusta de metadatos.
        
        Args:
            file_path: Ruta al archivo MP3
            chunk_size: Tamaño del chunk para lectura (default: 8KB)
            
        Returns:
            Diccionario con información del archivo
        """
        # Primero intentamos usar el método base para obtener info básica
        info = super().get_file_info(file_path, chunk_size)
        
        # Si info está vacía (error) o falta algún dato crítico, intentamos extraer de otra forma
        if not info or not info.get('artist') or not info.get('title'):
            try:
                filename = os.path.basename(file_path)
                filename_without_ext = os.path.splitext(filename)[0]
                
                # Usar la extracción mejorada
                artist, title = self.extract_artist_title_from_filename(
                    filename_without_ext,
                    fallback_artist=info.get('artist', ''),
                    fallback_title=info.get('title', '')
                )
                
                # Actualizar solo si pudimos extraer algo
                if artist:
                    info['artist'] = artist
                if title:
                    info['title'] = title
                    
                logger.info(f"Extracción mejorada aplicada a: {file_path}")
            except Exception as e:
                logger.error(f"Error en extracción mejorada para {file_path}: {e}")
        
        return info
    
    def analyze_filename_patterns(self, directory_path: str) -> Dict[str, int]:
        """Analiza patrones de nombres de archivo en un directorio.
        
        Esta función es útil para entender los patrones comunes en una colección
        de música y mejorar los algoritmos de extracción.
        
        Args:
            directory_path: Ruta al directorio con archivos MP3
            
        Returns:
            Diccionario con conteo de patrones encontrados
        """
        patterns = {
            "artist_title": 0,          # "Artist - Title"
            "artist_feat_title": 0,     # "Artist feat. X - Title"
            "artist_title_feat": 0,     # "Artist - Title feat. X"
            "artist_title_remix": 0,    # "Artist - Title (Remix)"
            "numbered": 0,              # "01 - Artist - Title"
            "no_separator": 0,          # Sin guion separador
            "inverted": 0,              # "Title - Artist"
            "unknown": 0                # No reconocido
        }
        
        if not os.path.isdir(directory_path):
            logger.error(f"No es un directorio válido: {directory_path}")
            return patterns
            
        mp3_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.mp3')]
        logger.info(f"Analizando {len(mp3_files)} archivos MP3 en {directory_path}")
        
        for mp3_file in mp3_files:
            filename = os.path.splitext(mp3_file)[0]
            
            if re.match(r'^\d+\s+[-\.]\s+', filename):
                patterns["numbered"] += 1
            elif ' - ' not in filename:
                patterns["no_separator"] += 1
            elif re.search(r'feat(?:uring|\.)?\s+', filename, re.IGNORECASE):
                if re.search(r'feat(?:uring|\.)?\s+.*?\s+-\s+', filename, re.IGNORECASE):
                    patterns["artist_feat_title"] += 1
                else:
                    patterns["artist_title_feat"] += 1
            elif re.search(r'\([^)]*(?:remix|mix|edit|version)[^)]*\)', filename, re.IGNORECASE):
                patterns["artist_title_remix"] += 1
            elif re.match(r'^.+?\s+-\s+.+$', filename):
                # Detectar si está invertido (heurística simple)
                parts = filename.split(' - ', 1)
                if len(parts[0].split()) > 3 and len(parts[1].split()) <= 2:
                    patterns["inverted"] += 1
                else:
                    patterns["artist_title"] += 1
            else:
                patterns["unknown"] += 1
                
        return patterns
    
    def _preserve_metadata(self, audio: ID3) -> Dict[str, Any]:
        """Preserve all metadata fields from an ID3 tag.
        
        Args:
            audio: ID3 object to extract metadata from
            
        Returns:
            Dictionary of field ID to value mappings
        """
        preserved = {}
        try:
            for frame_id, field_info in self.tag_fields.items():
                if frame_id in audio:
                    # Obtener el valor de texto
                    frame = audio[frame_id]
                    value = str(frame)
                    if value:  # Solo preservar valores no vacíos
                        preserved[frame_id] = value
                        logger.debug(f"Preservado {field_info['name']}: {value}")
                        
            # Manejar frames de texto de usuario por separado
            for frame in audio.getall('TXXX'):
                preserved[f"TXXX:{frame.desc}"] = frame.text
            
            logger.debug(f"Preservados {len(preserved)} campos")
            return preserved
            
        except Exception as e:
            logger.warning(f"Could not preserve metadata: {e}")
            return {}

    def _restore_metadata(self, audio: ID3, preserved: Dict[str, Any]) -> None:
        """Restore preserved metadata to an ID3 tag.
        
        Args:
            audio: ID3 object to restore metadata to
            preserved: Dictionary of field ID to value mappings
        """
        try:
            for frame_id, value in preserved.items():
                if frame_id.startswith('TXXX:'):
                    # Manejar frames de texto de usuario
                    desc = frame_id[5:]
                    frame = TXXX(encoding=3, desc=desc, text=value)
                    audio.add(frame)
                elif frame_id in self.tag_fields:
                    # Manejar frames estándar
                    audio[frame_id] = self.tag_fields[frame_id]['create'](value)
                    
            logger.debug(f"Restaurados {len(preserved)} campos")
            
        except Exception as e:
            logger.warning(f"Could not restore metadata: {e}")

    def update_metadata(self, file_path: str, updates: Dict[str, str], preserve_existing: bool = True) -> bool:
        """Update metadata in an MP3 file while preserving existing fields.
        
        Args:
            file_path: Path to MP3 file
            updates: Dictionary of friendly field names to new values
            preserve_existing: Whether to preserve existing metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Hacer backup primero
            if self.backup_dir:
                self._create_backup(file_path)
            
            # Cargar o crear tag ID3
            try:
                audio = ID3(file_path)
            except:
                audio = ID3()
            
            # Preservar metadata existente
            preserved = {}
            if preserve_existing:
                preserved = self._preserve_metadata(audio)
            
            # Actualizar campos especificados
            for field_name, new_value in updates.items():
                # Encontrar el ID de frame para este nombre de campo
                frame_id = None
                for fid, info in self.tag_fields.items():
                    if info['name'] == field_name:
                        frame_id = fid
                        break
                
                if frame_id and new_value:
                    # Crear y establecer el frame
                    audio[frame_id] = self.tag_fields[frame_id]['create'](new_value)
                    logger.debug(f"Actualizado {field_name} a: {new_value}")
            
            # Restaurar campos preservados que no fueron actualizados
            if preserve_existing:
                updated_fields = set(frame_id for field_name in updates.keys()
                                  for frame_id, info in self.tag_fields.items()
                                  if info['name'] == field_name)
                restore = {k: v for k, v in preserved.items()
                        if k not in updated_fields}
                self._restore_metadata(audio, restore)
            
            # Guardar cambios
            audio.save(file_path)
            logger.info(f"Metadata actualizada con éxito para {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando metadata: {e}")
            return False
    
    def _preserve_metadata(self, audio: mutagen.id3.ID3) -> Dict[str, str]:
        """Preserve all metadata fields from an ID3 tag.
        
        Args:
            audio: mutagen.id3.ID3 object to extract metadata from
            
        Returns:
            Dictionary of metadata fields and values to preserve
        """
        preserved = {}
        try:
            # ID3v2.4 tags we want to preserve
            tag_fields = {
                'TALB': 'album',
                'TCON': 'genre',
                'TCOM': 'composer',
                'TCOP': 'copyright',
                'TENC': 'encodedby',
                'TLEN': 'length',
                'TMOO': 'mood',
                'TPE2': 'albumartist',
                'TPUB': 'organization',
                'TLAN': 'language',
                'TRCK': 'tracknumber',
                'TPOS': 'discnumber',
                'TSRC': 'isrc',
                'TXXX': 'usertext'
            }
            
            for tag, field in tag_fields.items():
                if tag in audio:
                    preserved[field] = str(audio[tag])
            
            logger.debug(f"Preserved metadata fields: {list(preserved.keys())}")
            return preserved
            
        except Exception as e:
            logger.warning(f"Could not preserve metadata: {e}")
            return {}

# Creamos una pequeña función auxiliar para probar la clase mejorada
def compare_extraction_methods(file_path: str) -> Dict[str, str]:
    """Compara la extracción original vs. la mejorada."""
    result = {}
    
    # Manejador original
    original_handler = Mp3FileHandler()
    
    # Manejador mejorado
    enhanced_handler = EnhancedMp3FileHandler()
    
    # Extraer nombre base sin extensión
    filename = os.path.basename(file_path)
    base_name = os.path.splitext(filename)[0]
    
    # Método original
    orig_artist, orig_title = original_handler.extract_artist_title_from_filename(base_name)
    
    # Método mejorado
    enh_artist, enh_title = enhanced_handler.extract_artist_title_from_filename(base_name)
    
    # Recopilar resultados
    result['file_path'] = file_path
    result['base_name'] = base_name
    result['original'] = {
        'artist': orig_artist,
        'title': orig_title
    }
    result['enhanced'] = {
        'artist': enh_artist,
        'title': enh_title
    }
    
    # Indicar si hubo cambios
    result['artist_improved'] = orig_artist != enh_artist
    result['title_improved'] = orig_title != enh_title
    
    return result

"""
Extractor de metadatos de archivos de música
"""
from typing import Dict, Any, Optional
import logging
from pathlib import Path
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

class MetadataExtractor:
    """Extrae metadatos de archivos de música."""

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def extract_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extrae metadatos de un archivo de música.

        Args:
            file_path: Ruta al archivo

        Returns:
            Diccionario con los metadatos o None si hay error
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"No se encontró el archivo: {file_path}")

            if path.suffix.lower() != '.mp3':
                raise ValueError(f"Formato no soportado: {path.suffix}")

            # Cargar archivo con mutagen
            audio = MP3(file_path, ID3=EasyID3)
            
            # Extraer metadatos básicos
            metadata = {
                'id': str(path.stem),  # Usar nombre del archivo como ID temporal
                'title': self._get_tag(audio, 'title', path.stem),
                'artist': self._get_tag(audio, 'artist', 'Unknown Artist'),
                'album': self._get_tag(audio, 'album', 'Unknown Album'),
                'year': self._extract_year(audio),
                'genre': self._get_tag(audio, 'genre'),
                'path': str(path.absolute()),
                'bpm': self._extract_bpm(audio),
                'key': self._extract_key(audio)
            }

            # Extraer propiedades del audio
            audio_mp3 = MP3(file_path)
            if audio_mp3.info:
                metadata.update({
                    'duration': audio_mp3.info.length,
                    'bitrate': audio_mp3.info.bitrate,
                    'sample_rate': audio_mp3.info.sample_rate,
                    'channels': audio_mp3.info.channels
                })

            return metadata

        except Exception as e:
            self._logger.error(f"Error extrayendo metadatos de {file_path}: {str(e)}")
            return None

    def _get_tag(self, audio: EasyID3, tag: str, default: Any = None) -> Any:
        """
        Obtiene un tag específico del archivo.

        Args:
            audio: Objeto EasyID3
            tag: Nombre del tag
            default: Valor por defecto si no existe

        Returns:
            Valor del tag o default si no existe
        """
        try:
            value = audio.get(tag, [default])
            return value[0] if value and value[0] else default
        except Exception:
            return default

    def _extract_year(self, audio: EasyID3) -> Optional[int]:
        """
        Extrae el año de diferentes tags posibles.

        Args:
            audio: Objeto EasyID3

        Returns:
            Año como entero o None si no se encuentra
        """
        try:
            # Intentar diferentes tags donde podría estar el año
            for tag in ['date', 'originaldate', 'year']:
                value = self._get_tag(audio, tag)
                if value:
                    # Extraer los primeros 4 dígitos que encuentre
                    import re
                    match = re.search(r'\d{4}', str(value))
                    if match:
                        return int(match.group())
            return None
        except Exception:
            return None

    def _extract_bpm(self, audio: EasyID3) -> Optional[float]:
        """
        Extrae el BPM del archivo.

        Args:
            audio: Objeto EasyID3

        Returns:
            BPM como float o None si no se encuentra
        """
        try:
            bpm = self._get_tag(audio, 'bpm')
            return float(bpm) if bpm else None
        except (ValueError, TypeError):
            return None

    def _extract_key(self, audio: EasyID3) -> Optional[str]:
        """
        Extrae la clave musical del archivo.

        Args:
            audio: Objeto EasyID3

        Returns:
            Clave musical o None si no se encuentra
        """
        try:
            # Intentar diferentes tags donde podría estar la clave
            for tag in ['initialkey', 'key']:
                key = self._get_tag(audio, tag)
                if key:
                    return key
            return None
        except Exception:
            return None

    def scan_directory(self, directory: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Escanea un directorio en busca de archivos de música.

        Args:
            directory: Ruta al directorio
            recursive: Si debe buscar en subdirectorios

        Returns:
            Diccionario con resultados del escaneo
        """
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': [],
            'tracks': []
        }

        try:
            path = Path(directory)
            if not path.exists():
                raise ValueError(f"El directorio {directory} no existe")

            # Determinar patrón de búsqueda
            pattern = '**/*.mp3' if recursive else '*.mp3'
            
            # Escanear archivos
            for file_path in path.glob(pattern):
                results['total'] += 1
                
                metadata = self.extract_from_file(str(file_path))
                if metadata:
                    results['success'] += 1
                    results['tracks'].append(metadata)
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Error procesando {file_path}")

            return results

        except Exception as e:
            self._logger.error(f"Error escaneando directorio {directory}: {str(e)}")
            results['errors'].append(str(e))
            return results

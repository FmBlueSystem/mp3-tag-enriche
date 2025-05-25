"""
Servicio de gestión musical que integra con la base de datos
"""
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import uuid

from src.core.database.music_database import (
    MusicDatabase,
    DatabaseFactory,
    TrackMetadata
)
from .metadata_extractor import MetadataExtractor

class MusicService:
    """Servicio para gestionar la biblioteca musical."""

    def __init__(self, db_type: str = 'sqlite', db_path: str = 'music.db'):
        """
        Inicializa el servicio de música.

        Args:
            db_type: Tipo de base de datos ('sqlite' o 'json')
            db_path: Ruta al archivo de base de datos
        """
        self._logger = logging.getLogger(__name__)
        self.db = DatabaseFactory.create(db_type, db_path)
        if not self.db.connect():
            raise RuntimeError("No se pudo conectar a la base de datos")

    def __del__(self):
        """Asegura que la conexión se cierre al destruir el servicio."""
        self.db.disconnect()

    def add_track(self, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Añade un nuevo track a la biblioteca.

        Args:
            metadata: Diccionario con los metadatos del track

        Returns:
            ID del track si se añadió exitosamente, None si falló
        """
        try:
            track = TrackMetadata(**metadata)
            if self.db.update_track(track.id, metadata):
                return track.id
            return None
        except Exception as e:
            self._logger.error(f"Error añadiendo track: {str(e)}")
            return None

    def get_track(self, track_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un track por su ID.

        Args:
            track_id: ID del track

        Returns:
            Diccionario con los metadatos del track o None si no existe
        """
        try:
            track = self.db.get_track(track_id)
            if track:
                return vars(track)
            return None
        except Exception as e:
            self._logger.error(f"Error obteniendo track {track_id}: {str(e)}")
            return None

    def update_track(self, track_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Actualiza los metadatos de un track.

        Args:
            track_id: ID del track
            metadata: Nuevos metadatos

        Returns:
            True si se actualizó exitosamente
        """
        try:
            return self.db.update_track(track_id, metadata)
        except Exception as e:
            self._logger.error(f"Error actualizando track {track_id}: {str(e)}")
            return False

    def search_tracks(self, 
                     query: Optional[str] = None, 
                     filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Busca tracks por texto y/o filtros.

        Args:
            query: Texto a buscar en título, artista o álbum
            filters: Filtros adicionales (género, año, etc.)

        Returns:
            Lista de tracks que coinciden con la búsqueda
        """
        try:
            search_filters = filters or {}
            
            if query:
                # Implementar búsqueda por texto en múltiples campos
                # TODO: Mejorar con búsqueda fuzzy o indexación de texto
                tracks = []
                for track in self.db.get_tracks():
                    if (query.lower() in track.title.lower() or
                        query.lower() in track.artist.lower() or
                        query.lower() in track.album.lower()):
                        tracks.append(vars(track))
                return tracks
            
            return [vars(track) for track in self.db.get_tracks(filters=search_filters)]
            
        except Exception as e:
            self._logger.error(f"Error buscando tracks: {str(e)}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la biblioteca.

        Returns:
            Diccionario con estadísticas
        """
        try:
            tracks = self.db.get_tracks()
            
            # Extraer datos únicos
            genres = set()
            artists = set()
            albums = set()
            years = set()
            
            for track in tracks:
                if track.genre:
                    genres.add(track.genre)
                if track.artist:
                    artists.add(track.artist)
                if track.album:
                    albums.add(track.album)
                if track.year:
                    years.add(track.year)
            
            return {
                'total_tracks': len(tracks),
                'total_genres': len(genres),
                'total_artists': len(artists),
                'total_albums': len(albums),
                'year_range': [min(years), max(years)] if years else None,
                'genres': sorted(list(genres))
            }
            
        except Exception as e:
            self._logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {
                'total_tracks': 0,
                'total_genres': 0,
                'total_artists': 0,
                'total_albums': 0,
                'year_range': None,
                'genres': []
            }

    def import_tracks(self, directory: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Importa tracks desde un directorio.

        Args:
            directory: Ruta al directorio con archivos de música
            recursive: Si debe buscar en subdirectorios

        Returns:
            Diccionario con resultados de la importación
        """
        try:
            extractor = MetadataExtractor()
            scan_results = extractor.scan_directory(directory, recursive)
            
            results = {
                'total': scan_results['total'],
                'success': 0,
                'failed': 0,
                'errors': scan_results['errors'],
                'imported_tracks': []
            }

            # Procesar tracks encontrados
            for track_metadata in scan_results['tracks']:
                try:
                    # Generar ID único si no existe
                    if 'id' not in track_metadata or not track_metadata['id']:
                        track_metadata['id'] = str(uuid.uuid4())

                    # Añadir track a la base de datos
                    track_id = self.add_track(track_metadata)
                    if track_id:
                        results['success'] += 1
                        results['imported_tracks'].append(track_id)
                    else:
                        results['failed'] += 1
                        results['errors'].append(
                            f"No se pudo importar: {track_metadata.get('path', 'Unknown')}"
                        )
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(str(e))
            
            return results

        except Exception as e:
            self._logger.error(f"Error importando tracks: {str(e)}")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'errors': [str(e)],
                'imported_tracks': []
            }

    def export_playlist(self, tracks: List[str], format: str = 'm3u') -> Optional[str]:
        """
        Exporta una lista de tracks a un archivo de playlist.

        Args:
            tracks: Lista de IDs de tracks
            format: Formato de salida ('m3u' o 'm3u8')

        Returns:
            Contenido de la playlist o None si hay error
        """
        try:
            if format not in ['m3u', 'm3u8']:
                raise ValueError(f"Formato {format} no soportado")

            content = ['#EXTM3U']
            
            for track_id in tracks:
                track = self.db.get_track(track_id)
                if track and track.path:
                    # Agregar metadata en formato Extended M3U
                    duration = -1  # TODO: Obtener duración real
                    content.append(f'#EXTINF:{duration},{track.artist} - {track.title}')
                    content.append(track.path)

            return '\n'.join(content)

        except Exception as e:
            self._logger.error(f"Error exportando playlist: {str(e)}")
            return None

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
        Obtiene estadísticas generales de la biblioteca.

        Returns:
            Diccionario con estadísticas (total_tracks, total_artists, etc.)
        """
        try:
            tracks = self.db.get_tracks()
            
            # Recopilar datos
            artists = set()
            albums = set()
            genres = set()
            years = []
            
            for track in tracks:
                if track.artist:
                    artists.add(track.artist)
                if track.album:
                    albums.add(track.album)
                if track.genre:
                    genres.add(track.genre)
                if hasattr(track, 'year') and track.year:
                    years.append(track.year)
            
            # Crear estadísticas
            stats = {
                'total_tracks': len(tracks),
                'total_artists': len(artists),
                'total_albums': len(albums),
                'total_genres': len(genres),
                'years_range': f"{min(years) if years else 'N/A'}-{max(years) if years else 'N/A'}",
                'most_common_genre': max(genres, key=lambda x: sum(1 for t in tracks if t.genre == x)) if genres else 'N/A'
            }
            
            return stats
            
        except Exception as e:
            self._logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {
                'total_tracks': 0,
                'total_artists': 0,
                'total_albums': 0,
                'total_genres': 0,
                'years_range': 'N/A',
                'most_common_genre': 'N/A'
            }
            
    def import_files_with_manager(self, directory_path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Importa archivos utilizando el ImportManager directamente desde MusicService.
        Este método simplifica la integración entre ImportManager y MusicService.
        
        Args:
            directory_path: Ruta del directorio a importar
            recursive: Si buscar recursivamente en subdirectorios
            
        Returns:
            Diccionario con resultados de la importación
        """
        from ..importers.import_manager import ImportManager
        
        try:
            # Crear instancia de ImportManager
            import_manager = ImportManager()
            
            # Ejecutar importación
            result = import_manager.import_directory(
                directory_path,
                recursive=recursive,
                check_duplicates=True,
                extract_metadata=True
            )
            
            # Procesar tracks importados si es necesario
            for track_id in result.new_tracks:
                # Podemos realizar procesamiento adicional aquí si es necesario
                pass
                
            # Notificar cambios en la biblioteca
            self._logger.info(f"Biblioteca actualizada: {result.successful_imports} nuevos tracks")
            
            return {
                'total': result.total_processed,
                'success': result.successful_imports,
                'failed': result.failed_imports,
                'duplicates': result.duplicate_files,
                'errors': result.errors,
                'imported_tracks': result.new_tracks,
                'duration': result.duration_seconds
            }
            
        except Exception as e:
            self._logger.error(f"Error en importación integrada: {str(e)}")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'duplicates': 0,
                'errors': [str(e)],
                'imported_tracks': [],
                'duration': 0
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

    def get_all_tracks(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los tracks de la biblioteca.

        Returns:
            Lista con todos los tracks en formato diccionario
        """
        try:
            tracks = self.db.get_tracks()
            return [vars(track) for track in tracks]
        except Exception as e:
            self._logger.error(f"Error obteniendo todos los tracks: {str(e)}")
            return []

    def get_artists(self) -> List[str]:
        """
        Obtiene todos los artistas únicos de la biblioteca.

        Returns:
            Lista de artistas únicos
        """
        try:
            tracks = self.db.get_tracks()
            artists = set()
            for track in tracks:
                if track.artist:
                    artists.add(track.artist)
            return sorted(list(artists))
        except Exception as e:
            self._logger.error(f"Error obteniendo artistas: {str(e)}")
            return []

    def get_keys(self) -> List[str]:
        """
        Obtiene todas las claves musicales únicas de la biblioteca.

        Returns:
            Lista de claves musicales únicas
        """
        try:
            tracks = self.db.get_tracks()
            keys = set()
            for track in tracks:
                if track.key:
                    keys.add(track.key)
            return sorted(list(keys))
        except Exception as e:
            self._logger.error(f"Error obteniendo claves: {str(e)}")
            return []

    def get_genres(self) -> List[str]:
        """
        Obtiene todos los géneros únicos de la biblioteca.

        Returns:
            Lista de géneros únicos
        """
        try:
            tracks = self.db.get_tracks()
            genres = set()
            for track in tracks:
                if track.genre:
                    genres.add(track.genre)
            return sorted(list(genres))
        except Exception as e:
            self._logger.error(f"Error obteniendo géneros: {str(e)}")
            return []

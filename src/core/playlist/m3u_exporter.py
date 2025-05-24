"""
Exportador de playlists en formato M3U.
Permite exportar listas de reproducción para reproductores compatibles.
"""
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..database.music_database import MusicDatabase, Track, Playlist

logger = logging.getLogger(__name__)

class M3UExporter:
    """Clase para exportar playlists en formato M3U."""
    
    def __init__(self, database: MusicDatabase):
        """
        Inicializa el exportador.
        
        Args:
            database: Instancia de la base de datos musical
        """
        self.database = database
    
    def export_playlist(self, playlist_id: int, output_path: str, 
                        extended: bool = True, relative_paths: bool = False,
                        base_dir: Optional[str] = None) -> bool:
        """
        Exporta una playlist como archivo M3U.
        
        Args:
            playlist_id: ID de la playlist a exportar
            output_path: Ruta del archivo M3U de salida
            extended: Si es True, usa formato M3U extendido con metadatos
            relative_paths: Si es True, usa rutas relativas al base_dir
            base_dir: Directorio base para rutas relativas
            
        Returns:
            True si se exportó correctamente, False en caso contrario
        """
        try:
            # Obtener información de la playlist
            cursor = self.database.connection.execute(
                "SELECT * FROM playlists WHERE id = ?", 
                (playlist_id,)
            )
            playlist_row = cursor.fetchone()
            
            if not playlist_row:
                logger.error(f"Playlist no encontrada: {playlist_id}")
                return False
            
            # Obtener tracks de la playlist
            cursor = self.database.connection.execute('''
                SELECT t.* 
                FROM tracks t
                JOIN playlist_tracks pt ON t.id = pt.track_id
                WHERE pt.playlist_id = ?
                ORDER BY pt.position
            ''', (playlist_id,))
            
            tracks = [Track.from_row(row) for row in cursor.fetchall()]
            
            if not tracks:
                logger.warning(f"La playlist {playlist_id} no tiene tracks")
            
            # Crear directorio de salida si no existe
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Escribir archivo M3U
            with open(output_path, 'w', encoding='utf-8') as f:
                # Encabezado del archivo M3U
                if extended:
                    f.write("#EXTM3U\n")
                    f.write(f"#PLAYLIST:{playlist_row['name']}\n")
                
                # Escribir cada track
                for track in tracks:
                    filepath = track.filepath
                    
                    # Convertir a ruta relativa si se solicita
                    if relative_paths and base_dir:
                        try:
                            filepath = os.path.relpath(filepath, base_dir)
                        except ValueError:
                            # Si las unidades son diferentes, mantener ruta absoluta
                            logger.warning(f"No se pudo crear ruta relativa para {filepath}")
                    
                    # Escribir información extendida
                    if extended:
                        duration_secs = int(track.duration) if track.duration else 0
                        f.write(f"#EXTINF:{duration_secs},{track.artist} - {track.title}\n")
                    
                    # Escribir ruta del archivo
                    f.write(f"{filepath}\n")
            
            logger.info(f"Playlist '{playlist_row['name']}' exportada como M3U en {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando playlist {playlist_id}: {e}")
            return False
    
    def export_all_playlists(self, output_dir: str, extended: bool = True,
                           relative_paths: bool = False, base_dir: Optional[str] = None) -> Dict[str, bool]:
        """
        Exporta todas las playlists como archivos M3U.
        
        Args:
            output_dir: Directorio donde guardar los archivos M3U
            extended: Si es True, usa formato M3U extendido con metadatos
            relative_paths: Si es True, usa rutas relativas al base_dir
            base_dir: Directorio base para rutas relativas
            
        Returns:
            Diccionario con los nombres de las playlists y el éxito de la exportación
        """
        try:
            # Crear directorio de salida si no existe
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Obtener todas las playlists
            cursor = self.database.connection.execute("SELECT * FROM playlists")
            playlists = cursor.fetchall()
            
            results = {}
            for playlist in playlists:
                # Sanitizar nombre para archivo
                safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in playlist["name"])
                output_path = os.path.join(output_dir, f"{safe_name}.m3u")
                
                # Exportar playlist
                success = self.export_playlist(
                    playlist["id"], 
                    output_path, 
                    extended, 
                    relative_paths, 
                    base_dir
                )
                
                results[playlist["name"]] = success
            
            logger.info(f"Se exportaron {sum(results.values())} de {len(results)} playlists en {output_dir}")
            return results
            
        except Exception as e:
            logger.error(f"Error exportando todas las playlists: {e}")
            return {}
    
    def create_playlist_from_m3u(self, m3u_path: str, name: Optional[str] = None) -> Optional[int]:
        """
        Crea una playlist a partir de un archivo M3U.
        
        Args:
            m3u_path: Ruta del archivo M3U
            name: Nombre de la playlist (si es None, se usa el nombre del archivo)
            
        Returns:
            ID de la playlist creada o None si falló
        """
        try:
            # Verificar que el archivo existe
            if not os.path.exists(m3u_path):
                logger.error(f"Archivo M3U no encontrado: {m3u_path}")
                return None
            
            # Determinar el nombre de la playlist
            if name is None:
                name = os.path.splitext(os.path.basename(m3u_path))[0]
            
            # Leer archivo M3U
            filepaths = []
            with open(m3u_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    filepaths.append(line)
            
            if not filepaths:
                logger.warning(f"El archivo M3U {m3u_path} no contiene rutas de archivos")
                return None
            
            # Crear la playlist
            from ..database.music_database import Playlist
            playlist = Playlist(
                name=name,
                description=f"Importada desde {os.path.basename(m3u_path)}",
                is_dynamic=False
            )
            
            playlist_id = self.database.create_playlist(playlist)
            
            # Añadir tracks a la playlist
            position = 0
            for filepath in filepaths:
                # Buscar el track en la base de datos
                track = self.database.get_track_by_filepath(filepath)
                
                if track:
                    self.database.add_track_to_playlist(playlist_id, track.id, position)
                    position += 1
                else:
                    logger.warning(f"Track no encontrado en la base de datos: {filepath}")
            
            logger.info(f"Playlist '{name}' creada con {position} tracks desde {m3u_path}")
            return playlist_id
            
        except Exception as e:
            logger.error(f"Error creando playlist desde M3U {m3u_path}: {e}")
            return None

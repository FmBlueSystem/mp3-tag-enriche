"""
Utilidades y helpers para el sistema de reglas.
"""
import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from ..database.music_database import MusicDatabase, Track
import re

logger = logging.getLogger(__name__)

class PlaylistGenerator:
    """Generador de playlists basado en reglas."""
    
    def __init__(self, db_manager: MusicDatabase):
        """
        Inicializa el generador de playlists.
        
        Args:
            db_manager: Gestor de base de datos
        """
        self.db_manager = db_manager
    
    def generate_by_genre(self, genre: str, limit: int = 100) -> Optional[int]:
        """
        Genera una playlist por género.
        
        Args:
            genre: Género a filtrar
            limit: Número máximo de tracks
            
        Returns:
            ID de la playlist creada o None si falla
        """
        try:
            # Buscar tracks con el género especificado
            query = f"""
                SELECT * FROM tracks 
                WHERE genre LIKE ? 
                ORDER BY year DESC, artist 
                LIMIT ?
            """
            rows = self.db_manager.fetch_query(query, (f"%{genre}%", limit))
            
            if not rows:
                logger.warning(f"No se encontraron tracks para el género '{genre}'")
                return None
                
            # Crear la playlist
            from ..database.models import Playlist
            playlist = Playlist(
                name=f"Género: {genre}",
                description=f"Tracks del género {genre}",
                is_dynamic=True
            )
            
            # Serializar las reglas
            rules = {
                "type": "genre_filter",
                "params": {
                    "genre": genre,
                    "limit": limit
                }
            }
            playlist.rules_json = json.dumps(rules)
            
            # Guardar la playlist
            playlist_id = self.db_manager.create_playlist(playlist)
            
            # Añadir tracks a la playlist
            for i, row in enumerate(rows):
                track = Track.from_row(row)
                self.db_manager.add_track_to_playlist(playlist_id, track.id, i)
            
            logger.info(f"Playlist por género '{genre}' creada con {len(rows)} tracks")
            return playlist_id
            
        except Exception as e:
            logger.error(f"Error generando playlist por género: {e}")
            return None
    
    def generate_by_bpm_range(self, min_bpm: float, max_bpm: float, limit: int = 100) -> Optional[int]:
        """
        Genera una playlist por rango de BPM.
        
        Args:
            min_bpm: BPM mínimo
            max_bpm: BPM máximo
            limit: Número máximo de tracks
            
        Returns:
            ID de la playlist creada o None si falla
        """
        try:
            # Buscar tracks en el rango de BPM
            query = """
                SELECT * FROM tracks 
                WHERE bpm BETWEEN ? AND ? 
                ORDER BY bpm 
                LIMIT ?
            """
            rows = self.db_manager.fetch_query(query, (min_bpm, max_bpm, limit))
            
            if not rows:
                logger.warning(f"No se encontraron tracks para el rango de BPM {min_bpm}-{max_bpm}")
                return None
                
            # Crear la playlist
            from ..database.models import Playlist
            playlist_name = f"BPM: {min_bpm}-{max_bpm}"
            playlist = Playlist(
                name=playlist_name,
                description=f"Tracks con BPM entre {min_bpm} y {max_bpm}",
                is_dynamic=True
            )
            
            # Serializar las reglas
            rules = {
                "type": "bpm_range_filter",
                "params": {
                    "min_bpm": min_bpm,
                    "max_bpm": max_bpm,
                    "limit": limit
                }
            }
            playlist.rules_json = json.dumps(rules)
            
            # Guardar la playlist
            playlist_id = self.db_manager.create_playlist(playlist)
            
            # Añadir tracks a la playlist
            for i, row in enumerate(rows):
                track = Track.from_row(row)
                self.db_manager.add_track_to_playlist(playlist_id, track.id, i)
            
            logger.info(f"Playlist por BPM {min_bpm}-{max_bpm} creada con {len(rows)} tracks")
            return playlist_id
            
        except Exception as e:
            logger.error(f"Error generando playlist por BPM: {e}")
            return None
    
    def generate_energy_progression(self, start_energy: float, end_energy: float, 
                                   steps: int = 10, strict_mode: bool = False) -> Optional[int]:
        """
        Genera una playlist con progresión de energía.
        
        Args:
            start_energy: Nivel de energía inicial (0-1)
            end_energy: Nivel de energía final (0-1)
            steps: Número de pasos/tracks
            strict_mode: Si es estricto en la selección de tracks
            
        Returns:
            ID de la playlist creada o None si falla
        """
        try:
            # Calculamos el incremento de energía por paso
            energy_step = (end_energy - start_energy) / (steps - 1) if steps > 1 else 0
            
            # Crear la playlist
            from ..database.models import Playlist
            direction = "ascendente" if end_energy > start_energy else "descendente"
            playlist = Playlist(
                name=f"Progresión energética {direction}",
                description=f"Progresión de energía {start_energy:.1f} a {end_energy:.1f}",
                is_dynamic=True
            )
            
            # Serializar las reglas
            rules = {
                "type": "energy_progression",
                "params": {
                    "start_energy": start_energy,
                    "end_energy": end_energy,
                    "steps": steps,
                    "strict_mode": strict_mode
                }
            }
            playlist.rules_json = json.dumps(rules)
            
            # Guardar la playlist
            playlist_id = self.db_manager.create_playlist(playlist)
            
            # Coleccionar los tracks para cada nivel de energía
            selected_tracks = []
            used_track_ids = set()
            
            for i in range(steps):
                target_energy = start_energy + (i * energy_step)
                energy_range = 0.05 if strict_mode else 0.15
                
                # Buscar tracks cercanos a este nivel de energía
                query = """
                    SELECT * FROM tracks 
                    WHERE energy BETWEEN ? AND ? 
                    ORDER BY ABS(energy - ?) 
                    LIMIT 5
                """
                rows = self.db_manager.fetch_query(
                    query, 
                    (target_energy - energy_range, target_energy + energy_range, target_energy)
                )
                
                # Seleccionar un track que no hayamos usado ya
                for row in rows:
                    track = Track.from_row(row)
                    if track.id not in used_track_ids:
                        selected_tracks.append(track)
                        used_track_ids.add(track.id)
                        break
            
            # Añadir tracks seleccionados a la playlist
            for i, track in enumerate(selected_tracks):
                self.db_manager.add_track_to_playlist(playlist_id, track.id, i)
            
            logger.info(f"Playlist de progresión energética creada con {len(selected_tracks)} tracks")
            return playlist_id
            
        except Exception as e:
            logger.error(f"Error generando playlist por progresión de energía: {e}")
            return None
    
    def generate_camelot_mix(self, start_key: str, transitions: int = 12, 
                            energy_direction: str = "up") -> Optional[int]:
        """
        Genera una playlist con compatibilidad armónica Camelot.
        
        Args:
            start_key: Clave Camelot inicial (ej: '1A')
            transitions: Número de transiciones
            energy_direction: Dirección de energía ('up', 'down', 'stable')
            
        Returns:
            ID de la playlist creada o None si falla
        """
        try:
            # Validar la clave inicial
            if not re.match(r"^\d{1,2}[AB]$", start_key):
                logger.error(f"Clave Camelot inválida: {start_key}")
                return None
            
            # Crear la playlist
            from ..database.models import Playlist
            playlist = Playlist(
                name=f"Mix Camelot desde {start_key}",
                description=f"Mix armónico Camelot starting en {start_key}",
                is_dynamic=True
            )
            
            # Serializar las reglas
            rules = {
                "type": "camelot_mix",
                "params": {
                    "start_key": start_key,
                    "transitions": transitions,
                    "energy_direction": energy_direction
                }
            }
            playlist.rules_json = json.dumps(rules)
            
            # Guardar la playlist
            playlist_id = self.db_manager.create_playlist(playlist)
            
            # Seleccionar el primer track
            query = """
                SELECT * FROM tracks 
                WHERE camelot_key = ? 
                ORDER BY RANDOM() 
                LIMIT 1
            """
            rows = self.db_manager.fetch_query(query, (start_key,))
            
            if not rows:
                logger.warning(f"No se encontraron tracks para la clave inicial {start_key}")
                return playlist_id
            
            # Añadir el primer track
            current_track = Track.from_row(rows[0])
            current_key = current_track.camelot_key
            self.db_manager.add_track_to_playlist(playlist_id, current_track.id, 0)
            
            # Obtener transiciones compatibles y construir la playlist
            selected_tracks = [current_track]
            
            for i in range(1, transitions):
                # Obtener tracks compatibles con la clave actual
                compatible_tracks = self.db_manager.get_compatible_tracks(current_track.id, 10)
                
                if not compatible_tracks:
                    break
                
                # Filtrar por dirección de energía
                if energy_direction == "up":
                    filtered = [(t, s) for t, s in compatible_tracks if t.energy >= current_track.energy]
                elif energy_direction == "down":
                    filtered = [(t, s) for t, s in compatible_tracks if t.energy <= current_track.energy]
                else:  # stable
                    filtered = [(t, s) for t, s in compatible_tracks 
                                if 0.85 * current_track.energy <= t.energy <= 1.15 * current_track.energy]
                
                # Si no hay tracks que cumplan, usar los originales
                if not filtered:
                    filtered = compatible_tracks
                
                # Seleccionar el siguiente track (evitando repeticiones)
                next_track = None
                for track, _ in filtered:
                    if track.id not in [t.id for t in selected_tracks]:
                        next_track = track
                        break
                
                if not next_track:
                    break
                
                # Añadir el track a la playlist
                self.db_manager.add_track_to_playlist(playlist_id, next_track.id, i)
                selected_tracks.append(next_track)
                current_track = next_track
            
            logger.info(f"Playlist Camelot creada con {len(selected_tracks)} tracks")
            return playlist_id
            
        except Exception as e:
            logger.error(f"Error generando playlist Camelot: {e}")
            return None

class M3UExporter:
    """Exportador de playlists a formato M3U."""
    
    @staticmethod
    def export_playlist(db_manager: MusicDatabase, playlist_id: int, output_path: str) -> bool:
        """
        Exporta una playlist a formato M3U.
        
        Args:
            db_manager: Gestor de base de datos
            playlist_id: ID de la playlist a exportar
            output_path: Ruta donde guardar el archivo M3U
            
        Returns:
            True si la exportación fue exitosa
        """
        try:
            # Obtener información de la playlist
            playlist_rows = db_manager.fetch_query(
                "SELECT * FROM playlists WHERE id = ?", 
                (playlist_id,)
            )
            
            if not playlist_rows:
                logger.error(f"Playlist con ID {playlist_id} no encontrada")
                return False
            
            playlist_name = playlist_rows[0]["name"]
            
            # Obtener tracks de la playlist
            query = """
                SELECT t.* FROM tracks t
                JOIN playlist_tracks pt ON t.id = pt.track_id
                WHERE pt.playlist_id = ?
                ORDER BY pt.position
            """
            track_rows = db_manager.fetch_query(query, (playlist_id,))
            
            if not track_rows:
                logger.warning(f"Playlist {playlist_name} está vacía")
                return False
            
            # Crear el contenido del archivo M3U
            m3u_content = ["#EXTM3U"]
            
            for row in track_rows:
                track = Track.from_row(row)
                duration_seconds = int(track.duration) if track.duration else 0
                
                # Agregar información extendida del track
                m3u_content.append(f"#EXTINF:{duration_seconds},{track.artist} - {track.title}")
                m3u_content.append(track.filepath)
            
            # Escribir el archivo
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(m3u_content))
            
            logger.info(f"Playlist {playlist_name} exportada a {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando playlist a M3U: {e}")
            return False

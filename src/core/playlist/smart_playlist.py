"""
Generador de playlists inteligentes con criterios dinámicos.
"""
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import random

from ..database.music_database import MusicDatabase, Track, Playlist
from ..rules.rule_engine import RuleEngine

logger = logging.getLogger(__name__)

@dataclass
class PlaylistTemplate:
    """Plantilla para generar playlists inteligentes."""
    name: str
    description: str = ""
    rule_name: str = ""
    max_tracks: int = 100
    sort_by: str = "random"  # random, bpm_asc, bpm_desc, energy_asc, energy_desc, year_asc, year_desc
    energy_flow: Optional[str] = None  # None, "wave", "build", "cooldown"
    min_bpm: Optional[float] = None
    max_bpm: Optional[float] = None
    allow_duplicates: bool = False

class SmartPlaylistGenerator:
    """Generador de playlists inteligentes."""
    
    def __init__(self, database: MusicDatabase, rule_engine: RuleEngine):
        """
        Inicializa el generador.
        
        Args:
            database: Instancia de la base de datos musical
            rule_engine: Motor de reglas para filtrado
        """
        self.database = database
        self.rule_engine = rule_engine
    
    def generate_playlist(self, template: PlaylistTemplate) -> Optional[int]:
        """
        Genera una playlist a partir de una plantilla.
        
        Args:
            template: Plantilla con criterios para la playlist
            
        Returns:
            ID de la playlist generada o None si falló
        """
        try:
            # Obtener tracks según la regla (si hay)
            tracks = []
            if template.rule_name:
                rule = self.rule_engine.get_rule(template.rule_name)
                if rule:
                    tracks = self.rule_engine.find_matching_tracks(template.rule_name, limit=1000)
                    logger.info(f"Encontrados {len(tracks)} tracks para regla '{template.rule_name}'")
                else:
                    logger.warning(f"Regla no encontrada: {template.rule_name}")
            
            # Si no hay regla o no se encontraron tracks, obtener todos
            if not tracks:
                cursor = self.database.connection.execute(
                    "SELECT * FROM tracks ORDER BY RANDOM() LIMIT ?", 
                    (template.max_tracks * 2,)
                )
                tracks = [Track.from_row(row) for row in cursor.fetchall()]
                logger.info(f"Usando {len(tracks)} tracks aleatorios")
            
            # Aplicar filtros adicionales
            filtered_tracks = []
            for track in tracks:
                # Filtro de BPM
                if template.min_bpm is not None and (track.bpm is None or track.bpm < template.min_bpm):
                    continue
                if template.max_bpm is not None and (track.bpm is None or track.bpm > template.max_bpm):
                    continue
                
                filtered_tracks.append(track)
            
            if len(filtered_tracks) == 0:
                logger.warning("No hay tracks que cumplan los criterios")
                return None
            
            # Ordenar según criterio
            if template.sort_by == "random":
                random.shuffle(filtered_tracks)
            elif template.sort_by == "bpm_asc":
                filtered_tracks.sort(key=lambda t: t.bpm if t.bpm is not None else 0)
            elif template.sort_by == "bpm_desc":
                filtered_tracks.sort(key=lambda t: t.bpm if t.bpm is not None else 0, reverse=True)
            elif template.sort_by == "energy_asc":
                filtered_tracks.sort(key=lambda t: t.energy if t.energy is not None else 0)
            elif template.sort_by == "energy_desc":
                filtered_tracks.sort(key=lambda t: t.energy if t.energy is not None else 0, reverse=True)
            elif template.sort_by == "year_asc":
                filtered_tracks.sort(key=lambda t: t.year if t.year is not None else 0)
            elif template.sort_by == "year_desc":
                filtered_tracks.sort(key=lambda t: t.year if t.year is not None else 0, reverse=True)
            
            # Aplicar patrón de flujo de energía si se especifica
            if template.energy_flow and len(filtered_tracks) > 5:
                filtered_tracks = self._apply_energy_flow(filtered_tracks, template.energy_flow)
            
            # Limitar número de tracks
            if len(filtered_tracks) > template.max_tracks:
                filtered_tracks = filtered_tracks[:template.max_tracks]
            
            # Crear la playlist
            playlist = Playlist(
                name=template.name,
                description=template.description,
                rules_json=json.dumps({
                    "rule_name": template.rule_name,
                    "sort_by": template.sort_by,
                    "energy_flow": template.energy_flow,
                    "min_bpm": template.min_bpm,
                    "max_bpm": template.max_bpm
                }),
                is_dynamic=True
            )
            
            playlist_id = self.database.create_playlist(playlist)
            
            # Añadir tracks a la playlist
            for position, track in enumerate(filtered_tracks):
                self.database.add_track_to_playlist(playlist_id, track.id, position)
            
            logger.info(f"Playlist '{template.name}' generada con {len(filtered_tracks)} tracks")
            return playlist_id
            
        except Exception as e:
            logger.error(f"Error generando playlist: {e}")
            return None
    
    def _apply_energy_flow(self, tracks: List[Track], flow_type: str) -> List[Track]:
        """
        Aplica un patrón de flujo de energía a los tracks.
        
        Args:
            tracks: Lista de tracks a ordenar
            flow_type: Tipo de flujo de energía
            
        Returns:
            Lista de tracks ordenados según el patrón
        """
        # Asegurarse de que hay suficientes tracks
        if len(tracks) < 5:
            return tracks
        
        # Ordenar por energía para procesamiento
        energy_sorted = sorted(tracks, key=lambda t: t.energy if t.energy is not None else 0)
        
        result = []
        
        if flow_type == "wave":
            # Patrón oscilante: medio -> alto -> bajo -> alto -> medio
            segments = 5
            segment_size = len(tracks) // segments
            
            # Dividir en segmentos por energía
            very_low = energy_sorted[:segment_size]
            low = energy_sorted[segment_size:segment_size*2]
            mid = energy_sorted[segment_size*2:segment_size*3]
            high = energy_sorted[segment_size*3:segment_size*4]
            very_high = energy_sorted[segment_size*4:]
            
            # Construir onda
            result.extend(mid)
            result.extend(high)
            result.extend(very_high)
            result.extend(high)
            result.extend(mid)
            result.extend(low)
            result.extend(very_low)
            result.extend(low)
            result.extend(mid)
            
        elif flow_type == "build":
            # Incremento gradual: bajo -> medio -> alto
            third = len(tracks) // 3
            
            low_energy = energy_sorted[:third]
            mid_energy = energy_sorted[third:third*2]
            high_energy = energy_sorted[third*2:]
            
            result.extend(low_energy)
            result.extend(mid_energy)
            result.extend(high_energy)
            
        elif flow_type == "cooldown":
            # Descenso gradual: alto -> medio -> bajo
            third = len(tracks) // 3
            
            low_energy = energy_sorted[:third]
            mid_energy = energy_sorted[third:third*2]
            high_energy = energy_sorted[third*2:]
            
            result.extend(high_energy)
            result.extend(mid_energy)
            result.extend(low_energy)
            
        else:
            # Si el tipo no es reconocido, mantener el orden original
            return tracks
        
        return result
    
    def update_smart_playlist(self, playlist_id: int) -> bool:
        """
        Actualiza una playlist inteligente según sus reglas.
        
        Args:
            playlist_id: ID de la playlist a actualizar
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
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
            
            # Verificar que es dinámica
            if not playlist_row["is_dynamic"]:
                logger.warning(f"La playlist {playlist_id} no es dinámica")
                return False
            
            # Obtener configuración de la playlist
            rules_json = playlist_row["rules_json"]
            try:
                rules_data = json.loads(rules_json)
            except json.JSONDecodeError:
                logger.error(f"Error decodificando JSON de reglas para playlist {playlist_id}")
                return False
            
            # Crear plantilla desde la configuración
            template = PlaylistTemplate(
                name=playlist_row["name"],
                description=playlist_row["description"],
                rule_name=rules_data.get("rule_name", ""),
                sort_by=rules_data.get("sort_by", "random"),
                energy_flow=rules_data.get("energy_flow"),
                min_bpm=rules_data.get("min_bpm"),
                max_bpm=rules_data.get("max_bpm")
            )
            
            # Eliminar tracks actuales
            self.database.connection.execute(
                "DELETE FROM playlist_tracks WHERE playlist_id = ?",
                (playlist_id,)
            )
            
            # Regenerar la playlist
            tracks = []
            if template.rule_name:
                tracks = self.rule_engine.find_matching_tracks(template.rule_name, limit=1000)
            
            if not tracks:
                cursor = self.database.connection.execute(
                    "SELECT * FROM tracks ORDER BY RANDOM() LIMIT ?",
                    (template.max_tracks * 2,)
                )
                tracks = [Track.from_row(row) for row in cursor.fetchall()]
            
            # Aplicar filtros y ordenación
            filtered_tracks = []
            for track in tracks:
                if template.min_bpm is not None and (track.bpm is None or track.bpm < template.min_bpm):
                    continue
                if template.max_bpm is not None and (track.bpm is None or track.bpm > template.max_bpm):
                    continue
                filtered_tracks.append(track)
            
            # Ordenar según criterio
            if template.sort_by == "random":
                random.shuffle(filtered_tracks)
            elif template.sort_by == "bpm_asc":
                filtered_tracks.sort(key=lambda t: t.bpm if t.bpm is not None else 0)
            elif template.sort_by == "bpm_desc":
                filtered_tracks.sort(key=lambda t: t.bpm if t.bpm is not None else 0, reverse=True)
            elif template.sort_by == "energy_asc":
                filtered_tracks.sort(key=lambda t: t.energy if t.energy is not None else 0)
            elif template.sort_by == "energy_desc":
                filtered_tracks.sort(key=lambda t: t.energy if t.energy is not None else 0, reverse=True)
            
            # Aplicar patrón de flujo de energía
            if template.energy_flow and len(filtered_tracks) > 5:
                filtered_tracks = self._apply_energy_flow(filtered_tracks, template.energy_flow)
            
            # Limitar número de tracks
            if len(filtered_tracks) > template.max_tracks:
                filtered_tracks = filtered_tracks[:template.max_tracks]
            
            # Añadir tracks a la playlist
            for position, track in enumerate(filtered_tracks):
                self.database.add_track_to_playlist(playlist_id, track.id, position)
            
            logger.info(f"Playlist '{template.name}' actualizada con {len(filtered_tracks)} tracks")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando playlist inteligente: {e}")
            self.database.connection.rollback()
            return False
    
    def generate_energy_progression_playlist(self, name: str, seed_track_id: int, 
                                            direction: str = "build", tracks_count: int = 15) -> Optional[int]:
        """
        Genera una playlist con progresión de energía a partir de un track semilla.
        
        Args:
            name: Nombre de la playlist
            seed_track_id: ID del track semilla
            direction: Dirección de la progresión (build, cooldown, wave)
            tracks_count: Número de tracks en la playlist
            
        Returns:
            ID de la playlist generada o None si falló
        """
        try:
            # Obtener track semilla
            seed_track = self.database.get_track_by_id(seed_track_id)
            if not seed_track:
                logger.error(f"Track semilla no encontrado: {seed_track_id}")
                return None
            
            # Obtener tracks compatibles armónicamente
            compatible_tracks = self.database.get_compatible_tracks(seed_track_id, max_results=50)
            if not compatible_tracks:
                logger.warning(f"No se encontraron tracks compatibles con {seed_track_id}")
                return None
            
            # Filtrar por BPM similar (±10%)
            if seed_track.bpm:
                filtered_by_bpm = []
                for track, score in compatible_tracks:
                    if track.bpm and 0.9 * seed_track.bpm <= track.bpm <= 1.1 * seed_track.bpm:
                        filtered_by_bpm.append((track, score))
                
                if filtered_by_bpm:
                    compatible_tracks = filtered_by_bpm
            
            # Organizar por progresión de energía
            if seed_track.energy is not None:
                seed_energy = seed_track.energy
                
                # Ordenar por energía
                energy_sorted = sorted(
                    compatible_tracks, 
                    key=lambda x: x[0].energy if x[0].energy is not None else 0
                )
                
                result_tracks = []
                
                if direction == "build":
                    # Incremento gradual de energía
                    start_idx = 0
                    for i in range(len(energy_sorted)):
                        if energy_sorted[i][0].energy >= seed_energy:
                            start_idx = i
                            break
                    
                    # Añadir track semilla al inicio
                    result_tracks.append(seed_track)
                    
                    # Añadir tracks con energía creciente
                    for i in range(start_idx, len(energy_sorted)):
                        result_tracks.append(energy_sorted[i][0])
                        if len(result_tracks) >= tracks_count:
                            break
                
                elif direction == "cooldown":
                    # Descenso gradual de energía
                    start_idx = len(energy_sorted) - 1
                    for i in range(len(energy_sorted) - 1, -1, -1):
                        if energy_sorted[i][0].energy <= seed_energy:
                            start_idx = i
                            break
                    
                    # Añadir track semilla al inicio
                    result_tracks.append(seed_track)
                    
                    # Añadir tracks con energía decreciente
                    for i in range(start_idx, -1, -1):
                        result_tracks.append(energy_sorted[i][0])
                        if len(result_tracks) >= tracks_count:
                            break
                
                elif direction == "wave":
                    # Patrón ondulante alrededor de la energía semilla
                    mid_energy = []
                    higher_energy = []
                    lower_energy = []
                    
                    for track, _ in compatible_tracks:
                        if track.energy is None:
                            continue
                        
                        if abs(track.energy - seed_energy) <= 0.1:
                            mid_energy.append(track)
                        elif track.energy > seed_energy:
                            higher_energy.append(track)
                        else:
                            lower_energy.append(track)
                    
                    higher_energy.sort(key=lambda t: t.energy or 0)
                    lower_energy.sort(key=lambda t: t.energy or 0, reverse=True)
                    
                    # Construir patrón ondulante
                    result_tracks = [seed_track]  # Comenzar con semilla
                    
                    while len(result_tracks) < tracks_count:
                        # Añadir un track de energía más alta si hay disponible
                        if higher_energy:
                            result_tracks.append(higher_energy.pop(0))
                            if len(result_tracks) >= tracks_count:
                                break
                        
                        # Añadir un track de energía más baja si hay disponible
                        if lower_energy:
                            result_tracks.append(lower_energy.pop(0))
                            if len(result_tracks) >= tracks_count:
                                break
                        
                        # Añadir un track de energía similar si hay disponible
                        if mid_energy:
                            result_tracks.append(mid_energy.pop(0))
                            if len(result_tracks) >= tracks_count:
                                break
                        
                        # Si no hay más tracks disponibles, salir
                        if not higher_energy and not lower_energy and not mid_energy:
                            break
                
                else:
                    # Si no se reconoce la dirección, usar los tracks compatibles
                    result_tracks = [seed_track] + [t for t, _ in compatible_tracks[:tracks_count-1]]
            else:
                # Si no hay información de energía, usar los tracks compatibles
                result_tracks = [seed_track] + [t for t, _ in compatible_tracks[:tracks_count-1]]
            
            # Limitar número de tracks
            if len(result_tracks) > tracks_count:
                result_tracks = result_tracks[:tracks_count]
            
            # Crear la playlist
            playlist = Playlist(
                name=name,
                description=f"Progresión de energía '{direction}' a partir de {seed_track.title}",
                rules_json=json.dumps({
                    "seed_track_id": seed_track_id,
                    "direction": direction,
                    "generated_at": datetime.now().isoformat()
                }),
                is_dynamic=False  # Las playlists de progresión no son dinámicas
            )
            
            playlist_id = self.database.create_playlist(playlist)
            
            # Añadir tracks a la playlist
            for position, track in enumerate(result_tracks):
                self.database.add_track_to_playlist(playlist_id, track.id, position)
            
            logger.info(f"Playlist de progresión '{name}' generada con {len(result_tracks)} tracks")
            return playlist_id
            
        except Exception as e:
            logger.error(f"Error generando playlist de progresión: {e}")
            return None

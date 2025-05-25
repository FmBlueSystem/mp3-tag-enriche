import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

from .parser import parse_rule, validate_rule, LogicalExpression
from .rule_engine import RuleEngine, validate_order_by
from ..data import crud

logger = logging.getLogger(__name__)

class PlaylistGenerationError(Exception):
    """Excepción personalizada para errores en la generación de playlists."""
    pass

class SmartPlaylistGenerator:
    """
    Generador de playlists inteligentes que integra parsing, evaluación de reglas
    y persistencia en base de datos.
    """
    
    def __init__(self, db_connection):
        """
        Inicializa el generador con una conexión a la base de datos.
        
        Args:
            db_connection: Conexión SQLite a la base de datos
        """
        self.conn = db_connection
        self.rule_engine = RuleEngine(db_connection)
    
    def create_smart_playlist(self, name: str, rule_text: str, 
                            description: str = "", 
                            sort_field: str = None,
                            sort_order: str = "ASC",
                            max_tracks: int = None) -> Optional[int]:
        """
        Crea una nueva playlist inteligente con la regla especificada.
        
        Args:
            name: Nombre de la playlist
            rule_text: Regla en formato de texto (ej: "genre = 'Rock' AND bpm > 120")
            description: Descripción opcional de la playlist
            sort_field: Campo por el que ordenar los resultados
            sort_order: Orden de clasificación ("ASC" o "DESC")
            max_tracks: Número máximo de tracks en la playlist
            
        Returns:
            ID de la playlist creada o None si hubo error
            
        Raises:
            PlaylistGenerationError: Si hay errores en la validación o creación
        """
        try:
            # Validar la regla
            if not validate_rule(rule_text):
                raise PlaylistGenerationError(f"Regla no válida: {rule_text}")
            
            # Validar orden si se especifica
            if sort_field:
                order_clause = f"{sort_field} {sort_order}"
                if not validate_order_by(order_clause):
                    raise PlaylistGenerationError(f"Cláusula de orden no válida: {order_clause}")
            
            # Crear la playlist en la base de datos
            playlist_id = crud.create_smart_playlist(
                self.conn, 
                name, 
                description
            )
            
            if not playlist_id:
                raise PlaylistGenerationError(f"No se pudo crear la playlist '{name}'")
            
            # Actualizar campos de ordenación si se especifican
            if sort_field:
                crud.update_smart_playlist(
                    self.conn, 
                    playlist_id,
                    sort_field=sort_field,
                    sort_order=sort_order
                )
            
            # Añadir la regla a la playlist
            rule_id = crud.add_rule_to_playlist(self.conn, playlist_id, rule_text)
            if not rule_id:
                # Si falla añadir la regla, limpiar la playlist creada
                crud.delete_smart_playlist(self.conn, playlist_id)
                raise PlaylistGenerationError(f"No se pudo añadir la regla a la playlist")
            
            # Generar los tracks iniciales
            self.regenerate_playlist(playlist_id, max_tracks=max_tracks)
            
            logger.info(f"Playlist inteligente '{name}' creada con ID {playlist_id}")
            return playlist_id
            
        except Exception as e:
            logger.error(f"Error creando playlist '{name}': {e}")
            raise PlaylistGenerationError(f"Error creando playlist: {e}")
    
    def regenerate_playlist(self, playlist_id: int, max_tracks: int = None) -> int:
        """
        Regenera los tracks de una playlist inteligente basándose en sus reglas.
        
        Args:
            playlist_id: ID de la playlist a regenerar
            max_tracks: Número máximo de tracks a incluir
            
        Returns:
            Número de tracks añadidos a la playlist
            
        Raises:
            PlaylistGenerationError: Si hay errores en la regeneración
        """
        try:
            # Obtener la playlist
            playlist = crud.get_smart_playlist_by_id(self.conn, playlist_id)
            if not playlist:
                raise PlaylistGenerationError(f"Playlist con ID {playlist_id} no encontrada")
            
            # Obtener la regla
            rule_info = crud.get_rule_for_playlist(self.conn, playlist_id)
            if not rule_info:
                raise PlaylistGenerationError(f"No se encontró regla para playlist {playlist_id}")
            
            rule_text = rule_info['expression_text']
            
            # Parsear la regla
            try:
                expression = parse_rule(rule_text)
            except Exception as e:
                raise PlaylistGenerationError(f"Error parseando regla '{rule_text}': {e}")
            
            # Construir cláusula de orden
            order_by = None
            if playlist.get('sort_field'):
                sort_order = playlist.get('sort_order', 'ASC')
                order_by = f"{playlist['sort_field']} {sort_order}"
            
            # Obtener los IDs de tracks que cumplen la regla
            track_ids = self.rule_engine.get_track_ids_for_rule(
                expression,
                order_by=order_by,
                limit=max_tracks
            )
            
            # Limpiar tracks existentes de la playlist
            crud.clear_playlist_tracks(self.conn, playlist_id)
            
            # Añadir los nuevos tracks con ranking
            for rank, track_id in enumerate(track_ids):
                crud.add_track_to_playlist_results(self.conn, playlist_id, track_id, rank=rank)
            
            # Actualizar timestamp de última generación
            crud.update_smart_playlist(
                self.conn, 
                playlist_id, 
                last_generated_at=datetime.now()
            )
            
            logger.info(f"Playlist {playlist_id} regenerada con {len(track_ids)} tracks")
            return len(track_ids)
            
        except Exception as e:
            logger.error(f"Error regenerando playlist {playlist_id}: {e}")
            raise PlaylistGenerationError(f"Error regenerando playlist: {e}")
    
    def update_playlist_rule(self, playlist_id: int, new_rule_text: str, 
                           regenerate: bool = True, max_tracks: int = None) -> bool:
        """
        Actualiza la regla de una playlist inteligente.
        
        Args:
            playlist_id: ID de la playlist
            new_rule_text: Nueva regla en formato de texto
            regenerate: Si regenerar automáticamente la playlist
            max_tracks: Número máximo de tracks si se regenera
            
        Returns:
            True si se actualizó correctamente
            
        Raises:
            PlaylistGenerationError: Si hay errores en la actualización
        """
        try:
            # Validar la nueva regla
            if not validate_rule(new_rule_text):
                raise PlaylistGenerationError(f"Nueva regla no válida: {new_rule_text}")
            
            # Verificar que la playlist existe
            playlist = crud.get_smart_playlist_by_id(self.conn, playlist_id)
            if not playlist:
                raise PlaylistGenerationError(f"Playlist con ID {playlist_id} no encontrada")
            
            # Actualizar la regla
            rule_id = crud.add_rule_to_playlist(self.conn, playlist_id, new_rule_text)
            if not rule_id:
                raise PlaylistGenerationError("No se pudo actualizar la regla")
            
            # Regenerar si se solicita
            if regenerate:
                self.regenerate_playlist(playlist_id, max_tracks=max_tracks)
            
            logger.info(f"Regla de playlist {playlist_id} actualizada")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando regla de playlist {playlist_id}: {e}")
            raise PlaylistGenerationError(f"Error actualizando regla: {e}")
    
    def get_playlist_preview(self, rule_text: str, max_tracks: int = 10) -> List[Dict]:
        """
        Obtiene una vista previa de los tracks que cumpliría una regla sin crear la playlist.
        
        Args:
            rule_text: Regla a evaluar
            max_tracks: Número máximo de tracks en la vista previa
            
        Returns:
            Lista de diccionarios con información de los tracks
            
        Raises:
            PlaylistGenerationError: Si hay errores en la evaluación
        """
        try:
            # Validar y parsear la regla
            if not validate_rule(rule_text):
                raise PlaylistGenerationError(f"Regla no válida: {rule_text}")
            
            expression = parse_rule(rule_text)
            
            # Evaluar la regla
            tracks = self.rule_engine.evaluate_rule(expression, limit=max_tracks)
            
            return tracks
            
        except Exception as e:
            logger.error(f"Error obteniendo vista previa para regla '{rule_text}': {e}")
            raise PlaylistGenerationError(f"Error en vista previa: {e}")
    
    def get_playlist_stats(self, playlist_id: int) -> Dict:
        """
        Obtiene estadísticas de una playlist inteligente.
        
        Args:
            playlist_id: ID de la playlist
            
        Returns:
            Diccionario con estadísticas de la playlist
        """
        try:
            playlist = crud.get_smart_playlist_by_id(self.conn, playlist_id)
            if not playlist:
                raise PlaylistGenerationError(f"Playlist con ID {playlist_id} no encontrada")
            
            # Obtener tracks de la playlist
            tracks = crud.get_tracks_for_playlist(self.conn, playlist_id)
            
            if not tracks:
                return {
                    'playlist_name': playlist['name'],
                    'total_tracks': 0,
                    'total_duration': 0,
                    'avg_bpm': 0,
                    'avg_energy': 0,
                    'genres': [],
                    'years_range': None,
                    'last_generated': playlist.get('last_generated_at')
                }
            
            # Calcular estadísticas
            total_duration = sum(track.get('duration', 0) for track in tracks)
            bpms = [track['bpm'] for track in tracks if track.get('bpm')]
            energies = [track['energy'] for track in tracks if track.get('energy')]
            genres = list(set(track['genre'] for track in tracks if track.get('genre')))
            years = [track['year'] for track in tracks if track.get('year')]
            
            stats = {
                'playlist_name': playlist['name'],
                'total_tracks': len(tracks),
                'total_duration': total_duration,
                'total_duration_formatted': self._format_duration(total_duration),
                'avg_bpm': round(sum(bpms) / len(bpms), 1) if bpms else 0,
                'avg_energy': round(sum(energies) / len(energies), 1) if energies else 0,
                'genres': genres,
                'years_range': (min(years), max(years)) if years else None,
                'last_generated': playlist.get('last_generated_at')
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de playlist {playlist_id}: {e}")
            raise PlaylistGenerationError(f"Error obteniendo estadísticas: {e}")
    
    def export_playlist_m3u(self, playlist_id: int, output_path: str) -> bool:
        """
        Exporta una playlist inteligente a formato M3U.
        
        Args:
            playlist_id: ID de la playlist
            output_path: Ruta donde guardar el archivo M3U
            
        Returns:
            True si se exportó correctamente
        """
        try:
            playlist = crud.get_smart_playlist_by_id(self.conn, playlist_id)
            if not playlist:
                raise PlaylistGenerationError(f"Playlist con ID {playlist_id} no encontrada")
            
            tracks = crud.get_tracks_for_playlist(self.conn, playlist_id)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                f.write(f"# Playlist: {playlist['name']}\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n")
                f.write(f"# Total tracks: {len(tracks)}\n\n")
                
                for track in tracks:
                    duration = track.get('duration', 0)
                    title = track.get('title', 'Unknown')
                    artist = track.get('artist', 'Unknown')
                    path = track.get('path', '')
                    
                    f.write(f"#EXTINF:{duration},{artist} - {title}\n")
                    f.write(f"{path}\n")
            
            logger.info(f"Playlist {playlist_id} exportada a {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando playlist {playlist_id}: {e}")
            return False
    
    def _format_duration(self, seconds: int) -> str:
        """Formatea duración en segundos a formato legible."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

def regenerate_all_playlists(db_connection, max_tracks_per_playlist: int = None) -> Dict[str, int]:
    """
    Regenera todas las playlists inteligentes en la base de datos.
    
    Args:
        db_connection: Conexión a la base de datos
        max_tracks_per_playlist: Límite de tracks por playlist
        
    Returns:
        Diccionario con estadísticas de la regeneración
    """
    generator = SmartPlaylistGenerator(db_connection)
    
    # Obtener todas las playlists
    playlists = crud.get_all_smart_playlists(db_connection)
    
    stats = {
        'total_playlists': len(playlists),
        'successful': 0,
        'failed': 0,
        'total_tracks_generated': 0,
        'errors': []
    }
    
    for playlist in playlists:
        try:
            if playlist.get('is_enabled', True):  # Solo regenerar playlists habilitadas
                tracks_count = generator.regenerate_playlist(
                    playlist['playlist_id'], 
                    max_tracks=max_tracks_per_playlist
                )
                stats['successful'] += 1
                stats['total_tracks_generated'] += tracks_count
                logger.info(f"Regenerada playlist '{playlist['name']}' con {tracks_count} tracks")
            else:
                logger.info(f"Saltando playlist deshabilitada '{playlist['name']}'")
        except Exception as e:
            stats['failed'] += 1
            error_msg = f"Error regenerando '{playlist['name']}': {e}"
            stats['errors'].append(error_msg)
            logger.error(error_msg)
    
    return stats

# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de uso del generador de playlists
    from ..data.database_setup import setup_database
    
    # Configurar base de datos de prueba
    db_file = "test_playlist_generator.db"
    setup_database(db_file)
    
    conn = crud.create_connection(db_file)
    if not conn:
        print("No se pudo conectar a la base de datos")
        exit(1)
    
    # Poblar con datos de ejemplo
    crud.populate_sample_data(conn)
    
    # Crear generador
    generator = SmartPlaylistGenerator(conn)
    
    try:
        # Ejemplo 1: Crear playlist de rock
        print("=== Creando playlist de Rock ===")
        rock_playlist_id = generator.create_smart_playlist(
            name="Rock Classics",
            rule_text="genre = 'Rock'",
            description="Clásicos del rock",
            sort_field="year",
            sort_order="DESC"
        )
        print(f"Playlist de rock creada con ID: {rock_playlist_id}")
        
        # Ejemplo 2: Vista previa de una regla
        print("\n=== Vista previa de regla compleja ===")
        preview_tracks = generator.get_playlist_preview(
            "bpm > 120 AND energy >= 7",
            max_tracks=5
        )
        print(f"Vista previa: {len(preview_tracks)} tracks encontrados")
        for track in preview_tracks:
            print(f"  - {track['title']} by {track['artist']} (BPM: {track['bpm']}, Energy: {track['energy']})")
        
        # Ejemplo 3: Estadísticas de playlist
        if rock_playlist_id:
            print(f"\n=== Estadísticas de playlist {rock_playlist_id} ===")
            stats = generator.get_playlist_stats(rock_playlist_id)
            print(f"Nombre: {stats['playlist_name']}")
            print(f"Total tracks: {stats['total_tracks']}")
            print(f"Duración total: {stats['total_duration_formatted']}")
            print(f"BPM promedio: {stats['avg_bpm']}")
            print(f"Géneros: {', '.join(stats['genres'])}")
        
        # Ejemplo 4: Exportar a M3U
        if rock_playlist_id:
            print(f"\n=== Exportando playlist {rock_playlist_id} ===")
            export_success = generator.export_playlist_m3u(
                rock_playlist_id, 
                "rock_classics.m3u"
            )
            print(f"Exportación exitosa: {export_success}")
        
        # Ejemplo 5: Regenerar todas las playlists
        print("\n=== Regenerando todas las playlists ===")
        regen_stats = regenerate_all_playlists(conn, max_tracks_per_playlist=50)
        print(f"Playlists procesadas: {regen_stats['total_playlists']}")
        print(f"Exitosas: {regen_stats['successful']}")
        print(f"Fallidas: {regen_stats['failed']}")
        print(f"Total tracks generados: {regen_stats['total_tracks_generated']}")
        
    except PlaylistGenerationError as e:
        print(f"Error en generación de playlist: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")
    finally:
        conn.close()
        print("\nConexión cerrada.") 
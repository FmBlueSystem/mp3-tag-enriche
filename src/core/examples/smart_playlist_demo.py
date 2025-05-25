#!/usr/bin/env python3
"""
Demostración de SmartPlaylist con actualización automática.
Muestra la integración del sistema de triggers con playlists inteligentes.
"""

import os
import time
import logging
from datetime import datetime

from ..smart_playlist import SmartPlaylist, SmartPlaylistError

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_demo_playlist(music_path: str) -> SmartPlaylist:
    """
    Crea una playlist de demostración con reglas y triggers.
    
    Args:
        music_path: Ruta al directorio de música
        
    Returns:
        SmartPlaylist configurada
    """
    # Crear playlist con regla inicial
    playlist = SmartPlaylist(
        playlist_id="demo_001",
        name="House Music 2020+",
        rule_text="(genre = 'House') AND (year >= 2020) AND (bpm BETWEEN 120-128)"
    )
    
    # Agregar directorio de música
    playlist.add_music_path(music_path)
    
    # Configurar triggers
    playlist.setup_triggers({
        # Monitor de archivos
        'file_trigger': {
            'recursive': True,
            'file_patterns': {r'.*\.(mp3|flac)$'},
            'debounce_seconds': 1.0
        },
        
        # Actualizaciones programadas
        'schedule_trigger': {
            'cron_expression': '*/15 * * * *',  # Cada 15 minutos
            'timezone': 'UTC',
            'skip_missed': True
        },
        
        # Umbral de cambios
        'threshold_trigger': {
            'min_changes': 5,
            'max_wait_minutes': 10,
            'change_types': {'FILE_ADDED', 'FILE_MODIFIED'}
        }
    })
    
    return playlist

def test_rule_changes(playlist: SmartPlaylist):
    """
    Prueba cambios en la regla de la playlist.
    
    Args:
        playlist: SmartPlaylist a probar
    """
    logger.info("\nProbando cambios de regla...")
    
    # Regla válida
    new_rule = "(genre = 'Techno') AND (energy >= 0.8)"
    logger.info(f"Cambiando a regla válida: {new_rule}")
    playlist.set_rule(new_rule)
    logger.info(f"Estado: {playlist}")
    
    # Regla inválida
    bad_rule = "genre = 'House' AND AND energy > 0.5"
    logger.info(f"\nIntentando regla inválida: {bad_rule}")
    playlist.set_rule(bad_rule)
    logger.info(f"Estado: {playlist}")
    logger.info(f"Error: {playlist.error_message}")

def monitor_playlist(playlist: SmartPlaylist, duration_seconds: int = 300):
    """
    Monitorea la actividad de la playlist por un período.
    
    Args:
        playlist: SmartPlaylist a monitorear
        duration_seconds: Duración del monitoreo en segundos
    """
    logger.info("\nIniciando monitoreo de playlist...")
    
    try:
        start_time = datetime.now()
        end_time = start_time.timestamp() + duration_seconds
        
        while datetime.now().timestamp() < end_time:
            # Mostrar estadísticas cada 10 segundos
            stats = playlist.get_stats()
            logger.info(f"\nEstado actual de playlist:")
            logger.info(f"- Nombre: {stats['name']}")
            logger.info(f"- Tracks: {stats['track_count']}")
            logger.info(f"- Última actualización: {stats['last_update']}")
            logger.info(f"- Triggers activos: {stats['active_triggers']}")
            logger.info("- Estadísticas de triggers:")
            for trigger_type, trigger_stats in stats['trigger_stats'].items():
                logger.info(f"  * {trigger_type}: {trigger_stats}")
                
            # Esperar antes de la siguiente actualización
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("\nMonitoreo interrumpido por el usuario")
        
def main():
    """Punto de entrada principal de la demo"""
    try:
        # Directorio de música para la demo
        music_path = os.path.expanduser("~/Music")
        if not os.path.exists(music_path):
            music_path = "."  # Usar directorio actual si no existe ~/Music
            
        # Crear y configurar playlist
        playlist = create_demo_playlist(music_path)
        
        # Mostrar configuración inicial
        logger.info(f"Playlist creada: {playlist}")
        logger.info(f"Monitoreando directorio: {music_path}")
        
        # Probar cambios de regla
        test_rule_changes(playlist)
        
        # Monitorear actividad
        monitor_playlist(playlist, 300)  # 5 minutos
        
    except SmartPlaylistError as e:
        logger.error(f"Error de playlist: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        return 1
        
    return 0

if __name__ == '__main__':
    exit(main())

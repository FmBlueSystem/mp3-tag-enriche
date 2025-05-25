#!/usr/bin/env python3
"""
Demostración del sistema de triggers para playlists inteligentes.
Muestra el uso de los diferentes tipos de triggers y su integración.
"""

import os
import time
from datetime import datetime, timedelta
import logging

from ..trigger_manager import TriggerManager
from ..file_watcher import MusicFileWatcher
from ..trigger_types import FileTrigger, ScheduleTrigger, ThresholdTrigger

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_demo_triggers(music_path: str) -> TriggerManager:
    """
    Configura triggers de demostración para una playlist.
    
    Args:
        music_path: Ruta al directorio de música
        
    Returns:
        TriggerManager configurado con los triggers de demo
    """
    # Crear y configurar el manager
    manager = TriggerManager()
    
    # Configurar file watcher
    watcher = MusicFileWatcher(manager)
    
    # ID de ejemplo para la playlist
    playlist_id = "demo_playlist_001"
    
    # 1. Configurar File Trigger
    file_trigger = FileTrigger(playlist_id, watcher)
    file_trigger.configure({
        'watch_paths': {music_path},
        'file_patterns': {r'.*\.(mp3|flac|m4a|wav)$'},
        'ignore_patterns': {r'.*\.temp$', r'.*\.bak$'},
        'recursive': True,
        'debounce_seconds': 2.0
    })
    
    # 2. Configurar Schedule Trigger
    schedule_trigger = ScheduleTrigger(playlist_id)
    schedule_trigger.configure({
        'cron_expression': '*/5 * * * *',  # Cada 5 minutos
        'timezone': 'UTC',
        'skip_missed': True
    })
    
    # 3. Configurar Threshold Trigger
    threshold_trigger = ThresholdTrigger(playlist_id)
    threshold_trigger.configure({
        'min_changes': 5,
        'max_wait_minutes': 15,
        'change_types': {'FILE_ADDED', 'FILE_MODIFIED'},
        'batch_updates': True
    })
    
    # Registrar triggers
    manager.register_trigger(file_trigger)
    manager.register_trigger(schedule_trigger)
    manager.register_trigger(threshold_trigger)
    
    return manager

def monitor_triggers(manager: TriggerManager, duration_seconds: int = 300):
    """
    Monitorea la actividad de los triggers por un período.
    
    Args:
        manager: TriggerManager a monitorear
        duration_seconds: Duración del monitoreo en segundos
    """
    logger.info("Iniciando monitoreo de triggers...")
    
    # Iniciar el manager
    manager.start()
    
    try:
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        while datetime.now() < end_time:
            # Mostrar estadísticas cada 10 segundos
            stats = manager.get_stats()
            logger.info(f"Estado actual: {stats}")
            
            # Esperar antes de la siguiente actualización
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("Monitoreo interrumpido por el usuario")
    finally:
        manager.stop()
        logger.info("Monitoreo finalizado")

def main():
    """Punto de entrada principal de la demo"""
    try:
        # Directorio de música para la demo
        music_path = os.path.expanduser("~/Music")
        if not os.path.exists(music_path):
            music_path = "."  # Usar directorio actual si no existe ~/Music
            
        # Configurar triggers
        manager = setup_demo_triggers(music_path)
        
        # Mostrar configuración inicial
        logger.info(f"Monitoreando directorio: {music_path}")
        logger.info("Triggers configurados:")
        for playlist_id, triggers in manager._triggers.items():
            for trigger in triggers:
                logger.info(f"- {type(trigger).__name__}: {trigger.get_stats()}")
                
        # Monitorear por 5 minutos
        monitor_triggers(manager, 300)
        
    except Exception as e:
        logger.error(f"Error en la demo: {str(e)}", exc_info=True)
        return 1
        
    return 0

if __name__ == '__main__':
    exit(main())

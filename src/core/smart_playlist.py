from typing import List, Dict, Any, Optional, Set
import logging
from datetime import datetime
import os

from .parser import Parser
from .evaluator import Evaluator
from .triggers import (
    TriggerManager, MusicFileWatcher,
    FileTrigger, ScheduleTrigger, ThresholdTrigger,
    TriggerEvent, TriggerType
)

class SmartPlaylistError(Exception):
    """Excepción base para errores de playlist inteligente"""
    pass

class SmartPlaylist:
    """
    Playlist inteligente con actualización automática basada en reglas y triggers.
    """
    
    def __init__(self, playlist_id: str, name: str, rule_text: str):
        self.id = playlist_id
        self.name = name
        self.rule_text = rule_text
        self.creation_date = datetime.now()
        self.last_update = None
        self.tracks: List[Dict[str, Any]] = []
        
        # Componentes core
        self.parser = Parser()
        self.evaluator = Evaluator()
        self.trigger_manager = TriggerManager()
        self.file_watcher = None  # Se inicializa al configurar paths
        
        # Estado interno
        self.ast = None
        self.is_valid = False
        self.error_message = None
        self.active_triggers: Set[str] = set()
        self._music_paths: Set[str] = set()
        
        # Configurar logging
        self._logger = logging.getLogger(__name__)
        
        # Parsear regla inicial
        self._parse_rule()
        
    def _parse_rule(self):
        """Parsea la regla y actualiza el estado interno."""
        try:
            self.ast = self.parser.parse(self.rule_text)
            self.is_valid = True
            self.error_message = None
        except Exception as e:
            self.is_valid = False
            self.error_message = str(e)
            self._logger.error(f"Error parseando regla: {str(e)}")
            
    def set_rule(self, rule_text: str):
        """
        Actualiza la regla de la playlist.
        
        Args:
            rule_text: Nueva regla en formato texto
        """
        self.rule_text = rule_text
        self._parse_rule()
        
        # Regenerar playlist si la regla es válida
        if self.is_valid:
            self.refresh()
            
        # Notificar triggers de cambio de regla
        self._notify_rule_changed()
        
    def add_music_path(self, path: str):
        """
        Agrega un directorio de música para monitorear.
        
        Args:
            path: Ruta al directorio
        """
        if not os.path.exists(path):
            raise SmartPlaylistError(f"El directorio {path} no existe")
            
        self._music_paths.add(path)
        
        # Inicializar file watcher si es necesario
        if not self.file_watcher:
            self.file_watcher = MusicFileWatcher(self.trigger_manager)
            
        # Comenzar a monitorear el nuevo path
        self.file_watcher.start_watching(path)
        
        # Configurar trigger de archivos
        self._setup_file_trigger()
        
    def setup_triggers(self, config: Dict[str, Any]):
        """
        Configura los triggers para actualización automática.
        
        Args:
            config: Diccionario con configuración de triggers
        """
        # 1. File Trigger (si hay paths configurados)
        if self._music_paths and 'file_trigger' in config:
            self._setup_file_trigger(config['file_trigger'])
            
        # 2. Schedule Trigger
        if 'schedule_trigger' in config:
            self._setup_schedule_trigger(config['schedule_trigger'])
            
        # 3. Threshold Trigger
        if 'threshold_trigger' in config:
            self._setup_threshold_trigger(config['threshold_trigger'])
            
        # Iniciar el manager si hay triggers configurados
        if self.active_triggers:
            self.trigger_manager.start()
            
    def _setup_file_trigger(self, config: Optional[Dict[str, Any]] = None):
        """Configura el trigger de archivos."""
        if not self._music_paths:
            return
            
        trigger = FileTrigger(self.id, self.file_watcher)
        
        # Configuración por defecto
        trigger_config = {
            'watch_paths': self._music_paths,
            'file_patterns': {r'.*\.(mp3|flac|m4a|wav)$'},
            'ignore_patterns': {r'.*\.temp$', r'.*\.bak$'},
            'recursive': True,
            'debounce_seconds': 2.0
        }
        
        # Actualizar con config personalizada
        if config:
            trigger_config.update(config)
            
        trigger.configure(trigger_config)
        self.trigger_manager.register_trigger(trigger)
        self.active_triggers.add('file')
        
    def _setup_schedule_trigger(self, config: Dict[str, Any]):
        """Configura el trigger de horarios."""
        trigger = ScheduleTrigger(self.id)
        trigger.configure(config)
        self.trigger_manager.register_trigger(trigger)
        self.active_triggers.add('schedule')
        
    def _setup_threshold_trigger(self, config: Dict[str, Any]):
        """Configura el trigger de umbral."""
        trigger = ThresholdTrigger(self.id)
        trigger.configure(config)
        self.trigger_manager.register_trigger(trigger)
        self.active_triggers.add('threshold')
        
    def refresh(self):
        """
        Actualiza la lista de tracks basada en la regla actual.
        Retorna True si la actualización fue exitosa.
        """
        if not self.is_valid:
            return False
            
        try:
            # TODO: Implementar evaluación de regla contra biblioteca
            # Por ahora solo actualizamos timestamps
            self.last_update = datetime.now()
            return True
            
        except Exception as e:
            self._logger.error(f"Error actualizando playlist: {str(e)}")
            return False
            
    def _notify_rule_changed(self):
        """Notifica a los triggers que la regla cambió."""
        event = TriggerEvent(
            type=TriggerType.RULE_CHANGED,
            playlist_id=self.id,
            timestamp=datetime.now(),
            source="playlist",
            data={"rule": self.rule_text}
        )
        self.trigger_manager.process_event(event)
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas de la playlist.
        
        Returns:
            Dict con estadísticas
        """
        return {
            "id": self.id,
            "name": self.name,
            "is_valid": self.is_valid,
            "error_message": self.error_message,
            "track_count": len(self.tracks),
            "creation_date": self.creation_date,
            "last_update": self.last_update,
            "active_triggers": list(self.active_triggers),
            "music_paths": list(self._music_paths),
            "trigger_stats": self.trigger_manager.get_stats()
        }
        
    def __str__(self) -> str:
        status = "✓" if self.is_valid else "✗"
        return f"{self.name} [{status}] - {len(self.tracks)} tracks"

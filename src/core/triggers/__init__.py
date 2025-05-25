"""
Sistema de triggers para actualización automática de playlists inteligentes.
"""

from .base_trigger import (
    BaseTrigger, TriggerEvent, TriggerType,
    TriggerError, ConfigurationError, ExecutionError
)
from .trigger_manager import TriggerManager
from .file_watcher import MusicFileWatcher
from .trigger_types.file_trigger import FileTrigger
from .trigger_types.schedule_trigger import ScheduleTrigger, ScheduleError
from .trigger_types.threshold_trigger import ThresholdTrigger

__all__ = [
    # Base
    'BaseTrigger',
    'TriggerEvent',
    'TriggerType',
    'TriggerError',
    'ConfigurationError',
    'ExecutionError',
    
    # Core
    'TriggerManager',
    'MusicFileWatcher',
    
    # Trigger Types
    'FileTrigger',
    'ScheduleTrigger',
    'ScheduleError',
    'ThresholdTrigger'
]

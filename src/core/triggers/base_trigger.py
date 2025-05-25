from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

class TriggerType(Enum):
    """Tipos de triggers soportados por el sistema"""
    FILE_ADDED = "file_added"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    METADATA_UPDATED = "metadata_updated"
    RULE_CHANGED = "rule_changed"
    SCHEDULED = "scheduled"
    THRESHOLD = "threshold"
    
@dataclass
class TriggerEvent:
    """Evento generado cuando se dispara un trigger"""
    type: TriggerType
    playlist_id: str
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    
    def __str__(self) -> str:
        return f"TriggerEvent({self.type.value} for {self.playlist_id} at {self.timestamp})"

class BaseTrigger(ABC):
    """
    Clase base para todos los tipos de triggers.
    Define la interfaz común que deben implementar todos los triggers.
    """
    
    def __init__(self, playlist_id: str, enabled: bool = True):
        self.playlist_id = playlist_id
        self.enabled = enabled
        self.last_triggered = None
        self.trigger_count = 0
        self.error_count = 0
        self.last_error = None
        self._config = {}
        
    @abstractmethod
    def should_trigger(self, event: TriggerEvent) -> bool:
        """
        Determina si el trigger debe ejecutarse dado un evento.
        
        Args:
            event: El evento a evaluar
            
        Returns:
            bool: True si el trigger debe ejecutarse
        """
        pass
        
    @abstractmethod
    def execute(self, event: TriggerEvent) -> bool:
        """
        Ejecuta la acción del trigger.
        
        Args:
            event: El evento que disparó el trigger
            
        Returns:
            bool: True si la ejecución fue exitosa
        """
        pass
        
    def enable(self):
        """Habilita el trigger"""
        self.enabled = True
        
    def disable(self):
        """Deshabilita el trigger"""
        self.enabled = False
        
    def configure(self, config: Dict[str, Any]):
        """
        Configura el trigger con parámetros específicos.
        
        Args:
            config: Diccionario de configuración
        """
        self._config.update(config)
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.
        
        Args:
            key: Clave de configuración
            default: Valor por defecto si la clave no existe
            
        Returns:
            El valor de configuración o el default
        """
        return self._config.get(key, default)
        
    def record_execution(self, success: bool, error: Optional[Exception] = None):
        """
        Registra la ejecución del trigger.
        
        Args:
            success: Si la ejecución fue exitosa
            error: Excepción si hubo error
        """
        self.last_triggered = datetime.now()
        self.trigger_count += 1
        
        if not success:
            self.error_count += 1
            self.last_error = error
            
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del trigger.
        
        Returns:
            Dict con estadísticas de ejecución
        """
        return {
            "playlist_id": self.playlist_id,
            "enabled": self.enabled,
            "trigger_count": self.trigger_count,
            "error_count": self.error_count,
            "last_triggered": self.last_triggered,
            "last_error": str(self.last_error) if self.last_error else None,
            "config": self._config
        }

class TriggerError(Exception):
    """Excepción base para errores de triggers"""
    pass

class ConfigurationError(TriggerError):
    """Error en la configuración de un trigger"""
    pass

class ExecutionError(TriggerError):
    """Error durante la ejecución de un trigger"""
    pass

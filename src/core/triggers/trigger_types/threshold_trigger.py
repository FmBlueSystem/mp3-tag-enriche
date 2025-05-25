from typing import Dict, Any, List, Set
from datetime import datetime, timedelta

from ..base_trigger import BaseTrigger, TriggerEvent, TriggerType

class ThresholdTrigger(BaseTrigger):
    """
    Trigger que se activa cuando se acumula cierta cantidad de cambios
    o se alcanza un umbral específico en una playlist.
    """
    
    def __init__(self, playlist_id: str):
        super().__init__(playlist_id)
        
        # Configuración por defecto
        self._config.update({
            'min_changes': 10,           # Número mínimo de cambios para activar
            'max_wait_minutes': 30,      # Tiempo máximo de espera sin importar cambios
            'change_types': set(),       # Tipos de cambios a monitorear (vacío = todos)
            'batch_updates': True,       # Procesar cambios en batch
            'reset_after_trigger': True  # Resetear contadores después de trigger
        })
        
        # Estado interno
        self._changes: List[TriggerEvent] = []
        self._last_trigger = None
        self._first_change = None
        
    def configure(self, config: Dict[str, Any]):
        """
        Configura el trigger con parámetros específicos.
        
        Args:
            config: Diccionario de configuración
        """
        super().configure(config)
        
        # Convertir tipos de cambios a set si se proporcionan
        if 'change_types' in config:
            self._config['change_types'] = set(
                TriggerType(t) if isinstance(t, str) else t
                for t in config['change_types']
            )
            
    def should_trigger(self, event: TriggerEvent) -> bool:
        """
        Determina si se debe activar el trigger basado en los cambios acumulados.
        
        Args:
            event: El evento a evaluar
            
        Returns:
            bool: True si se debe activar el trigger
        """
        # Si el evento no es del tipo esperado
        if self._config['change_types'] and event.type not in self._config['change_types']:
            return False
            
        # Registrar primer cambio si es el primero
        if not self._first_change:
            self._first_change = datetime.now()
            
        # Agregar el cambio a la lista
        self._changes.append(event)
        
        # Verificar condiciones de activación
        return self._should_activate()
        
    def execute(self, event: TriggerEvent) -> bool:
        """
        Ejecuta el trigger procesando todos los cambios acumulados.
        
        Args:
            event: El evento que disparó el trigger
            
        Returns:
            bool: True si la ejecución fue exitosa
        """
        try:
            if not self._changes:
                return True
                
            # Procesar todos los cambios acumulados
            success = self._process_changes()
            
            if success and self._config['reset_after_trigger']:
                self._reset_state()
                
            self.record_execution(success)
            return success
            
        except Exception as e:
            self.record_execution(False, e)
            return False
            
    def _should_activate(self) -> bool:
        """
        Evalúa si se cumplen las condiciones para activar el trigger.
        
        Returns:
            bool: True si se deben procesar los cambios
        """
        now = datetime.now()
        
        # Si hay suficientes cambios acumulados
        if len(self._changes) >= self._config['min_changes']:
            return True
            
        # Si ha pasado el tiempo máximo de espera desde el primer cambio
        if self._first_change:
            max_wait = timedelta(minutes=self._config['max_wait_minutes'])
            if now - self._first_change >= max_wait:
                return True
                
        return False
        
    def _process_changes(self) -> bool:
        """
        Procesa los cambios acumulados.
        
        Returns:
            bool: True si el procesamiento fue exitoso
        """
        try:
            # Aquí implementarías la lógica específica para procesar
            # los cambios y actualizar la playlist
            
            # Por ejemplo:
            # - Agrupar cambios por tipo
            # - Identificar archivos afectados
            # - Regenerar la playlist con los cambios
            
            changes_by_type = self._group_changes_by_type()
            
            # TODO: Implementar lógica específica de actualización
            # Por ahora solo registramos la ejecución
            
            self._last_trigger = datetime.now()
            return True
            
        except Exception as e:
            self.record_execution(False, e)
            return False
            
    def _group_changes_by_type(self) -> Dict[TriggerType, List[TriggerEvent]]:
        """
        Agrupa los cambios acumulados por tipo.
        
        Returns:
            Dict con eventos agrupados por tipo de trigger
        """
        groups: Dict[TriggerType, List[TriggerEvent]] = {}
        
        for event in self._changes:
            if event.type not in groups:
                groups[event.type] = []
            groups[event.type].append(event)
            
        return groups
        
    def _reset_state(self):
        """Resetea el estado interno del trigger"""
        self._changes.clear()
        self._first_change = None
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del trigger.
        
        Returns:
            Dict con estadísticas
        """
        stats = super().get_stats()
        
        changes_by_type = self._group_changes_by_type()
        
        stats.update({
            'pending_changes': len(self._changes),
            'changes_by_type': {
                trigger_type.value: len(events)
                for trigger_type, events in changes_by_type.items()
            },
            'first_change': self._first_change,
            'last_trigger': self._last_trigger,
            'monitored_types': [t.value for t in self._config['change_types']]
        })
        
        return stats
        
    def get_pending_changes(self) -> List[TriggerEvent]:
        """
        Retorna los cambios pendientes de procesar.
        
        Returns:
            Lista de eventos pendientes
        """
        return self._changes.copy()

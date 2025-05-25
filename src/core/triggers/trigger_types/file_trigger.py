from typing import Set, Dict, Any, Optional
import os
import re
from datetime import datetime

from ..base_trigger import BaseTrigger, TriggerEvent, TriggerType
from ..file_watcher import MusicFileWatcher

class FileTrigger(BaseTrigger):
    """
    Trigger que se activa en respuesta a cambios en archivos de música.
    Monitorea archivos específicos o patrones que afectan a una playlist.
    """
    
    def __init__(self, playlist_id: str, file_watcher: MusicFileWatcher):
        super().__init__(playlist_id)
        self.file_watcher = file_watcher
        
        # Configuración por defecto
        self._config.update({
            'watch_paths': set(),          # Directorios a monitorear
            'file_patterns': set(),        # Patrones de nombre de archivo
            'ignore_patterns': set(),      # Patrones a ignorar
            'recursive': True,             # Monitorear subdirectorios
            'debounce_seconds': 2.0,       # Tiempo de debounce
            'batch_updates': True,         # Agrupar múltiples cambios
            'max_batch_size': 100,         # Máximo de cambios por batch
            'monitor_metadata': True       # Monitorear cambios en metadatos
        })
        
        # Estado interno
        self._pending_changes = []
        self._last_batch_time = None
        
    def configure(self, config: Dict[str, Any]):
        """
        Configura el trigger con parámetros específicos.
        
        Args:
            config: Diccionario de configuración
        """
        super().configure(config)
        
        # Iniciar monitoreo de nuevas rutas
        for path in self._config['watch_paths']:
            try:
                self.file_watcher.start_watching(path)
            except Exception as e:
                self.record_execution(False, e)
                
    def should_trigger(self, event: TriggerEvent) -> bool:
        """
        Determina si un evento debe disparar el trigger.
        
        Args:
            event: El evento a evaluar
            
        Returns:
            bool: True si el trigger debe ejecutarse
        """
        # Solo procesar eventos de archivo
        if event.type not in [
            TriggerType.FILE_ADDED,
            TriggerType.FILE_MODIFIED,
            TriggerType.FILE_DELETED
        ]:
            return False
            
        file_path = event.data.get('file_path', '')
        
        # Verificar si el archivo está en una ruta monitoreada
        if not self._is_in_watched_paths(file_path):
            return False
            
        # Verificar patrones de archivo
        filename = os.path.basename(file_path)
        if not self._matches_patterns(filename):
            return False
            
        # Verificar patrones de ignorar
        if self._matches_ignore_patterns(filename):
            return False
            
        # Si llegamos aquí, el evento es relevante
        return True
        
    def execute(self, event: TriggerEvent) -> bool:
        """
        Ejecuta la acción del trigger.
        
        Args:
            event: El evento que disparó el trigger
            
        Returns:
            bool: True si la ejecución fue exitosa
        """
        try:
            # Agregar cambio al batch
            self._pending_changes.append(event)
            
            # Verificar si debemos procesar el batch
            now = datetime.now().timestamp()
            should_process = (
                len(self._pending_changes) >= self._config['max_batch_size'] or
                (self._last_batch_time and 
                 now - self._last_batch_time >= self._config['debounce_seconds'])
            )
            
            if should_process:
                return self._process_batch()
                
            # Si no procesamos ahora, programar para más tarde
            self._last_batch_time = now
            return True
            
        except Exception as e:
            self.record_execution(False, e)
            return False
            
    def _process_batch(self) -> bool:
        """
        Procesa un batch de cambios acumulados.
        
        Returns:
            bool: True si el procesamiento fue exitoso
        """
        if not self._pending_changes:
            return True
            
        try:
            # Aquí implementarías la lógica específica de actualización
            # de la playlist basada en los cambios acumulados
            
            # Por ahora solo logueamos los cambios
            changes = len(self._pending_changes)
            self._pending_changes.clear()
            self._last_batch_time = None
            
            return True
            
        except Exception as e:
            self.record_execution(False, e)
            return False
            
    def _is_in_watched_paths(self, file_path: str) -> bool:
        """
        Verifica si un archivo está en alguna de las rutas monitoreadas.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            bool: True si el archivo está en una ruta monitoreada
        """
        file_path = os.path.abspath(file_path)
        return any(
            file_path.startswith(os.path.abspath(path))
            for path in self._config['watch_paths']
        )
        
    def _matches_patterns(self, filename: str) -> bool:
        """
        Verifica si un nombre de archivo coincide con los patrones configurados.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            bool: True si el archivo coincide con algún patrón
        """
        if not self._config['file_patterns']:
            return True  # Sin patrones = aceptar todo
            
        return any(
            re.match(pattern, filename, re.IGNORECASE)
            for pattern in self._config['file_patterns']
        )
        
    def _matches_ignore_patterns(self, filename: str) -> bool:
        """
        Verifica si un nombre de archivo coincide con patrones de ignorar.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            bool: True si el archivo debe ser ignorado
        """
        return any(
            re.match(pattern, filename, re.IGNORECASE)
            for pattern in self._config['ignore_patterns']
        )
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del trigger.
        
        Returns:
            Dict con estadísticas
        """
        stats = super().get_stats()
        stats.update({
            'pending_changes': len(self._pending_changes),
            'watched_paths': list(self._config['watch_paths']),
            'file_patterns': list(self._config['file_patterns']),
            'ignore_patterns': list(self._config['ignore_patterns'])
        })
        return stats

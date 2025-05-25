from typing import Dict, List, Optional, Set
from datetime import datetime
import logging
import queue
import threading
import time

from .base_trigger import (
    BaseTrigger, TriggerEvent, TriggerType, 
    TriggerError, ExecutionError
)

class TriggerManager:
    """
    Gestor central de triggers del sistema.
    Maneja el registro, ejecución y monitoreo de todos los triggers.
    """
    
    def __init__(self):
        self._triggers: Dict[str, List[BaseTrigger]] = {}
        self._event_queue = queue.Queue()
        self._worker_thread = None
        self._running = False
        self._lock = threading.Lock()
        self._active_playlists: Set[str] = set()
        
        # Configurar logging
        self._logger = logging.getLogger(__name__)
        
    def start(self):
        """Inicia el procesamiento de eventos en background"""
        with self._lock:
            if not self._running:
                self._running = True
                self._worker_thread = threading.Thread(
                    target=self._event_processor_loop,
                    daemon=True
                )
                self._worker_thread.start()
                self._logger.info("TriggerManager iniciado")
                
    def stop(self):
        """Detiene el procesamiento de eventos"""
        with self._lock:
            if self._running:
                self._running = False
                if self._worker_thread:
                    self._worker_thread.join(timeout=5.0)
                    self._worker_thread = None
                self._logger.info("TriggerManager detenido")
                
    def register_trigger(self, trigger: BaseTrigger) -> bool:
        """
        Registra un nuevo trigger para una playlist.
        
        Args:
            trigger: El trigger a registrar
            
        Returns:
            bool: True si se registró exitosamente
        """
        playlist_id = trigger.playlist_id
        
        with self._lock:
            if playlist_id not in self._triggers:
                self._triggers[playlist_id] = []
            
            # Evitar duplicados
            for existing in self._triggers[playlist_id]:
                if type(existing) == type(trigger):
                    self._logger.warning(
                        f"Trigger tipo {type(trigger).__name__} ya existe "
                        f"para playlist {playlist_id}"
                    )
                    return False
                    
            self._triggers[playlist_id].append(trigger)
            self._active_playlists.add(playlist_id)
            
            self._logger.info(
                f"Trigger {type(trigger).__name__} registrado "
                f"para playlist {playlist_id}"
            )
            return True
            
    def unregister_trigger(self, playlist_id: str, trigger_type: type) -> bool:
        """
        Elimina un trigger específico de una playlist.
        
        Args:
            playlist_id: ID de la playlist
            trigger_type: Tipo de trigger a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        with self._lock:
            if playlist_id not in self._triggers:
                return False
                
            triggers = self._triggers[playlist_id]
            for i, trigger in enumerate(triggers):
                if type(trigger) == trigger_type:
                    triggers.pop(i)
                    if not triggers:
                        del self._triggers[playlist_id]
                        self._active_playlists.remove(playlist_id)
                    self._logger.info(
                        f"Trigger {trigger_type.__name__} eliminado "
                        f"de playlist {playlist_id}"
                    )
                    return True
                    
            return False
            
    def process_event(self, event: TriggerEvent):
        """
        Procesa un evento, encolándolo para evaluación.
        
        Args:
            event: El evento a procesar
        """
        self._event_queue.put(event)
        self._logger.debug(f"Evento encolado: {event}")
        
    def _event_processor_loop(self):
        """Loop principal de procesamiento de eventos"""
        while self._running:
            try:
                # Esperar por eventos con timeout para poder
                # chequear _running periódicamente
                try:
                    event = self._event_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                    
                self._handle_event(event)
                self._event_queue.task_done()
                
            except Exception as e:
                self._logger.error(
                    f"Error en event_processor_loop: {str(e)}",
                    exc_info=True
                )
                time.sleep(1.0)  # Evitar loop infinito en caso de error
                
    def _handle_event(self, event: TriggerEvent):
        """
        Maneja un evento, evaluándolo contra todos los triggers relevantes.
        
        Args:
            event: El evento a manejar
        """
        playlist_id = event.playlist_id
        
        # Si el evento es específico para una playlist
        if playlist_id and playlist_id in self._triggers:
            self._evaluate_playlist_triggers(playlist_id, event)
            return
            
        # Si es un evento global, evaluar contra todas las playlists activas
        for playlist_id in self._active_playlists:
            self._evaluate_playlist_triggers(playlist_id, event)
            
    def _evaluate_playlist_triggers(self, playlist_id: str, event: TriggerEvent):
        """
        Evalúa un evento contra todos los triggers de una playlist.
        
        Args:
            playlist_id: ID de la playlist
            event: Evento a evaluar
        """
        triggers = self._triggers.get(playlist_id, [])
        
        for trigger in triggers:
            if not trigger.enabled:
                continue
                
            try:
                if trigger.should_trigger(event):
                    success = trigger.execute(event)
                    trigger.record_execution(success)
                    
                    if success:
                        self._logger.info(
                            f"Trigger {type(trigger).__name__} ejecutado "
                            f"exitosamente para playlist {playlist_id}"
                        )
                    else:
                        self._logger.warning(
                            f"Trigger {type(trigger).__name__} falló "
                            f"para playlist {playlist_id}"
                        )
                        
            except Exception as e:
                self._logger.error(
                    f"Error evaluando trigger {type(trigger).__name__} "
                    f"para playlist {playlist_id}: {str(e)}",
                    exc_info=True
                )
                trigger.record_execution(False, e)
                
    def get_triggers(self, playlist_id: str) -> List[BaseTrigger]:
        """
        Retorna todos los triggers registrados para una playlist.
        
        Args:
            playlist_id: ID de la playlist
            
        Returns:
            Lista de triggers
        """
        return self._triggers.get(playlist_id, []).copy()
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del manager.
        
        Returns:
            Dict con estadísticas
        """
        stats = {
            "active_playlists": len(self._active_playlists),
            "total_triggers": sum(len(t) for t in self._triggers.values()),
            "queue_size": self._event_queue.qsize(),
            "is_running": self._running,
            "playlists": {}
        }
        
        for playlist_id, triggers in self._triggers.items():
            stats["playlists"][playlist_id] = {
                "trigger_count": len(triggers),
                "triggers": [
                    {
                        "type": type(t).__name__,
                        **t.get_stats()
                    }
                    for t in triggers
                ]
            }
            
        return stats
        
    def clear_all(self):
        """Elimina todos los triggers registrados"""
        with self._lock:
            self._triggers.clear()
            self._active_playlists.clear()
            self._logger.info("Todos los triggers eliminados")

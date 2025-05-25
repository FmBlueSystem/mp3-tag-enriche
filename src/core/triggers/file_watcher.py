from typing import Set, Dict, Any, Optional
import os
import time
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler, FileSystemEvent,
    FileCreatedEvent, FileModifiedEvent, FileDeletedEvent
)

from .base_trigger import TriggerType, TriggerEvent
from .trigger_manager import TriggerManager

class MusicFileWatcher(FileSystemEventHandler):
    """
    Monitorea cambios en los archivos de música y genera eventos
    para el TriggerManager.
    """
    
    def __init__(self, trigger_manager: TriggerManager):
        super().__init__()
        self.trigger_manager = trigger_manager
        self.observers: Dict[str, Observer] = {}
        self.watched_paths: Set[str] = set()
        self.supported_extensions = {'.mp3', '.flac', '.m4a', '.wav'}
        
        # Cache para manejo de duplicados
        self._event_cache = {}
        self._cache_timeout = 2.0  # segundos
        
    def start_watching(self, path: str):
        """
        Comienza a monitorear un directorio.
        
        Args:
            path: Ruta al directorio a monitorear
        """
        if not os.path.exists(path):
            raise ValueError(f"La ruta {path} no existe")
            
        if path in self.observers:
            return  # Ya está siendo monitoreado
            
        observer = Observer()
        observer.schedule(self, path, recursive=True)
        observer.start()
        
        self.observers[path] = observer
        self.watched_paths.add(path)
        
    def stop_watching(self, path: str):
        """
        Detiene el monitoreo de un directorio.
        
        Args:
            path: Ruta del directorio a dejar de monitorear
        """
        observer = self.observers.get(path)
        if observer:
            observer.stop()
            observer.join()
            del self.observers[path]
            self.watched_paths.remove(path)
            
    def stop_all(self):
        """Detiene todo el monitoreo"""
        for observer in self.observers.values():
            observer.stop()
            observer.join()
        self.observers.clear()
        self.watched_paths.clear()
        
    def on_created(self, event: FileCreatedEvent):
        """Maneja la creación de nuevos archivos"""
        if not event.is_directory and self._is_music_file(event.src_path):
            self._handle_file_event(
                event,
                TriggerType.FILE_ADDED,
                f"Nuevo archivo: {os.path.basename(event.src_path)}"
            )
            
    def on_modified(self, event: FileModifiedEvent):
        """Maneja modificaciones de archivos"""
        if not event.is_directory and self._is_music_file(event.src_path):
            self._handle_file_event(
                event,
                TriggerType.FILE_MODIFIED,
                f"Archivo modificado: {os.path.basename(event.src_path)}"
            )
            
    def on_deleted(self, event: FileDeletedEvent):
        """Maneja eliminación de archivos"""
        if not event.is_directory and self._is_music_file(event.src_path):
            self._handle_file_event(
                event,
                TriggerType.FILE_DELETED,
                f"Archivo eliminado: {os.path.basename(event.src_path)}"
            )
            
    def _is_music_file(self, path: str) -> bool:
        """
        Determina si un archivo es un archivo de música soportado.
        
        Args:
            path: Ruta al archivo
            
        Returns:
            bool: True si es un archivo de música soportado
        """
        return os.path.splitext(path)[1].lower() in self.supported_extensions
        
    def _handle_file_event(
        self,
        event: FileSystemEvent,
        trigger_type: TriggerType,
        description: str
    ):
        """
        Procesa un evento de archivo y genera el evento de trigger correspondiente.
        
        Args:
            event: Evento del sistema de archivos
            trigger_type: Tipo de trigger a generar
            description: Descripción del evento
        """
        # Chequear cache para evitar eventos duplicados
        cache_key = f"{event.src_path}:{trigger_type.value}"
        now = time.time()
        
        if cache_key in self._event_cache:
            last_time = self._event_cache[cache_key]
            if now - last_time < self._cache_timeout:
                return  # Ignorar evento duplicado
                
        self._event_cache[cache_key] = now
        
        # Limpiar cache viejo
        self._clean_event_cache(now)
        
        # Crear y enviar evento de trigger
        trigger_event = TriggerEvent(
            type=trigger_type,
            playlist_id="",  # Vacío porque es un evento global
            timestamp=now,
            source="file_watcher",
            data={
                "file_path": event.src_path,
                "description": description,
                "event_type": event.event_type
            }
        )
        
        self.trigger_manager.process_event(trigger_event)
        
    def _clean_event_cache(self, current_time: float):
        """
        Limpia entradas viejas del cache de eventos.
        
        Args:
            current_time: Tiempo actual en segundos desde epoch
        """
        expired_keys = [
            key for key, timestamp in self._event_cache.items()
            if current_time - timestamp > self._cache_timeout
        ]
        
        for key in expired_keys:
            del self._event_cache[key]
            
    def get_watched_files(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna información sobre los archivos siendo monitoreados.
        
        Returns:
            Dict con información de archivos por directorio
        """
        result = {}
        
        for path in self.watched_paths:
            files = []
            try:
                for root, _, filenames in os.walk(path):
                    for filename in filenames:
                        if self._is_music_file(filename):
                            file_path = os.path.join(root, filename)
                            files.append({
                                "name": filename,
                                "path": file_path,
                                "size": os.path.getsize(file_path),
                                "modified": os.path.getmtime(file_path)
                            })
            except Exception as e:
                files.append({"error": f"Error scanning {path}: {str(e)}"})
                
            result[path] = {
                "file_count": len(files),
                "files": files
            }
            
        return result

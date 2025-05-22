"""Processing thread module for background tasks."""
import os
import uuid
from pathlib import Path
import logging
from PySide6.QtCore import QThread, Signal
from typing import Optional, List, Dict, Any

from ...core.file_handler import Mp3FileHandler
from ..models.genre_model import GenreModel
from .task_queue import TaskQueue, TaskState, Task

logger = logging.getLogger(__name__)

class ProcessingThread(QThread):
    """Hilo para procesamiento asíncrono de archivos con cola de tareas."""
    progress = Signal(str)
    finished = Signal(dict)
    file_processed = Signal(str, str, bool)  # filepath, message, is_error
    task_state_changed = Signal(str, TaskState)  # task_id, new_state
    circuit_breaker_opened = Signal()
    circuit_breaker_closed = Signal()

    def __init__(self, file_paths: List[str] = None, model: GenreModel = None, analyze_only: bool = True,
                 confidence: float = 0.3, max_genres: int = 3,
                 rename_files: bool = False, backup_dir: Optional[str] = None,
                 task_queue: Optional[TaskQueue] = None, parent=None):
        super().__init__(parent)
        from threading import Lock
        self._thread_lock = Lock()
        self.file_paths = file_paths if file_paths is not None else []
        self.analyze_only = analyze_only
        self.confidence = confidence
        self.max_genres = max_genres
        self.rename_files = rename_files
        self.backup_dir = backup_dir
        self.model = model
        # Inicializar TaskQueue si no se proporciona una
        self.task_queue = task_queue if task_queue is not None else TaskQueue()
        self.is_running = True
        # Asegurar que el file_handler del modelo use el backup_dir proporcionado al thread.
        if self.model and hasattr(self.model, 'detector') and self.model.detector and \
           hasattr(self.model.detector, 'file_handler') and self.model.detector.file_handler:
            if hasattr(self.model.detector.file_handler, 'set_backup_dir'):
                current_fh_backup_dir = getattr(self.model.detector.file_handler, 'backup_dir', None)
                new_thread_backup_path_obj = Path(self.backup_dir) if self.backup_dir else None
                if current_fh_backup_dir != new_thread_backup_path_obj:
                    self.model.detector.file_handler.set_backup_dir(self.backup_dir)
                else:
                    logger.debug(f"ProcessingThread: backup_dir ({self.backup_dir}) ya está configurado en file_handler.")
            else:
                logger.error("ProcessingThread: Mp3FileHandler en el modelo no tiene método 'set_backup_dir'. "
                             "El respaldo podría no funcionar como se espera.")
        else:
            logger.error("ProcessingThread: No se pudo acceder a model.detector.file_handler. "
                         "El respaldo podría no funcionar como se espera.")
        self.is_running = True

    def stop(self):
        """Detiene el procesamiento de manera segura."""
        self.is_running = False
        
    def process_file(self, filepath: str) -> Dict[str, Any]:
        """Procesa un archivo individual."""
        try:
            if self.analyze_only:
                result = self.model.analyze(filepath, chunk_size=8192)
            else:
                result = self.model.process(
                    filepath,
                    self.confidence,
                    self.max_genres,
                    self.rename_files,
                    chunk_size=8192
                )
            return result
        except Exception as e:
            logger.error(f"Error procesando {filepath}: {str(e)}")
            return {"error": str(e)}

    def run(self):
        """Ejecuta el procesamiento de archivos en segundo plano usando la cola de tareas."""
        if not hasattr(self, '_thread_lock'):
            from threading import Lock
            self._thread_lock = Lock()
            
        if not self.file_paths:
            self.progress.emit("No hay archivos seleccionados para procesar.")
            self.finished.emit({
                "total": 0,
                "success": 0,
                "errors": 0,
                "renamed": 0,
                "details": []
            })
            return

        # Inicializar contadores
        processed_count = 0
        success_count = 0
        error_count = 0
        renamed_count = 0
        results_details = []

        # Crear tareas para cada archivo
        tasks = {}
        for filepath in self.file_paths:
            task_id = str(uuid.uuid4())
            with self._thread_lock:
                task = self.task_queue.add_task(
                    task_id,
                    self.process_file,
                    filepath
                )
                tasks[task_id] = (task, filepath)

        # Procesar tareas
        retry_count = 0
        max_retries = 3
        
        while self.is_running and processed_count < len(self.file_paths):
            task = self.task_queue.get_next_task()
            if not task:
                if self.task_queue.circuit_breaker.is_open:
                    if retry_count < max_retries:
                        self.circuit_breaker_opened.emit()
                        self.msleep(min(5000 * (retry_count + 1), 30000))  # Backoff exponencial
                        retry_count += 1
                        continue
                    else:
                        logger.error("Máximo número de reintentos alcanzado")
                        break
                else:
                    # Si no hay más tareas pero no hemos procesado todo, esperar brevemente
                    if processed_count < len(self.file_paths):
                        self.msleep(100)
                        continue
                    break

            try:
                filepath = next(fp for _, (t, fp) in tasks.items() if t == task)
            except StopIteration:
                logger.error("No se encontró el filepath asociado a la tarea")
                continue
            self.progress.emit(f"Procesando {Path(filepath).name}")
            try:
                with self._thread_lock:
                    self.task_state_changed.emit(task.id, TaskState.RUNNING)
                    result = task.func(task.args[0])
                    
                    actual_error = result.get("error")
                    if actual_error:
                        self.task_queue.complete_task(task, error=actual_error)
                        self.task_state_changed.emit(task.id, TaskState.FAILED)
                        error_count += 1
                        logger.error(f"Error al procesar {filepath}: {actual_error}")
                        self.file_processed.emit(filepath, f"Error: {actual_error}", True)
                    else:
                        self.task_queue.complete_task(task, result=result)
                        self.task_state_changed.emit(task.id, TaskState.COMPLETED)
                
                if "written" in result:
                    if result["written"]:
                        success_count += 1
                        if not ("renamed" in result and result["renamed"]):
                            message = str(result.get("message", "Éxito en escritura de metadatos."))
                            self.file_processed.emit(filepath, message, False)
                    else:
                        error_count += 1
                        err_msg = result.get('error', 'Error desconocido durante escritura de metadatos')
                        self.file_processed.emit(filepath, f"Error al escribir metadatos: {err_msg}", True)
                elif not self.analyze_only:
                    error_count += 1
                    self.file_processed.emit(filepath, "Error: Resultado inesperado del procesamiento", True)
                else:
                    success_count += 1
                    
                    # Buscar géneros tanto en detected_genres como en found_genres
                    genres = result.get("detected_genres", {}) or result.get("found_genres", {})
                    
                    if genres:
                        genre_str = ", ".join(
                            f"{g} ({c:.2f})" if isinstance(c, float) else f"{g}"
                            for g, c in sorted(genres.items(), key=lambda x: x[1], reverse=True)
                        )
                        self.file_processed.emit(filepath, f"Éxito en análisis. Géneros detectados: {genre_str}", False)
                    else:
                        logger.warning(f"No se encontraron géneros en el resultado para {filepath}")
                        self.file_processed.emit(filepath, "No se detectaron géneros", False)
                        
                    logger.debug(f"Resultado del análisis para {filepath}: {result}")

                # La señal circuit_breaker_closed se emite en el manejador de éxito
                if not self.task_queue.circuit_breaker.is_open:
                    self.circuit_breaker_closed.emit()
                    logger.debug("Circuit breaker cerrado después de procesamiento exitoso")
                
                processed_count += 1
                total_files = len(self.file_paths)
                self.progress.emit(f"Procesado: {processed_count}/{total_files} - {os.path.basename(filepath)}")

                if "renamed" in result:                    
                    if result["renamed"]:
                        renamed_count += 1
                        new_filepath_val = result.get('new_filepath')
                        if result.get("message"):
                             msg = str(result.get("message", ""))
                             logger.debug(f"Emitiendo mensaje de renombrado para {filepath}: {msg}")
                             self.file_processed.emit(filepath, msg, False)
                        elif new_filepath_val:
                             msg = f"Renombrado a: {os.path.basename(new_filepath_val)}"
                             logger.debug(f"Emitiendo mensaje de renombrado para {filepath}: {msg}")
                             self.file_processed.emit(filepath, msg, False)

                    elif result.get("success") and result.get("new_path") == filepath:
                        if result.get("message"):
                            msg = str(result.get("message", ""))
                            logger.debug(f"Emitiendo mensaje sin cambios para {filepath}: {msg}")
                            self.file_processed.emit(filepath, msg, False)
                        else:
                            msg = "Tags actualizados (nombre sin cambios)."
                            logger.debug(f"Emitiendo mensaje de actualización para {filepath}: {msg}")
                            self.file_processed.emit(filepath, msg, False)
                    else:
                        rename_specific_error = result.get("error")
                        if rename_specific_error and not actual_error:
                            error_msg = f"Fallo al renombrar/actualizar tags: {rename_specific_error}"
                            logger.debug(f"Emitiendo error de renombrado para {filepath}: {error_msg}")
                            self.file_processed.emit(filepath, error_msg, True)
                        elif not actual_error and not result.get("success"):
                             error_msg = f"Fallo al renombrar/actualizar tags: {result.get('message', 'Razón desconocida')}"
                             logger.debug(f"Emitiendo error de actualización para {filepath}: {error_msg}")
                             self.file_processed.emit(filepath, error_msg, True)

                results_details.append({
                    "filepath": filepath,
                    "written_metadata_success": result.get("written", False),
                    "current_genre": result.get("current_genre", ""),
                    "selected_genres_written": result.get("selected_genres_written", []),
                    "threshold_used": result.get("threshold_used", 0.3),
                    "renamed_to": result.get("new_filepath", ""),
                    "error": result.get("error", ""),
                    "rename_error": result.get("error", ""),
                    "rename_message": result.get("message", ""),
                    "detected_genres_initial_clean": result.get("detected_genres_initial_clean", {}),
                    "detected_genres_written": result.get("selected_genres_written", []),
                    "tag_update_error": result.get("tag_update_error", "")
                })
            except Exception as e:
                with self._thread_lock:
                    error_count += 1
                    error_msg = f"Error: {str(e)}"
                    logger.error(f"Error al procesar {filepath}: {str(e)}")
                    self.task_queue.complete_task(task, error=error_msg)
                    self.task_state_changed.emit(task.id, TaskState.FAILED)
                    self.file_processed.emit(filepath, error_msg, True)

        try:
            # Limpiar tareas completadas
            with self._thread_lock:
                self.task_queue._active_tasks = [
                    t for t in self.task_queue._active_tasks
                    if t.state not in (TaskState.COMPLETED, TaskState.FAILED)
                ]
                
            self.finished.emit({
                "total": total_files,
                "success": success_count,
                "errors": error_count,
                "renamed": renamed_count,
                "details": results_details
            })
        except Exception as e:
            logger.error(f"Error finalizando el procesamiento: {str(e)}")

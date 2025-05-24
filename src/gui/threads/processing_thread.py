"""Processing thread module for background tasks."""
import os
import uuid
from pathlib import Path
import logging
from PySide6.QtCore import QThread, Signal
from typing import Optional, List, Dict, Any

from ...core.file_handler import Mp3FileHandler
from ...core.rules.rule_engine import RuleEngine
from ...core.rules.utils import PlaylistGenerator, M3UExporter
from ...core.rules.triggers import TriggerSystem
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

    def __init__(self, file_paths: List[str] = None, model: GenreModel = None,
                 confidence: float = 0.3, max_genres: int = 3,
                 rename_files: bool = False, backup_dir: Optional[str] = None,
                 db_manager=None, rule_engine=None, folder_organizer=None,
                 organize_files: bool = False, task_queue: Optional[TaskQueue] = None, parent=None):
        super().__init__(parent)
        from threading import Lock
        self._thread_lock = Lock()
        self.file_paths = file_paths if file_paths is not None else []
        self.confidence = confidence
        self.max_genres = max_genres
        self.rename_files = rename_files
        self.backup_dir = backup_dir
        self.model = model
        self.db_manager = db_manager
        self.rule_engine = rule_engine
        self.folder_organizer = folder_organizer
        self.organize_files = organize_files
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
        logger.debug(f"Iniciando process_file para {filepath}") # Added logging
        try:
            logger.debug(f"Modo procesamiento para {filepath}") # Added logging
            result = self.model.process(
                filepath,
                self.confidence,
                self.max_genres,
                self.rename_files,
                chunk_size=8192
            )
            
            # Si se completó exitosamente y se solicitó organización, organizar el archivo
            if (not result.get("error") and self.organize_files and 
                self.folder_organizer and self.db_manager):
                try:
                    # Buscar el track en la DB usando la ruta del archivo
                    tracks_data = self.db_manager.fetch_query("SELECT * FROM tracks WHERE filepath = ?", (filepath,))
                    if tracks_data:
                        from ...core.database.models import Track
                        track_obj = Track.from_row(tracks_data[0])
                        
                        # Solo organizar si tiene metadatos completos
                        if track_obj.genre and track_obj.year:
                            org_result = self.folder_organizer.organize_track_file(track_obj, dry_run=False)
                            if org_result.get("success"):
                                # Actualizar el resultado para indicar que se organizó
                                result["organized"] = True
                                result["new_organized_path"] = org_result.get("new_path")
                                logger.info(f"Archivo organizado: {filepath} -> {org_result.get('new_path')}")
                                
                                # Aplicar reglas al track procesado
                                if self.rule_engine:
                                    track_data = track_obj.__dict__
                                    # Incluir datos adicionales relevantes para reglas
                                    track_data.update({
                                        "processing_result": result,
                                        "new_filepath": org_result.get("new_path")
                                    })
                                    
                                    # Configurar contexto para acciones
                                    context = {
                                        "db_manager": self.db_manager,
                                        "file_handler": self.model.file_handler if hasattr(self.model, "file_handler") else None
                                    }
                                    
                                    # Aplicar reglas
                                    rule_results = self.rule_engine.apply_rules(track_data, context)
                                    result["rule_results"] = rule_results
                                    
                                    if rule_results.get("applied_rules"):
                                        logger.info(f"Reglas aplicadas a {filepath}: {', '.join(rule_results.get('applied_rules', []))}")
                            else:
                                logger.warning(f"Falló la organización de {filepath}: {org_result.get('error')}")
                                result["organize_error"] = org_result.get("error")
                        else:
                            logger.info(f"Saltando organización de {filepath} - metadatos incompletos")
                    else:
                        logger.warning(f"Track no encontrado en DB para organización: {filepath}")
                except Exception as org_e:
                    logger.error(f"Error durante organización de {filepath}: {org_e}", exc_info=True)
                    result["organize_error"] = str(org_e)
            
            logger.debug(f"process_file completado para {filepath}. Resultado: {result}") # Added logging
            return result
        except Exception as e:
            logger.error(f"Excepción en process_file para {filepath}: {str(e)}", exc_info=True) # Added logging with exc_info
            return {"error": str(e)}

    def run(self):
        """Ejecuta el procesamiento de archivos en segundo plano usando la cola de tareas."""
        logger.info("ProcessingThread.run iniciado.") # Added logging
        if not hasattr(self, '_thread_lock'):
            from threading import Lock
            self._thread_lock = Lock()
        
        total_files = len(self.file_paths)  # <-- Inicialización temprana
        
        if not self.file_paths:
            logger.info("No hay archivos seleccionados para procesar. Finalizando run.") # Added logging
            self.progress.emit("No hay archivos seleccionados para procesar.")
            self.finished.emit({
                "total": 0,
                "success": 0,
                "errors": 0,
                "renamed": 0,
                "details": []
            })
            return

        logger.info(f"Total de archivos a procesar: {len(self.file_paths)}") # Added logging

        # Inicializar contadores
        processed_count = 0
        success_count = 0
        error_count = 0
        renamed_count = 0
        results_details = []

        # Crear tareas para cada archivo
        logger.info("Creando tareas para cada archivo.") # Added logging
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
        logger.info(f"Tareas creadas: {len(tasks)}") # Added logging

        # Procesar tareas
        retry_count = 0
        max_retries = 3
        
        logger.info("Iniciando procesamiento de tareas.") # Added logging
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
                logger.debug(f"Obtenido filepath {filepath} para tarea {task.id}") # Added logging
            except StopIteration:
                logger.error("No se encontró el filepath asociado a la tarea")
                continue
            logger.info(f"Emitiendo progress signal para {Path(filepath).name}") # Added logging
            self.progress.emit(f"Procesando {Path(filepath).name}")
            try:
                logger.debug(f"Iniciando ejecución de tarea {task.id} para {filepath}") # Added logging
                with self._thread_lock:
                    logger.debug(f"Emitiendo task_state_changed RUNNING para tarea {task.id}") # Added logging
                    self.task_state_changed.emit(task.id, TaskState.RUNNING)
                    result = task.func(task.args[0])
                    logger.debug(f"Tarea {task.id} ejecutada. Resultado: {result}") # Added logging
                    
                    actual_error = result.get("error")
                    if actual_error:
                        logger.error(f"Tarea {task.id} fallida con error: {actual_error}") # Added logging
                        self.task_queue.complete_task(task, error=actual_error)
                        logger.debug(f"Emitiendo task_state_changed FAILED para tarea {task.id}") # Added logging
                        self.task_state_changed.emit(task.id, TaskState.FAILED)
                        error_count += 1
                        logger.error(f"Error al procesar {filepath}: {actual_error}")
                        logger.info(f"Emitiendo file_processed error para {filepath}") # Added logging
                        self.file_processed.emit(filepath, f"Error: {actual_error}", True)
                    else:
                        logger.debug(f"Tarea {task.id} completada exitosamente.") # Added logging
                        self.task_queue.complete_task(task, result=result)
                        logger.debug(f"Emitiendo task_state_changed COMPLETED para tarea {task.id}") # Added logging
                        self.task_state_changed.emit(task.id, TaskState.COMPLETED)
                
                # Determine message and error status based on result
                message = ""
                is_error = False

                if actual_error:
                    message = f"Error: {actual_error}"
                    is_error = True
                    error_count += 1 # Increment error_count here
                elif "written" in result and result["written"]:
                    # Metadata written successfully
                    if "renamed" in result and result["renamed"]:
                        # File was also renamed
                        message = result.get("message", f"Renombrado a: {os.path.basename(result.get('new_filepath', ''))}")
                        renamed_count += 1 # Increment renamed_count here
                    else:
                        # Metadata written, but file not renamed (either not requested or name was correct)
                        message = result.get("message", "Metadatos actualizados.")
                    success_count += 1 # Increment success_count here
                    is_error = False
                elif "written" in result and not result["written"]:
                    # Metadata writing failed
                    message = result.get('error', 'Error desconocido durante escritura de metadatos')
                    is_error = True
                    error_count += 1 # Increment error_count here
                elif result.get("success") is False:
                     # Catch other specific errors or failures not covered above
                     message = result.get('message', result.get('error', 'Fallo desconocido durante el procesamiento'))
                     is_error = True
                     error_count += 1 # Increment error_count here
                else:
                    # Processing completed successfully
                    genres = result.get("detected_genres", {}) or result.get("found_genres", {})
                    if genres:
                        genre_str = ", ".join(
                            f"{g} ({c:.2f})" if isinstance(c, float) else f"{g}"
                            for g, c in sorted(genres.items(), key=lambda x: x[1], reverse=True)
                        )
                        message = f"Procesamiento exitoso. Géneros: {genre_str}"
                    else:
                        message = result.get("message", "Procesamiento completado")
                    success_count += 1 # Increment success_count here
                    is_error = False

                # Emit the signal with the determined message and error status
                self.file_processed.emit(filepath, message, is_error)

                # The signal circuit_breaker_closed is emitted in the success handler
                if not self.task_queue.circuit_breaker.is_open and not is_error:
                    self.circuit_breaker_closed.emit()
                    logger.debug("Circuit breaker cerrado después de procesamiento exitoso")

                processed_count += 1
                total_files = len(self.file_paths)
                self.progress.emit(f"Procesado: {processed_count}/{total_files} - {os.path.basename(filepath)}")

                results_details.append({
                    "filepath": filepath,
                    "written_metadata_success": result.get("written", False),
                    "current_genre": result.get("current_genre", ""),
                    "selected_genres_written": result.get("selected_genres_written", []),
                    "threshold_used": result.get("threshold_used", 0.3),
                    "renamed_to": result.get("new_filepath", ""),
                    "error": result.get("error", ""),
                    "rename_error": result.get("error", ""), # Keep for compatibility with existing results_details structure
                    "rename_message": result.get("message", ""), # Keep for compatibility
                    "detected_genres_initial_clean": result.get("detected_genres_initial_clean", {}),
                    "detected_genres_written": result.get("selected_genres_written", []),
                    "tag_update_error": result.get("tag_update_error", "") # Keep for compatibility
                })
            except Exception as e:
                logger.error(f"Excepción no manejada durante el procesamiento de tarea {task.id} para {filepath}: {str(e)}", exc_info=True) # Added logging with exc_info
                with self._thread_lock:
                    error_count += 1
                    error_msg = f"Error: {str(e)}"
                    logger.error(f"Error al procesar {filepath}: {str(e)}")
                    self.task_queue.complete_task(task, error=error_msg)
                    logger.debug(f"Emitiendo task_state_changed FAILED para tarea {task.id} debido a excepción no manejada.") # Added logging
                    self.task_state_changed.emit(task.id, TaskState.FAILED)
                    logger.info(f"Emitiendo file_processed error para {filepath} debido a excepción no manejada.") # Added logging
                    self.file_processed.emit(filepath, error_msg, True)

        try:
            logger.info("Limpiando tareas completadas.") # Added logging
            # Limpiar tareas completadas
            with self._thread_lock:
                self.task_queue._active_tasks = [
                    t for t in self.task_queue._active_tasks
                    if t.state not in (TaskState.COMPLETED, TaskState.FAILED)
                ]
                logger.debug(f"Tareas activas después de limpieza: {len(self.task_queue._active_tasks)}") # Added logging
                
            logger.info("Emitiendo finished signal.") # Added logging
            self.finished.emit({
                "total": total_files,
                "success": success_count,
                "errors": error_count,
                "renamed": renamed_count,
                "details": results_details
            })
            logger.info("ProcessingThread.run finalizado.") # Added logging
        except Exception as e:
            logger.error(f"Error finalizando el procesamiento: {str(e)}", exc_info=True) # Added logging with exc_info

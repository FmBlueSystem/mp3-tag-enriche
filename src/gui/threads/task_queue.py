"""Task queue implementation for async processing."""
from typing import Callable, Any, List, Optional
from queue import Queue
import logging
from dataclasses import dataclass
from enum import Enum
from threading import Lock

logger = logging.getLogger(__name__)

class TaskState(Enum):
    """Estados posibles de una tarea."""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    """Representa una tarea en la cola."""
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    state: TaskState = TaskState.PENDING
    result: Any = None
    error: Optional[str] = None

class CircuitBreaker:
    """Implementación del patrón Circuit Breaker."""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.is_open = False
        self._lock = Lock()
        
    def record_failure(self) -> bool:
        """Registra una falla y abre el circuito si se alcanza el umbral."""
        with self._lock:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.is_open = True
                logger.warning(f"Circuit breaker abierto después de {self.failures} fallos")
                return True
            return False
            
    def record_success(self):
        """Registra un éxito y reinicia el contador de fallos."""
        with self._lock:
            self.failures = 0
            self.is_open = False
            
    def allow_request(self) -> bool:
        """Determina si se permite una nueva solicitud."""
        return not self.is_open

class TaskQueue:
    """Cola de tareas con circuit breaker."""
    
    def __init__(self):
        self.queue: Queue = Queue()
        self.circuit_breaker = CircuitBreaker()
        self._active_tasks: List[Task] = []
        self._lock = Lock()
        
    def add_task(self, task_id: str, func: Callable, *args, **kwargs) -> Task:
        """Añade una nueva tarea a la cola."""
        task = Task(task_id, func, args, kwargs)
        with self._lock:
            self._active_tasks.append(task)
        self.queue.put(task)
        logger.debug(f"Tarea {task_id} añadida a la cola")
        return task
        
    def get_next_task(self) -> Optional[Task]:
        """Obtiene la siguiente tarea si el circuit breaker lo permite."""
        if not self.circuit_breaker.allow_request():
            logger.warning("Circuit breaker abierto - no se procesan más tareas")
            return None
            
        try:
            return self.queue.get_nowait()
        except Queue.Empty:
            return None
            
    def complete_task(self, task: Task, result: Any = None, error: Optional[str] = None):
        """Marca una tarea como completada o fallida."""
        with self._lock:
            task.result = result
            task.error = error
            task.state = TaskState.FAILED if error else TaskState.COMPLETED
            
            if error:
                if self.circuit_breaker.record_failure():
                    logger.error(f"Circuit breaker activado después de error en tarea {task.id}")
            else:
                self.circuit_breaker.record_success()
                
    def cancel_task(self, task_id: str) -> bool:
        """Cancela una tarea pendiente."""
        with self._lock:
            for task in self._active_tasks:
                if task.id == task_id and task.state == TaskState.PENDING:
                    task.state = TaskState.CANCELLED
                    logger.info(f"Tarea {task_id} cancelada")
                    return True
        return False
        
    def get_task_status(self, task_id: str) -> Optional[TaskState]:
        """Obtiene el estado actual de una tarea."""
        with self._lock:
            for task in self._active_tasks:
                if task.id == task_id:
                    return task.state
        return None
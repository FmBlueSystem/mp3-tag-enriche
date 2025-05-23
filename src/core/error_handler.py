"""
Sistema centralizado de manejo de errores con recuperación automática.
"""
import logging
import time
import traceback
from typing import Dict, Any, Optional, Callable, List, Type
from dataclasses import dataclass, field
from enum import Enum
import functools

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Niveles de severidad de errores."""
    LOW = "low"          # Errores menores que no afectan funcionalidad principal
    MEDIUM = "medium"    # Errores que pueden degradar performance
    HIGH = "high"        # Errores que afectan funcionalidad principal
    CRITICAL = "critical" # Errores que pueden causar fallas completas

@dataclass
class ErrorContext:
    """Contexto detallado de un error."""
    timestamp: float = field(default_factory=time.time)
    error_type: str = ""
    error_message: str = ""
    traceback_str: str = ""
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    component: str = ""
    operation: str = ""
    user_data: Dict[str, Any] = field(default_factory=dict)
    recovery_attempted: bool = False
    recovery_successful: bool = False

class ErrorRecoveryStrategy:
    """Estrategia de recuperación de errores."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
    def should_retry(self, error_context: ErrorContext, attempt: int) -> bool:
        """Determina si se debe intentar recuperación."""
        if attempt >= self.max_retries:
            return False
            
        # No reintentar errores críticos de configuración
        if "configuration" in error_context.component.lower():
            return False
            
        # No reintentar errores de archivo no encontrado
        if "FileNotFoundError" in error_context.error_type:
            return False
            
        return True
        
    def get_delay(self, attempt: int) -> float:
        """Calcula delay exponencial para reintentos."""
        return min(60, (self.backoff_factor ** attempt))

class ErrorHandler:
    """Sistema centralizado de manejo de errores."""
    
    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.recovery_strategy = ErrorRecoveryStrategy()
        self.error_callbacks: Dict[str, List[Callable]] = {}
        self.component_stats: Dict[str, Dict[str, int]] = {}
        
    def register_error_callback(self, component: str, callback: Callable[[ErrorContext], None]):
        """Registra callback para errores de un componente específico."""
        if component not in self.error_callbacks:
            self.error_callbacks[component] = []
        self.error_callbacks[component].append(callback)
        
    def handle_error(self, 
                    error: Exception,
                    component: str = "",
                    operation: str = "",
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    user_data: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """Maneja un error y registra contexto detallado."""
        
        error_context = ErrorContext(
            error_type=type(error).__name__,
            error_message=str(error),
            traceback_str=traceback.format_exc(),
            severity=severity,
            component=component,
            operation=operation,
            user_data=user_data or {}
        )
        
        # Registrar en historial
        self.error_history.append(error_context)
        
        # Actualizar estadísticas
        self._update_component_stats(component, error_context.error_type)
        
        # Log según severidad
        self._log_error(error_context)
        
        # Ejecutar callbacks
        self._execute_callbacks(component, error_context)
        
        # Limitar historial a últimos 1000 errores
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
            
        return error_context
        
    def _update_component_stats(self, component: str, error_type: str):
        """Actualiza estadísticas de errores por componente."""
        if component not in self.component_stats:
            self.component_stats[component] = {}
        if error_type not in self.component_stats[component]:
            self.component_stats[component][error_type] = 0
        self.component_stats[component][error_type] += 1
        
    def _log_error(self, error_context: ErrorContext):
        """Registra error en logs según severidad."""
        log_msg = f"[{error_context.component}:{error_context.operation}] {error_context.error_type}: {error_context.error_message}"
        
        if error_context.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_msg, extra={"error_context": error_context})
        elif error_context.severity == ErrorSeverity.HIGH:
            logger.error(log_msg, extra={"error_context": error_context})
        elif error_context.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_msg, extra={"error_context": error_context})
        else:
            logger.info(log_msg, extra={"error_context": error_context})
            
    def _execute_callbacks(self, component: str, error_context: ErrorContext):
        """Ejecuta callbacks registrados para el componente."""
        callbacks = self.error_callbacks.get(component, [])
        for callback in callbacks:
            try:
                callback(error_context)
            except Exception as e:
                logger.error(f"Error ejecutando callback: {e}")
                
    def get_error_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de errores."""
        total_errors = len(self.error_history)
        
        # Errores por severidad
        severity_counts = {}
        for ctx in self.error_history:
            sev = ctx.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
        # Errores recientes (última hora)
        recent_cutoff = time.time() - 3600
        recent_errors = [ctx for ctx in self.error_history if ctx.timestamp > recent_cutoff]
        
        return {
            "total_errors": total_errors,
            "recent_errors": len(recent_errors),
            "severity_distribution": severity_counts,
            "component_stats": self.component_stats.copy(),
            "most_common_errors": self._get_most_common_errors()
        }
        
    def _get_most_common_errors(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtiene los errores más comunes."""
        error_counts = {}
        for ctx in self.error_history:
            key = f"{ctx.component}:{ctx.error_type}"
            if key not in error_counts:
                error_counts[key] = {"count": 0, "example": ctx}
            error_counts[key]["count"] += 1
            
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1]["count"], reverse=True)
        
        return [
            {
                "component_error": key,
                "count": data["count"],
                "last_message": data["example"].error_message,
                "severity": data["example"].severity.value
            }
            for key, data in sorted_errors[:limit]
        ]

def retry_on_error(max_retries: int = 3, 
                  backoff_factor: float = 1.5,
                  exceptions: tuple = (Exception,),
                  component: str = "",
                  operation: str = ""):
    """Decorador para reintentar operaciones en caso de error."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = get_global_error_handler()
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        # Último intento, registrar error
                        error_context = error_handler.handle_error(
                            e, component=component, operation=operation
                        )
                        raise
                    
                    # Calcular delay y esperar
                    delay = min(60, (backoff_factor ** attempt))
                    logger.warning(f"Intento {attempt + 1} falló en {component}:{operation}, reintentando en {delay}s")
                    time.sleep(delay)
                    
            return None  # No debería llegar aquí
        return wrapper
    return decorator

# Instancia global
_global_error_handler: Optional[ErrorHandler] = None

def get_global_error_handler() -> ErrorHandler:
    """Obtiene la instancia global del manejador de errores."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler

def setup_error_handling():
    """Configura el sistema de manejo de errores."""
    error_handler = get_global_error_handler()
    
    # Callbacks de ejemplo para componentes específicos
    def api_error_callback(error_context: ErrorContext):
        """Callback especializado para errores de API."""
        if "rate limit" in error_context.error_message.lower():
            logger.info("Rate limit detectado, activando throttling")
            
    def cache_error_callback(error_context: ErrorContext):
        """Callback especializado para errores de cache."""
        if "permission" in error_context.error_message.lower():
            logger.warning("Error de permisos en cache, verificar directorio")
            
    error_handler.register_error_callback("api", api_error_callback)
    error_handler.register_error_callback("cache", cache_error_callback)
    
    logger.info("Sistema de manejo de errores configurado") 
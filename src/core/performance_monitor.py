"""
Sistema avanzado de monitoreo de performance y métricas en tiempo real.
"""
import time
import psutil
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import deque, defaultdict
import json
import logging
from pathlib import Path
import statistics

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Métrica individual de performance."""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

@dataclass
class SystemMetrics:
    """Métricas del sistema."""
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_threads: int
    timestamp: float = field(default_factory=time.time)

class PerformanceAlert:
    """Sistema de alertas para métricas de performance."""
    
    def __init__(self, name: str, threshold: float, condition: str = "greater"):
        """
        Inicializa una alerta de performance.
        
        Args:
            name: Nombre de la métrica a monitorear
            threshold: Umbral que dispara la alerta
            condition: 'greater', 'less', 'equal'
        """
        self.name = name
        self.threshold = threshold
        self.condition = condition
        self.triggered = False
        self.last_trigger_time = 0
        self.callbacks: List[Callable[[str, float, float], None]] = []
        
    def add_callback(self, callback: Callable[[str, float, float], None]):
        """Añade callback que se ejecuta cuando se dispara la alerta."""
        self.callbacks.append(callback)
        
    def check(self, value: float) -> bool:
        """Verifica si la métrica dispara la alerta."""
        triggered = False
        
        if self.condition == "greater" and value > self.threshold:
            triggered = True
        elif self.condition == "less" and value < self.threshold:
            triggered = True
        elif self.condition == "equal" and abs(value - self.threshold) < 0.001:
            triggered = True
            
        if triggered and not self.triggered:
            # Nueva activación
            self.triggered = True
            self.last_trigger_time = time.time()
            for callback in self.callbacks:
                try:
                    callback(self.name, value, self.threshold)
                except Exception as e:
                    logger.error(f"Error ejecutando callback de alerta: {e}")
        elif not triggered:
            self.triggered = False
            
        return triggered

class PerformanceMonitor:
    """Monitor avanzado de performance del sistema."""
    
    def __init__(self, 
                 metrics_history_size: int = 1000,
                 collection_interval: float = 1.0):
        """
        Inicializa el monitor de performance.
        
        Args:
            metrics_history_size: Tamaño del historial de métricas
            collection_interval: Intervalo de recolección en segundos
        """
        self.metrics_history: deque = deque(maxlen=metrics_history_size)
        self.custom_metrics: defaultdict = defaultdict(lambda: deque(maxlen=metrics_history_size))
        self.system_metrics_history: deque = deque(maxlen=metrics_history_size)
        self.collection_interval = collection_interval
        self.alerts: Dict[str, PerformanceAlert] = {}
        
        # Threading para recolección automática
        self._collection_thread: Optional[threading.Thread] = None
        self._stop_collection = threading.Event()
        self._lock = threading.Lock()
        
        # Estadísticas de operaciones
        self.operation_stats: defaultdict = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "recent_times": deque(maxlen=100)
        })
        
        # Estado inicial del sistema para cálculos relativos
        self._last_network_io = psutil.net_io_counters()
        
    def start_monitoring(self):
        """Inicia la recolección automática de métricas."""
        if self._collection_thread and self._collection_thread.is_alive():
            return
            
        self._stop_collection.clear()
        self._collection_thread = threading.Thread(
            target=self._collect_metrics_loop,
            daemon=True
        )
        self._collection_thread.start()
        logger.info("Monitor de performance iniciado")
        
    def stop_monitoring(self):
        """Detiene la recolección de métricas."""
        self._stop_collection.set()
        if self._collection_thread:
            self._collection_thread.join(timeout=5)
        logger.info("Monitor de performance detenido")
        
    def _collect_metrics_loop(self):
        """Loop principal de recolección de métricas."""
        while not self._stop_collection.is_set():
            try:
                self._collect_system_metrics()
                self._check_alerts()
            except Exception as e:
                logger.error(f"Error recolectando métricas: {e}")
                
            self._stop_collection.wait(self.collection_interval)
            
    def _collect_system_metrics(self):
        """Recolecta métricas del sistema."""
        try:
            # CPU y memoria
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            
            # Disco
            disk = psutil.disk_usage('/')
            
            # Red (diferencial)
            current_net = psutil.net_io_counters()
            
            # Threads activos
            active_threads = threading.active_count()
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_gb=memory.available / (1024**3),
                disk_usage_percent=disk.percent,
                disk_free_gb=disk.free / (1024**3),
                network_bytes_sent=current_net.bytes_sent,
                network_bytes_recv=current_net.bytes_recv,
                active_threads=active_threads
            )
            
            with self._lock:
                self.system_metrics_history.append(metrics)
                
        except Exception as e:
            logger.error(f"Error recolectando métricas del sistema: {e}")
            
    def add_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, unit: str = ""):
        """Añade una métrica personalizada."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            tags=tags or {},
            unit=unit
        )
        
        with self._lock:
            self.custom_metrics[name].append(metric)
            self.metrics_history.append(metric)
            
    def record_operation(self, operation_name: str, duration: float):
        """Registra estadísticas de una operación."""
        with self._lock:
            stats = self.operation_stats[operation_name]
            stats["count"] += 1
            stats["total_time"] += duration
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["min_time"] = min(stats["min_time"], duration)
            stats["max_time"] = max(stats["max_time"], duration)
            stats["recent_times"].append(duration)
            
    def add_alert(self, name: str, threshold: float, condition: str = "greater") -> PerformanceAlert:
        """Añade una alerta de performance."""
        alert = PerformanceAlert(name, threshold, condition)
        self.alerts[name] = alert
        return alert
        
    def _check_alerts(self):
        """Verifica todas las alertas configuradas."""
        latest_system_metrics = None
        with self._lock:
            if self.system_metrics_history:
                latest_system_metrics = self.system_metrics_history[-1]
                
        if not latest_system_metrics:
            return
            
        # Verificar alertas del sistema
        system_values = {
            "cpu_percent": latest_system_metrics.cpu_percent,
            "memory_percent": latest_system_metrics.memory_percent,
            "disk_usage_percent": latest_system_metrics.disk_usage_percent,
            "active_threads": latest_system_metrics.active_threads
        }
        
        for metric_name, value in system_values.items():
            if metric_name in self.alerts:
                self.alerts[metric_name].check(value)
                
        # Verificar alertas de métricas personalizadas
        for metric_name, alert in self.alerts.items():
            if metric_name in self.custom_metrics and self.custom_metrics[metric_name]:
                latest_value = self.custom_metrics[metric_name][-1].value
                alert.check(latest_value)
                
    def get_system_summary(self) -> Dict[str, Any]:
        """Obtiene resumen actual del sistema."""
        with self._lock:
            if not self.system_metrics_history:
                return {}
                
            latest = self.system_metrics_history[-1]
            
            # Calcular promedios de los últimos 10 minutos
            recent_cutoff = time.time() - 600  # 10 minutos
            recent_metrics = [m for m in self.system_metrics_history if m.timestamp > recent_cutoff]
            
            if recent_metrics:
                avg_cpu = statistics.mean([m.cpu_percent for m in recent_metrics])
                avg_memory = statistics.mean([m.memory_percent for m in recent_metrics])
            else:
                avg_cpu = latest.cpu_percent
                avg_memory = latest.memory_percent
                
            return {
                "current": {
                    "cpu_percent": latest.cpu_percent,
                    "memory_percent": latest.memory_percent,
                    "memory_available_gb": latest.memory_available_gb,
                    "disk_usage_percent": latest.disk_usage_percent,
                    "disk_free_gb": latest.disk_free_gb,
                    "active_threads": latest.active_threads
                },
                "averages_10min": {
                    "cpu_percent": avg_cpu,
                    "memory_percent": avg_memory
                },
                "alerts_active": [name for name, alert in self.alerts.items() if alert.triggered]
            }
            
    def get_operation_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de operaciones."""
        with self._lock:
            result = {}
            for op_name, stats in self.operation_stats.items():
                recent_times = list(stats["recent_times"])
                
                result[op_name] = {
                    "total_operations": stats["count"],
                    "avg_duration": stats["avg_time"],
                    "min_duration": stats["min_time"] if stats["min_time"] != float('inf') else 0,
                    "max_duration": stats["max_time"],
                    "recent_avg": statistics.mean(recent_times) if recent_times else 0,
                    "operations_per_second": len(recent_times) / 100.0 if recent_times else 0
                }
                
            return result
            
    def export_metrics(self, filepath: str):
        """Exporta métricas a archivo JSON."""
        try:
            data = {
                "timestamp": time.time(),
                "system_summary": self.get_system_summary(),
                "operation_stats": self.get_operation_stats(),
                "custom_metrics": {
                    name: [
                        {
                            "value": m.value,
                            "timestamp": m.timestamp,
                            "tags": m.tags,
                            "unit": m.unit
                        }
                        for m in metrics_deque
                    ]
                    for name, metrics_deque in self.custom_metrics.items()
                }
            }
            
            Path(filepath).write_text(json.dumps(data, indent=2))
            logger.info(f"Métricas exportadas a {filepath}")
            
        except Exception as e:
            logger.error(f"Error exportando métricas: {e}")

def operation_timer(operation_name: str, monitor: Optional[PerformanceMonitor] = None):
    """Decorador para medir tiempo de operaciones."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if monitor:
                    monitor.record_operation(operation_name, duration)
                else:
                    # Usar monitor global si existe
                    global_monitor = getattr(operation_timer, '_global_monitor', None)
                    if global_monitor:
                        global_monitor.record_operation(operation_name, duration)
                        
                return result
            except Exception as e:
                duration = time.time() - start_time
                if monitor:
                    monitor.record_operation(f"{operation_name}_error", duration)
                raise
                
        return wrapper
    return decorator

# Monitor global opcional
_global_performance_monitor: Optional[PerformanceMonitor] = None

def get_global_performance_monitor() -> Optional[PerformanceMonitor]:
    """Obtiene el monitor de performance global."""
    return _global_performance_monitor

def setup_performance_monitoring(auto_start: bool = True) -> PerformanceMonitor:
    """Configura el sistema de monitoreo de performance."""
    global _global_performance_monitor
    
    monitor = PerformanceMonitor()
    _global_performance_monitor = monitor
    
    # Configurar alertas por defecto
    cpu_alert = monitor.add_alert("cpu_percent", 80.0, "greater")
    memory_alert = monitor.add_alert("memory_percent", 85.0, "greater")
    disk_alert = monitor.add_alert("disk_usage_percent", 90.0, "greater")
    
    # Callbacks de alertas
    def system_alert_callback(metric_name: str, value: float, threshold: float):
        logger.warning(f"Alerta de sistema: {metric_name} = {value:.2f}% (umbral: {threshold}%)")
        
    cpu_alert.add_callback(system_alert_callback)
    memory_alert.add_callback(system_alert_callback)
    disk_alert.add_callback(system_alert_callback)
    
    # Configurar decorador global
    operation_timer._global_monitor = monitor
    
    if auto_start:
        monitor.start_monitoring()
        
    logger.info("Sistema de monitoreo de performance configurado")
    return monitor 
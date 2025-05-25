#!/usr/bin/env python3
"""
📊 API METRICS - NUEVA BIBLIOTECA v2.0
=====================================
Sistema de métricas para tracking de APIs musicales
"""

import time
import threading
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class APIMetrics:
    """Métricas para una API específica."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rate_limited_calls: int = 0
    total_latency: float = 0.0
    min_latency: float = float('inf')
    max_latency: float = 0.0
    recent_latencies: deque = field(default_factory=lambda: deque(maxlen=100))
    last_call_time: Optional[float] = None
    first_call_time: Optional[float] = None
    
    def add_call(self, success: bool, latency: float, rate_limited: bool = False):
        """Añadir una llamada a las métricas."""
        now = time.time()
        
        self.total_calls += 1
        self.total_latency += latency
        self.recent_latencies.append(latency)
        
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            
        if rate_limited:
            self.rate_limited_calls += 1
            
        # Actualizar latencias min/max
        self.min_latency = min(self.min_latency, latency)
        self.max_latency = max(self.max_latency, latency)
        
        # Actualizar timestamps
        self.last_call_time = now
        if self.first_call_time is None:
            self.first_call_time = now
            
    @property
    def success_rate(self) -> float:
        """Tasa de éxito (0.0 - 1.0)."""
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
        
    @property
    def average_latency(self) -> float:
        """Latencia promedio en segundos."""
        if self.total_calls == 0:
            return 0.0
        return self.total_latency / self.total_calls
        
    @property
    def recent_average_latency(self) -> float:
        """Latencia promedio de las últimas 100 llamadas."""
        if not self.recent_latencies:
            return 0.0
        return sum(self.recent_latencies) / len(self.recent_latencies)
        
    @property
    def calls_per_minute(self) -> float:
        """Llamadas por minuto basado en el historial."""
        if self.first_call_time is None or self.last_call_time is None:
            return 0.0
            
        duration_minutes = (self.last_call_time - self.first_call_time) / 60.0
        if duration_minutes == 0:
            return 0.0
            
        return self.total_calls / duration_minutes
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertir métricas a diccionario."""
        return {
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'rate_limited_calls': self.rate_limited_calls,
            'success_rate': self.success_rate,
            'average_latency': self.average_latency,
            'recent_average_latency': self.recent_average_latency,
            'min_latency': self.min_latency if self.min_latency != float('inf') else 0.0,
            'max_latency': self.max_latency,
            'calls_per_minute': self.calls_per_minute,
            'last_call_time': self.last_call_time,
            'first_call_time': self.first_call_time
        }

class MetricsTracker:
    """
    Tracker de métricas para múltiples APIs.
    Thread-safe y optimizado para alto rendimiento.
    """
    
    def __init__(self):
        """Inicializar el tracker de métricas."""
        self.metrics: Dict[str, APIMetrics] = defaultdict(APIMetrics)
        self.lock = threading.Lock()
        self.start_time = time.time()
        
    def record_api_call(self, 
                       api_name: str, 
                       success: bool, 
                       latency: float,
                       rate_limited: bool = False) -> None:
        """
        Registrar una llamada a API.
        
        Args:
            api_name: Nombre de la API
            success: Si la llamada fue exitosa
            latency: Latencia en segundos
            rate_limited: Si la llamada fue limitada por rate limiting
        """
        with self.lock:
            self.metrics[api_name].add_call(success, latency, rate_limited)
            
        logger.debug(f"API call recorded: {api_name} - "
                    f"Success: {success}, Latency: {latency:.3f}s, "
                    f"Rate Limited: {rate_limited}")
                    
    def get_metrics(self, api_name: str) -> Dict[str, Any]:
        """
        Obtener métricas para una API específica.
        
        Args:
            api_name: Nombre de la API
            
        Returns:
            Diccionario con métricas de la API
        """
        with self.lock:
            if api_name not in self.metrics:
                return {}
            return self.metrics[api_name].to_dict()
            
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtener métricas para todas las APIs.
        
        Returns:
            Diccionario con métricas de todas las APIs
        """
        with self.lock:
            return {
                api_name: metrics.to_dict() 
                for api_name, metrics in self.metrics.items()
            }
            
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen general de métricas.
        
        Returns:
            Diccionario con resumen de métricas
        """
        with self.lock:
            total_calls = sum(m.total_calls for m in self.metrics.values())
            total_successful = sum(m.successful_calls for m in self.metrics.values())
            total_failed = sum(m.failed_calls for m in self.metrics.values())
            total_rate_limited = sum(m.rate_limited_calls for m in self.metrics.values())
            
            # Calcular latencia promedio ponderada
            total_latency = sum(m.total_latency for m in self.metrics.values())
            avg_latency = total_latency / total_calls if total_calls > 0 else 0.0
            
            # Tiempo de ejecución total
            uptime = time.time() - self.start_time
            
            return {
                'total_apis': len(self.metrics),
                'total_calls': total_calls,
                'successful_calls': total_successful,
                'failed_calls': total_failed,
                'rate_limited_calls': total_rate_limited,
                'overall_success_rate': total_successful / total_calls if total_calls > 0 else 0.0,
                'average_latency': avg_latency,
                'uptime_seconds': uptime,
                'calls_per_minute': (total_calls / (uptime / 60.0)) if uptime > 0 else 0.0
            }
            
    def reset_metrics(self, api_name: Optional[str] = None) -> None:
        """
        Resetear métricas.
        
        Args:
            api_name: API específica a resetear, o None para todas
        """
        with self.lock:
            if api_name:
                if api_name in self.metrics:
                    self.metrics[api_name] = APIMetrics()
            else:
                self.metrics.clear()
                self.start_time = time.time()
                
        logger.info(f"Metrics reset for: {api_name or 'all APIs'}")
        
    def get_top_apis_by_calls(self, limit: int = 5) -> list:
        """
        Obtener las APIs con más llamadas.
        
        Args:
            limit: Número máximo de APIs a retornar
            
        Returns:
            Lista de tuplas (api_name, total_calls)
        """
        with self.lock:
            sorted_apis = sorted(
                self.metrics.items(),
                key=lambda x: x[1].total_calls,
                reverse=True
            )
            
            return [(name, metrics.total_calls) for name, metrics in sorted_apis[:limit]]
            
    def get_slowest_apis(self, limit: int = 5) -> list:
        """
        Obtener las APIs más lentas.
        
        Args:
            limit: Número máximo de APIs a retornar
            
        Returns:
            Lista de tuplas (api_name, average_latency)
        """
        with self.lock:
            apis_with_calls = [
                (name, metrics) for name, metrics in self.metrics.items()
                if metrics.total_calls > 0
            ]
            
            sorted_apis = sorted(
                apis_with_calls,
                key=lambda x: x[1].average_latency,
                reverse=True
            )
            
            return [(name, metrics.average_latency) for name, metrics in sorted_apis[:limit]]
            
    def get_apis_with_errors(self) -> list:
        """
        Obtener APIs que han tenido errores.
        
        Returns:
            Lista de tuplas (api_name, error_rate, total_errors)
        """
        with self.lock:
            apis_with_errors = []
            
            for name, metrics in self.metrics.items():
                if metrics.failed_calls > 0:
                    error_rate = metrics.failed_calls / metrics.total_calls
                    apis_with_errors.append((name, error_rate, metrics.failed_calls))
                    
            # Ordenar por tasa de error descendente
            apis_with_errors.sort(key=lambda x: x[1], reverse=True)
            
            return apis_with_errors
            
    def export_metrics(self) -> Dict[str, Any]:
        """
        Exportar todas las métricas en formato completo.
        
        Returns:
            Diccionario completo con todas las métricas y metadatos
        """
        with self.lock:
            return {
                'timestamp': time.time(),
                'summary': self.get_summary(),
                'apis': self.get_all_metrics(),
                'top_apis_by_calls': self.get_top_apis_by_calls(),
                'slowest_apis': self.get_slowest_apis(),
                'apis_with_errors': self.get_apis_with_errors()
            }
            
    def log_summary(self) -> None:
        """Log un resumen de métricas."""
        summary = self.get_summary()
        
        logger.info("=== API METRICS SUMMARY ===")
        logger.info(f"Total APIs: {summary['total_apis']}")
        logger.info(f"Total Calls: {summary['total_calls']}")
        logger.info(f"Success Rate: {summary['overall_success_rate']:.2%}")
        logger.info(f"Average Latency: {summary['average_latency']:.3f}s")
        logger.info(f"Calls/Minute: {summary['calls_per_minute']:.1f}")
        
        # Log APIs con errores
        apis_with_errors = self.get_apis_with_errors()
        if apis_with_errors:
            logger.warning("APIs with errors:")
            for api_name, error_rate, total_errors in apis_with_errors:
                logger.warning(f"  {api_name}: {error_rate:.2%} error rate ({total_errors} errors)")
                
        logger.info("=== END SUMMARY ===")

# Instancia global del tracker
_global_tracker = MetricsTracker()

def get_global_tracker() -> MetricsTracker:
    """Obtener la instancia global del tracker de métricas."""
    return _global_tracker

def record_api_call(api_name: str, success: bool, latency: float, rate_limited: bool = False) -> None:
    """Función de conveniencia para registrar llamadas a API."""
    _global_tracker.record_api_call(api_name, success, latency, rate_limited)

def get_api_metrics(api_name: str) -> Dict[str, Any]:
    """Función de conveniencia para obtener métricas de una API."""
    return _global_tracker.get_metrics(api_name)

def get_all_metrics() -> Dict[str, Dict[str, Any]]:
    """Función de conveniencia para obtener todas las métricas."""
    return _global_tracker.get_all_metrics()

def log_metrics_summary() -> None:
    """Función de conveniencia para log del resumen de métricas."""
    _global_tracker.log_summary()
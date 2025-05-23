"""
Optimizador de memoria para el sistema de procesamiento de archivos.
Ajusta automáticamente parámetros según los recursos disponibles del sistema.
"""

import psutil
import gc
import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MemoryConfig:
    """Configuración optimizada de memoria basada en recursos del sistema."""
    batch_size: int = 10
    max_active_tasks: int = 100
    memory_cleanup_interval: int = 5
    gc_threshold: float = 0.8  # % de memoria para forzar GC
    max_memory_mb: int = 1024  # Límite máximo de memoria en MB
    chunk_size: int = 8192

class MemoryOptimizer:
    """Optimizador automático de memoria para procesamiento de archivos."""
    
    def __init__(self):
        self.system_memory_gb = psutil.virtual_memory().total / (1024**3)
        self.cpu_count = psutil.cpu_count()
        self.config = self._generate_optimal_config()
        
    def _generate_optimal_config(self) -> MemoryConfig:
        """Genera configuración óptima basada en recursos del sistema."""
        try:
            memory_gb = self.system_memory_gb
            cpu_count = self.cpu_count
            
            logger.info(f"Sistema detectado: {memory_gb:.1f}GB RAM, {cpu_count} CPUs")
            
            # Configuración base según memoria disponible
            if memory_gb >= 16:
                # Sistema de alta capacidad
                config = MemoryConfig(
                    batch_size=20,
                    max_active_tasks=200,
                    memory_cleanup_interval=10,
                    gc_threshold=0.85,
                    max_memory_mb=2048,
                    chunk_size=16384
                )
                logger.info("Configuración HIGH-END aplicada")
                
            elif memory_gb >= 8:
                # Sistema medio
                config = MemoryConfig(
                    batch_size=15,
                    max_active_tasks=150,
                    memory_cleanup_interval=7,
                    gc_threshold=0.80,
                    max_memory_mb=1536,
                    chunk_size=12288
                )
                logger.info("Configuración MEDIA aplicada")
                
            elif memory_gb >= 4:
                # Sistema básico
                config = MemoryConfig(
                    batch_size=10,
                    max_active_tasks=100,
                    memory_cleanup_interval=5,
                    gc_threshold=0.75,
                    max_memory_mb=1024,
                    chunk_size=8192
                )
                logger.info("Configuración BÁSICA aplicada")
                
            else:
                # Sistema limitado
                config = MemoryConfig(
                    batch_size=5,
                    max_active_tasks=50,
                    memory_cleanup_interval=3,
                    gc_threshold=0.70,
                    max_memory_mb=512,
                    chunk_size=4096
                )
                logger.info("Configuración LIMITADA aplicada")
            
            # Ajustes adicionales según CPUs
            if cpu_count <= 2:
                config.batch_size = max(5, config.batch_size // 2)
                config.max_active_tasks = max(25, config.max_active_tasks // 2)
                logger.info(f"Ajustado para CPU limitada: batch_size={config.batch_size}")
            
            return config
            
        except Exception as e:
            logger.error(f"Error generando configuración óptima: {e}")
            # Configuración conservadora por defecto
            return MemoryConfig()
    
    def get_current_memory_usage(self) -> Dict[str, float]:
        """Obtiene el uso actual de memoria del sistema."""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info()
            
            return {
                "system_percent": memory.percent,
                "system_available_gb": memory.available / (1024**3),
                "process_rss_mb": process_memory.rss / (1024**2),
                "process_vms_mb": process_memory.vms / (1024**2),
            }
        except Exception as e:
            logger.error(f"Error obteniendo uso de memoria: {e}")
            return {}
    
    def should_force_gc(self) -> bool:
        """Determina si se debe forzar garbage collection."""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent / 100.0
            
            return memory_percent >= self.config.gc_threshold
        except Exception as e:
            logger.error(f"Error verificando necesidad de GC: {e}")
            return False
    
    def optimize_for_file_count(self, file_count: int) -> MemoryConfig:
        """Optimiza configuración específicamente para número de archivos."""
        config = MemoryConfig(
            batch_size=self.config.batch_size,
            max_active_tasks=self.config.max_active_tasks,
            memory_cleanup_interval=self.config.memory_cleanup_interval,
            gc_threshold=self.config.gc_threshold,
            max_memory_mb=self.config.max_memory_mb,
            chunk_size=self.config.chunk_size
        )
        
        if file_count > 100:
            # Muchos archivos - reducir batch size para estabilidad
            config.batch_size = max(5, config.batch_size // 2)
            config.memory_cleanup_interval = max(3, config.memory_cleanup_interval // 2)
            config.gc_threshold = max(0.6, config.gc_threshold - 0.1)
            logger.info(f"Optimizado para {file_count} archivos: batch_size={config.batch_size}")
            
        elif file_count > 50:
            # Archivos moderados - ajuste ligero
            config.batch_size = max(7, int(config.batch_size * 0.75))
            config.memory_cleanup_interval = max(4, config.memory_cleanup_interval - 1)
            logger.info(f"Ajustado para {file_count} archivos: batch_size={config.batch_size}")
        
        return config
    
    def force_memory_cleanup(self):
        """Fuerza limpieza agresiva de memoria."""
        try:
            logger.info("Iniciando limpieza agresiva de memoria...")
            
            # Múltiples pasadas de garbage collection
            for i in range(3):
                collected = gc.collect()
                logger.debug(f"GC pasada {i+1}: {collected} objetos recolectados")
            
            # Obtener estadísticas post-limpieza
            memory_info = self.get_current_memory_usage()
            logger.info(f"Post-limpieza - RAM sistema: {memory_info.get('system_percent', 0):.1f}%, "
                       f"Proceso: {memory_info.get('process_rss_mb', 0):.1f}MB")
                       
        except Exception as e:
            logger.error(f"Error durante limpieza de memoria: {e}")
    
    def monitor_memory_pressure(self) -> Dict[str, Any]:
        """Monitorea presión de memoria y recomienda acciones."""
        try:
            memory_info = self.get_current_memory_usage()
            system_percent = memory_info.get("system_percent", 0)
            process_mb = memory_info.get("process_rss_mb", 0)
            
            recommendations = []
            
            if system_percent > 90:
                recommendations.append("CRÍTICO: Memoria del sistema muy alta")
                recommendations.append("Reducir batch_size inmediatamente")
                
            elif system_percent > 80:
                recommendations.append("ADVERTENCIA: Memoria del sistema alta")
                recommendations.append("Considerar reducir batch_size")
            
            if process_mb > self.config.max_memory_mb:
                recommendations.append(f"ADVERTENCIA: Proceso usando {process_mb:.0f}MB > límite {self.config.max_memory_mb}MB")
                recommendations.append("Forzar limpieza de memoria")
            
            return {
                "memory_info": memory_info,
                "pressure_level": "CRÍTICO" if system_percent > 90 else 
                                "ALTO" if system_percent > 80 else 
                                "MODERADO" if system_percent > 70 else "NORMAL",
                "recommendations": recommendations,
                "should_pause": system_percent > 95
            }
            
        except Exception as e:
            logger.error(f"Error monitoreando presión de memoria: {e}")
            return {"pressure_level": "DESCONOCIDO", "recommendations": []}
    
    def get_recommended_settings(self, file_count: int = 50) -> Dict[str, Any]:
        """Obtiene configuración recomendada para número específico de archivos."""
        optimized_config = self.optimize_for_file_count(file_count)
        memory_status = self.monitor_memory_pressure()
        
        return {
            "config": optimized_config,
            "memory_status": memory_status,
            "system_info": {
                "total_memory_gb": self.system_memory_gb,
                "cpu_count": self.cpu_count,
                "recommended_for_files": file_count
            }
        }

# Instancia global del optimizador
_optimizer = None

def get_memory_optimizer() -> MemoryOptimizer:
    """Obtiene instancia global del optimizador de memoria."""
    global _optimizer
    if _optimizer is None:
        _optimizer = MemoryOptimizer()
    return _optimizer

def get_optimal_config_for_files(file_count: int) -> MemoryConfig:
    """Función conveniente para obtener configuración óptima."""
    optimizer = get_memory_optimizer()
    return optimizer.optimize_for_file_count(file_count) 
#!/usr/bin/env python3
"""
⏱️ RATE LIMITER - NUEVA BIBLIOTECA v2.0
======================================
Control de límites de API usando algoritmo Token Bucket
"""

import time
import threading
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class TokenBucket:
    """Implementación de Token Bucket para rate limiting."""
    capacity: int           # Capacidad máxima de tokens
    fill_rate: float       # Tokens por segundo
    tokens: float          # Tokens actuales
    last_update: float     # Última actualización
    lock: threading.Lock   # Lock para thread safety
    
    def __post_init__(self):
        """Inicialización post-creación."""
        if not hasattr(self, 'lock'):
            self.lock = threading.Lock()
        if not hasattr(self, 'last_update'):
            self.last_update = time.time()
        if not hasattr(self, 'tokens'):
            self.tokens = float(self.capacity)

class RateLimiter:
    """
    Gestor de rate limiting para múltiples APIs.
    Usa algoritmo Token Bucket para control de velocidad.
    """
    
    def __init__(self):
        """Inicializar el rate limiter."""
        self.buckets: Dict[str, TokenBucket] = {}
        self.global_lock = threading.Lock()
        
    def create_limit(self, key: str, capacity: int, fill_rate: float) -> None:
        """
        Crear un nuevo límite de velocidad.
        
        Args:
            key: Identificador único del límite
            capacity: Capacidad máxima de tokens (burst)
            fill_rate: Tokens por segundo (velocidad sostenida)
        """
        with self.global_lock:
            self.buckets[key] = TokenBucket(
                capacity=capacity,
                fill_rate=fill_rate,
                tokens=float(capacity),
                last_update=time.time(),
                lock=threading.Lock()
            )
            
    def acquire(self, key: str, tokens: int = 1, wait: bool = False) -> bool:
        """
        Intentar adquirir tokens del bucket.
        
        Args:
            key: Identificador del límite
            tokens: Número de tokens a adquirir
            wait: Si esperar cuando no hay tokens suficientes
            
        Returns:
            True si se adquirieron los tokens, False si no
        """
        if key not in self.buckets:
            # Si no existe el bucket, crear uno por defecto
            self.create_limit(key, capacity=10, fill_rate=1.0)
            
        bucket = self.buckets[key]
        
        with bucket.lock:
            # Actualizar tokens basado en tiempo transcurrido
            now = time.time()
            time_passed = now - bucket.last_update
            
            # Añadir tokens basado en fill_rate
            new_tokens = time_passed * bucket.fill_rate
            bucket.tokens = min(bucket.capacity, bucket.tokens + new_tokens)
            bucket.last_update = now
            
            # Verificar si hay suficientes tokens
            if bucket.tokens >= tokens:
                bucket.tokens -= tokens
                return True
            elif wait:
                # Calcular tiempo de espera necesario
                tokens_needed = tokens - bucket.tokens
                wait_time = tokens_needed / bucket.fill_rate
                
                # Esperar fuera del lock para no bloquear otros hilos
                bucket.lock.release()
                try:
                    time.sleep(wait_time)
                    return self.acquire(key, tokens, wait=False)
                finally:
                    bucket.lock.acquire()
            
            return False
            
    def get_status(self, key: str) -> Optional[Dict[str, float]]:
        """
        Obtener estado actual de un bucket.
        
        Args:
            key: Identificador del límite
            
        Returns:
            Diccionario con estado del bucket o None si no existe
        """
        if key not in self.buckets:
            return None
            
        bucket = self.buckets[key]
        
        with bucket.lock:
            # Actualizar tokens antes de reportar estado
            now = time.time()
            time_passed = now - bucket.last_update
            new_tokens = time_passed * bucket.fill_rate
            current_tokens = min(bucket.capacity, bucket.tokens + new_tokens)
            
            return {
                'capacity': bucket.capacity,
                'fill_rate': bucket.fill_rate,
                'current_tokens': current_tokens,
                'utilization': (bucket.capacity - current_tokens) / bucket.capacity
            }
            
    def reset_bucket(self, key: str) -> bool:
        """
        Resetear un bucket a su capacidad máxima.
        
        Args:
            key: Identificador del límite
            
        Returns:
            True si se reseteo exitosamente, False si no existe
        """
        if key not in self.buckets:
            return False
            
        bucket = self.buckets[key]
        
        with bucket.lock:
            bucket.tokens = float(bucket.capacity)
            bucket.last_update = time.time()
            
        return True
        
    def remove_limit(self, key: str) -> bool:
        """
        Remover un límite de velocidad.
        
        Args:
            key: Identificador del límite
            
        Returns:
            True si se removió exitosamente, False si no existía
        """
        with self.global_lock:
            if key in self.buckets:
                del self.buckets[key]
                return True
            return False
            
    def get_all_status(self) -> Dict[str, Dict[str, float]]:
        """
        Obtener estado de todos los buckets.
        
        Returns:
            Diccionario con estado de todos los buckets
        """
        status = {}
        
        with self.global_lock:
            for key in list(self.buckets.keys()):
                bucket_status = self.get_status(key)
                if bucket_status:
                    status[key] = bucket_status
                    
        return status
        
    def cleanup_unused(self, max_age: float = 3600.0) -> int:
        """
        Limpiar buckets no utilizados recientemente.
        
        Args:
            max_age: Edad máxima en segundos
            
        Returns:
            Número de buckets removidos
        """
        now = time.time()
        removed = 0
        
        with self.global_lock:
            keys_to_remove = []
            
            for key, bucket in self.buckets.items():
                with bucket.lock:
                    if (now - bucket.last_update) > max_age:
                        keys_to_remove.append(key)
                        
            for key in keys_to_remove:
                del self.buckets[key]
                removed += 1
                
        return removed
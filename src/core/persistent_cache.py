"""Persistent disk-based cache implementation with advanced features."""
import json
import os
import time
import zlib
from threading import Lock
from typing import Any, Dict, Optional, Union
import logging
from pathlib import Path
from collections import OrderedDict
import sys

logger = logging.getLogger(__name__)

class CacheEntry:
    """Representa una entrada en el caché con metadatos."""
    
    def __init__(self, value: Any, expires: float, size: int, data_type: str):
        self.value = value
        self.expires = expires
        self.size = size
        self.data_type = data_type
        self.last_accessed = time.time()

    def to_dict(self) -> dict:
        """Convierte la entrada a diccionario para serialización."""
        return {
            "value": self.value,
            "expires": self.expires,
            "size": self.size,
            "data_type": self.data_type,
            "last_accessed": self.last_accessed
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CacheEntry':
        """Crea una entrada desde un diccionario deserializado."""
        entry = cls(
            data["value"],
            data["expires"],
            data["size"],
            data["data_type"]
        )
        entry.last_accessed = data.get("last_accessed", time.time())
        return entry

class PersistentCache:
    """Caché persistente en disco con TTL, límites de tamaño y optimizaciones."""
    
    def __init__(self, cache_dir: str, 
                 default_ttl: int = 3600,
                 max_size_bytes: int = 100 * 1024 * 1024,  # 100MB default
                 compression_threshold: int = 1024,  # 1KB
                 ttl_policy: Dict[str, int] = None):
        """Inicializa el caché persistente.
        
        Args:
            cache_dir: Directorio para almacenar archivos de caché
            default_ttl: TTL predeterminado en segundos (default: 1 hora)
            max_size_bytes: Tamaño máximo del caché en bytes
            compression_threshold: Tamaño mínimo para comprimir en bytes
            ttl_policy: Diccionario de TTLs por tipo de dato {"type": seconds}
        """
        self._cache_dir = Path(cache_dir)
        self._default_ttl = default_ttl
        self._max_size_bytes = max_size_bytes
        self._compression_threshold = compression_threshold
        self._ttl_policy = ttl_policy or {}
        self._lock = Lock()
        self._current_size = 0
        self._lru_cache = OrderedDict()  # key -> tamaño
        
        # Estadísticas mejoradas
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "compression_savings": 0,
            "current_size": 0,
            "entries": 0
        }
        
        # Crear directorio de caché si no existe
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar caché
        self._init_cache()
        
    def _init_cache(self) -> None:
        """Inicializa el caché cargando entradas existentes y limpiando expiradas."""
        self._current_size = 0
        self._lru_cache.clear()
        
        # Cargar entradas existentes
        for cache_file in self._cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    entry = json.load(f)
                    entry_obj = CacheEntry.from_dict(entry)
                    
                # Verificar expiración
                if entry_obj.expires <= time.time():
                    cache_file.unlink()
                    self._stats["evictions"] += 1
                    continue
                    
                key = cache_file.stem
                self._lru_cache[key] = entry_obj.size
                self._current_size += entry_obj.size
                
            except (json.JSONDecodeError, KeyError, OSError) as e:
                logger.warning(f"Error cargando archivo de caché {cache_file}: {e}")
                try:
                    cache_file.unlink()
                except OSError:
                    pass
        
        self._stats["current_size"] = self._current_size
        self._stats["entries"] = len(self._lru_cache)
        
    def _get_ttl(self, data_type: str) -> int:
        """Obtiene el TTL para un tipo de dato específico."""
        return self._ttl_policy.get(data_type, self._default_ttl)
    
    def _compress_value(self, value: Union[str, bytes]) -> tuple[bytes, int]:
        """Comprime un valor si supera el umbral."""
        if isinstance(value, str):
            value = value.encode('utf-8')
        
        original_size = len(value)
        if original_size >= self._compression_threshold:
            compressed = zlib.compress(value)
            saved = original_size - len(compressed)
            self._stats["compression_savings"] += saved
            return compressed, original_size
        return value, original_size
    
    def _decompress_value(self, value: Union[str, bytes]) -> Any:
        """Descomprime un valor si está comprimido."""
        if isinstance(value, bytes):
            try:
                return zlib.decompress(value).decode('utf-8')
            except zlib.error:
                return value
        return value
    
    def _enforce_size_limit(self) -> None:
        """Aplica el límite de tamaño eliminando entradas según LRU."""
        while self._current_size > self._max_size_bytes and self._lru_cache:
            key, size = self._lru_cache.popitem(last=False)  # FIFO
            self._current_size -= size
            cache_path = self._get_cache_path(key)
            
            try:
                cache_path.unlink()
                self._stats["evictions"] += 1
            except OSError:
                pass
            
        self._stats["current_size"] = self._current_size
        
    def _get_cache_path(self, key: str) -> Path:
        """Obtiene la ruta del sistema de archivos para una clave de caché."""
        return self._cache_dir / f"{key}.json"

    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché.
        
        Args:
            key: Clave a recuperar
            
        Returns:
            Valor en caché si se encuentra y no ha expirado, None en caso contrario
        """
        cache_path = self._get_cache_path(key)
        
        with self._lock:
            try:
                if not cache_path.exists():
                    self._stats["misses"] += 1
                    return None
                
                with open(cache_path, 'r') as f:
                    entry_dict = json.load(f)
                    entry = CacheEntry.from_dict(entry_dict)
                
                # Verificar expiración
                if entry.expires <= time.time():
                    cache_path.unlink()
                    self._lru_cache.pop(key, None)
                    self._current_size -= entry.size
                    self._stats["evictions"] += 1
                    self._stats["misses"] += 1
                    return None
                
                # Actualizar LRU
                if key in self._lru_cache:
                    self._lru_cache.move_to_end(key)
                
                entry.last_accessed = time.time()
                with open(cache_path, 'w') as f:
                    json.dump(entry.to_dict(), f)
                
                self._stats["hits"] += 1
                return self._decompress_value(entry.value)
                
            except (json.JSONDecodeError, KeyError, OSError) as e:
                logger.warning(f"Error leyendo caché para clave {key}: {e}")
                try:
                    cache_path.unlink()
                    self._lru_cache.pop(key, None)
                except OSError:
                    pass
                self._stats["misses"] += 1
                return None

    def set(self, key: str, value: Any, data_type: str = "default") -> None:
        """Establece un valor en el caché.
        
        Args:
            key: Clave de caché
            value: Valor a almacenar
            data_type: Tipo de dato para política de TTL
        """
        cache_path = self._get_cache_path(key)
        
        with self._lock:
            try:
                # Comprimir si es necesario
                compressed_value, original_size = self._compress_value(value)
                
                # Crear entrada
                entry = CacheEntry(
                    value=compressed_value,
                    expires=time.time() + self._get_ttl(data_type),
                    size=original_size,
                    data_type=data_type
                )
                
                # Actualizar tamaño
                old_size = 0
                if key in self._lru_cache:
                    old_size = self._lru_cache[key]
                    self._current_size -= old_size
                
                self._current_size += original_size
                self._lru_cache[key] = original_size
                self._lru_cache.move_to_end(key)
                
                # Aplicar límite de tamaño
                self._enforce_size_limit()
                
                # Guardar entrada
                with open(cache_path, 'w') as f:
                    json.dump(entry.to_dict(), f)
                
                self._stats["current_size"] = self._current_size
                self._stats["entries"] = len(self._lru_cache)
                    
            except (OSError, TypeError) as e:
                logger.error(f"Error escribiendo caché para clave {key}: {e}")

    def delete(self, key: str) -> None:
        """Elimina una entrada del caché.
        
        Args:
            key: Clave de caché a eliminar
        """
        cache_path = self._get_cache_path(key)
        
        with self._lock:
            try:
                if key in self._lru_cache:
                    self._current_size -= self._lru_cache[key]
                    del self._lru_cache[key]
                cache_path.unlink()
                self._stats["current_size"] = self._current_size
                self._stats["entries"] = len(self._lru_cache)
            except OSError:
                pass

    def clear(self) -> None:
        """Limpia todas las entradas del caché."""
        with self._lock:
            for cache_file in self._cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except OSError:
                    pass
            self._lru_cache.clear()
            self._current_size = 0
            self._stats = {
                "hits": 0,
                "misses": 0,
                "evictions": 0,
                "compression_savings": 0,
                "current_size": 0,
                "entries": 0
            }

    def get_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas del caché.
        
        Returns:
            Dict con conteos de hits/misses/evictions y métricas de tamaño
        """
        with self._lock:
            stats = self._stats.copy()
            stats["memory_usage"] = sys.getsizeof(self._lru_cache)
            return stats
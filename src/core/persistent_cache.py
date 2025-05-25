#!/usr/bin/env python3
"""
💾 PERSISTENT CACHE - NUEVA BIBLIOTECA v2.0
==========================================
Cache persistente para respuestas de APIs musicales
"""

import os
import json
import time
import hashlib
import threading
from pathlib import Path
from typing import Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)

class PersistentCache:
    """
    Cache persistente con TTL (Time To Live) para respuestas de APIs.
    Almacena datos en archivos JSON en disco.
    """
    
    def __init__(self, cache_dir: Path, default_ttl: int = 3600):
        """
        Inicializar el cache persistente.
        
        Args:
            cache_dir: Directorio donde almacenar archivos de cache
            default_ttl: Tiempo de vida por defecto en segundos (1 hora)
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.lock = threading.Lock()
        
        # Crear directorio de cache si no existe
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivo de metadatos para tracking de TTL
        self.metadata_file = self.cache_dir / "_cache_metadata.json"
        self.metadata = self._load_metadata()
        
    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Cargar metadatos de cache desde disco."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading cache metadata: {e}")
        
        return {}
        
    def _save_metadata(self) -> None:
        """Guardar metadatos de cache a disco."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving cache metadata: {e}")
            
    def _get_cache_key_hash(self, key: str) -> str:
        """
        Generar hash seguro para usar como nombre de archivo.
        
        Args:
            key: Clave original del cache
            
        Returns:
            Hash MD5 de la clave
        """
        return hashlib.md5(key.encode('utf-8')).hexdigest()
        
    def _get_cache_file_path(self, key: str) -> Path:
        """
        Obtener ruta del archivo de cache para una clave.
        
        Args:
            key: Clave del cache
            
        Returns:
            Path del archivo de cache
        """
        key_hash = self._get_cache_key_hash(key)
        return self.cache_dir / f"{key_hash}.json"
        
    def _is_expired(self, key: str) -> bool:
        """
        Verificar si una entrada de cache ha expirado.
        
        Args:
            key: Clave del cache
            
        Returns:
            True si ha expirado, False si no
        """
        if key not in self.metadata:
            return True
            
        metadata = self.metadata[key]
        created_at = metadata.get('created_at', 0)
        ttl = metadata.get('ttl', self.default_ttl)
        
        return (time.time() - created_at) > ttl
        
    def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor del cache.
        
        Args:
            key: Clave del cache
            
        Returns:
            Valor almacenado o None si no existe o ha expirado
        """
        with self.lock:
            # Verificar si la entrada ha expirado
            if self._is_expired(key):
                self.delete(key)
                return None
                
            # Intentar cargar el archivo
            cache_file = self._get_cache_file_path(key)
            
            try:
                if cache_file.exists():
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        logger.debug(f"Cache hit for key: {key}")
                        return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error reading cache file for key {key}: {e}")
                self.delete(key)
                
            return None
            
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Almacenar valor en el cache.
        
        Args:
            key: Clave del cache
            value: Valor a almacenar (debe ser serializable a JSON)
            ttl: Tiempo de vida en segundos (None = usar default)
            
        Returns:
            True si se almacenó exitosamente, False si no
        """
        if ttl is None:
            ttl = self.default_ttl
            
        with self.lock:
            try:
                # Guardar datos en archivo
                cache_file = self._get_cache_file_path(key)
                
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(value, f, indent=2, ensure_ascii=False)
                
                # Actualizar metadatos
                self.metadata[key] = {
                    'created_at': time.time(),
                    'ttl': ttl,
                    'file_path': str(cache_file),
                    'size_bytes': cache_file.stat().st_size
                }
                
                self._save_metadata()
                logger.debug(f"Cache set for key: {key}")
                return True
                
            except (json.JSONEncodeError, IOError) as e:
                logger.error(f"Error writing cache file for key {key}: {e}")
                return False
                
    def delete(self, key: str) -> bool:
        """
        Eliminar entrada del cache.
        
        Args:
            key: Clave del cache
            
        Returns:
            True si se eliminó exitosamente, False si no existía
        """
        with self.lock:
            cache_file = self._get_cache_file_path(key)
            
            # Eliminar archivo si existe
            if cache_file.exists():
                try:
                    cache_file.unlink()
                except OSError as e:
                    logger.error(f"Error deleting cache file for key {key}: {e}")
                    return False
                    
            # Eliminar de metadatos
            if key in self.metadata:
                del self.metadata[key]
                self._save_metadata()
                
            logger.debug(f"Cache deleted for key: {key}")
            return True
            
    def clear(self) -> int:
        """
        Limpiar todo el cache.
        
        Returns:
            Número de entradas eliminadas
        """
        with self.lock:
            count = 0
            
            # Eliminar todos los archivos de cache
            for cache_file in self.cache_dir.glob("*.json"):
                if cache_file.name != "_cache_metadata.json":
                    try:
                        cache_file.unlink()
                        count += 1
                    except OSError as e:
                        logger.error(f"Error deleting cache file {cache_file}: {e}")
                        
            # Limpiar metadatos
            self.metadata.clear()
            self._save_metadata()
            
            logger.info(f"Cache cleared: {count} entries deleted")
            return count
            
    def cleanup_expired(self) -> int:
        """
        Limpiar entradas expiradas del cache.
        
        Returns:
            Número de entradas eliminadas
        """
        with self.lock:
            expired_keys = []
            
            # Identificar claves expiradas
            for key in list(self.metadata.keys()):
                if self._is_expired(key):
                    expired_keys.append(key)
                    
            # Eliminar entradas expiradas
            for key in expired_keys:
                self.delete(key)
                
            logger.info(f"Cache cleanup: {len(expired_keys)} expired entries deleted")
            return len(expired_keys)
            
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del cache.
        
        Returns:
            Diccionario con estadísticas
        """
        with self.lock:
            total_entries = len(self.metadata)
            total_size = sum(
                meta.get('size_bytes', 0) 
                for meta in self.metadata.values()
            )
            
            # Contar entradas expiradas
            expired_count = sum(
                1 for key in self.metadata.keys() 
                if self._is_expired(key)
            )
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_count,
                'active_entries': total_entries - expired_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_directory': str(self.cache_dir),
                'default_ttl': self.default_ttl
            }
            
    def exists(self, key: str) -> bool:
        """
        Verificar si una clave existe y no ha expirado.
        
        Args:
            key: Clave del cache
            
        Returns:
            True si existe y es válida, False si no
        """
        with self.lock:
            return not self._is_expired(key)
            
    def get_keys(self) -> list:
        """
        Obtener lista de todas las claves activas (no expiradas).
        
        Returns:
            Lista de claves activas
        """
        with self.lock:
            return [
                key for key in self.metadata.keys() 
                if not self._is_expired(key)
            ]
            
    def set_ttl(self, key: str, ttl: int) -> bool:
        """
        Actualizar TTL de una entrada existente.
        
        Args:
            key: Clave del cache
            ttl: Nuevo tiempo de vida en segundos
            
        Returns:
            True si se actualizó exitosamente, False si no existe
        """
        with self.lock:
            if key in self.metadata and not self._is_expired(key):
                self.metadata[key]['ttl'] = ttl
                self._save_metadata()
                return True
            return False
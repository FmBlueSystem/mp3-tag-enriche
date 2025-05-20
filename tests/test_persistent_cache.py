"""Pruebas unitarias para el sistema de caché persistente."""
import os
import time
import pytest
from pathlib import Path
from src.core.persistent_cache import PersistentCache

@pytest.fixture
def cache_dir(tmp_path):
    """Fixture que proporciona un directorio temporal para las pruebas."""
    cache_path = tmp_path / "test_cache"
    return str(cache_path)

@pytest.fixture
def cache(cache_dir):
    """Fixture que proporciona una instancia de caché para las pruebas."""
    ttl_policy = {
        "api_response": 7200,  # 2 horas
        "metadata": 86400,     # 24 horas
        "thumbnails": 3600     # 1 hora
    }
    return PersistentCache(
        cache_dir=cache_dir,
        default_ttl=3600,
        max_size_bytes=5 * 1024 * 1024,  # 5MB
        compression_threshold=512,
        ttl_policy=ttl_policy
    )

def test_basic_cache_operations(cache):
    """Prueba operaciones básicas del caché."""
    # Prueba set/get
    cache.set("test_key", "test_value")
    assert cache.get("test_key") == "test_value"
    
    # Prueba delete
    cache.delete("test_key")
    assert cache.get("test_key") is None

def test_ttl_expiration(cache):
    """Prueba la expiración por TTL."""
    # Configurar TTL corto para la prueba
    cache._default_ttl = 1
    
    cache.set("expire_key", "expire_value")
    assert cache.get("expire_key") == "expire_value"
    
    # Esperar a que expire
    time.sleep(1.1)
    assert cache.get("expire_key") is None

def test_ttl_policy(cache):
    """Prueba políticas de TTL por tipo de dato."""
    # Guardar con diferentes tipos
    cache.set("api_key", "api_data", "api_response")
    cache.set("meta_key", "meta_data", "metadata")
    
    # Verificar que los datos persisten según su política
    assert cache.get("api_key") == "api_data"
    assert cache.get("meta_key") == "meta_data"

def test_size_limit_and_lru(cache):
    """Prueba límites de tamaño y política LRU."""
    # Configurar límite pequeño para la prueba
    cache._max_size_bytes = 1024  # 1KB
    
    # Añadir datos hasta superar el límite
    large_data = "x" * 512  # 512 bytes
    cache.set("data1", large_data)
    cache.set("data2", large_data)
    cache.set("data3", large_data)
    
    # El dato más antiguo debería ser eliminado
    assert cache.get("data1") is None
    assert cache.get("data2") == large_data
    assert cache.get("data3") == large_data

def test_compression(cache):
    """Prueba compresión de datos."""
    # Datos que superan el umbral de compresión
    large_data = "test_data" * 100
    cache.set("compressed_key", large_data)
    
    # Verificar que los datos se recuperan correctamente
    assert cache.get("compressed_key") == large_data
    
    # Verificar que hubo ahorro por compresión
    stats = cache.get_stats()
    assert stats["compression_savings"] > 0

def test_stats_tracking(cache):
    """Prueba seguimiento de estadísticas."""
    # Generar algunas operaciones
    cache.set("stats_key1", "value1")
    cache.set("stats_key2", "value2")
    cache.get("stats_key1")
    cache.get("nonexistent_key")
    
    # Verificar estadísticas
    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["entries"] == 2
    assert stats["current_size"] > 0

def test_concurrent_access(cache):
    """Prueba acceso concurrente al caché."""
    from concurrent.futures import ThreadPoolExecutor
    import random
    import string
    
    def random_string(length):
        return ''.join(random.choices(string.ascii_letters, k=length))
    
    def worker():
        key = random_string(10)
        value = random_string(100)
        cache.set(key, value)
        assert cache.get(key) == value
        cache.delete(key)
        assert cache.get(key) is None
    
    # Ejecutar operaciones concurrentes
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(worker) for _ in range(10)]
        for future in futures:
            future.result()

def test_cache_persistence(cache_dir):
    """Prueba persistencia del caché entre reinicios."""
    # Crear primera instancia y guardar datos
    cache1 = PersistentCache(cache_dir)
    cache1.set("persist_key", "persist_value")
    
    # Crear nueva instancia y verificar datos
    cache2 = PersistentCache(cache_dir)
    assert cache2.get("persist_key") == "persist_value"

def test_invalid_data_handling(cache):
    """Prueba manejo de datos inválidos."""
    # Intentar guardar tipos no serializables
    with pytest.raises(TypeError):
        cache.set("invalid_key", lambda x: x)
    
    # Crear archivo de caché corrupto
    cache_path = Path(cache._cache_dir) / "corrupt.json"
    cache_path.write_text("invalid json")
    
    # Verificar que se maneja correctamente
    assert cache.get("corrupt") is None

# Nuevas pruebas añadidas para mejorar cobertura

def test_edge_cases(cache):
    """Prueba casos límite."""
    # Clave muy larga
    long_key = "x" * 1000
    cache.set(long_key, "value")
    assert cache.get(long_key) == "value"
    
    # Valor nulo
    cache.set("null_key", None)
    assert cache.get("null_key") is None
    
    # Valor muy grande (cercano al límite)
    large_value = "x" * (5 * 1024 * 1024 - 1000)  # Casi 5MB
    cache.set("large_key", large_value)
    assert cache.get("large_key") == large_value

def test_ttl_edge_cases(cache):
    """Prueba casos límite de TTL."""
    # TTL de 0 (expiración inmediata)
    cache.set("zero_ttl", "value", ttl=0)
    assert cache.get("zero_ttl") is None
    
    # TTL negativo (debería usar el default)
    cache.set("negative_ttl", "value", ttl=-1)
    assert cache.get("negative_ttl") == "value"
    
    # TTL muy grande
    cache.set("large_ttl", "value", ttl=1000000000)
    assert cache.get("large_ttl") == "value"

def test_error_recovery(cache, cache_dir):
    """Prueba recuperación de errores."""
    # Simular error de permisos
    os.chmod(cache_dir, 0o000)
    try:
        with pytest.raises(IOError):
            cache.set("permission_key", "value")
    finally:
        os.chmod(cache_dir, 0o755)
    
    # Simular archivo corrupto con JSON parcial
    cache_file = Path(cache._cache_dir) / "partial.json"
    cache_file.write_text('{"key": "value", "corrupted')
    assert cache.get("partial") is None
    
    # Simular error de espacio en disco
    huge_value = "x" * (cache._max_size_bytes + 1)
    with pytest.raises(ValueError):
        cache.set("huge_key", huge_value)

def test_cleanup_policy(cache):
    """Prueba políticas de limpieza."""
    # Llenar el caché hasta el límite
    small_data = "x" * 100
    for i in range(100):
        cache.set(f"key_{i}", small_data)
    
    # Verificar que se eliminaron las entradas más antiguas
    assert cache.get("key_0") is None
    
    # Verificar que las entradas más recientes permanecen
    assert cache.get(f"key_99") == small_data
    
    # Forzar limpieza explícita
    cache.cleanup()
    stats = cache.get_stats()
    assert stats["current_size"] <= cache._max_size_bytes

def test_concurrent_error_handling(cache):
    """Prueba manejo de errores concurrentes."""
    from concurrent.futures import ThreadPoolExecutor
    
    def error_worker():
        try:
            # Intentar operaciones que pueden fallar
            cache.set(None, "value")
            cache.get(None)
            cache.delete(None)
        except Exception as e:
            assert isinstance(e, (TypeError, ValueError))
    
    # Ejecutar operaciones de error concurrentemente
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(error_worker) for _ in range(5)]
        for future in futures:
            future.result()
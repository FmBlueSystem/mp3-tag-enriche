#!/usr/bin/env python3
"""
🚀 CLIENTE API MEJORADO - PREVENCIÓN DE CONGELAMIENTO
=====================================================

Cliente optimizado que resuelve los problemas identificados en las APIs:
- Gestión agresiva de conexiones HTTP
- Rate limiting simplificado y eficiente  
- Supresión de logs verbosos
- Context managers para gestión de recursos
- Timeouts estrictos y cleanup automático
"""

import os
import sys
import time
import logging
import gc
from contextlib import contextmanager
from typing import Dict, Any, Optional, List
from threading import Lock
from dataclasses import dataclass

# Suprimir logs problemáticos ANTES de importar las APIs
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('musicbrainzngs').setLevel(logging.ERROR)
logging.getLogger('musicbrainzngs.musicbrainzngs').setLevel(logging.ERROR)
logging.getLogger('mutagen').setLevel(logging.WARNING)
logging.getLogger('spotipy').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

# Agregar directorio del proyecto
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)

logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """Configuración para una API específica."""
    rate_limit: float = 1.0  # Llamadas por segundo
    timeout: int = 15        # Timeout en segundos
    max_retries: int = 2     # Máximo reintentos
    suppress_logs: bool = True

class SimpleRateLimiter:
    """Rate limiter simple y eficiente sin locks complejos."""
    
    def __init__(self, calls_per_second: float = 1.0):
        self.min_interval = 1.0 / calls_per_second
        self.last_called = 0
        self._lock = Lock()
    
    def wait_if_needed(self):
        """Esperar si es necesario para respetar el rate limit."""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_called
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                time.sleep(sleep_time)
            self.last_called = time.time()

class ImprovedHTTPSession:
    """Sesión HTTP mejorada con gestión automática de recursos."""
    
    def __init__(self, timeout: int = 15):
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configurar reintentos más agresivos
        retry_strategy = Retry(
            total=2,  # Solo 2 reintentos
            backoff_factor=0.3,  # Backoff más rápido
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'])
        )
        
        # Configurar adaptador con pool pequeño
        adapter = HTTPAdapter(
            pool_connections=2,   # Solo 2 pools
            pool_maxsize=5,      # Máximo 5 conexiones por pool
            max_retries=retry_strategy
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def request(self, *args, **kwargs):
        """Realizar request con timeout garantizado."""
        kwargs.setdefault('timeout', self.timeout)
        return self.session.request(*args, **kwargs)
    
    def close(self):
        """Cerrar sesión y limpiar recursos."""
        if hasattr(self, 'session') and self.session:
            self.session.close()
    
    def __del__(self):
        """Asegurar cierre al destruir objeto."""
        self.close()

class SafeAPIWrapper:
    """Wrapper seguro para llamadas API con gestión de recursos."""
    
    def __init__(self, api_instance, config: APIConfig):
        self.api = api_instance
        self.config = config
        self.rate_limiter = SimpleRateLimiter(config.rate_limit)
        self.http_session = ImprovedHTTPSession(config.timeout)
        
        # Inyectar nuestra sesión HTTP si es posible
        if hasattr(api_instance, 'session'):
            api_instance.session.close()  # Cerrar sesión anterior
            api_instance.session = self.http_session.session
        elif hasattr(api_instance, 'http_client'):
            if hasattr(api_instance.http_client, 'session'):
                api_instance.http_client.session.close()
                api_instance.http_client.session = self.http_session.session
    
    def safe_call(self, method_name: str, *args, **kwargs):
        """Llamada segura con rate limiting y cleanup."""
        # Rate limiting antes de la llamada
        self.rate_limiter.wait_if_needed()
        
        # Obtener método del API
        method = getattr(self.api, method_name)
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Timeout con signal (solo en Unix)
                if hasattr(os, 'fork'):  # Unix-like systems
                    import signal
                    
                    def timeout_handler(signum, frame):
                        raise TimeoutError(f"API call timeout after {self.config.timeout}s")
                    
                    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(self.config.timeout)
                    
                    try:
                        result = method(*args, **kwargs)
                        # Limpiar memoria inmediatamente
                        gc.collect()
                        return result
                    finally:
                        signal.alarm(0)
                        signal.signal(signal.SIGALRM, old_handler)
                else:
                    # Fallback para sistemas sin signal
                    result = method(*args, **kwargs)
                    gc.collect()
                    return result
                    
            except Exception as e:
                if attempt == self.config.max_retries:
                    logger.error(f"API call {method_name} failed after {self.config.max_retries + 1} attempts: {e}")
                    return self._get_empty_result()
                
                # Backoff exponencial
                wait_time = 0.5 * (2 ** attempt)
                time.sleep(wait_time)
        
        return self._get_empty_result()
    
    def _get_empty_result(self):
        """Resultado vacío estándar para APIs."""
        return {
            "genres": [],
            "year": None,
            "album": None,
            "source_api": self.api.__class__.__name__
        }
    
    def close(self):
        """Cerrar recursos."""
        self.http_session.close()
        
        # Cerrar recursos del API si tiene método close
        if hasattr(self.api, 'close'):
            self.api.close()
    
    def __del__(self):
        """Cleanup al destruir."""
        self.close()

class ImprovedAPIManager:
    """Gestor de APIs mejorado con configuración optimizada."""
    
    def __init__(self):
        # Configuración optimizada para evitar congelamiento
        self.api_configs = {
            'MusicBrainzAPI': APIConfig(
                rate_limit=0.5,      # 1 llamada cada 2 segundos
                timeout=15,
                max_retries=1,
                suppress_logs=True
            ),
            'DiscogsAPI': APIConfig(
                rate_limit=1.0,      # 1 llamada por segundo
                timeout=20,
                max_retries=2,
                suppress_logs=True
            ),
            'SpotifyAPI': APIConfig(
                rate_limit=1.0,      # 1 llamada por segundo
                timeout=10,
                max_retries=2,
                suppress_logs=True
            ),
            'LastFmAPI': APIConfig(
                rate_limit=0.5,      # 1 llamada cada 2 segundos
                timeout=15,
                max_retries=1,
                suppress_logs=True
            )
        }
        
        self.safe_apis: Dict[str, SafeAPIWrapper] = {}
        self.initialized = False
    
    @contextmanager
    def managed_api_session(self):
        """Context manager para gestión automática de APIs."""
        try:
            yield self
        finally:
            self.close_all()
    
    def initialize_api(self, api_class, **kwargs):
        """Inicializar una API con wrapper seguro."""
        api_name = api_class.__name__
        config = self.api_configs.get(api_name, APIConfig())
        
        try:
            # Crear instancia del API
            api_instance = api_class(**kwargs)
            
            # Envolver en SafeAPIWrapper
            safe_api = SafeAPIWrapper(api_instance, config)
            self.safe_apis[api_name] = safe_api
            
            logger.info(f"✅ {api_name} inicializada con config: rate_limit={config.rate_limit}, timeout={config.timeout}")
            return safe_api
            
        except Exception as e:
            logger.error(f"❌ Error inicializando {api_name}: {e}")
            return None
    
    def get_track_info_safe(self, api_name: str, artist: str, track: str) -> Dict[str, Any]:
        """Obtener información de track de forma segura."""
        safe_api = self.safe_apis.get(api_name)
        if not safe_api:
            logger.warning(f"API {api_name} no disponible")
            return {
                "genres": [],
                "year": None,
                "album": None,
                "source_api": api_name,
                "error": "API no disponible"
            }
        
        return safe_api.safe_call('get_track_info', artist, track)
    
    def close_all(self):
        """Cerrar todas las APIs y limpiar recursos."""
        logger.info("🧹 Cerrando todas las APIs y limpiando recursos...")
        
        for api_name, safe_api in self.safe_apis.items():
            try:
                safe_api.close()
                logger.debug(f"✅ {api_name} cerrada")
            except Exception as e:
                logger.error(f"❌ Error cerrando {api_name}: {e}")
        
        self.safe_apis.clear()
        
        # Forzar garbage collection
        gc.collect()

def create_improved_apis():
    """Crear APIs mejoradas con configuración optimizada."""
    from src.core.music_apis import MusicBrainzAPI, LastFmAPI, DiscogsAPI
    
    manager = ImprovedAPIManager()
    
    # Inicializar APIs una por una con manejo de errores
    apis_to_init = [
        (MusicBrainzAPI, {'email': 'user@example.com'}),
        (LastFmAPI, {}),
        (DiscogsAPI, {})
    ]
    
    # Intentar Spotify si está disponible
    try:
        from src.core.spotify_api import SpotifyAPI
        apis_to_init.append((SpotifyAPI, {}))
    except ImportError:
        logger.info("Spotify API no disponible")
    
    for api_class, kwargs in apis_to_init:
        manager.initialize_api(api_class, **kwargs)
    
    return manager

def test_improved_apis():
    """Probar las APIs mejoradas."""
    logger.info("🧪 Probando APIs mejoradas...")
    
    with create_improved_apis().managed_api_session() as manager:
        # Prueba con un artista conocido
        test_cases = [
            ("Queen", "Bohemian Rhapsody"),
            ("The Beatles", "Hey Jude"),
            ("Madonna", "Like a Virgin")
        ]
        
        for artist, track in test_cases:
            logger.info(f"\n🎵 Probando: {artist} - {track}")
            
            for api_name in manager.safe_apis.keys():
                try:
                    result = manager.get_track_info_safe(api_name, artist, track)
                    genres = result.get('genres', [])
                    year = result.get('year')
                    logger.info(f"   {api_name}: {len(genres)} géneros, año: {year}")
                except Exception as e:
                    logger.error(f"   {api_name}: Error - {e}")
            
            # Pequeña pausa entre pruebas
            time.sleep(1)

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_improved_apis() 
#!/usr/bin/env python3
"""
⚙️ API CONFIGURATION - NUEVA BIBLIOTECA v2.0
===========================================
Configuración centralizada para APIs musicales
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class APIConfig:
    """Configuración para una API específica."""
    enabled: bool = True
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    rate_limit_capacity: int = 5
    rate_limit_fill_rate: float = 1.0
    timeout: int = 30
    max_retries: int = 3
    cache_ttl: int = 3600  # 1 hora
    priority: int = 1  # 1 = alta, 5 = baja

class MusicAPIConfiguration:
    """
    Configuración centralizada para todas las APIs musicales.
    Maneja claves de API, límites de velocidad y configuraciones.
    """
    
    # Configuraciones por defecto para cada API
    DEFAULT_CONFIGS = {
        'musicbrainz': APIConfig(
            enabled=True,
            rate_limit_capacity=1,
            rate_limit_fill_rate=0.5,
            timeout=30,
            max_retries=3,
            cache_ttl=7200,  # 2 horas
            priority=1
        ),
        'lastfm': APIConfig(
            enabled=True,
            api_key=os.getenv('LASTFM_API_KEY', 'b7651b3758d74bd0f47df535a5ddf45d'),
            api_secret=os.getenv('LASTFM_API_SECRET', 'eb38d3f09f394d652c93d948972a3285'),
            rate_limit_capacity=10,
            rate_limit_fill_rate=5.0,
            timeout=20,
            max_retries=3,
            cache_ttl=3600,  # 1 hora
            priority=2
        ),
        'discogs': APIConfig(
            enabled=True,
            api_key=os.getenv('DISCOGS_API_TOKEN', 'pTWfxAgLTSTbXzbNFvAvqXNKawGiDVELrBLnfoNv'),
            base_url='https://api.discogs.com/',
            rate_limit_capacity=5,
            rate_limit_fill_rate=1.0,
            timeout=25,
            max_retries=3,
            cache_ttl=3600,  # 1 hora
            priority=3
        ),
        'wikipedia': APIConfig(
            enabled=True,
            base_url='https://en.wikipedia.org/w/api.php',
            rate_limit_capacity=10,
            rate_limit_fill_rate=2.0,
            timeout=20,
            max_retries=2,
            cache_ttl=7200,  # 2 horas
            priority=4
        ),
        'itunes': APIConfig(
            enabled=True,
            base_url='https://itunes.apple.com/search',
            rate_limit_capacity=5,
            rate_limit_fill_rate=0.33,
            timeout=15,
            max_retries=2,
            cache_ttl=3600,  # 1 hora
            priority=5
        ),
        'acousticbrainz': APIConfig(
            enabled=False,  # Deshabilitado por defecto (requiere MBID)
            base_url='https://acousticbrainz.org/api/v1/',
            rate_limit_capacity=5,
            rate_limit_fill_rate=1.0,
            timeout=20,
            max_retries=2,
            cache_ttl=7200,  # 2 horas
            priority=6
        )
    }
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Inicializar configuración de APIs.
        
        Args:
            config_file: Archivo de configuración personalizado (opcional)
        """
        self.configs = self.DEFAULT_CONFIGS.copy()
        
        # Cargar configuración personalizada si existe
        if config_file and config_file.exists():
            self._load_config_file(config_file)
            
        # Aplicar variables de entorno
        self._apply_env_overrides()
        
    def _load_config_file(self, config_file: Path) -> None:
        """Cargar configuración desde archivo JSON/YAML."""
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                custom_config = json.load(f)
                
            for api_name, config_data in custom_config.items():
                if api_name in self.configs:
                    # Actualizar configuración existente
                    for key, value in config_data.items():
                        if hasattr(self.configs[api_name], key):
                            setattr(self.configs[api_name], key, value)
                            
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
            
    def _apply_env_overrides(self) -> None:
        """Aplicar overrides desde variables de entorno."""
        env_mappings = {
            'MUSICBRAINZ_ENABLED': ('musicbrainz', 'enabled', bool),
            'LASTFM_API_KEY': ('lastfm', 'api_key', str),
            'LASTFM_API_SECRET': ('lastfm', 'api_secret', str),
            'LASTFM_ENABLED': ('lastfm', 'enabled', bool),
            'DISCOGS_API_TOKEN': ('discogs', 'api_key', str),
            'DISCOGS_ENABLED': ('discogs', 'enabled', bool),
            'WIKIPEDIA_ENABLED': ('wikipedia', 'enabled', bool),
            'ITUNES_ENABLED': ('itunes', 'enabled', bool),
            'ACOUSTICBRAINZ_ENABLED': ('acousticbrainz', 'enabled', bool),
        }
        
        for env_var, (api_name, attr_name, type_func) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    if type_func == bool:
                        value = env_value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        value = type_func(env_value)
                    setattr(self.configs[api_name], attr_name, value)
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid value for {env_var}: {e}")
                    
    def get_config(self, api_name: str) -> APIConfig:
        """
        Obtener configuración para una API específica.
        
        Args:
            api_name: Nombre de la API
            
        Returns:
            Configuración de la API
        """
        return self.configs.get(api_name, APIConfig())
        
    def get_enabled_apis(self) -> Dict[str, APIConfig]:
        """
        Obtener solo las APIs habilitadas.
        
        Returns:
            Diccionario con APIs habilitadas
        """
        return {
            name: config for name, config in self.configs.items()
            if config.enabled
        }
        
    def get_apis_by_priority(self) -> list:
        """
        Obtener APIs ordenadas por prioridad.
        
        Returns:
            Lista de tuplas (nombre, config) ordenadas por prioridad
        """
        enabled_apis = self.get_enabled_apis()
        return sorted(
            enabled_apis.items(),
            key=lambda x: x[1].priority
        )
        
    def disable_api(self, api_name: str) -> None:
        """
        Deshabilitar una API específica.
        
        Args:
            api_name: Nombre de la API a deshabilitar
        """
        if api_name in self.configs:
            self.configs[api_name].enabled = False
            
    def enable_api(self, api_name: str) -> None:
        """
        Habilitar una API específica.
        
        Args:
            api_name: Nombre de la API a habilitar
        """
        if api_name in self.configs:
            self.configs[api_name].enabled = True
            
    def update_api_config(self, api_name: str, **kwargs) -> None:
        """
        Actualizar configuración de una API.
        
        Args:
            api_name: Nombre de la API
            **kwargs: Parámetros de configuración a actualizar
        """
        if api_name in self.configs:
            for key, value in kwargs.items():
                if hasattr(self.configs[api_name], key):
                    setattr(self.configs[api_name], key, value)
                    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de configuración.
        
        Returns:
            Diccionario con estadísticas
        """
        enabled_count = len(self.get_enabled_apis())
        total_count = len(self.configs)
        
        return {
            'total_apis': total_count,
            'enabled_apis': enabled_count,
            'disabled_apis': total_count - enabled_count,
            'apis_by_priority': [name for name, _ in self.get_apis_by_priority()],
            'config_summary': {
                name: {
                    'enabled': config.enabled,
                    'priority': config.priority,
                    'has_api_key': bool(config.api_key)
                }
                for name, config in self.configs.items()
            }
        }

# Instancia global de configuración
_global_config = MusicAPIConfiguration()

def get_api_config(api_name: str) -> APIConfig:
    """Función de conveniencia para obtener configuración de API."""
    return _global_config.get_config(api_name)

def get_enabled_apis() -> Dict[str, APIConfig]:
    """Función de conveniencia para obtener APIs habilitadas."""
    return _global_config.get_enabled_apis()

def get_apis_by_priority() -> list:
    """Función de conveniencia para obtener APIs por prioridad."""
    return _global_config.get_apis_by_priority() 
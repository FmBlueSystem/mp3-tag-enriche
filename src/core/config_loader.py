"""
Módulo de configuración mejorada para parámetros dinámicos del sistema.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default configuration file paths
CONFIG_PATHS = [
    "config/api_keys.json",
    os.path.expanduser("~/.genredetector/api_keys.json"),
    "/etc/genredetector/api_keys.json"
]

class DynamicConfig:
    """Gestor de configuración dinámica para el sistema de detección de géneros."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/dynamic_settings.json"
        self.config = self._load_default_config()
        self.load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Carga la configuración por defecto del sistema."""
        return {
            "genre_detection": {
                "base_threshold": 0.3,
                "dynamic_threshold": True,
                "min_threshold": 0.1,
                "max_threshold": 0.8,
                "fallback_enabled": True,
                "require_multiple_sources": False
            },
            "processing": {
                "max_retries": 3,
                "api_timeout": 30,
                "parallel_workers": 4,
                "circuit_breaker_threshold": 5
            },
            "cache": {
                "max_age_days": 30,
                "cleanup_interval_hours": 24,
                "max_cache_size_mb": 100
            },
            "ui": {
                "auto_refresh_interval": 1000,
                "max_table_rows": 1000,
                "enable_debug_mode": False
            }
        }
    
    def load_config(self) -> None:
        """Carga configuración desde archivo si existe."""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                self._merge_config(file_config)
                logger.info(f"Configuración cargada desde {self.config_file}")
        except Exception as e:
            logger.warning(f"Error cargando configuración: {e}, usando valores por defecto")
    
    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """Fusiona configuración nueva con la existente."""
        for section, values in new_config.items():
            if section in self.config:
                self.config[section].update(values)
            else:
                self.config[section] = values
    
    def get_dynamic_threshold(self, api_count: int, confidence_spread: float) -> float:
        """
        Calcula umbral dinámico basado en calidad de datos disponibles.
        
        Args:
            api_count: Número de APIs que respondieron
            confidence_spread: Dispersión en las puntuaciones de confianza
            
        Returns:
            Umbral ajustado dinámicamente
        """
        if not self.config["genre_detection"]["dynamic_threshold"]:
            return self.config["genre_detection"]["base_threshold"]
        
        base = self.config["genre_detection"]["base_threshold"]
        min_thresh = self.config["genre_detection"]["min_threshold"]
        max_thresh = self.config["genre_detection"]["max_threshold"]
        
        # Ajustar basado en número de fuentes
        if api_count >= 3:
            # Muchas fuentes -> umbral más bajo
            threshold = base * 0.8
        elif api_count == 2:
            # Fuentes moderadas -> umbral normal
            threshold = base
        else:
            # Pocas fuentes -> umbral más alto
            threshold = base * 1.2
        
        # Ajustar basado en dispersión de confianza
        if confidence_spread > 0.5:
            # Alta dispersión -> ser más conservador
            threshold += 0.1
        elif confidence_spread < 0.2:
            # Baja dispersión -> ser más permisivo
            threshold -= 0.1
        
        # Aplicar límites
        threshold = max(min_thresh, min(max_thresh, threshold))
        
        logger.debug(f"Umbral dinámico calculado: {threshold} (APIs: {api_count}, dispersión: {confidence_spread})")
        return threshold
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración."""
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value: Any) -> None:
        """Establece un valor de configuración."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def save_config(self) -> None:
        """Guarda la configuración actual a archivo."""
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuración guardada en {self.config_file}")
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")

# Instancia global de configuración
config = DynamicConfig()

def load_api_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load API configuration from the specified path or predefined paths.
    
    Args:
        config_path: Path to the configuration file (optional)
        
    Returns:
        Dictionary containing the API configuration
    """
    # Check explicit path first
    if config_path and os.path.exists(config_path):
        return _load_config_file(config_path)
    
    # Try predefined paths
    for path in CONFIG_PATHS:
        if os.path.exists(path):
            return _load_config_file(path)
    
    # No configuration found, return empty dictionary
    return {
        "spotify": {},
        "lastfm": {},
        "discogs": {},
        "musicbrainz": {}
    }

def _load_config_file(path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file.
    
    Args:
        path: Path to the configuration file
        
    Returns:
        Dictionary containing the configuration
    """
    try:
        with open(path, 'r') as f:
            config = json.load(f)
        return config
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading configuration from {path}: {e}")
        return {
            "spotify": {},
            "lastfm": {},
            "discogs": {},
            "musicbrainz": {}
        }

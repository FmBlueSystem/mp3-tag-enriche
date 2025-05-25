#!/usr/bin/env python3
"""
⚙️ CONFIGURATION MODULE - NUEVA BIBLIOTECA v2.0
===============================================
Módulo de configuración para Nueva Biblioteca
"""

from .api_config import (
    APIConfig,
    MusicAPIConfiguration,
    get_api_config,
    get_enabled_apis,
    get_apis_by_priority
)

__all__ = [
    'APIConfig',
    'MusicAPIConfiguration',
    'get_api_config',
    'get_enabled_apis',
    'get_apis_by_priority'
] 
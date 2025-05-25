"""
Módulos de extracción y enriquecimiento de metadatos.
"""

from .extractor import MetadataExtractor
from .enricher import MetadataEnricher

__all__ = [
    'MetadataExtractor',
    'MetadataEnricher',
]
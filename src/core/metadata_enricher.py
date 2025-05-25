#!/usr/bin/env python3
"""
🎵 METADATA ENRICHER - NUEVA BIBLIOTECA v2.0
===========================================
Enriquecimiento inteligente de metadatos musicales usando múltiples APIs
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from .music_apis import (
    MusicBrainzAPI, LastFmAPI, DiscogsAPI, 
    WikipediaAPI, iTunesAPI, AcousticBrainzAPI
)
from .genre_normalizer import GenreNormalizer
from .api_metrics import record_api_call, get_all_metrics
from ..config.api_config import get_enabled_apis, get_apis_by_priority

logger = logging.getLogger(__name__)

@dataclass
class EnrichmentResult:
    """Resultado del enriquecimiento de metadatos."""
    artist: str
    track: str
    genres: Dict[str, float] = field(default_factory=dict)
    year: Optional[str] = None
    album: Optional[str] = None
    confidence_score: float = 0.0
    sources_used: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir resultado a diccionario."""
        return {
            'artist': self.artist,
            'track': self.track,
            'genres': self.genres,
            'year': self.year,
            'album': self.album,
            'confidence_score': self.confidence_score,
            'sources_used': self.sources_used,
            'processing_time': self.processing_time,
            'errors': self.errors
        }

class MetadataEnricher:
    """
    Enriquecedor de metadatos musicales que consulta múltiples APIs
    y combina los resultados para obtener información completa y precisa.
    """
    
    def __init__(self, max_workers: int = 3, timeout: float = 60.0):
        """
        Inicializar el enriquecedor de metadatos.
        
        Args:
            max_workers: Número máximo de workers para consultas paralelas
            timeout: Timeout total para el enriquecimiento en segundos
        """
        self.max_workers = max_workers
        self.timeout = timeout
        
        # Inicializar APIs disponibles
        self.apis = self._initialize_apis()
        
        # Configurar executor para consultas paralelas
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        logger.info(f"MetadataEnricher initialized with {len(self.apis)} APIs")
        
    def _initialize_apis(self) -> Dict[str, Any]:
        """Inicializar instancias de APIs habilitadas."""
        apis = {}
        enabled_apis = get_enabled_apis()
        
        for api_name, config in enabled_apis.items():
            try:
                if api_name == 'musicbrainz':
                    apis[api_name] = MusicBrainzAPI()
                elif api_name == 'lastfm':
                    apis[api_name] = LastFmAPI(
                        api_key=config.api_key,
                        api_secret=config.api_secret
                    )
                elif api_name == 'discogs':
                    apis[api_name] = DiscogsAPI(api_token=config.api_key)
                elif api_name == 'wikipedia':
                    apis[api_name] = WikipediaAPI()
                elif api_name == 'itunes':
                    apis[api_name] = iTunesAPI()
                elif api_name == 'acousticbrainz':
                    apis[api_name] = AcousticBrainzAPI()
                    
                logger.debug(f"Initialized {api_name} API")
                
            except Exception as e:
                logger.error(f"Failed to initialize {api_name} API: {e}")
                
        return apis
        
    def _query_single_api(self, api_name: str, api_instance: Any, 
                         artist: str, track: str) -> Tuple[str, Dict[str, Any]]:
        """
        Consultar una sola API de forma thread-safe.
        
        Args:
            api_name: Nombre de la API
            api_instance: Instancia de la API
            artist: Nombre del artista
            track: Título de la canción
            
        Returns:
            Tupla con (nombre_api, resultado)
        """
        start_time = time.time()
        
        try:
            result = api_instance.get_track_info(artist, track)
            
            # Añadir metadatos del resultado
            result['api_name'] = api_name
            result['query_time'] = time.time() - start_time
            result['success'] = True
            
            logger.debug(f"{api_name} query completed in {result['query_time']:.2f}s")
            return api_name, result
            
        except Exception as e:
            error_msg = f"{api_name} query failed: {str(e)}"
            logger.warning(error_msg)
            
            return api_name, {
                'api_name': api_name,
                'query_time': time.time() - start_time,
                'success': False,
                'error': error_msg,
                'genres': [],
                'year': None,
                'album': None
            }
            
    def _combine_results(self, api_results: Dict[str, Dict[str, Any]]) -> EnrichmentResult:
        """
        Combinar resultados de múltiples APIs en un resultado unificado.
        
        Args:
            api_results: Diccionario con resultados de cada API
            
        Returns:
            Resultado combinado del enriquecimiento
        """
        # Extraer información básica
        artist = ""
        track = ""
        combined_genres = defaultdict(list)
        years = []
        albums = []
        sources_used = []
        errors = []
        total_time = 0.0
        
        # Procesar resultados de cada API
        for api_name, result in api_results.items():
            if result.get('success', False):
                sources_used.append(api_name)
                
                # Acumular géneros con sus fuentes
                for genre in result.get('genres', []):
                    if genre and genre.strip():
                        combined_genres[genre].append(api_name)
                        
                # Acumular años
                if result.get('year'):
                    years.append(result['year'])
                    
                # Acumular álbumes
                if result.get('album'):
                    albums.append(result['album'])
                    
            else:
                if result.get('error'):
                    errors.append(result['error'])
                    
            total_time += result.get('query_time', 0.0)
            
        # Normalizar y puntuar géneros
        normalized_genres = {}
        for genre, api_sources in combined_genres.items():
            # Normalizar género
            norm_genre, norm_confidence = GenreNormalizer.normalize(genre)
            
            # Calcular puntuación basada en:
            # 1. Número de APIs que reportan el género
            # 2. Confianza de la normalización
            # 3. Prioridad de las APIs (APIs con mayor prioridad tienen más peso)
            api_weight = len(api_sources) * 0.3  # Peso por consenso
            norm_weight = norm_confidence * 0.4   # Peso por confianza de normalización
            priority_weight = self._calculate_priority_weight(api_sources) * 0.3
            
            final_score = min(1.0, api_weight + norm_weight + priority_weight)
            
            if norm_genre in normalized_genres:
                # Si ya existe, mantener la puntuación más alta
                normalized_genres[norm_genre] = max(
                    normalized_genres[norm_genre], 
                    final_score
                )
            else:
                normalized_genres[norm_genre] = final_score
                
        # Seleccionar año más común
        selected_year = None
        if years:
            year_counts = defaultdict(int)
            for year in years:
                year_counts[year] += 1
            selected_year = max(year_counts.items(), key=lambda x: x[1])[0]
            
        # Seleccionar álbum más común
        selected_album = None
        if albums:
            album_counts = defaultdict(int)
            for album in albums:
                album_counts[album] += 1
            selected_album = max(album_counts.items(), key=lambda x: x[1])[0]
            
        # Calcular puntuación de confianza general
        confidence_score = self._calculate_confidence_score(
            len(sources_used), 
            len(normalized_genres),
            bool(selected_year),
            bool(selected_album)
        )
        
        # Obtener información básica del primer resultado exitoso
        for result in api_results.values():
            if result.get('success', False):
                artist = artist or result.get('artist', '')
                track = track or result.get('track', '')
                break
                
        return EnrichmentResult(
            artist=artist,
            track=track,
            genres=normalized_genres,
            year=selected_year,
            album=selected_album,
            confidence_score=confidence_score,
            sources_used=sources_used,
            processing_time=total_time,
            errors=errors
        )
        
    def _calculate_priority_weight(self, api_sources: List[str]) -> float:
        """Calcular peso basado en la prioridad de las APIs."""
        priority_map = {name: config.priority for name, config in get_apis_by_priority()}
        
        total_weight = 0.0
        for api_name in api_sources:
            # Invertir prioridad: prioridad 1 = peso 1.0, prioridad 5 = peso 0.2
            priority = priority_map.get(api_name, 5)
            weight = 1.0 / priority
            total_weight += weight
            
        return min(1.0, total_weight / len(api_sources))
        
    def _calculate_confidence_score(self, num_sources: int, num_genres: int,
                                  has_year: bool, has_album: bool) -> float:
        """Calcular puntuación de confianza general."""
        # Componentes de la puntuación
        source_score = min(1.0, num_sources / 3.0)  # Máximo con 3 fuentes
        genre_score = min(1.0, num_genres / 5.0)    # Máximo con 5 géneros
        metadata_score = (has_year * 0.5) + (has_album * 0.5)  # Año y álbum
        
        # Promedio ponderado
        weights = [0.4, 0.3, 0.3]  # Fuentes, géneros, metadatos
        scores = [source_score, genre_score, metadata_score]
        
        return sum(w * s for w, s in zip(weights, scores))
        
    def enrich_metadata(self, artist: str, track: str) -> EnrichmentResult:
        """
        Enriquecer metadatos de una canción consultando múltiples APIs.
        
        Args:
            artist: Nombre del artista
            track: Título de la canción
            
        Returns:
            Resultado del enriquecimiento con metadatos combinados
        """
        start_time = time.time()
        
        # Validar entrada
        if not artist or not track or not artist.strip() or not track.strip():
            return EnrichmentResult(
                artist=artist or "",
                track=track or "",
                errors=["Invalid artist or track name"]
            )
            
        logger.info(f"Enriching metadata for: {artist} - {track}")
        
        # Preparar consultas paralelas
        futures = {}
        api_results = {}
        
        try:
            # Lanzar consultas a todas las APIs habilitadas
            for api_name, api_instance in self.apis.items():
                future = self.executor.submit(
                    self._query_single_api,
                    api_name, api_instance, artist, track
                )
                futures[future] = api_name
                
            # Recopilar resultados con timeout
            for future in as_completed(futures, timeout=self.timeout):
                try:
                    api_name, result = future.result()
                    api_results[api_name] = result
                    
                except Exception as e:
                    api_name = futures[future]
                    logger.error(f"Error processing {api_name} result: {e}")
                    api_results[api_name] = {
                        'api_name': api_name,
                        'success': False,
                        'error': str(e),
                        'genres': [],
                        'year': None,
                        'album': None
                    }
                    
        except Exception as e:
            logger.error(f"Error during parallel API queries: {e}")
            return EnrichmentResult(
                artist=artist,
                track=track,
                errors=[f"Query execution failed: {str(e)}"]
            )
            
        # Combinar resultados
        result = self._combine_results(api_results)
        result.artist = artist
        result.track = track
        result.processing_time = time.time() - start_time
        
        logger.info(
            f"Enrichment completed in {result.processing_time:.2f}s. "
            f"Sources: {len(result.sources_used)}, "
            f"Genres: {len(result.genres)}, "
            f"Confidence: {result.confidence_score:.2f}"
        )
        
        return result
        
    def enrich_batch(self, tracks: List[Tuple[str, str]]) -> List[EnrichmentResult]:
        """
        Enriquecer metadatos para múltiples canciones.
        
        Args:
            tracks: Lista de tuplas (artista, canción)
            
        Returns:
            Lista de resultados de enriquecimiento
        """
        logger.info(f"Starting batch enrichment for {len(tracks)} tracks")
        
        results = []
        for i, (artist, track) in enumerate(tracks, 1):
            logger.debug(f"Processing track {i}/{len(tracks)}: {artist} - {track}")
            
            result = self.enrich_metadata(artist, track)
            results.append(result)
            
            # Pequeña pausa entre tracks para ser respetuoso con las APIs
            time.sleep(0.1)
            
        logger.info(f"Batch enrichment completed. {len(results)} tracks processed")
        return results
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del enriquecedor.
        
        Returns:
            Diccionario con estadísticas
        """
        api_metrics = get_all_metrics()
        
        return {
            'available_apis': list(self.apis.keys()),
            'max_workers': self.max_workers,
            'timeout': self.timeout,
            'api_metrics': api_metrics,
            'total_apis_initialized': len(self.apis)
        }
        
    def close(self):
        """Cerrar el executor y limpiar recursos."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
            logger.info("MetadataEnricher executor closed")

# Instancia global del enriquecedor
_global_enricher = None

def get_global_enricher() -> MetadataEnricher:
    """Obtener la instancia global del enriquecedor."""
    global _global_enricher
    if _global_enricher is None:
        _global_enricher = MetadataEnricher()
    return _global_enricher

def enrich_track_metadata(artist: str, track: str) -> EnrichmentResult:
    """Función de conveniencia para enriquecer metadatos de una canción."""
    enricher = get_global_enricher()
    return enricher.enrich_metadata(artist, track)

def enrich_batch_metadata(tracks: List[Tuple[str, str]]) -> List[EnrichmentResult]:
    """Función de conveniencia para enriquecimiento en lote."""
    enricher = get_global_enricher()
    return enricher.enrich_batch(tracks) 
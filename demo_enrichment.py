#!/usr/bin/env python3
"""
🎵 DEMO: ENRIQUECIMIENTO DE METADATOS - NUEVA BIBLIOTECA v2.0
===========================================================
Demostración del sistema de enriquecimiento de metadatos musicales
"""

import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Añadir src al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.core.metadata_enricher import MetadataEnricher, enrich_track_metadata
    from src.core.api_metrics import get_all_metrics, log_metrics_summary
    from src.config.api_config import get_enabled_apis, get_apis_by_priority
    from src.core.genre_normalizer import GenreNormalizer
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Asegúrate de que todos los módulos estén en su lugar.")
    print("Nota: Algunas dependencias pueden no estar instaladas (mutagen, musicbrainzngs, pylast, etc.)")
    sys.exit(1)

def demo_single_track():
    """Demostrar enriquecimiento de una sola canción."""
    print("\n🎵 === DEMO: ENRIQUECIMIENTO DE UNA CANCIÓN ===")
    
    # Ejemplo de canción
    artist = "The Beatles"
    track = "Hey Jude"
    
    print(f"🔍 Enriqueciendo: {artist} - {track}")
    
    # Enriquecer metadatos
    result = enrich_track_metadata(artist, track)
    
    # Mostrar resultados
    print(f"\n📊 RESULTADOS:")
    print(f"   Artista: {result.artist}")
    print(f"   Canción: {result.track}")
    print(f"   Año: {result.year or 'No encontrado'}")
    print(f"   Álbum: {result.album or 'No encontrado'}")
    print(f"   Confianza: {result.confidence_score:.2f}")
    print(f"   Fuentes: {', '.join(result.sources_used)}")
    print(f"   Tiempo: {result.processing_time:.2f}s")
    
    if result.genres:
        print(f"\n🎭 GÉNEROS ENCONTRADOS:")
        for genre, confidence in sorted(result.genres.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {genre}: {confidence:.2f}")
    else:
        print("\n❌ No se encontraron géneros")
        
    if result.errors:
        print(f"\n⚠️ ERRORES:")
        for error in result.errors:
            print(f"   • {error}")

def demo_batch_enrichment():
    """Demostrar enriquecimiento en lote."""
    print("\n🎵 === DEMO: ENRIQUECIMIENTO EN LOTE ===")
    
    # Lista de canciones de ejemplo
    tracks = [
        ("Pink Floyd", "Comfortably Numb"),
        ("Led Zeppelin", "Stairway to Heaven"),
        ("Queen", "Bohemian Rhapsody"),
        ("The Rolling Stones", "Paint It Black"),
        ("AC/DC", "Back in Black")
    ]
    
    print(f"🔍 Enriqueciendo {len(tracks)} canciones...")
    
    # Crear enriquecedor
    enricher = MetadataEnricher()
    
    try:
        # Enriquecer en lote
        results = enricher.enrich_batch(tracks)
        
        # Mostrar resultados
        print(f"\n📊 RESULTADOS DEL LOTE:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.artist} - {result.track}")
            print(f"   Año: {result.year or 'N/A'}")
            print(f"   Álbum: {result.album or 'N/A'}")
            print(f"   Géneros: {len(result.genres)}")
            print(f"   Confianza: {result.confidence_score:.2f}")
            print(f"   Fuentes: {', '.join(result.sources_used)}")
            
            # Mostrar top 3 géneros
            if result.genres:
                top_genres = sorted(result.genres.items(), key=lambda x: x[1], reverse=True)[:3]
                genres_str = ", ".join([f"{g}({c:.2f})" for g, c in top_genres])
                print(f"   Top géneros: {genres_str}")
                
    finally:
        enricher.close()

def demo_genre_normalizer():
    """Demostrar el normalizador de géneros."""
    print("\n🎭 === DEMO: NORMALIZADOR DE GÉNEROS ===")
    
    # Géneros de ejemplo para normalizar
    test_genres = [
        "rock music",
        "alternative rock",
        "hip-hop",
        "electronic dance music",
        "rhythm and blues",
        "heavy metal",
        "pop rock",
        "indie",
        "techno music",
        "jazz fusion"
    ]
    
    print("🔍 Normalizando géneros...")
    
    for genre in test_genres:
        normalized, confidence = GenreNormalizer.normalize(genre)
        category = GenreNormalizer.get_genre_category(normalized)
        
        print(f"   '{genre}' → '{normalized}' ({category}) [{confidence:.2f}]")

def demo_api_configuration():
    """Demostrar configuración de APIs."""
    print("\n⚙️ === DEMO: CONFIGURACIÓN DE APIS ===")
    
    # Mostrar APIs habilitadas
    enabled_apis = get_enabled_apis()
    print(f"📡 APIs habilitadas: {len(enabled_apis)}")
    
    for api_name, config in enabled_apis.items():
        print(f"   • {api_name}: prioridad {config.priority}, "
              f"límite {config.rate_limit_capacity}/{config.rate_limit_fill_rate}s")
    
    # Mostrar orden de prioridad
    print(f"\n🏆 Orden de prioridad:")
    for i, (api_name, config) in enumerate(get_apis_by_priority(), 1):
        print(f"   {i}. {api_name} (prioridad {config.priority})")

def demo_metrics():
    """Mostrar métricas de las APIs."""
    print("\n📊 === DEMO: MÉTRICAS DE APIS ===")
    
    metrics = get_all_metrics()
    
    if not metrics:
        print("📭 No hay métricas disponibles (no se han hecho llamadas a APIs)")
        return
        
    print("📈 Métricas actuales:")
    for api_name, api_metrics in metrics.items():
        print(f"\n🔹 {api_name}:")
        print(f"   Llamadas totales: {api_metrics.get('total_calls', 0)}")
        print(f"   Tasa de éxito: {api_metrics.get('success_rate', 0):.2%}")
        print(f"   Latencia promedio: {api_metrics.get('average_latency', 0):.3f}s")
        print(f"   Llamadas/minuto: {api_metrics.get('calls_per_minute', 0):.1f}")

def main():
    """Función principal del demo."""
    print("🎵 NUEVA BIBLIOTECA v2.0 - DEMO DE ENRIQUECIMIENTO DE METADATOS")
    print("=" * 70)
    
    try:
        # Ejecutar demos
        demo_api_configuration()
        demo_genre_normalizer()
        demo_single_track()
        demo_batch_enrichment()
        demo_metrics()
        
        # Mostrar resumen final de métricas
        print("\n📊 === RESUMEN FINAL DE MÉTRICAS ===")
        log_metrics_summary()
        
        print("\n✅ Demo completado exitosamente!")
        print("\n💡 El sistema de enriquecimiento está listo para usar en Nueva Biblioteca.")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante el demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
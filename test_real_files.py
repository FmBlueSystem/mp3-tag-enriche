"""Script para pruebas con archivos MP3 reales."""
import os
import time
import logging
import psutil
import json
from pathlib import Path
from src.core.genre_detector import GenreDetector
from src.core.file_handler import Mp3FileHandler
from src.core.music_apis import LastFmAPI, MusicBrainzAPI, DiscogsAPI

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_memory_usage():
    """Obtener uso actual de memoria."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB

def test_performance():
    """Ejecutar pruebas de rendimiento con archivos reales."""
    
    # Directorio con archivos de prueba
    test_dir = Path("/Volumes/My Passport/Dj compilation 2025/DMS/Mayo25/X-Mix Club Classics/X-MIX CLUB CLASSICS BEST OF 320 (Seperated Tracks)")
    
    # Inicializar APIs y detector
    # Inicializar APIs con manejo de errores
    apis = []
    
    try:
        lastfm = LastFmAPI()
        if lastfm.network:  # Verificar que se inicializó correctamente
            apis.append(lastfm)
            logger.info("LastFM API inicializada correctamente")
        else:
            logger.error("Error al inicializar LastFM API")
    except Exception as e:
        logger.error(f"Error creando LastFM API: {e}")

    try:
        mb_api = MusicBrainzAPI()
        apis.append(mb_api)
        logger.info("MusicBrainz API inicializada correctamente")
    except Exception as e:
        logger.error(f"Error creando MusicBrainz API: {e}")

    try:
        discogs = DiscogsAPI()
        apis.append(discogs)
        logger.info("Discogs API inicializada correctamente")
    except Exception as e:
        logger.error(f"Error creando Discogs API: {e}")

    if not apis:
        logger.error("No se pudo inicializar ninguna API")
        return
    
    handler = Mp3FileHandler()
    detector = GenreDetector(apis=apis, file_handler=handler)
    
    # Recolectar métricas
    metrics = {
        "files": [],
        "memory": {
            "initial": get_memory_usage(),
            "peak": 0,
            "final": 0
        },
        "timing": {
            "total": 0,
            "per_file": {}
        },
        "genres": {
            "normalized": {},
            "raw": {},
            "by_api": {
                "lastfm": {},
                "musicbrainz": {},
                "discogs": {}
            }
        },
        "errors": []
    }

    try:
        start_time = time.time()
        
        # Procesar cada archivo
        for mp3_file in test_dir.glob("*.mp3"):
            file_metrics = {
                "name": mp3_file.name,
                "size": mp3_file.stat().st_size / 1024 / 1024,  # MB
                "processing_time": 0,
                "memory_delta": 0
            }
            
            logger.info(f"\nProcesando: {mp3_file.name}")
            file_start = time.time()
            mem_before = get_memory_usage()
            
            try:
                result = detector.analyze_file(str(mp3_file))
                
                # Registrar géneros detectados
                if "detected_genres" in result:
                    # Convertir cualquier clave no string a string
                    for genre, confidence in result["detected_genres"].items():
                        genre_str = str(genre)
                        metrics["genres"]["normalized"][genre_str] = \
                            metrics["genres"]["normalized"].get(genre_str, 0) + 1
                
                if "current_genres" in result:
                    for genre in result["current_genres"]:
                        genre_str = str(genre)
                        metrics["genres"]["raw"][genre_str] = \
                            metrics["genres"]["raw"].get(genre_str, 0) + 1
                
            except Exception as e:
                error_msg = f"Error procesando {mp3_file.name}: {str(e)}"
                logger.error(error_msg)
                metrics["errors"].append(error_msg)
                continue
            
            # Actualizar métricas del archivo
            file_metrics["processing_time"] = time.time() - file_start
            file_metrics["memory_delta"] = get_memory_usage() - mem_before
            metrics["files"].append(file_metrics)
            
            # Actualizar memoria pico
            current_mem = get_memory_usage()
            metrics["memory"]["peak"] = max(metrics["memory"]["peak"], current_mem)
            
            logger.info(
                f"Completado: {mp3_file.name}\n"
                f"Tiempo: {file_metrics['processing_time']:.2f}s\n"
                f"Memoria: {file_metrics['memory_delta']:.2f}MB\n"
            )
    
    finally:
        # Finalizar métricas
        metrics["timing"]["total"] = time.time() - start_time
        metrics["memory"]["final"] = get_memory_usage()
        
        # Guardar resultados
        with open("test_results.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        logger.info("\nResultados finales:")
        logger.info(f"Tiempo total: {metrics['timing']['total']:.2f}s")
        logger.info(f"Memoria inicial: {metrics['memory']['initial']:.2f}MB")
        logger.info(f"Memoria pico: {metrics['memory']['peak']:.2f}MB")
        logger.info(f"Memoria final: {metrics['memory']['final']:.2f}MB")
        logger.info(f"Errores encontrados: {len(metrics['errors'])}")
        
if __name__ == "__main__":
    test_performance()
# multi_source_metadata.py
"""
Módulo para consultar y validar metadatos musicales desde múltiples fuentes:
- Last.fm
- Discogs
- MusicBrainz
- Spotify (fase futura con OAuth)

Funcionalidades:
✔ Consulta por título + artista
✔ Extracción de género(s), año de lanzamiento y álbum
✔ Fusión de resultados con validación y priorización.

Requiere:
- Claves API configuradas en music_apis.py o pasadas a las clases API.
"""

import requests # Mantener por si alguna API lo usa directamente, aunque ahora debería ser vía music_apis.py
import logging
import re
from typing import List, Optional, Dict, Any
import threading # Para la paralelización futura
from queue import Queue # Para la paralelización futura

# Importar las clases API del módulo music_apis
from .music_apis import MusicBrainzAPI, LastFmAPI, DiscogsAPI # Asegúrate que la ruta sea correcta

# --- Configuración de Logging y Constantes ---
logger = logging.getLogger(__name__)

# BLACKLIST_GENRE_TERMS y is_decade_pattern se mantienen como están.
BLACKLIST_GENRE_TERMS = {
    # Originales
    'various', 'unknown', 'miscellaneous', 'compilation', 'greatest hits',
    'hits', 'decade', 'retro', 'classic', 'oldies', 'general', 'adult',
    # Añadidos desde logs y análisis
    'aln-sh', 'pro trump', 'lol', 'death by automobile', 'alliteration', 
    '2008 universal fire victim', 'pop and chart', 'american', 'dj remix service',
    'english', 'british', 'incomplete remix', 'o happy day', # Términos muy genéricos o no musicales
    'various artists', 'soundtrack', 'score', 'theme', 'cover', 'tribute',
    'live', 'acoustic', 'instrumental', 'remix', 'medley', # Descriptores, no géneros primarios
    'singer-songwriter', # A veces útil, pero a menudo demasiado genérico si hay alternativas
    'world', # Demasiado amplio
    'uncategorized', 'other', 'undefined',
    # Posibles términos problemáticos de MusicBrainz/Discogs
    'spokenword', 'audiobook', 'podcast', 'interview', 'comedy',
    'education', 'health', 'fitness', 'religion', 'spirituality',
    'experimental', # A menos que sea el único género, suele ser muy vago
    'avant-garde' # Similar a experimental
}

def is_decade_pattern(genre_item: str) -> bool:
    """Verifica si un género coincide con un patrón de década (ej. '1970s', '70s', '80's')."""
    genre_lower = genre_item.lower()
    # Patrón para: 1970s, 2000s, 70s, 80s, 70's, 80's
    return bool(re.match(r'^((19|20)\d0s|\d0s|\d0\'s)$', genre_lower))

def _filter_and_limit_final_genres(input_genres: List[str], max_genres_to_return: int = 3) -> List[str]:
    """
    Filtra la lista de géneros fusionados usando una blacklist y patrones de década,
    luego capitaliza, elimina duplicados y limita la cantidad de géneros.
    """
    if not input_genres:
        return []

    genres_cleaned = []
    for item_from_list in input_genres:
        # Asegurarse que item_from_list sea string antes de operar con él
        if not isinstance(item_from_list, str):
            logger.warning(f"Elemento no string encontrado en input_genres: {item_from_list}. Saltando.")
            continue

        genre_lower = item_from_list.strip().lower() 
        
        if genre_lower in BLACKLIST_GENRE_TERMS or is_decade_pattern(item_from_list):
            logger.info(f"Filtrando género no deseado/patrón de década: '{item_from_list}'")
            continue
            
        genre_processed = item_from_list.strip().title() 
        
        if genre_processed not in genres_cleaned:
            genres_cleaned.append(genre_processed)
            
        if len(genres_cleaned) >= max_genres_to_return:
            break
    return genres_cleaned

# --- Funciones de consulta directa a Last.fm y Discogs ELIMINADAS ---
# get_lastfm_tags, get_lastfm_release_year, get_lastfm_album
# _discogs_request, get_discogs_release_info, get_discogs_tags, 
# get_discogs_release_year, get_discogs_album
# Ahora usaremos las clases API.

# --- Nueva función query_all_sources ---
def query_all_sources(artist: str, title: str, email_for_musicbrainz: str = "user@example.com") -> Dict[str, Any]:
    """
    Consulta múltiples fuentes (Last.fm, Discogs, MusicBrainz) usando las clases API en paralelo
    y devuelve metadatos fusionados y validados.
    """
    logger.info(f"Iniciando consulta multi-fuente PARALELA para: {artist} - {title}")

    lastfm_api = LastFmAPI()
    discogs_api = DiscogsAPI()
    musicbrainz_api = MusicBrainzAPI(email=email_for_musicbrainz)

    apis_config = [
        {"name": "Last.fm", "client": lastfm_api},
        {"name": "Discogs", "client": discogs_api},
        {"name": "MusicBrainz", "client": musicbrainz_api}
    ]

    results_queue = Queue()
    threads = []

    def api_worker(client, api_name_w, artist_w, title_w, queue_w):
        logger.info(f"Thread worker iniciando consulta a {api_name_w} para {artist_w} - {title_w}")
        try:
            info = client.get_track_info(artist_w, title_w)
            queue_w.put({"name": api_name_w, "data": info, "status": "ok"})
        except Exception as e:
            logger.error(f"Excepción en thread worker para {api_name_w}: {e}", exc_info=True)
            # Poner None o un dict de error en la cola para que el hilo principal sepa que terminó con error
            queue_w.put({"name": api_name_w, "data": None, "status": "error", "error_message": str(e)})

    for api_conf in apis_config:
        thread = threading.Thread(target=api_worker, 
                                  args=(api_conf["client"], api_conf["name"], artist, title, results_queue))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join() # Esperar a que todos los hilos terminen

    # --- Recolección de datos desde la cola ---
    all_candidate_genres: List[str] = []
    candidate_years: Dict[str, str] = {}
    candidate_albums: Dict[str, str] = {}
    processed_sources_log: List[str] = [] # Log de estado de cada API

    while not results_queue.empty():
        result_item = results_queue.get()
        api_name = result_item["name"]
        info = result_item["data"]
        status = result_item["status"]

        if status == "ok" and info:
            processed_sources_log.append(f"{api_name}:ok")
            if info.get("genres"):
                valid_genres = [g for g in info["genres"] if isinstance(g, str)]
                all_candidate_genres.extend(valid_genres)
                logger.debug(f"{api_name} genres: {valid_genres}")
            if info.get("year"):
                candidate_years[api_name] = str(info["year"])
                logger.debug(f"{api_name} year: {info['year']}")
            if info.get("album"):
                candidate_albums[api_name] = str(info["album"]).strip()
                logger.debug(f"{api_name} album: {info['album']}")
        elif status == "error":
            processed_sources_log.append(f"{api_name}:error - {result_item.get('error_message', 'Unknown error')}")
            logger.error(f"Error reportado por {api_name} thread: {result_item.get('error_message')}")
        else: # status ok pero no info, o status desconocido
            processed_sources_log.append(f"{api_name}:no_data_or_unexpected_status")
            logger.warning(f"{api_name} no devolvió datos o tuvo un estado inesperado.")

    # --- Fusión de Metadatos ---
    final_result = {
        "genres": [],
        "year": None,
        "album": None,
        "source_details": {} # Para loggear de dónde vino cada pieza de info
    }

    # Prioridad para Año: Discogs > MusicBrainz > Last.fm
    if candidate_years.get("Discogs"):
        final_result["year"] = candidate_years["Discogs"]
        final_result["source_details"]["year"] = "Discogs"
    elif candidate_years.get("MusicBrainz"):
        final_result["year"] = candidate_years["MusicBrainz"]
        final_result["source_details"]["year"] = "MusicBrainz"
    elif candidate_years.get("Last.fm"):
        final_result["year"] = candidate_years["Last.fm"]
        final_result["source_details"]["year"] = "Last.fm"

    # Prioridad para Álbum: Discogs > MusicBrainz > Last.fm (considerar similitud para Last.fm)
    # Discogs y MusicBrainz suelen tener títulos de álbum más canónicos.
    if candidate_albums.get("Discogs"):
        final_result["album"] = candidate_albums["Discogs"]
        final_result["source_details"]["album"] = "Discogs"
    elif candidate_albums.get("MusicBrainz"):
        final_result["album"] = candidate_albums["MusicBrainz"]
        final_result["source_details"]["album"] = "MusicBrainz"
    elif candidate_albums.get("Last.fm"):
        final_result["album"] = candidate_albums["Last.fm"]
        final_result["source_details"]["album"] = "Last.fm"
    
    # Podríamos añadir una lógica más compleja si hay conflicto y los álbumes son muy diferentes.
    # Por ejemplo, si Discogs y MusicBrainz difieren, podríamos registrar el conflicto.

    # --- Fusión y Filtrado Final de Géneros ---
    # Eliminar duplicados de all_candidate_genres manteniendo el orden (aproximadamente)
    # y capitalizando de forma consistente para el filtrado.
    processed_unique_candidate_genres = []
    seen_genres_lower = set()
    for genre_str in all_candidate_genres:
        if not isinstance(genre_str, str): continue # Seguridad extra
        g_lower = genre_str.strip().lower()
        if g_lower and g_lower not in seen_genres_lower: # No añadir vacíos
            processed_unique_candidate_genres.append(genre_str.strip())
            seen_genres_lower.add(g_lower)
            
    logger.info(f"Géneros candidatos de todas las fuentes (antes de filtrar): {processed_unique_candidate_genres}")
    
    if processed_unique_candidate_genres:
        final_result["genres"] = _filter_and_limit_final_genres(processed_unique_candidate_genres, max_genres_to_return=3)
        logger.info(f"Géneros finales después de sanitizar y limitar a 3: {final_result['genres']}")
        if final_result["genres"]: # Solo añadir fuente de géneros si se obtuvieron géneros
             final_result["source_details"]["genres"] = "Consolidated" # Indicar que son de múltiples fuentes
    else:
        logger.info("No hay géneros candidatos para procesar.")
        final_result["genres"] = []

    # Crear un string de 'source' para resumen, similar al anterior
    # Esto podría mejorarse para ser más detallado con final_result["source_details"]
    source_summary_parts = []
    if final_result["year"]: source_summary_parts.append(f"Y:{final_result['source_details']['year'][0]}")
    if final_result["album"]: source_summary_parts.append(f"A:{final_result['source_details']['album'][0]}")
    if final_result["genres"]:
        genre_src_flags = []
        # Usar el processed_sources_log para determinar las fuentes que contribuyeron con géneros
        # Esta lógica podría mejorarse si queremos saber exactamente qué API contribuyó qué género
        # Por ahora, si la API tuvo éxito (status 'ok') y devolvió *algún* dato, asumimos que pudo haber contribuido.
        if any("Last.fm:ok" in s for s in processed_sources_log): genre_src_flags.append("L")
        if any("Discogs:ok" in s for s in processed_sources_log): genre_src_flags.append("D")
        if any("MusicBrainz:ok" in s for s in processed_sources_log): genre_src_flags.append("M")
        if genre_src_flags: source_summary_parts.append(f"G:{'+'.join(genre_src_flags)}")
        
    final_result["source"] = sorted(list(set(source_summary_parts)))

    logger.info(f"Resultado final PARALELO para {artist} - {title}: {final_result}")
    return final_result


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG) # Cambiado a DEBUG para pruebas más detalladas
    
    # Asegurarse que el logger de music_apis también esté en DEBUG si se quiere ver su output
    logging.getLogger("src.core.music_apis").setLevel(logging.DEBUG)

    # Obtener email del usuario para MusicBrainz (o usar uno por defecto)
    # Esto es importante para cumplir con los términos de MusicBrainz.
    # Idealmente, la aplicación lo pediría o lo tendría en una config.
    mb_email = input("Por favor, introduce tu email para MusicBrainz API (o presiona Enter para usar 'test@example.com'): ")
    if not mb_email:
        mb_email = "test@example.com"
    print(f"Usando email: {mb_email} para MusicBrainz.")

    test_cases = [
        ("Michael Jackson", "Billie Jean"),
        ("Queen", "Bohemian Rhapsody"),
        ("Madonna", "Like a Prayer"),
        ("Daft Punk", "Get Lucky"),
        ("Nirvana", "Smells Like Teen Spirit"),
        ("Artista Super Incorrecto 123", "Título Super Ficticio XYZ")
    ]

    for artist, title in test_cases:
        print(f"--- {artist} - {title} ---")
        print(query_all_sources(artist, title, email_for_musicbrainz=mb_email))
        print("\\n")
        time.sleep(1) # Pequeña pausa entre pruebas generales, las APIs tienen su propio rate limiting. 
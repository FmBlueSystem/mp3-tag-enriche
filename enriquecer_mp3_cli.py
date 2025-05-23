import os
import sys
import logging

# 🔧 PARCHE: Suprimir logs verbosos que causan congelamiento
import logging
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('musicbrainzngs').setLevel(logging.ERROR)
logging.getLogger('musicbrainzngs.musicbrainzngs').setLevel(logging.ERROR)
logging.getLogger('mutagen').setLevel(logging.WARNING)
logging.getLogger('spotipy').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('pylast').setLevel(logging.WARNING)

import traceback
from src.core.genre_detector import GenreDetector
from src.core.music_apis import MusicBrainzAPI, LastFmAPI, DiscogsAPI
from src.core.file_handler import Mp3FileHandler
try:
    from src.core.spotify_api import SpotifyAPI
    SPOTIFY_AVAILABLE = True
except ImportError:
    SPOTIFY_AVAILABLE = False

# Check if config loader is available
try:
    from src.core.config_loader import load_api_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

from mutagen.easyid3 import EasyID3
import argparse

# --- Sanitización de metadatos vacíos ---
RELEVANT_TAGS = [
    "date", "genre", "composer", "performer", "albumartist", "tracknumber",
    "totaltracks", "discnumber", "totaldiscs", "comment", "title", "artist", "album"
]

def sanitize_mp3_tags(file_path):
    try:
        audio = EasyID3(file_path)
        changed = False
        for tag in RELEVANT_TAGS:
            if tag in audio:
                values = [v.strip() for v in audio[tag]]
                # Si algún valor está vacío, lo reemplazamos por "Desconocido"
                new_values = [v if v else "Desconocido" for v in values]
                # Si todos los valores son vacíos, eliminamos el campo
                if all(v == "" for v in values):
                    del audio[tag]
                    changed = True
                elif values != new_values:
                    audio[tag] = new_values
                    changed = True
        if changed:
            audio.save()
    except Exception as e:
        logging.error(f"Error sanitizando metadatos en {file_path}: {e}")

# Configurar logging a archivo
logging.basicConfig(
    filename='enriquecer_mp3_cli.log',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Configura aquí el directorio raíz de tus MP3
ROOT_DIR = "/Volumes/My Passport/Dj compilation 2025/DMS/DMS 80s"

# Inicializar APIs
apis = [
    MusicBrainzAPI(email="user@example.com"),
    LastFmAPI(),
    DiscogsAPI()
]

# Agregar Spotify API si está disponible
if SPOTIFY_AVAILABLE:
    try:
        # Try to load config from file
        if CONFIG_AVAILABLE:
            config = load_api_config()
            spotify_config = config.get("spotify", {})
            client_id = spotify_config.get("client_id")
            client_secret = spotify_config.get("client_secret")
            
            if client_id and client_secret:
                spotify_api = SpotifyAPI(client_id=client_id, client_secret=client_secret)
                apis.append(spotify_api)
                logging.info("Spotify API enabled")
                print("Spotify API habilitada.")
            else:
                logging.warning("Spotify API credentials missing or empty in config file")
                print("AVISO: Credenciales de Spotify faltantes o vacías en el archivo de configuración.")
        else:
            logging.warning("Config loader not available, continuing without Spotify")
            print("AVISO: Cargador de configuración no disponible, continuando sin Spotify.")
    except Exception as e:
        logging.error(f"Error initializing Spotify API: {e}")
        print(f"ERROR: No se pudo inicializar la API de Spotify: {e}")

# Inicializar detector y file handler
file_handler = Mp3FileHandler()
genre_detector = GenreDetector(apis=apis, file_handler=file_handler)

def get_mp3_files(root_dir):
    mp3_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith('.mp3'):
                mp3_files.append(os.path.join(root, file))
    return mp3_files

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Enriquecer archivos MP3 con metadatos de género desde múltiples fuentes")
    
    parser.add_argument(
        "--directory", "-d",
        help="Directorio que contiene los archivos MP3 a procesar",
        default=ROOT_DIR
    )
    
    parser.add_argument(
        "--no-spotify",
        help="Deshabilitar el uso de la API de Spotify",
        action="store_true"
    )
    
    parser.add_argument(
        "--config",
        help="Ruta al archivo de configuración de API",
        default=None
    )
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Update ROOT_DIR if provided in arguments
    process_dir = args.directory
    
    mp3_files = get_mp3_files(process_dir)
    total = len(mp3_files)
    logging.info(f"Procesando {total} archivos MP3 en {ROOT_DIR}")
    print(f"Procesando {total} archivos MP3...")
    procesados = 0
    errores = 0
    for idx, file_path in enumerate(mp3_files, 1):
        try:
            logging.info(f"[{idx}/{total}] Procesando: {file_path}")
            result = genre_detector.analyze_file(file_path)
            
            # Skip files with missing metadata only if we couldn't get artist or title from either tags or filename
            if not result.get('metadata', {}).get('artist') or not result.get('metadata', {}).get('title'):
                print(f"[SKIP] {os.path.basename(file_path)} | Missing both artist and title")
                logging.warning(f"Skipping file with completely missing metadata: {file_path}")
                continue
            def to_str(g):
                if isinstance(g, str):
                    return g
                elif isinstance(g, tuple):
                    return str(g[0])
                else:
                    return str(g)
            detected_genres = [to_str(g) for g in result.get('detected_genres', {}).keys()]
            if not detected_genres:
                detected_genres = ['Desconocido']
            logging.info(f"Géneros detectados: {detected_genres}")
            # --- Detectar año ---
            year = result.get('year') or result.get('date') or None
            if not year:
                # Buscar en los resultados de las APIs si hay año
                api_results = result.get('api_results', {})
                for api_name, api_result in api_results.items():
                    logging.info(f"Checking year in {api_name}: {api_result.get('year')}")
                    y = api_result.get('year') or api_result.get('date')
                    if y:
                        year = y
                        logging.info(f"Found year {year} from {api_name}")
                        break
            if not year:
                year = "Desconocido"
            logging.info(f"Year to be written: {year}")
            # --- Escribir metadatos ---
            file_handler.write_genre(file_path, detected_genres, backup=True)
            if year and year != "Desconocido":
                try:
                    file_handler.write_year(file_path, year)
                    logging.info(f"Año escrito: {year}")
                except Exception as e:
                    logging.error(f"Error escribiendo año en {file_path}: {e}\n{traceback.format_exc()}")
            # Sanitizar metadatos relevantes para que ningún campo quede vacío
            sanitize_mp3_tags(file_path)
            print(f"[OK] {os.path.basename(file_path)} | Géneros: {detected_genres} | Año: {year}")
            logging.info(f"[OK] {os.path.basename(file_path)} | Géneros: {detected_genres} | Año: {year}")
            procesados += 1
        except Exception as e:
            errores += 1
            print(f"[ERROR] {os.path.basename(file_path)}: {e}")
            logging.error(f"Error procesando {file_path}: {e}\n{traceback.format_exc()}")
    print(f"\nProcesados: {procesados}, Errores: {errores}")
    logging.info(f"Procesados: {procesados}, Errores: {errores}")

if __name__ == "__main__":
    main() 
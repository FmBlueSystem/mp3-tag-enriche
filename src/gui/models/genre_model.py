"""Genre processing model module."""
import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Set
import logging
import time
from collections import defaultdict
from queue import Queue
from threading import Lock

from ...core.genre_detector import GenreDetector
from ...core.file_handler import Mp3FileHandler
from ...core.music_apis import MusicBrainzAPI

# Try to import all available APIs
try:
    from ...core.spotify_api import SpotifyAPI
    SPOTIFY_AVAILABLE = True
except ImportError:
    SPOTIFY_AVAILABLE = False

try:
    from ...core.music_apis import LastFmAPI, DiscogsAPI
    EXTENDED_APIS_AVAILABLE = True
except ImportError:
    EXTENDED_APIS_AVAILABLE = False

try:
    from ...core.config_loader import load_api_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)

BLACKLIST_GENRE_TERMS_MODEL = {
    'victim', 'fire', 'universal', 'compilation', 'unknown', 'soundtrack',
    "http", "fix", "tag", "mess", "error", "todo", "check", 
    "wrong", "unclassifiable", "other", "others", 
    "delete", "seen live", "favorites", "favourite", "test", 
    "misc", "checked", "need", "spotify", "lastfm", "indy", 
    "artist", "artists", "video", "title", 
    "dj", "remix", "mix", "bootleg", "edit", "promo", "radio", "club", "live",
    "album", "single", "track", "version", "original", "extended", "instrumental"
}

class UpdateBuffer:
    """Buffer para actualizaciones por lotes."""
    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
        self.updates: Queue = Queue()
        self.lock = Lock()
        self._pending_count = 0
    
    def add(self, item: Dict) -> None:
        """Agrega un item al buffer."""
        with self.lock:
            self.updates.put(item)
            self._pending_count += 1
    
    def flush(self) -> List[Dict]:
        """Obtiene los items pendientes hasta batch_size."""
        items = []
        with self.lock:
            while not self.updates.empty() and len(items) < self.batch_size:
                items.append(self.updates.get())
                self._pending_count -= 1
        return items

    @property
    def pending_count(self) -> int:
        """Retorna cantidad de items pendientes."""
        with self.lock:
            return self._pending_count

class GenreIndex:
    """Índice para búsqueda eficiente de géneros."""
    def __init__(self):
        self.by_genre: Dict[str, Set[str]] = defaultdict(set)
        self.by_confidence: Dict[float, Set[str]] = defaultdict(set)
        self.lock = Lock()
    
    def add(self, filepath: str, genres: List[str], confidence: float) -> None:
        """Agrega un archivo a los índices."""
        with self.lock:
            for genre in genres:
                self.by_genre[genre.lower()].add(filepath)
            self.by_confidence[confidence].add(filepath)
    
    def remove(self, filepath: str) -> None:
        """Elimina un archivo de los índices."""
        with self.lock:
            for genre_files in self.by_genre.values():
                genre_files.discard(filepath)
            for conf_files in self.by_confidence.values():
                conf_files.discard(filepath)

    def search(self, genre: Optional[str] = None, min_confidence: float = 0.0) -> Set[str]:
        """Busca archivos que cumplan los criterios."""
        with self.lock:
            results = set()
            if genre:
                results.update(self.by_genre.get(genre.lower(), set()))
            if min_confidence > 0:
                for conf, files in self.by_confidence.items():
                    if conf >= min_confidence:
                        results.update(files)
            return results

def clean_and_split_genre_payload(raw_genre_name: str) -> List[str]:
    """Limpia y divide una cadena de género en una lista de géneros válidos."""
    if not raw_genre_name:
        return []

    # Primero limpiar caracteres especiales y espacios extras
    cleaned = re.sub(r'[\r\n\t]+', ' ', raw_genre_name)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    raw_items = re.split(r'[;,/]', cleaned)
    genres_cleaned_parts = []

    for item in raw_items:
        genre_part = item.strip()
        if not genre_part:
            continue
        if any(term in genre_part.lower() for term in BLACKLIST_GENRE_TERMS_MODEL):
            continue
        if re.search(r'\b(19|20)\d{2}\b', genre_part):  # Corregido el regex
            genre_part = re.sub(r'\s*\b(19|20)\d{2}\b', '', genre_part)
        
        genre_title_case = genre_part.title()
        genre_title_case = genre_title_case.strip()  # Asegurar que no haya espacios extras

        if (len(genre_title_case) > 1 and
            not genre_title_case.isdigit() and
            not all(c in "!@#$%^&*()[]{};:,./<>?\\\\|`~-=_+" for c in genre_title_case)):
            if genre_title_case not in genres_cleaned_parts:
                genres_cleaned_parts.append(genre_title_case)
    
    return genres_cleaned_parts

class GenreModel:
    """Modelo para el procesamiento de géneros musicales."""
    def __init__(self, backup_dir: Optional[str] = None):
        self.file_handler = Mp3FileHandler(backup_dir=backup_dir)
        
        # Configure all available APIs
        apis = [MusicBrainzAPI()]
        
        # Add Spotify API if available
        if SPOTIFY_AVAILABLE and CONFIG_AVAILABLE:
            try:
                # Try to load Spotify configuration
                config = load_api_config()
                spotify_config = config.get("spotify", {})
                client_id = spotify_config.get("client_id")
                client_secret = spotify_config.get("client_secret")
                
                if client_id and client_secret:
                    logger.info("Añadiendo Spotify API al GenreModel GUI")
                    spotify_api = SpotifyAPI(client_id=client_id, client_secret=client_secret)
                    apis.append(spotify_api)
                else:
                    logger.warning("Credenciales de Spotify faltantes en la configuración")
            except Exception as e:
                logger.warning(f"Error al inicializar Spotify API en GUI: {e}")
        
        # Add other APIs if available
        if EXTENDED_APIS_AVAILABLE:
            try:
                apis.append(DiscogsAPI())
                logger.info("Añadiendo Discogs API al GenreModel GUI")
            except Exception as e:
                logger.warning(f"Error al inicializar Discogs API en GUI: {e}")
        
        self.detector = GenreDetector(
            apis=apis,
            file_handler=self.file_handler
        )
        
        logger.info(f"GenreModel inicializado con {len(apis)} APIs: {[api.__class__.__name__ for api in apis]}")
        
        self.min_confidence = 0.2
        self.max_api_tags = 100
        self.rename_after_update = True
        
        # Nuevos componentes para optimización
        self.update_buffer = UpdateBuffer()
        self.genre_index = GenreIndex()
        self._cache: Dict[str, Dict] = {}
        self._cache_lock = Lock()
    
    def _cache_result(self, filepath: str, result: Dict) -> None:
        """Cachea el resultado del análisis."""
        with self._cache_lock:
            self._cache[filepath] = result.copy()
            if "processed_genres" in result:
                self.genre_index.add(
                    filepath,
                    list(result["processed_genres"].keys()),
                    max(result["processed_genres"].values(), default=0.0)
                )

    def _get_cached(self, filepath: str) -> Optional[Dict]:
        """Obtiene resultado cacheado si existe."""
        with self._cache_lock:
            return self._cache.get(filepath)

    def process_chunks(self, filepaths: List[str], chunk_size: int = 8192) -> List[Dict]:
        """Procesa archivos en chunks para mejor rendimiento."""
        results = []
        for filepath in filepaths:
            cached = self._get_cached(filepath)
            if cached:
                results.append(cached)
                continue
            
            result = self.analyze(filepath, chunk_size)
            self._cache_result(filepath, result)
            results.append(result)
        
        return results

    @property
    def backup_dir(self) -> Optional[str]:
        """Obtiene la ruta del directorio de respaldo actual del file_handler."""
        if self.file_handler and self.file_handler.backup_dir:
            return str(self.file_handler.backup_dir)
        return None

    def update_backup_dir(self, new_backup_dir: Optional[str]):
        """Actualiza el directorio de respaldo en el file_handler."""
        if self.file_handler:
            self.file_handler.set_backup_dir(new_backup_dir)
            logger.info(f"Directorio de respaldo del GenreModel actualizado a: {new_backup_dir}")
        else:
            logger.warning("GenreModel: file_handler no está inicializado, no se puede actualizar backup_dir.")

    def verify_file_exists(self, filepath: str) -> tuple[bool, str]:
        """Verifica si un archivo existe usando múltiples métodos."""
        exists = False
        error_msg = ""
        
        try:
            path_obj = Path(filepath)
            if path_obj.exists():
                exists = True
        except Exception as e:
            error_msg = f"Error con Path.exists(): {str(e)}"
        
        if not exists:
            try:
                if os.path.exists(filepath):
                    exists = True
                else:
                    error_msg = f"os.path.exists() reporta que el archivo no existe"
            except Exception as e:
                error_msg += f", Error con os.path.exists(): {str(e)}"
        
        if not exists:
            try:
                with open(filepath, 'rb'):
                    exists = True
            except Exception as e:
                error_msg += f", Error al intentar abrir archivo: {str(e)}"
        
        return exists, error_msg

    def process_genres(self, detected_genres: Dict[str, float], max_tags: int) -> Dict[str, float]:
        """Procesa y filtra los géneros detectados."""
        processed_api_genres = {}
        sorted_api_genres = sorted(detected_genres.items(), key=lambda x: x[1], reverse=True)
        temp_unique_cleaned_genres = {}

        for i, (raw_genre_name, score) in enumerate(sorted_api_genres):
            if i >= max_tags:
                break
            
            cleaned_sub_genres = clean_and_split_genre_payload(raw_genre_name)
            for cleaned_name in cleaned_sub_genres:
                lower_cleaned_name = cleaned_name.lower()
                existing_score = temp_unique_cleaned_genres.get(lower_cleaned_name, (None, -1.0))[1]
                if score > existing_score:
                    temp_unique_cleaned_genres[lower_cleaned_name] = (cleaned_name, score)
        
        return {orig_name: scr for orig_name, scr in temp_unique_cleaned_genres.values()}

    def analyze(self, filepath: str, chunk_size: int = 8192) -> Dict:
        """Analiza un archivo para detectar sus géneros."""
        try:
            exists, error_msg = self.verify_file_exists(filepath)
            if not exists:
                return {"error": f"Archivo inaccesible: {filepath}. {error_msg}"}
            
            if not self.detector.file_handler.is_valid_mp3(filepath):
                return {"error": f"Archivo MP3 inválido: {filepath}"}
                
            result = self.detector.analyze_file(filepath, chunk_size=chunk_size)
            
            # Preservar todos los géneros encontrados
            raw_api_genres = {}
            raw_api_genres.update(result.get("detected_genres", {}))
            raw_api_genres.update(result.get("found_genres", {}))
            
            if raw_api_genres:
                result["processed_genres"] = self.process_genres(
                    raw_api_genres,
                    self.max_api_tags
                )
            result["raw_api_genres"] = raw_api_genres
            
            # Asegurar que found_genres se preserven
            if "found_genres" in result:
                result["detected_genres"] = result["found_genres"]
            
            return result
        except Exception as e:
            logger.error(f"Error detallado en GenreModel.analyze para {filepath}: {e}", exc_info=True)
            return {"error": f"Error al analizar '{os.path.basename(filepath)}': {type(e).__name__}"}

    def select_genres(self, filtered_genres: Dict[str, float], confidence: float, max_genres: int) -> List[str]:
        """Selecciona los mejores géneros basados en confianza."""
        selected_genres = []
        for genre, conf in sorted(filtered_genres.items(), key=lambda x: x[1], reverse=True):
            if conf >= confidence:
                normalized = genre[0].upper() + genre[1:] if genre else ""
                if normalized.lower() not in [g.lower() for g in selected_genres]:
                    selected_genres.append(normalized)
                    if len(selected_genres) >= max_genres:
                        break
        return selected_genres

    def process(self, filepath: str, confidence: float, max_genres: int, rename_flag: bool, chunk_size: int = 8192) -> Dict:
        """Procesa un archivo para actualizar sus géneros."""
        try:
            exists, error_msg = self.verify_file_exists(filepath)
            if not exists:
                return {"error": f"Archivo inaccesible: {filepath}. {error_msg}", "written": False}
                
            if not self.detector.file_handler.is_valid_mp3(filepath):
                return {"error": f"Archivo MP3 inválido: {filepath}", "written": False}
            
            analysis = self.analyze(filepath, chunk_size=chunk_size)
            
            # Usar tanto processed_genres como raw_api_genres
            genres = analysis.get("processed_genres", {})
            if not genres:
                genres = analysis.get("raw_api_genres", {})
            
            filtered_genres = {}
            for genre, conf in genres.items():
                if len(genre) < 50 and len(genre.strip()) > 1:
                    filtered_genres[genre] = conf
            
            if not filtered_genres:
                return {
                    "error": f"No se detectaron géneros válidos para este archivo",
                    "written": False,
                    "detected_genres": genres,
                    "raw_api_genres": analysis.get("raw_api_genres", {})
                }
            
            adaptive_confidence = confidence
            if not any(conf >= confidence for conf in filtered_genres.values()):
                adaptive_confidence = min(self.min_confidence, max(0.1, confidence - 0.2))
            
            selected_genres = self.select_genres(filtered_genres, adaptive_confidence, max_genres)
            
            if not selected_genres and filtered_genres:
                top_genre = max(filtered_genres.items(), key=lambda x: x[1])
                normalized = top_genre[0][0].upper() + top_genre[0][1:] if top_genre[0] else ""
                selected_genres.append(normalized)
                adaptive_confidence = top_genre[1]
            
            if not selected_genres:
                return {
                    "error": f"No se detectaron géneros con confianza suficiente",
                    "written": False,
                    "detected_genres": filtered_genres,
                    "raw_api_genres": analysis.get("raw_api_genres", {}),
                    "threshold_used": adaptive_confidence
                }
            
            try:
                backup_success = self.detector.file_handler._create_backup(filepath)
                if not backup_success:
                    logger.warning(f"Advertencia: No se pudo crear copia de seguridad para {filepath}")
                
                if self.rename_after_update:
                    current_filepath_for_rename = filepath 
                    rename_result = self.detector.file_handler.rename_file_by_genre(
                        current_filepath_for_rename, 
                        genres_to_write=selected_genres,
                        perform_os_rename_action=rename_flag
                    )
                    
                    current_error = rename_result.get("error")
                    result = {
                        "written": rename_result.get("success", False),
                        "renamed": rename_result.get("success", False) and rename_result.get("new_path") != filepath,
                        "new_filepath": rename_result.get("new_path"),
                        "message": rename_result.get("message", ""),
                        "current_genre": ";".join(selected_genres),
                        "selected_genres_written": selected_genres,
                        "threshold_used": adaptive_confidence
                    }
                    if current_error:
                        result["error"] = current_error
                    
                else:
                    success = self.detector.file_handler.write_genre(filepath, selected_genres, backup=False)
                    result = {"written": success}
                    if success:
                        time.sleep(0.2)
                        info_after_write = self.detector.file_handler.get_file_info(filepath)
                        result["current_genre"] = info_after_write.get("current_genre", "")
                        result["selected_genres_written"] = selected_genres
                        result["threshold_used"] = adaptive_confidence
                    else:
                        result["error"] = f"Error al escribir géneros en {filepath}"
            
                return result
            except Exception as write_error:
                return {
                    "error": f"Error al escribir en el archivo: {str(write_error)}",
                    "written": False,
                    "selected_genres_written": selected_genres
                }
                
        except Exception as e:
            logger.error(f"Error detallado en GenreModel.process para {filepath}: {e}", exc_info=True)
            return {"error": f"Error al procesar '{os.path.basename(filepath)}': {type(e).__name__}", "written": False}

    def update_results(self, results: dict) -> None:
        """Actualiza el modelo con los resultados procesados."""
        if not isinstance(results, dict):
            logger.warning("update_results: resultados no es un diccionario")
            return
        for filepath, result in results.items():
            self._cache_result(filepath, result)

    def rowCount(self):
        """Devuelve el número de elementos almacenados en el modelo."""
        return len(self._cache)

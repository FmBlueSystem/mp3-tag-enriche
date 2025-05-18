"""MP3 file handling and tag management module."""
from typing import Dict, List, Optional
from pathlib import Path
import shutil
import os
from datetime import datetime
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, TCON
from mutagen.mp3 import MP3
import re
import logging

logger = logging.getLogger(__name__)

# Diccionarios de corrección estilística para formateo de tags
KNOWN_TITLES = {
    # Clave (sin espacios, PascalCase) -> Valor deseado
    "StayinAlive": "Stayin' Alive",
    "Ymca": "YMCA",
    "RappersDelight": "Rapper's Delight", # Corregido con apóstrofe
    "GoodTimes": "Good Times",
    # ... añadir más según sea necesario
}

KNOWN_ARTISTS = {
    # Clave (sin espacios, PascalCase) -> Valor deseado
    "SugarHillGang": "Sugar Hill Gang",
    "TheBeeGees": "The Bee Gees",
    "KC&TheSunshineBand": "KC & The Sunshine Band",
    # ... añadir más según sea necesario
}

# Acrónimos que deben permanecer en mayúsculas en el formateo Title Case
KNOWN_ACRONYMS_TITLE_CASE = {"YMCA", "DJ", "UK", "USA", "EP", "LP", "MTV", "KC"}

def _format_text_to_spaced_title_case(text: str) -> str:
    """Convierte una cadena de texto a Title Case con espacios, manejando acrónimos."""
    if not text:
        return ""
    
    s = str(text) # Asegurar que sea string
    # Reemplazar separadores comunes (incluyendo paréntesis) con espacios.
    # Los paréntesis se reintroducirán formateados por format_title_tag si son parte del sufijo.
    s = re.sub(r'[\\-_\\.\\(\\)]+', ' ', s) 
    s = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', r' \\g<0>', s) # Dividir CamelCase: wordWord -> word Word
    s = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', r' \\g<0>', s) # Dividir Acrónimos: ACRONYMWord -> ACRONYM Word
    s = re.sub(r'\\s+', ' ', s).strip() # Normalizar múltiples espacios a uno solo y quitar de extremos

    words = s.split(' ')
    processed_words = []

    for word in words:
        if not word:
            continue
        
        # Manejar palabras con apóstrofes o guiones internamente (ej. O'Malley, Stayin')
        # Esto es una heurística y puede necesitar ajustes.
        # La idea es capitalizar sub-partes alrededor de apóstrofes/guiones.
        if "'" in word and len(word) > 1:
            parts = word.split("'")
            processed_words.append("'".join([p.capitalize() for p in parts]))
        elif "-" in word and len(word) > 1:
            parts = word.split("-")
            processed_words.append("-".join([p.capitalize() for p in parts]))
        elif word.upper() in KNOWN_ACRONYMS_TITLE_CASE:
            processed_words.append(word.upper())
        else:
            processed_words.append(word.capitalize()) # Capitalize normal para la mayoría de palabras

    return " ".join(processed_words)

def format_title_tag(raw_title: Optional[str]) -> str:
    """Formatea el título para tags ID3."""
    if not raw_title:
        return "Unknown Title"
    
    cleaned_title = str(raw_title) # Asegurar que sea string
    cleaned_title = re.sub(r'\\s+', ' ', cleaned_title).strip()
    # No reemplazar paréntesis aquí, _format_text_to_spaced_title_case los tratará como separadores.
    #cleaned_title = cleaned_title.replace('( ', '(').replace(' )', ')')
    #cleaned_title = cleaned_title.replace('[', '(').replace(']', ')')

    # Intentar extraer la parte principal y todo lo que parezca un sufijo entre paréntesis o después de un guion
    # Esta regex es más compleja para capturar varios patrones de sufijo.
    # Patrón: "Título Principal (Sufijo1) (Sufijo2) - Algo Más"
    # O: "Título Principal - Sufijo Detallado"
    # O: "Título Principal (Sufijo Detallado)"
    
    # Primero, manejar el caso de "Título - Parte Adicional"
    # y luego si la "Parte Adicional" contiene paréntesis.
    
    main_part_raw = cleaned_title
    suffix_part_raw = ""

    # Priorizar el guion como separador principal si está fuera de paréntesis obvios
    # Esto es heurístico. Podríamos buscar el último " - " que no esté dentro de un nivel de paréntesis.
    # Por simplicidad, si hay " - ", dividimos tentativamente.
    if " - " in cleaned_title:
        parts = cleaned_title.split(" - ", 1)
        main_part_raw = parts[0].strip()
        if len(parts) > 1:
            suffix_part_raw = parts[1].strip()
    
    # Ahora, si la parte principal aún contiene paréntesis al final, tratar de extraerlos.
    # O si no había guion, y el título termina en paréntesis.
    match_parens = re.match(r'^(.*?)\\s*(\\((?:[^)(]+|\\((?:[^)(]+|\\([^)(]*\\))*\\))*\\))$', main_part_raw)
    if match_parens:
        main_part_raw = match_parens.group(1).strip()
        # Añadir el contenido del paréntesis al inicio del suffix_part_raw (si ya había algo del guion)
        parenthetical_suffix = match_parens.group(2).strip()
        if suffix_part_raw:
            suffix_part_raw = f"{parenthetical_suffix} - {suffix_part_raw}"
        else:
            suffix_part_raw = parenthetical_suffix
            
    # Clave de búsqueda para KNOWN_TITLES 
    # Usar _to_pascal_case para generar una clave más consistente para la búsqueda
    # Reemplazamos los paréntesis en la clave de búsqueda para que coincida con el formato de KNOWN_TITLES
    temp_main_key_pascal = _to_pascal_case(main_part_raw.replace('(', ' ').replace(')', ' '))
    
    if temp_main_key_pascal in KNOWN_TITLES:
        main_formatted = KNOWN_TITLES[temp_main_key_pascal]
    else:
        main_formatted = _format_text_to_spaced_title_case(main_part_raw)
    
    # Formatear el sufijo si existe
    formatted_suffix = ""
    if suffix_part_raw:
        # Si el sufijo comienza con paréntesis y termina con paréntesis (caso simple de "(Contenido)")
        if suffix_part_raw.startswith("(") and suffix_part_raw.endswith(")"):
            content_inside_parens = suffix_part_raw[1:-1].strip()
            formatted_suffix = f" ({_format_text_to_spaced_title_case(content_inside_parens)})"
        else: # Para sufijos más complejos como "(Sufijo1) - Algo Más"
            formatted_suffix = f" - {_format_text_to_spaced_title_case(suffix_part_raw)}" # Asumir que es un " - Algo"

    # Combinar parte principal y sufijo formateado
    # Asegurar un solo espacio si ambos existen y el sufijo no empieza ya con espacio (como lo hace " (Algo)")
    final_title = main_formatted
    if formatted_suffix:
        if formatted_suffix.startswith(" (") or formatted_suffix.startswith(" - "):
            final_title += formatted_suffix
        else: # Caso poco probable si la lógica anterior es correcta
            final_title += " " + formatted_suffix
            
    return final_title.strip()

def format_artist_tag(raw_artist: Optional[str]) -> str:
    """Formatea el artista para tags ID3."""
    if not raw_artist:
        return "Unknown Artist"
    
    cleaned_artist = str(raw_artist) # Asegurar que sea string
    # Clave de búsqueda para KNOWN_ARTISTS (sin espacios, PascalCase simple para la clave)
    lookup_key = ''.join(word.capitalize() for word in cleaned_artist.split()) 

    if lookup_key in KNOWN_ARTISTS:
        return KNOWN_ARTISTS[lookup_key]
    
    return _format_text_to_spaced_title_case(cleaned_artist)

def _to_pascal_case(text: str) -> str:
    """Convierte un texto a PascalCase (UpperCamelCase) de forma más robusta."""
    if not text:
        return ""
    
    # 1. Reemplazar separadores comunes (guiones, underscores, puntos) con espacios.
    s = re.sub(r'[\\-_\\.]+', ' ', text)
    
    # 2. Insertar espacios para separar palabras unidas por CamelCase/PascalCase.
    s = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', r' \\g<0>', s) # wordWord -> word Word
    s = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', r' \\g<0>', s) # ACRONYMWord -> ACRONYM Word

    # 3. Dividir por espacios.
    words = s.split()
    
    processed_words = []
    # Lista (no exhaustiva) de acrónimos comunes que se quieren preservar en mayúsculas.
    known_acronyms = {"DJ", "YMCA", "USA", "UK", "EP", "LP", "MTV"} 

    for word in words:
        if not word:
            continue
        
        # Mantener acrónimos conocidos en mayúsculas.
        if word.upper() in known_acronyms: # Comprobar contra la versión en mayúsculas del acrónimo
            processed_words.append(word.upper())
        # Si la palabra es toda mayúsculas (y no es un acrónimo conocido o es una sola letra)
        elif word.isupper() and len(word) > 1: 
            processed_words.append(word[0].upper() + word[1:].lower()) # "THE" -> "The"
        elif word.isupper() and len(word) == 1: # Letras solas mayúsculas como "A"
            processed_words.append(word) 
        else: # Palabras mixtas o minúsculas
            processed_words.append(word[0].upper() + word[1:].lower() if word else "")

    return "".join(processed_words)

class Mp3FileHandler:
    """Handles MP3 file operations and tag management."""
    
    def __init__(self, backup_dir: Optional[str] = None, verbose: bool = False):
        """Initialize the file handler.
        
        Args:
            backup_dir: Directory for file backups (optional)
            verbose: Enable verbose logging (not directly used by logger level here, assumes parent configures)
        """
        self.set_backup_dir(backup_dir)
            
    def set_backup_dir(self, backup_dir_path: Optional[str]):
        """Sets or updates the backup directory."""
        if backup_dir_path:
            self.backup_dir = Path(backup_dir_path)
            try:
                self.backup_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Backup directory set to: {self.backup_dir}")
            except Exception as e:
                logger.error(f"Could not create or access backup directory {self.backup_dir}: {e}")
                self.backup_dir = None # Fallback to no backup
        else:
            self.backup_dir = None
        
        if not self.backup_dir:
            logger.info("No backup directory specified or creation/access failed. Backups will be disabled.")

    def _get_backup_path(self, file_path: str) -> Optional[Path]:
        """Generate backup file path.
        
        Args:
            file_path: Original file path
            
        Returns:
            Path object for backup file, or None if backup_dir is not set
        """
        if not self.backup_dir:
            return None
        original = Path(file_path)
        backup_file_name = f"{original.stem}_backup_{datetime.now().strftime('%Y%m%d%H%M%S%f')}{original.suffix}"
        return self.backup_dir / backup_file_name
            
    def _create_backup(self, file_path: str) -> bool:
        """Create a backup of the file before modification.
        
        Args:
            file_path: Path to the MP3 file
            
        Returns:
            True if backup was successful, False otherwise
        """
        backup_path = self._get_backup_path(file_path)
        if not backup_path:
            logger.info(f"Backup skipped for {file_path} as no backup directory is configured.")
            return False
            
        try:
            src_path = Path(file_path)
            
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src_path, backup_path)
            logger.info(f"Backup created for {src_path.name} at {backup_path}")
            
            if backup_path.exists() and backup_path.stat().st_size > 0:
                return True
            else:
                logger.error(f"Backup verification failed for {backup_path}. File missing or empty.")
                return False
            
        except Exception as e:
            logger.error(f"Backup error for {file_path} to {backup_path}: {e}")
            return False
            
    def read_tags(self, file_path: str) -> Dict[str, List[str]]:
        """Read metadata tags from an MP3 file."""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found when trying to read tags: {file_path}")
                return {}
                
            audio = EasyID3(file_path)
            return {key: audio.get(key, []) for key in audio.keys()}
            
        except Exception as e:
            logger.error(f"Error reading tags from {file_path}: {e}")
            return {}
            
    def write_genre(self, file_path: str, genres: List[str], backup: bool = True) -> bool:
        """Write genre tags to an MP3 file."""
        from .genre_normalizer import GenreNormalizer
        
        if backup:
            if not self._create_backup(file_path):
                logger.warning(f"Failed to create backup for {file_path}. Proceeding without backup.")
            
        try:
            try:
                audio = EasyID3(file_path)
            except Exception:
                logger.info(f"No EasyID3 tags found for {file_path}, attempting to add them.")
                audio_mp3 = MP3(file_path)
                audio_mp3.add_tags()
                audio_mp3.save()
                audio = EasyID3(file_path)
            
            normalized_genres = GenreNormalizer.normalize_list(genres)
            audio['genre'] = normalized_genres
            audio.save()
            logger.info(f"Genres written successfully to {file_path}: {normalized_genres}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing genres to {file_path}: {e}")
            return False
            
    def get_file_info(self, file_path: str) -> Dict[str, str]:
        """Get basic information about an MP3 file."""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found when trying to get_file_info: {file_path}")
                return {}
                
            audio = MP3(file_path)
            info = {
                'length': str(int(audio.info.length)),
                'bitrate': str(audio.info.bitrate // 1000) + ' kbps',
                'sample_rate': str(audio.info.sample_rate) + ' Hz',
                'mode': audio.info.mode
            }
            
            try:
                id3 = EasyID3(file_path)
                info.update({
                    'title': id3.get('title', [''])[0],
                    'artist': id3.get('artist', [''])[0],
                    'album': id3.get('album', [''])[0],
                    'current_genre': ';'.join(id3.get('genre', ['']))
                })
                logger.info(f"Successfully retrieved file info for: {file_path}")
                
            except Exception as e:
                logger.error(f"Error reading ID3 tags for {file_path}: {e}")
                
            return info
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {}
            
    def rename_file_by_genre(
        self, 
        file_path: str, 
        genres_to_write: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Renombra el archivo, actualiza metadatos de Artista/Título y opcionalmente Género.
           Formato nombre archivo: Artista - Titulo.extension (con Artista y Titulo formateados)
           Metadatos ID3: Artista, Titulo y Género (si se provee) se actualizan.
        """
        result = {"success": False, "original_path": file_path, "message": ""}
        
        try:
            original_path_obj = Path(file_path)
            if not original_path_obj.exists():
                result["error"] = "Original file does not exist."
                result["message"] = "Error: Original file not found."
                return result

            file_info = self.get_file_info(file_path) # Esto lee los tags existentes
            if not file_info:
                result["error"] = "Could not read file info for renaming/tagging."
                result["message"] = result["error"]
                return result
            
            artist_raw = file_info.get('artist')
            title_raw = file_info.get('title')

            if not artist_raw and not title_raw:
                # Si no hay artista ni título, podríamos optar por no hacer nada o usar defaults.
                # Por ahora, si ambos faltan, no se procesa para evitar "Unknown Artist - Unknown Title".
                result["error"] = "Missing both artist and title metadata. Cannot process."
                result["message"] = result["error"]
                return result
            
            # Usar valores existentes o "Unknown" si uno falta, para que el formateo no falle
            formatted_artist = format_artist_tag(artist_raw if artist_raw else "Unknown Artist")
            formatted_title = format_title_tag(title_raw if title_raw else "Unknown Title")
            
            # Si después del formateo alguno queda como "Unknown..." y el original no lo era,
            # podríamos decidir revertir al original o loggearlo.
            # Por simplicidad, continuamos con el valor formateado (que podría ser "Unknown...").

            # Actualizar metadatos ID3 de Artista y Título en el archivo original
            try:
                audio = EasyID3(str(original_path_obj)) # EasyID3 necesita str path
                audio['artist'] = formatted_artist
                audio['title'] = formatted_title
                if genres_to_write is not None:
                    from .genre_normalizer import GenreNormalizer # Import local para evitar circularidad
                    normalized_genres = GenreNormalizer.normalize_list(genres_to_write)
                    audio['genre'] = normalized_genres
                    logger.info(f"Metadatos de Género actualizados para '{original_path_obj.name}' a: {normalized_genres}")
                
                audio.save()
                log_msg_tags = f"Metadatos Artist/Title actualizados para '{original_path_obj.name}' a: Art: '{formatted_artist}', Title: '{formatted_title}'"
                if genres_to_write is not None:
                    log_msg_tags += f", Genres: {normalized_genres}"
                logger.info(log_msg_tags)
                result["tags_updated"] = True
            except Exception as tag_error:
                logger.error(f"Error actualizando metadatos para '{original_path_obj.name}': {tag_error}")
                result["tags_updated"] = False
                result["tag_update_error"] = str(tag_error)
                # No necesariamente detenemos el proceso de renombrado por esto, pero lo registramos.

            # Construir el nuevo nombre de archivo basado en los tags formateados
            # La heurística del espacio antes del paréntesis se puede aplicar aquí si es necesario,
            # o mejor aún, integrarla en format_title_tag si es un requisito general del título.
            # format_title_tag ya maneja los paréntesis en el sufijo.
            new_name_base = f"{formatted_artist} - {formatted_title}"
            
            # Sanitizar caracteres problemáticos para nombres de archivo (excepto ' y & que podrían ser válidos)
            # Reemplazar / \ : * ? " < > | con _
            # Permitir apóstrofes y ampersands si KNOWN_TITLES/ARTISTS los usan.
            new_name_base_sanitized = re.sub(r'[\\/*?:"<>|]+', '_', new_name_base)
            # Adicionalmente, asegurar que no termine con puntos o espacios (problema en Windows)
            new_name_base_sanitized = new_name_base_sanitized.strip('. ')

            if not new_name_base_sanitized:
                 result["error"] = "Generated filename base is empty after sanitization."
                 result["message"] = result["error"]
                 return result

            new_filename_with_ext = f"{new_name_base_sanitized}{original_path_obj.suffix}"
            new_path = original_path_obj.with_name(new_filename_with_ext)
            
            if new_path == original_path_obj:
                result["success"] = True # Aunque no haya cambio de nombre, los tags pudieron actualizarse
                result["message"] = "Tags actualizados. El nombre de archivo generado es el mismo que el original."
                result["new_path"] = str(original_path_obj)
                return result

            # Renombrar el archivo físico
            os.rename(str(original_path_obj), str(new_path))
            logger.info(f"Archivo '{original_path_obj.name}' renombrado a '{new_path.name}'")
            
            result["success"] = True
            result["new_path"] = str(new_path)
            result["message"] = f"Archivo renombrado a {new_path.name} y tags actualizados."
            return result
            
        except Exception as e:
            logger.error(f"Error durante renombrado/actualización de tags para {file_path}: {e}", exc_info=True)
            result["error"] = str(e)
            result["message"] = f"Error durante renombrado/actualización de tags: {e}"
            return result
            
    def is_valid_mp3(self, file_path: str) -> bool:
        """Check if the file is a valid MP3."""
        if not os.path.exists(file_path):
            return False
            
        try:
            MP3(file_path)
            return True
        except:
            return False

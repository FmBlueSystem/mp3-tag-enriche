"""MP3 file handling and tag management module."""
from typing import Dict, List, Optional, Tuple
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

# Diccionarios y constantes para formateo de tags

# Géneros comunes que deben ser eliminados del título
COMMON_GENRES = {
    "Pop", "Rock", "Hip-Hop", "Hip Hop", "R&B", "RnB", "Dance", "Electronic",
    "House", "Techno", "Trance", "Dubstep", "Drum And Bass", "Jazz", "Blues",
    "Country", "Folk", "Metal", "Classical", "Latin", "Reggae", "Funk", "Soul"
}

# Sufijos que deben preservarse aunque contengan géneros
PROTECTED_SUFFIXES = {
    "Original Mix", "Club Mix", "Radio Mix", "Extended Mix", "Remix",
    "Radio Edit", "Club Edit", "Instrumental", "Acapella", "Dub Mix",
    "VIP Mix", "Re-Edit", "Remaster", "Live Version", "Acoustic Version"
}

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

    # Limpieza preliminar de patrones problemáticos literales y caracteres no deseados.
    # Eliminar la secuencia literal '\\g<0>' si aparece.
    s = s.replace('\\\\g<0>', '') # Reemplaza la cadena literal \\g<0>
    
    # Reemplazar múltiples puntos o caracteres especiales problemáticos (no letras, números, espacios, apóstrofes, guiones básicos) con espacio
    # Esto es para limpiar cosas como "Artista.....Nombre" o "Artista&&&Nombre"
    # Mantener apóstrofes y guiones que pueden ser parte de nombres.
    s = re.sub(r"[^a-zA-Z0-9\s'-'’]+", ' ', s) # Usar comillas dobles para el raw string y listar ' y ' directamente.

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

    # Extraer y preservar sufijos protegidos
    protected_suffix = ""
    for suffix in PROTECTED_SUFFIXES:
        # Buscar sufijos protegidos en patrones comunes
        patterns = [
            fr" {re.escape(suffix)}$",  # Al final
            fr"\({re.escape(suffix)}\)",  # Entre paréntesis
            fr" - {re.escape(suffix)}$",  # Después de guion
        ]
        
        for pattern in patterns:
            match = re.search(pattern, cleaned_title, re.IGNORECASE)
            if match:
                protected_suffix = match.group()
                cleaned_title = cleaned_title[:match.start()].strip()
                break
        if protected_suffix:  # Si encontramos un sufijo protegido, dejar de buscar
            break

    # Eliminar referencias a géneros
    for genre in COMMON_GENRES:
        # Patrones para eliminar géneros
        patterns = [
            fr"\s+{re.escape(genre)}\s*$",  # Al final
            fr"\s*\({re.escape(genre)}\)\s*",  # Entre paréntesis
            fr"\s+{re.escape(genre)}\s+(?=\()",  # Antes de paréntesis
            fr"\s+-\s+{re.escape(genre)}\s*$",  # Después de guion al final
        ]
        
        for pattern in patterns:
            cleaned_title = re.sub(pattern, '', cleaned_title, flags=re.IGNORECASE)

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
            
    # Formatear la parte principal
    temp_main_key_pascal = _to_pascal_case(main_part_raw.replace('(', ' ').replace(')', ' '))
    if temp_main_key_pascal in KNOWN_TITLES:
        main_formatted = KNOWN_TITLES[temp_main_key_pascal]
    else:
        main_formatted = _format_text_to_spaced_title_case(main_part_raw)
    
    # Formatear el sufijo no protegido si existe
    formatted_suffix = ""
    if suffix_part_raw:
        # Eliminar géneros del sufijo también
        clean_suffix = suffix_part_raw
        for genre in COMMON_GENRES:
            clean_suffix = re.sub(fr'\s*{re.escape(genre)}\s*', '', clean_suffix, flags=re.IGNORECASE)
        
        # Si el sufijo comienza y termina con paréntesis
        if clean_suffix.startswith("(") and clean_suffix.endswith(")"):
            content = clean_suffix[1:-1].strip()
            if content:  # Solo si quedó contenido después de limpiar géneros
                formatted_suffix = f" ({_format_text_to_spaced_title_case(content)})"
        elif clean_suffix:  # Si hay contenido después de limpiar géneros
            formatted_suffix = f" - {_format_text_to_spaced_title_case(clean_suffix)}"

    # Construir el título final
    final_title = main_formatted

    # Añadir sufijo formateado si existe
    if formatted_suffix:
        final_title += formatted_suffix

    # Añadir sufijo protegido al final si existe
    if protected_suffix:
        if protected_suffix.startswith(" ") or protected_suffix.startswith("("):
            final_title += protected_suffix
        else:
            final_title += " " + protected_suffix

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
        self.tag_fields = [
            'title', 'artist', 'album', 'genre', 'date', 
            'composer', 'conductor', 'albumartist', 'copyright',
            'encodedby', 'mood', 'organization', 'language',
            'performer', 'isrc', 'discnumber', 'tracknumber'
        ]
    
    def set_backup_dir(self, backup_dir_path: Optional[str]):
        """Sets or updates the backup directory."""
        logger.debug(f"Attempting to set backup directory to: {backup_dir_path}")
        if backup_dir_path:
            try:
                self.backup_dir = Path(backup_dir_path)
                logger.debug(f"Converted to Path object: {self.backup_dir}")
                
                # Verify the path exists or can be created
                self.backup_dir.mkdir(parents=True, exist_ok=True)
                
                # Verify write permissions by attempting to write a test file
                test_file = self.backup_dir / '.test_write'
                try:
                    test_file.touch()
                    test_file.unlink()  # Clean up test file
                    logger.debug("Write permission test successful")
                except Exception as e:
                    raise PermissionError(f"No write permission: {e}")
                
                logger.info(f"Backup directory set to: {self.backup_dir}")
                return
                
            except Exception as e:
                logger.error(f"Could not create or access backup directory {backup_dir_path}: {e}", exc_info=True)
                self.backup_dir = None # Fallback to no backup
        else:
            logger.debug("No backup directory path provided")
            self.backup_dir = None
        
        if not self.backup_dir:
            logger.warning("No backup directory specified or creation/access failed. Backups will be disabled.")

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
            
    def read_tags(self, file_path: str, chunk_size: int = 8192) -> Dict[str, List[str]]:
        """Lee metadata tags de un archivo MP3.
        
        Args:
            file_path: Ruta al archivo MP3
            chunk_size: No usado, mantenido por compatibilidad
        """
        if not os.path.exists(file_path):
            logger.warning(f"Archivo no encontrado al intentar leer tags: {file_path}")
            return {}
            
        try:
            # Intentar cargar con EasyID3 primero (más simple)
            try:
                audio = EasyID3(file_path)
                return {key: audio.get(key, []) for key in audio.keys()}
            except Exception as e:
                logger.debug(f"EasyID3 falló, intentando con ID3: {e}")
                
            # Si EasyID3 falla, intentar con ID3
            try:
                audio = ID3(file_path)
                result = {}
                
                # Mapear frames ID3 a tags simples
                for key in audio.keys():
                    if key.startswith('T'):  # Text frames
                        clean_key = key[4:].lower()  # TALB -> alb
                        result[clean_key] = [str(audio[key])]
                
                return result
            except Exception as e:
                logger.debug(f"ID3 también falló: {e}")
                return {}
            
        except Exception as e:
            logger.error(f"Error leyendo tags de {file_path}: {e}")
            return {}
            
    def write_genre(self, file_path: str, genres: List[str], backup: bool = True, chunk_size: int = 8192) -> bool:
        """Escribe tags de género a un archivo MP3.
        
        Args:
            file_path: Ruta al archivo MP3
            genres: Lista de géneros a escribir
            backup: Si se debe crear backup
            chunk_size: Tamaño del chunk para lectura/escritura (no usado directamente)
        """
        from .genre_normalizer import GenreNormalizer
        
        if backup:
            if not self._create_backup(file_path):
                logger.warning(f"No se pudo crear backup para {file_path}. Procediendo sin backup.")
        
        try:
            # Normalizar géneros
            normalized_genres = [g[0] if isinstance(g, tuple) else g for g in GenreNormalizer.normalize_list(genres)]
            
            # Intentar primero con EasyID3
            try:
                audio = EasyID3(file_path)
                audio['genre'] = normalized_genres
                audio.save()
                logger.info(f"Géneros escritos exitosamente usando EasyID3 en {file_path}: {normalized_genres}")
                return True
            except Exception as e:
                logger.warning(f"EasyID3 falló, intentando con ID3: {e}")
            
            # Si EasyID3 falla, intentar con ID3
            try:
                audio = ID3(file_path)
                audio.add(TCON(encoding=3, text=normalized_genres))
                audio.save(v2_version=3)
                logger.info(f"Géneros escritos exitosamente usando ID3 en {file_path}: {normalized_genres}")
                return True
            except Exception as e:
                logger.warning(f"ID3 también falló: {e}")
            
            raise Exception("No se pudieron escribir los tags usando EasyID3 ni ID3")
            
        except Exception as e:
            logger.error(f"Error escribiendo géneros en {file_path}: {e}")
            return False
            
    def get_file_info(self, file_path: str, chunk_size: int = 8192) -> Dict[str, str]:
        """Obtiene información básica sobre un archivo MP3 usando chunks.
        
        Args:
            file_path: Ruta al archivo MP3
            chunk_size: Tamaño del chunk para lectura en bytes (default: 8KB)
        """
        if not os.path.exists(file_path):
            logger.warning(f"Archivo no encontrado al intentar get_file_info: {file_path}")
            return {}

        try:
            info = {}
            
            # Usar context manager para el manejo de recursos
            with open(file_path, 'rb') as f:
                # Leer headers MP3 para información básica
                header = f.read(10)  # ID3v2 header
                
                # Calcular tamaño del archivo
                f.seek(0, 2)  # Ir al final
                file_size = f.tell()
                f.seek(0)  # Volver al inicio
                
                # Detectar frames MP3 para obtener información técnica
                f.seek(-128, 2)  # Ir a posición de ID3v1 si existe
                has_id3v1 = f.read(3) == b'TAG'
                
                # Calcular duración aproximada basada en bitrate promedio
                duration = file_size * 8 / (320 * 1000)  # Asumiendo máximo bitrate
                
                info.update({
                    'length': str(int(duration)),
                    'bitrate': '320 kbps',  # Valor por defecto
                    'sample_rate': '44100 Hz',  # Valor común
                    'mode': 'stereo'  # Valor por defecto
                })
            
            # Leer tags usando el método optimizado
            tags = self.read_tags(file_path, chunk_size)
            
            # First try to get metadata from tags
            if tags:
                info.update({
                    'title': tags.get('title', [''])[0],
                    'artist': tags.get('artist', [''])[0],
                    'album': tags.get('album', [''])[0],
                    'current_genre': ';'.join(tags.get('genre', []))
                })
                logger.debug(f"Información de archivo recuperada con éxito desde tags: {file_path}")
            
            # If artist or title is missing, try to extract from filename
            if not info.get('artist') or not info.get('title'):
                filename = os.path.basename(file_path)
                filename_without_ext = os.path.splitext(filename)[0]
                artist, title = self.extract_artist_title_from_filename(filename_without_ext)
                
                # Only update missing fields
                if not info.get('artist'):
                    info['artist'] = artist
                if not info.get('title'):
                    info['title'] = title
                
                if artist or title:
                    logger.info(f"Extraída información de nombre de archivo para: {file_path}")
            
            return info
            
        except Exception as e:
            logger.error(f"Error obteniendo información del archivo {file_path}: {e}")
            return {}
            
    def rename_file_by_genre(
        self,
        file_path: str,
        genres_to_write: Optional[List[str]] = None,
        perform_os_rename_action: bool = True,
        include_genre_in_filename: bool = False,  # Siempre False por defecto para excluir géneros del nombre
        max_genres_in_filename: int = 2  # Mantenido por compatibilidad pero no se usa si include_genre_in_filename es False
    ) -> Dict[str, str]:
        """Rename file and update metadata with genre support.
        
        Args:
            file_path: Path to the MP3 file
            genres_to_write: List of genres to write to ID3 tags
            perform_os_rename_action: Whether to physically rename the file
            include_genre_in_filename: Whether to include genres in filename
            max_genres_in_filename: Maximum number of genres to include in filename
            
        Returns:
            Dictionary with operation results
        """
        result = {"success": False, "original_path": file_path, "message": ""}
        
        try:
            original_path_obj = Path(file_path)
            if not original_path_obj.exists():
                result["error"] = "Original file does not exist."
                result["message"] = "Error: Original file not found."
                return result

            filename_stem = original_path_obj.stem
            file_extension = original_path_obj.suffix.lower() # ej: .mp3

            if file_extension != ".mp3":
                result["error"] = "Not an MP3 file."
                result["message"] = "Error: El archivo no es MP3."
                return result

            # Leer tags actuales para obtener artista/título base si el nombre de archivo no es útil
            # Esto podría ser una estrategia de fallback, por ahora asumimos que el nombre de archivo es la fuente principal.
            current_tags = self.read_tags(str(original_path_obj))
            raw_artist_from_tag = current_tags.get('artist', [""])[0]
            raw_title_from_tag = current_tags.get('title', [""])[0]

            # Extract artist and title from filename
            artist_part_raw, title_part_raw = self.extract_artist_title_from_filename(
                filename_stem,
                fallback_artist=raw_artist_from_tag or "Unknown Artist",
                fallback_title=raw_title_from_tag or filename_stem
            )
            
            # Formatear Artista y Título para los tags y el nuevo nombre de archivo
            formatted_artist = format_artist_tag(artist_part_raw)
            formatted_title = format_title_tag(title_part_raw)
            
            logger.debug(f"Original artist: '{artist_part_raw}', title: '{title_part_raw}'")
            logger.debug(f"Formatted artist: '{formatted_artist}', title: '{formatted_title}'")

            # Actualizar metadatos ID3 de Artista y Título en el archivo original
            # También escribir géneros si se proporcionan
            try:
                # Preserve existing metadata
                preserved_metadata = self._preserve_metadata(str(original_path_obj), str(original_path_obj))
                
                # Create new EasyID3 tags
                audio = EasyID3(str(original_path_obj))
                
                # Restore preserved metadata
                for field, values in preserved_metadata.items():
                    if field not in ['artist', 'title', 'genre']:  # Don't overwrite fields we're explicitly setting
                        audio[field] = values
                
                # Set the main fields, never truncate these
                audio['artist'] = formatted_artist
                audio['title'] = formatted_title
                
                # Handle genres
                if genres_to_write is not None:
                    if genres_to_write:
                        audio['genre'] = genres_to_write
                        logger.info(f"Genre metadata updated for '{original_path_obj.name}' to: {genres_to_write}")
                    else:
                        if 'genre' in audio:
                            del audio['genre']
                            logger.info(f"Genre tag removed for '{original_path_obj.name}'")
                
                # Save all metadata
                audio.save()
                
                logger.info(f"Metadata updated for '{original_path_obj.name}': Artist='{formatted_artist}', Title='{formatted_title}', Fields={list(audio.keys())}")
                result["success"] = True
                result["message"] = "Metadata updated successfully."
                result["updated_fields"] = list(audio.keys())

            except Exception as e:
                logger.error(f"Error al escribir tags ID3 en {original_path_obj.name}: {e}", exc_info=True)
                result["error"] = f"Error al escribir tags: {e}"
                result["message"] = f"Error: No se pudieron escribir los tags en {original_path_obj.name}."
                # Devolver aquí porque si los tags no se pueden escribir, no tiene sentido renombrar.
                return result

            # Build new filename without genre
            new_filename_stem = f"{formatted_artist} - {formatted_title}"
            
            # Género removido intencionalmente del nombre del archivo
            # El género solo se mantendrá en los metadatos ID3
                
            # Handle special characters
            replacements = {
                '/': '⁄',  # Use unicode division slash
                '\\': '⧵',  # Use unicode reverse solidus
                ':': '꞉',   # Use unicode modifier letter colon
                '*': '∗',   # Use unicode asterisk operator
                '?': '？',   # Use unicode full width question mark
                '"': "'",   # Replace quotes with apostrophe
                '<': '❮',   # Use unicode heavy left-pointing angle bracket
                '>': '❯',   # Use unicode heavy right-pointing angle bracket
                '|': '⏐',   # Use unicode vertical line
                '\0': '',   # Remove null bytes
            }
            
            for char, replacement in replacements.items():
                new_filename_stem = new_filename_stem.replace(char, replacement)
                
            # Ensure filename length is within limits (255 bytes for most filesystems)
            # Account for extension length and some buffer
            max_length = 240 - len(file_extension)
            if len(new_filename_stem.encode('utf-8')) > max_length:
                # Try to preserve as much as possible while staying within limits
                new_filename_stem = new_filename_stem.encode('utf-8')[:max_length].decode('utf-8', 'ignore')
            
            new_filename = new_filename_stem + file_extension
            new_path = original_path_obj.parent / new_filename
            
            # Handle name conflicts
            counter = 1
            while new_path.exists() and new_path != original_path_obj:
                base_stem = new_filename_stem
                counter_str = f" ({counter})"
                
                # Ensure we don't exceed length limits even with counter
                max_stem_length = max_length - len(counter_str)
                if len(base_stem.encode('utf-8')) > max_stem_length:
                    base_stem = base_stem.encode('utf-8')[:max_stem_length].decode('utf-8', 'ignore')
                    
                new_filename = base_stem + counter_str + file_extension
                new_path = original_path_obj.parent / new_filename
                counter += 1

            result["new_path"] = str(new_path) # Guardar la ruta potencial incluso si no se renombra

            # Renombrar el archivo FÍSICAMENTE solo si se solicita y es necesario
            if perform_os_rename_action and original_path_obj.resolve() != new_path.resolve():
                try:
                    original_path_obj.rename(new_path)
                    logger.info(f"Archivo '{original_path_obj.name}' renombrado a '{new_path.name}'")
                    result["message"] = f"Metadatos actualizados y archivo renombrado a '{new_path.name}'."
                    # 'success' ya es True por la escritura de tags
                except OSError as e_os:
                    logger.error(f"Error al renombrar el archivo '{original_path_obj.name}' a '{new_path.name}': {e_os}", exc_info=True)
                    result["error"] = f"Error al renombrar: {e_os}"
                    # Mantener el mensaje de éxito de tags si los tags se escribieron,
                    # pero añadir que el renombrado falló.
                    result["message"] = f"Metadatos actualizados. Error al renombrar el archivo: {e_os}"
                    # Aunque el renombrado falle, los tags se actualizaron, así que success puede seguir siendo True overall.
                    # El contador de 'renombrados' en la GUI se basará en si new_path != original_path y no hay error aquí.
            elif perform_os_rename_action and original_path_obj.resolve() == new_path.resolve():
                logger.info(f"El nombre del archivo '{original_path_obj.name}' ya está en el formato deseado. No se necesita renombrado físico.")
                result["message"] = f"Metadatos actualizados. El nombre del archivo ya es correcto."
            elif not perform_os_rename_action:
                logger.info(f"Renombrado físico del archivo omitido para '{original_path_obj.name}' según la configuración.")
                result["message"] = "Metadatos actualizados. Renombrado físico omitido."

            return result

        except Exception as e:
            logger.error(f"Error en rename_file_by_genre para {file_path}: {e}", exc_info=True)
            result["error"] = f"Error inesperado en la operación de archivo: {e}"
            result["message"] = f"Error inesperado al procesar {Path(file_path).name}."
            return result
            
    def extract_artist_title_from_filename(self, filename: str, fallback_artist: str = "", fallback_title: str = "") -> Tuple[str, str]:
        """Extract artist and title from a filename.
        
        Args:
            filename: The filename (without extension) to parse
            fallback_artist: Artist name to use if no artist can be extracted
            fallback_title: Title to use if no title can be extracted
            
        Returns:
            Tuple containing (artist, title)
        """
        artist = ""
        title = ""
        
        # Try to split on " - " first
        if " - " in filename:
            parts = filename.split(" - ", 1)
            artist = parts[0].strip()
            title = parts[1].strip()
        else:
            # If no separator found, use fallbacks
            artist = fallback_artist
            title = fallback_title or filename  # Use full filename as title if no fallback
            
        return artist, title

    def is_valid_mp3(self, file_path: str) -> bool:
        """Check if the file is a valid MP3."""
        if not os.path.exists(file_path):
            return False
            
        try:
            MP3(file_path)
            return True
        except:
            return False
    
    def _preserve_metadata(self, target_path: str, source_path: str) -> Dict[str, List[str]]:
        """Preserve metadata from source file when updating target file.
        
        Args:
            target_path: Path to file being updated
            source_path: Path to original file to preserve metadata from
            
        Returns:
            Dictionary of metadata fields and values
        """
        preserved = {}
        try:
            source_audio = EasyID3(str(source_path))
            for field in self.tag_fields:
                if field in source_audio:
                    preserved[field] = source_audio[field]
            logger.debug(f"Preserved metadata fields from {source_path}: {list(preserved.keys())}")
            return preserved
        except Exception as e:
            logger.warning(f"Could not preserve metadata: {e}")
            return {}

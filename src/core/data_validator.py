"""
Sistema de validación de datos y sanitización para prevenir errores y vulnerabilidades.
"""
import re
import os
import logging
from typing import Dict, List, Any, Optional, Union, Set
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlparse
import unicodedata

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Resultado de validación."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_value: Any = None

class DataValidator:
    """Validador y sanitizador de datos."""
    
    # Patrones de validación
    FILENAME_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
    ARTIST_TITLE_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_\(\)\[\]\.\,\'\&\+\!\?]+$')
    SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_\.\,\'\(\)]+$')
    
    # Caracteres peligrosos para diferentes contextos
    DANGEROUS_FILENAME_CHARS = set('<>:"/\\|?*')
    DANGEROUS_SHELL_CHARS = set(';&|`$()[]{}*?<>')
    
    # Extensiones de archivo permitidas
    ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.flac', '.wav', '.m4a', '.ogg', '.aac'}
    
    @classmethod
    def validate_filename(cls, filename: str, max_length: int = 255) -> ValidationResult:
        """Valida y sanitiza un nombre de archivo."""
        errors = []
        warnings = []
        
        if not filename:
            errors.append("Nombre de archivo vacío")
            return ValidationResult(False, errors, warnings)
            
        # Verificar longitud
        if len(filename) > max_length:
            errors.append(f"Nombre de archivo demasiado largo ({len(filename)} > {max_length})")
            
        # Verificar caracteres peligrosos
        dangerous_chars = cls.DANGEROUS_FILENAME_CHARS.intersection(set(filename))
        if dangerous_chars:
            errors.append(f"Caracteres peligrosos encontrados: {dangerous_chars}")
            
        # Verificar nombres reservados de Windows
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
            'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4',
            'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved_names:
            errors.append(f"Nombre reservado del sistema: {name_without_ext}")
            
        # Sanitizar
        sanitized = cls._sanitize_filename(filename)
        
        if sanitized != filename:
            warnings.append("Nombre de archivo fue sanitizado")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized
        )
        
    @classmethod
    def _sanitize_filename(cls, filename: str) -> str:
        """Sanitiza un nombre de archivo."""
        # Normalizar Unicode
        filename = unicodedata.normalize('NFKD', filename)
        
        # Reemplazar caracteres peligrosos
        filename = cls.FILENAME_INVALID_CHARS.sub('_', filename)
        
        # Eliminar espacios múltiples
        filename = re.sub(r'\s+', ' ', filename).strip()
        
        # Eliminar puntos al final (problemático en Windows)
        filename = filename.rstrip('.')
        
        # Asegurar que no esté vacío
        if not filename or filename == '_':
            filename = "unknown_file"
            
        return filename
        
    @classmethod
    def validate_artist_title(cls, text: str, field_name: str) -> ValidationResult:
        """Valida y sanitiza nombres de artista o título."""
        errors = []
        warnings = []
        
        if not text:
            errors.append(f"{field_name} vacío")
            return ValidationResult(False, errors, warnings)
            
        # Verificar longitud razonable
        if len(text) > 200:
            warnings.append(f"{field_name} muy largo ({len(text)} caracteres)")
            
        # Sanitizar
        sanitized = cls._sanitize_artist_title(text)
        
        if sanitized != text:
            warnings.append(f"{field_name} fue sanitizado")
            
        # Verificar que no sea solo espacios o caracteres especiales
        if not sanitized.strip() or not re.search(r'[a-zA-Z0-9]', sanitized):
            errors.append(f"{field_name} no contiene caracteres válidos")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized
        )
        
    @classmethod
    def _sanitize_artist_title(cls, text: str) -> str:
        """Sanitiza texto de artista o título."""
        # Normalizar Unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Eliminar caracteres de control
        text = ''.join(char for char in text if not unicodedata.category(char).startswith('C'))
        
        # Limpiar espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    @classmethod
    def validate_file_path(cls, file_path: str) -> ValidationResult:
        """Valida una ruta de archivo."""
        errors = []
        warnings = []
        
        if not file_path:
            errors.append("Ruta de archivo vacía")
            return ValidationResult(False, errors, warnings)
            
        try:
            path = Path(file_path)
            
            # Verificar si es absoluta o relativa válida
            if not path.is_absolute() and not cls._is_safe_relative_path(str(path)):
                errors.append("Ruta relativa insegura (contiene .. o similares)")
                
            # Verificar extensión si es archivo de audio
            if path.suffix.lower() and path.suffix.lower() not in cls.ALLOWED_AUDIO_EXTENSIONS:
                warnings.append(f"Extensión no reconocida: {path.suffix}")
                
            # Verificar que no sea un directorio especial
            special_dirs = {'.', '..', '~'}
            if path.name in special_dirs:
                errors.append(f"Nombre de directorio especial: {path.name}")
                
        except Exception as e:
            errors.append(f"Error procesando ruta: {e}")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=str(Path(file_path).resolve()) if not errors else None
        )
        
    @classmethod
    def _is_safe_relative_path(cls, path: str) -> bool:
        """Verifica si una ruta relativa es segura (no sale del directorio base)."""
        # Resolver la ruta y verificar que no contenga .. que escape
        try:
            normalized = os.path.normpath(path)
            return not (normalized.startswith('..') or '/..' in normalized or '\\..\\' in normalized)
        except:
            return False
            
    @classmethod
    def validate_url(cls, url: str) -> ValidationResult:
        """Valida una URL."""
        errors = []
        warnings = []
        
        if not url:
            errors.append("URL vacía")
            return ValidationResult(False, errors, warnings)
            
        try:
            parsed = urlparse(url)
            
            # Verificar esquema
            if parsed.scheme not in {'http', 'https'}:
                errors.append(f"Esquema de URL no permitido: {parsed.scheme}")
                
            # Verificar que tenga dominio
            if not parsed.netloc:
                errors.append("URL sin dominio válido")
                
            # Verificar caracteres peligrosos
            dangerous_chars = cls.DANGEROUS_SHELL_CHARS.intersection(set(url))
            if dangerous_chars:
                warnings.append(f"Caracteres potencialmente peligrosos: {dangerous_chars}")
                
        except Exception as e:
            errors.append(f"URL malformada: {e}")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=url if not errors else None
        )
        
    @classmethod
    def validate_genre_list(cls, genres: List[str]) -> ValidationResult:
        """Valida una lista de géneros musicales."""
        errors = []
        warnings = []
        sanitized_genres = []
        
        if not genres:
            warnings.append("Lista de géneros vacía")
            return ValidationResult(True, errors, warnings, [])
            
        # Géneros conocidos (lista básica, se puede expandir)
        known_genres = {
            'rock', 'pop', 'jazz', 'blues', 'country', 'electronic', 'hip hop',
            'classical', 'folk', 'reggae', 'punk', 'metal', 'alternative',
            'indie', 'dance', 'house', 'techno', 'ambient', 'experimental',
            'world', 'latin', 'r&b', 'soul', 'funk', 'disco', 'new wave'
        }
        
        for genre in genres:
            if not isinstance(genre, str):
                errors.append(f"Género no es string: {type(genre)}")
                continue
                
            # Sanitizar género
            sanitized_genre = cls._sanitize_genre(genre)
            
            if not sanitized_genre:
                warnings.append(f"Género vacío después de sanitizar: {genre}")
                continue
                
            # Verificar longitud
            if len(sanitized_genre) > 50:
                warnings.append(f"Género muy largo: {sanitized_genre[:20]}...")
                sanitized_genre = sanitized_genre[:50]
                
            # Verificar si es conocido
            if sanitized_genre.lower() not in known_genres:
                warnings.append(f"Género no reconocido: {sanitized_genre}")
                
            sanitized_genres.append(sanitized_genre)
            
        # Eliminar duplicados preservando orden
        seen = set()
        unique_genres = []
        for genre in sanitized_genres:
            if genre.lower() not in seen:
                seen.add(genre.lower())
                unique_genres.append(genre)
                
        if len(unique_genres) != len(sanitized_genres):
            warnings.append("Se encontraron géneros duplicados")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=unique_genres
        )
        
    @classmethod
    def _sanitize_genre(cls, genre: str) -> str:
        """Sanitiza un género musical."""
        # Normalizar y limpiar
        genre = unicodedata.normalize('NFKD', genre)
        genre = re.sub(r'\s+', ' ', genre).strip()
        
        # Convertir a título apropiado
        genre = genre.title()
        
        # Correcciones comunes
        corrections = {
            'Hip Hop': 'Hip-Hop',
            'R&B': 'R&B',
            'Rnb': 'R&B',
            'Electronic Dance Music': 'Electronic',
            'Edm': 'Electronic'
        }
        
        return corrections.get(genre, genre)
        
    @classmethod
    def validate_metadata_dict(cls, metadata: Dict[str, Any]) -> ValidationResult:
        """Valida un diccionario completo de metadatos."""
        errors = []
        warnings = []
        sanitized_metadata = {}
        
        required_fields = {'artist', 'title'}
        optional_fields = {'album', 'year', 'genre', 'track_number'}
        
        # Verificar campos requeridos
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                errors.append(f"Campo requerido faltante: {field}")
            else:
                # Validar campo específico
                if field in {'artist', 'title'}:
                    result = cls.validate_artist_title(str(metadata[field]), field)
                    if not result.is_valid:
                        errors.extend(result.errors)
                    warnings.extend(result.warnings)
                    sanitized_metadata[field] = result.sanitized_value
                    
        # Validar campos opcionales
        for field in optional_fields:
            if field in metadata and metadata[field]:
                value = metadata[field]
                
                if field == 'genre':
                    if isinstance(value, str):
                        genres = [g.strip() for g in value.split(';') if g.strip()]
                    elif isinstance(value, list):
                        genres = value
                    else:
                        warnings.append(f"Tipo de género inesperado: {type(value)}")
                        genres = [str(value)]
                        
                    result = cls.validate_genre_list(genres)
                    warnings.extend(result.warnings)
                    sanitized_metadata[field] = ';'.join(result.sanitized_value)
                    
                elif field == 'year':
                    try:
                        year = int(value)
                        if year < 1900 or year > 2030:
                            warnings.append(f"Año fuera de rango razonable: {year}")
                        sanitized_metadata[field] = year
                    except (ValueError, TypeError):
                        warnings.append(f"Año inválido: {value}")
                        
                elif field == 'track_number':
                    try:
                        track = int(value)
                        if track < 1 or track > 999:
                            warnings.append(f"Número de pista fuera de rango: {track}")
                        sanitized_metadata[field] = track
                    except (ValueError, TypeError):
                        warnings.append(f"Número de pista inválido: {value}")
                        
                else:
                    # Campo de texto general
                    result = cls.validate_artist_title(str(value), field)
                    warnings.extend(result.warnings)
                    sanitized_metadata[field] = result.sanitized_value
                    
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized_metadata
        )

class SecurityValidator:
    """Validador especializado en aspectos de seguridad."""
    
    @classmethod
    def is_safe_for_shell(cls, text: str) -> bool:
        """Verifica si un texto es seguro para usar en comandos shell."""
        dangerous_patterns = [
            r'[;&|`$()[\]{}*?<>]',  # Caracteres shell peligrosos
            r'\.\./|\.\.\\"',        # Path traversal
            r'^\s*[-/]',            # Parámetros que parecen flags
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text):
                return False
                
        return True
        
    @classmethod
    def sanitize_for_shell(cls, text: str) -> str:
        """Sanitiza texto para uso seguro en shell."""
        # Escapar caracteres especiales
        import shlex
        return shlex.quote(text)
        
    @classmethod
    def validate_cache_key(cls, key: str) -> ValidationResult:
        """Valida una clave de cache."""
        errors = []
        warnings = []
        
        if not key:
            errors.append("Clave de cache vacía")
            return ValidationResult(False, errors, warnings)
            
        # Verificar longitud
        if len(key) > 250:
            errors.append(f"Clave de cache demasiado larga: {len(key)}")
            
        # Verificar caracteres seguros
        if not re.match(r'^[a-zA-Z0-9_\-:.]+$', key):
            errors.append("Clave de cache contiene caracteres no permitidos")
            
        # Sanitizar
        sanitized = re.sub(r'[^a-zA-Z0-9_\-:.]', '_', key)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized
        )

# Funciones de conveniencia
def safe_filename(filename: str) -> str:
    """Devuelve una versión segura de un nombre de archivo."""
    result = DataValidator.validate_filename(filename)
    return result.sanitized_value or "unknown_file"

def safe_artist_title(text: str) -> str:
    """Devuelve una versión segura de artista o título."""
    result = DataValidator.validate_artist_title(text, "text")
    return result.sanitized_value or "Unknown"

def validate_and_log(validation_result: ValidationResult, context: str = ""):
    """Registra resultados de validación en logs."""
    if not validation_result.is_valid:
        logger.error(f"Validación fallida {context}: {validation_result.errors}")
    
    if validation_result.warnings:
        logger.warning(f"Advertencias de validación {context}: {validation_result.warnings}") 
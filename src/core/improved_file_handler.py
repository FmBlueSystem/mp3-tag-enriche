"""Módulo mejorado para manejo de archivos MP3 y extracción de metadatos."""
from typing import Dict, List, Optional, Tuple, Union
import re
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Patrones comunes para identificar artistas y títulos en nombres de archivo
FILENAME_PATTERNS = [
    # Patrón clásico: "Artista - Título"
    r'^(?P<artist>.+?)\s+-\s+(?P<title>.+)$',
    
    # Patrón con remix/version: "Artista - Título (Remix)"
    r'^(?P<artist>.+?)\s+-\s+(?P<title>.+?)(?:\s+[\(\[](?:[\w\s]+\s+)?(?:Remix|Mix|Edit|Version|Radio|Club|Extended|Instrumental|Acapella|Dub|VIP)[\)\]])$',
    
    # Patrón con featuring: "Artista - Título (feat. OtroArtista)"
    r'^(?P<artist>.+?)\s+-\s+(?P<title>.+?)(?:\s+[\(\[]feat(?:uring|\.)?[\s\.]+(?:.+?)[\)\]])$',
    
    # Patrón con featuring integrado: "Artista feat. OtroArtista - Título"
    r'^(?P<artist>.+?(?:\s+feat(?:uring|\.)?[\s\.]+(?:.+?)))\s+-\s+(?P<title>.+)$',
    
    # Patrón con año: "Artista - Título (Año)"
    r'^(?P<artist>.+?)\s+-\s+(?P<title>.+?)(?:\s+[\(\[]\d{4}[\)\]])$',
    
    # Patrón invertido: "Título - Artista" (menos común pero existe)
    r'^(?P<title>.+?)\s+-\s+(?:by\s+)?(?P<artist>.+)$',
    
    # Patrón con múltiples artistas: "Artista1 & Artista2 - Título"
    r'^(?P<artist>.+?(?:\s+(?:&|and|con|with|y|ft\.?|feat\.?)\s+.+?))\s+-\s+(?P<title>.+)$',
    
    # Patrón de nombre de archivo DJ: "XX-XX Artist - Title"
    r'^(?:\d+[\-\.]\d+\s+)?(?P<artist>.+?)\s+-\s+(?P<title>.+)$',
    
    # Patrón con BPM o key: "Artista - Título [BPM]" o "Artista - Título [Key]"
    r'^(?P<artist>.+?)\s+-\s+(?P<title>.+?)(?:\s+[\(\[]\d+(?:[\s\.]?\w+)?[\)\]])$',
]

def extract_artist_title_improved(filename: str, 
                                 fallback_artist: str = "", 
                                 fallback_title: str = "") -> Tuple[str, str]:
    """Extrae artista y título desde un nombre de archivo usando patrones avanzados.
    
    Args:
        filename: Nombre de archivo (sin extensión) a analizar
        fallback_artist: Nombre de artista a usar si no se puede extraer
        fallback_title: Título a usar si no se puede extraer
        
    Returns:
        Tupla con (artista, título)
    """
    # Eliminar números de track al principio si existen
    cleaned_filename = re.sub(r'^(\d+[\s\._-]+)', '', filename)
    
    # Eliminar información de álbum entre corchetes si existe
    cleaned_filename = re.sub(r'\s+\[(?:álbum|album|compilation|recopilación|OST).*?\]', '', cleaned_filename, flags=re.IGNORECASE)
    
    # Intentar reconocer patrones comunes
    for pattern in FILENAME_PATTERNS:
        match = re.match(pattern, cleaned_filename, re.IGNORECASE)
        if match:
            artist = match.group('artist').strip()
            title = match.group('title').strip()
            
            # Validación básica: asegurarse de que ambos tengan contenido
            if artist and title:
                logger.debug(f"Patrón detectado: {pattern}")
                logger.debug(f"Extracción exitosa: Artist='{artist}', Title='{title}'")
                return artist, title
    
    # Si no se reconoce ningún patrón pero hay un guion, usar el método básico
    if " - " in cleaned_filename:
        parts = cleaned_filename.split(" - ", 1)
        if len(parts) == 2:
            artist = parts[0].strip()
            title = parts[1].strip()
            
            # Verificar si el formato podría estar invertido (título primero)
            # Esto es heurístico y podría mejorarse con una lista de artistas conocidos
            if len(artist.split()) > 4 and len(title.split()) < 3:
                # Probablemente está invertido
                artist, title = title, artist
                
            return artist, title
    
    # Última opción: intentar detectar casos de "Artist_Title" o "Artist-Title" sin espacios
    for separator in ['_', '-']:
        if separator in cleaned_filename and ' ' not in cleaned_filename:
            parts = cleaned_filename.split(separator, 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
    
    # Si todo falla, usar fallbacks
    artist = fallback_artist
    title = fallback_title or cleaned_filename
    
    logger.debug(f"No se pudo extraer artista/título, usando fallbacks: Artist='{artist}', Title='{title}'")
    return artist, title

def post_process_artist(artist: str) -> str:
    """Realiza post-procesamiento en el nombre del artista."""
    if not artist:
        return "Unknown Artist"
    
    # Eliminar prefijos como "The" si está al final entre paréntesis
    artist = re.sub(r',\s+The$', '', artist)
    
    # Eliminar información irrelevante
    artist = re.sub(r'\(Official\)|\(Official Artist\)|\(VEVO\)', '', artist, flags=re.IGNORECASE).strip()
    
    # Normalizar feat/ft./featuring
    artist = re.sub(r'feat\.?(?=\s)', 'feat.', artist, flags=re.IGNORECASE)
    artist = re.sub(r'ft\.?(?=\s)', 'ft.', artist, flags=re.IGNORECASE)
    
    # Capitalizar nombres propios básicos (no incluye reglas complejas para todas las excepciones)
    return ' '.join(word.capitalize() if word.lower() not in ['feat.', 'ft.', 'and', 'or', 'the', 'of', 'by', 'with'] 
                  else word for word in artist.split())

def post_process_title(title: str) -> str:
    """Realiza post-procesamiento en el título de la canción."""
    if not title:
        return "Unknown Title"
    
    # Eliminar información irrelevante
    title = re.sub(r'\(Official (?:Video|Audio|Music Video|Lyric Video)\)|\(VEVO\)|\(Audio\)', '', title, flags=re.IGNORECASE).strip()
    
    # Normalizar remix/version/edit designations
    title = re.sub(r'(?<=\s)rmx(?=[\s\)\]])|\bremx\b', 'Remix', title, flags=re.IGNORECASE)
    title = re.sub(r'(?<=\s)ed(?:it)?(?=[\s\)\]])|\bedit\b', 'Edit', title, flags=re.IGNORECASE)
    title = re.sub(r'(?<=\s)ext(?:ended)?(?=[\s\)\]])|\bextended\b', 'Extended', title, flags=re.IGNORECASE)
    
    # Capitalizar primera letra de cada palabra excepto conectores
    return ' '.join(word.capitalize() if word.lower() not in ['a', 'an', 'the', 'in', 'on', 'at', 'by', 'for', 'with', 'and', 'but', 'or'] or i == 0
                  else word for i, word in enumerate(title.split()))

def extract_and_clean_metadata(filename: str, 
                              tag_artist: str = "", 
                              tag_title: str = "") -> Tuple[str, str]:
    """Extrae y limpia metadatos de un nombre de archivo con post-procesamiento.
    
    Args:
        filename: Nombre de archivo sin extensión
        tag_artist: Artista desde etiquetas ID3 (fallback)
        tag_title: Título desde etiquetas ID3 (fallback)
        
    Returns:
        Tupla (artista_procesado, título_procesado)
    """
    # Extraer información básica
    raw_artist, raw_title = extract_artist_title_improved(filename, tag_artist, tag_title)
    
    # Aplicar post-procesamiento
    processed_artist = post_process_artist(raw_artist)
    processed_title = post_process_title(raw_title)
    
    return processed_artist, processed_title

# Función de ejemplo para integrar con el código existente
def test_extraction_and_formatting(input_filename: str) -> Dict[str, str]:
    """Función de prueba para la nueva implementación."""
    result = {}
    
    # Extraer nombre base sin extensión
    base_name = os.path.splitext(os.path.basename(input_filename))[0]
    
    # Extraer y limpiar metadatos
    artist, title = extract_and_clean_metadata(base_name)
    
    # Agregar al resultado
    result['filename'] = input_filename
    result['base_name'] = base_name
    result['extracted_artist'] = artist
    result['extracted_title'] = title
    
    return result

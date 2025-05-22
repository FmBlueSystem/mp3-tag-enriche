"""Test de extracción mejorada de metadatos desde nombres de archivo."""
import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Agregar el directorio del proyecto al path para importaciones relativas
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from src.core.improved_file_handler import (
    extract_artist_title_improved,
    post_process_artist,
    post_process_title,
    extract_and_clean_metadata,
    test_extraction_and_formatting
)

# Casos de prueba: diferentes patrones de nombres de archivo
test_cases = [
    # Caso básico
    "Artist - Title",
    
    # Con remix
    "Artist - Title (Remix)",
    "Artist - Title (Club Remix)",
    "Artist - Title [Extended Mix]",
    "Artist - Title (Radio Edit)",
    
    # Con featuring
    "Artist - Title (feat. Other Artist)",
    "Artist feat. Other Artist - Title",
    "Artist ft. Other Artist - Title",
    "Artist featuring Other Artist - Title",
    
    # Con año
    "Artist - Title (2023)",
    
    # Con multiple info
    "Artist - Title (Remix) [2023]",
    "Artist - Title (feat. Other Artist) (Remix)",
    
    # Nombres de archivo reales complejos
    "01. Calvin Harris - Summer (Calvin Harris & R3hab Remix)",
    "Avicii - Levels (Skrillex Remix) [HQ]",
    "DJ Snake ft. Justin Bieber - Let Me Love You",
    "Daft Punk - Around The World (Official Video) [HD]",
    "16-02 DJ Snake, Lil Jon - Turn Down For What (Original Mix)",
    "Dua Lipa - Don't Start Now [Official Music Video]",
    
    # Casos invertidos o sin guiones
    "Billie Jean - Michael Jackson",
    "Thriller by Michael Jackson",
    "Queen_Bohemian_Rhapsody",
    
    # Casos confusos o difíciles
    "The Beatles, The Rolling Stones - Come Together (Live)",
    "Ultimate Remix Collection - Best of 80s",
    "01 - Track 1",
    "Unknown Artist - Track 01",
    "Viola Wills - Hot For You Ultimix By Les Massengale",
    "Joan Jett - I Love Rock Roll Quantized - Super Short Edit",
    "X-Mix Club Classics####InvalidArtist@@@@"
]

def main():
    """Ejecuta los casos de prueba."""
    print("PRUEBA DE EXTRACCIÓN MEJORADA DE METADATOS")
    print("=" * 50)
    
    for i, filename in enumerate(test_cases, 1):
        print(f"\nCaso #{i}: '{filename}'")
        print("-" * 50)
        
        # Método básico (equivalente al original pero con patrones mejorados)
        artist, title = extract_artist_title_improved(filename)
        print(f"Extracción básica:")
        print(f"  Artist: '{artist}'")
        print(f"  Title: '{title}'")
        
        # Método completo con post-procesamiento
        artist, title = extract_and_clean_metadata(filename)
        print(f"Extracción mejorada con limpieza:")
        print(f"  Artist: '{artist}'")
        print(f"  Title: '{title}'")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script para demostrar las mejoras en la extracción de metadatos de archivos MP3.
Este script busca archivos MP3 en un directorio, compara la extracción 
original y mejorada, y muestra un informe detallado.
"""
import os
import sys
import logging
import argparse
from typing import Dict, List, Tuple
from pathlib import Path
from tabulate import tabulate

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar el directorio del proyecto al path para importaciones relativas
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)

# Importar los manipuladores de archivos
from src.core.file_handler import Mp3FileHandler
from src.core.enhanced_mp3_handler import EnhancedMp3FileHandler, compare_extraction_methods

# Lista de casos de prueba para demostrar la funcionalidad mejorada
TEST_CASES = [
    "Artist - Title",
    "Artist_Title",
    "Artist-Title",
    "01 - Artist - Title",
    "01. Artist - Title",
    "Artist feat. OtherArtist - Title",
    "Artist - Title feat. OtherArtist",
    "Artist - Title (Remix)",
    "Artist - Title [Official Video]",
    "Artist - Title (Official Audio)",
    "Artist & OtherArtist - Title",
    "Title - Artist",  # Caso invertido
    "01-01 Artist - Title",
    "Artist - Title (2023)",
    "Artist - Title [320kbps]",
]

def create_test_report(test_cases: List[str] = None) -> None:
    """
    Genera un informe de prueba con casos de ejemplo para demostrar las mejoras.
    
    Args:
        test_cases: Lista de nombres de archivo de prueba
    """
    if not test_cases:
        test_cases = TEST_CASES
    
    # Handlers para comparación
    original = Mp3FileHandler()
    enhanced = EnhancedMp3FileHandler()
    
    print("\nDEMOSTRACIÓN DE MEJORAS EN EXTRACCIÓN DE METADATOS")
    print("=" * 60)
    print("Comparación de la extracción original vs. mejorada con casos de prueba")
    print("-" * 60)
    
    table_data = []
    
    for filename in test_cases:
        # Extracción original
        orig_artist, orig_title = original.extract_artist_title_from_filename(filename)
        
        # Extracción mejorada
        enh_artist, enh_title = enhanced.extract_artist_title_from_filename(filename)
        
        # Comprobar si hubo mejora
        is_improved = (orig_artist != enh_artist) or (orig_title != enh_title)
        improved_mark = "✓" if is_improved else "="
        
        # Agregar a datos de tabla
        table_data.append([
            filename,
            f"{orig_artist} - {orig_title}",
            f"{enh_artist} - {enh_title}",
            improved_mark
        ])
    
    # Mostrar informe
    headers = ["Nombre de archivo", "Original (Artist - Title)", "Mejorado (Artist - Title)", "¿Mejorado?"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Estadísticas
    improved_count = sum(1 for row in table_data if row[3] == "✓")
    total = len(table_data)
    
    print(f"\nEstadísticas:")
    print(f"  Total casos: {total}")
    print(f"  Casos mejorados: {improved_count} ({improved_count/total*100:.1f}%)")
    print(f"  Sin cambios: {total - improved_count} ({(total-improved_count)/total*100:.1f}%)")

def analyze_real_files(directory: str, limit: int = 10, verbose: bool = False) -> None:
    """
    Analiza archivos MP3 reales en un directorio.
    
    Args:
        directory: Directorio a analizar
        limit: Número máximo de archivos a procesar
        verbose: Si True, muestra información detallada
    """
    if not os.path.isdir(directory):
        logger.error(f"Directorio no válido: {directory}")
        return
    
    # Encontrar archivos MP3
    mp3_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.mp3'):
                mp3_files.append(os.path.join(root, file))
                if len(mp3_files) >= limit:
                    break
        if len(mp3_files) >= limit:
            break
    
    if not mp3_files:
        logger.error(f"No se encontraron archivos MP3 en: {directory}")
        return
    
    logger.info(f"Analizando {len(mp3_files)} archivos MP3...")
    
    # Comparar métodos de extracción
    print("\nCOMPARACIÓN CON ARCHIVOS REALES")
    print("=" * 60)
    
    table_headers = ["Nombre de archivo", "Original (Artist - Title)", "Mejorado (Artist - Title)", "¿Mejorado?"]
    table_data = []
    
    improved_artists = 0
    improved_titles = 0
    
    for file_path in mp3_files:
        # Obtener comparación
        result = compare_extraction_methods(file_path)
        
        # Contar mejoras específicas
        if result['artist_improved']:
            improved_artists += 1
        if result['title_improved']:
            improved_titles += 1
        
        # Formatear para mostrar
        filename = os.path.basename(file_path)
        orig_metadata = f"{result['original']['artist']} - {result['original']['title']}"
        enhanced_metadata = f"{result['enhanced']['artist']} - {result['enhanced']['title']}"
        improved = "✓" if result['artist_improved'] or result['title_improved'] else "="
        
        table_data.append([filename, orig_metadata, enhanced_metadata, improved])
        
        if verbose:
            print(f"\nDetalles para: {filename}")
            print(f"  Original: Artist='{result['original']['artist']}', Title='{result['original']['title']}'")
            print(f"  Mejorado: Artist='{result['enhanced']['artist']}', Title='{result['enhanced']['title']}'")
    
    print(tabulate(table_data, headers=table_headers, tablefmt="grid"))
    
    # Estadísticas
    total_files = len(table_data)
    improved_count = sum(1 for row in table_data if row[3] == "✓")
    
    print(f"\nEstadísticas de mejora:")
    print(f"  Total archivos: {total_files}")
    print(f"  Archivos con metadatos mejorados: {improved_count} ({improved_count/total_files*100:.1f}%)")
    print(f"  Mejoras en artistas: {improved_artists} ({improved_artists/total_files*100:.1f}%)")
    print(f"  Mejoras en títulos: {improved_titles} ({improved_titles/total_files*100:.1f}%)")

def analyze_patterns(directory: str) -> None:
    """
    Analiza los patrones de nombres de archivo en un directorio.
    
    Args:
        directory: Directorio a analizar
    """
    handler = EnhancedMp3FileHandler()
    patterns = handler.analyze_filename_patterns(directory)
    
    print("\nANÁLISIS DE PATRONES DE NOMBRES DE ARCHIVO")
    print("=" * 50)
    
    total = sum(patterns.values())
    if total == 0:
        print("No se encontraron archivos MP3 para analizar")
        return
    
    table_data = []
    for pattern, count in patterns.items():
        percentage = (count / total) * 100
        table_data.append([pattern, count, f"{percentage:.1f}%"])
    
    print(tabulate(table_data, 
                  headers=["Patrón", "Cantidad", "Porcentaje"],
                  tablefmt="grid"))

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Demostrar mejoras en extracción de metadatos')
    
    parser.add_argument('--directory', '-d', type=str, 
                       help='Directorio con archivos MP3 a analizar')
    
    parser.add_argument('--limit', '-l', type=int, default=10,
                       help='Número máximo de archivos a analizar (default: 10)')
    
    parser.add_argument('--analyze-patterns', '-a', action='store_true',
                       help='Analizar patrones de nombres en el directorio')
    
    parser.add_argument('--test-cases', '-t', action='store_true',
                       help='Mostrar casos de prueba predefinidos')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Modo verboso con información detallada')
    
    args = parser.parse_args()
    
    # Mostrar casos de prueba predefinidos
    if args.test_cases:
        create_test_report()
    
    # Analizar directorio si se especifica
    if args.directory:
        if args.analyze_patterns:
            analyze_patterns(args.directory)
        
        analyze_real_files(args.directory, args.limit, args.verbose)
    
    # Si no se especifica directorio ni test_cases, mostrar ayuda
    if not args.directory and not args.test_cases:
        parser.print_help()

if __name__ == "__main__":
    main()

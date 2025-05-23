"""Script para probar la extracción mejorada de metadatos con archivos reales."""
import os
import sys
import logging
import argparse
from typing import Dict, List
from pathlib import Path
from tabulate import tabulate

# Configurar logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar el directorio del proyecto al path para importaciones relativas
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)

# Importar los manipuladores de archivos
from src.core.file_handler import Mp3FileHandler
from src.core.enhanced_mp3_handler import EnhancedMp3FileHandler, compare_extraction_methods

def parse_args():
    """Configurar y parsear argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Comparar extracción de metadatos original vs. mejorada')
    
    parser.add_argument('--directory', '-d', type=str, 
                        help='Directorio con archivos MP3 a analizar')
    
    parser.add_argument('--files', '-f', type=str, nargs='+',
                        help='Lista específica de archivos MP3 a analizar')
    
    parser.add_argument('--limit', '-l', type=int, default=10,
                        help='Número máximo de archivos a analizar (default: 10)')
    
    parser.add_argument('--analyze-patterns', '-a', action='store_true',
                        help='Analizar patrones de nombres en el directorio')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Modo verboso con información detallada')
    
    return parser.parse_args()

def get_mp3_files(directory: str, limit: int = None) -> List[str]:
    """Obtiene la lista de archivos MP3 en un directorio.
    
    Args:
        directory: Ruta al directorio
        limit: Número máximo de archivos a devolver
        
    Returns:
        Lista de rutas a archivos MP3
    """
    if not os.path.isdir(directory):
        logger.error(f"No es un directorio válido: {directory}")
        return []
    
    mp3_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.mp3'):
                mp3_files.append(os.path.join(root, file))
                if limit and len(mp3_files) >= limit:
                    return mp3_files
    
    return mp3_files

def analyze_patterns(directory: str) -> None:
    """Analiza y muestra patrones de nombres de archivo en un directorio.
    
    Args:
        directory: Ruta al directorio con archivos MP3
    """
    if not os.path.isdir(directory):
        logger.error(f"No es un directorio válido: {directory}")
        return
    
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

def compare_and_display(files: List[str], verbose: bool = False) -> None:
    """Compara y muestra los resultados de extracción original vs. mejorada.
    
    Args:
        files: Lista de rutas a archivos MP3
        verbose: Si True, muestra información detallada
    """
    if not files:
        print("No se especificaron archivos para analizar")
        return
    
    print("\nCOMPARACIÓN DE MÉTODOS DE EXTRACCIÓN")
    print("=" * 50)
    
    table_headers = ["Nombre de archivo", "Original (Artist - Title)", "Mejorado (Artist - Title)", "¿Mejorado?"]
    table_data = []
    
    for file_path in files:
        if not os.path.exists(file_path):
            logger.warning(f"Archivo no encontrado: {file_path}")
            continue
        
        # Obtener comparación
        result = compare_extraction_methods(file_path)
        
        # Formatear para mostrar
        filename = os.path.basename(file_path)
        orig_metadata = f"{result['original']['artist']} - {result['original']['title']}"
        enhanced_metadata = f"{result['enhanced']['artist']} - {result['enhanced']['title']}"
        improved = "✓" if result['artist_improved'] or result['title_improved'] else "="
        
        table_data.append([filename, orig_metadata, enhanced_metadata, improved])
        
        if verbose:
            print(f"\nDetalles para: {filename}")
            print(f"  Nombre base: {result['base_name']}")
            print(f"  Original: Artist='{result['original']['artist']}', Title='{result['original']['title']}'")
            print(f"  Mejorado: Artist='{result['enhanced']['artist']}', Title='{result['enhanced']['title']}'")
            print(f"  Mejoras: Artist={result['artist_improved']}, Title={result['title_improved']}")
    
    print(tabulate(table_data, headers=table_headers, tablefmt="grid"))
    
    # Estadísticas finales
    improved_count = sum(1 for row in table_data if row[3] == "✓")
    same_count = sum(1 for row in table_data if row[3] == "=")
    
    print(f"\nEstadísticas:")
    print(f"  Total archivos: {len(table_data)}")
    print(f"  Metadatos mejorados: {improved_count} ({improved_count/len(table_data)*100:.1f}%)")
    print(f"  Sin cambios: {same_count} ({same_count/len(table_data)*100:.1f}%)")

def main():
    """Función principal."""
    args = parse_args()
    
    # Configurar nivel de logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Obtener lista de archivos a analizar
    files_to_analyze = []
    
    if args.files:
        files_to_analyze = [f for f in args.files if os.path.exists(f) and f.lower().endswith('.mp3')]
        logger.info(f"Analizando {len(files_to_analyze)} archivos especificados")
    
    elif args.directory:
        files_to_analyze = get_mp3_files(args.directory, args.limit)
        logger.info(f"Encontrados {len(files_to_analyze)} archivos MP3 en {args.directory}")
        
        # Análisis de patrones si se solicita
        if args.analyze_patterns:
            analyze_patterns(args.directory)
    
    else:
        logger.error("Debe especificar un directorio o archivos para analizar")
        return
    
    # Realizar y mostrar la comparación
    compare_and_display(files_to_analyze, args.verbose)

if __name__ == "__main__":
    main()

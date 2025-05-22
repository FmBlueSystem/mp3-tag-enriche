#!/usr/bin/env python3
"""
Script para procesar por lotes archivos MP3 con el nuevo método de extracción.
Este script puede actualizar las etiquetas ID3 de los archivos MP3 con los
metadatos extraídos mejorados.
"""
import os
import sys
import logging
import argparse
import mutagen
from mutagen.id3 import ID3, TIT2, TPE1
from typing import Dict, List, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
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
from src.core.enhanced_mp3_handler import EnhancedMp3FileHandler

# Crear directorio de backups
backup_dir = os.path.join(project_dir, "mp3_backups")
os.makedirs(backup_dir, exist_ok=True)
logger.info(f"Usando directorio de backups: {backup_dir}")

def process_file(file_path: str, dry_run: bool = True, force: bool = False, debug: bool = False) -> Dict:
    """
    Procesa un archivo MP3 actualizando sus metadatos.
    
    Args:
        file_path: Ruta al archivo MP3
        dry_run: Si True, solo simula los cambios sin aplicarlos
        force: Si True, actualiza etiquetas aunque ya existan
        debug: Si True, muestra información detallada de diagnóstico
        
    Returns:
        Diccionario con los resultados del procesamiento
    """
    result = {
        'file': file_path,
        'filename': os.path.basename(file_path),
        'original': {},
        'enhanced': {},
        'updated': False,
        'error': None,
        'debug_info': {}
    }
    
    try:
        # Obtener metadatos actuales
        try:
            audio = ID3(file_path)
            current_artist = str(audio.get('TPE1', ''))
            current_title = str(audio.get('TIT2', ''))
            
            result['original'] = {
                'artist': current_artist,
                'title': current_title
            }
        except Exception as e:
            logger.debug(f"No se pudieron leer etiquetas ID3 de {file_path}: {e}")
            audio = None
            result['original'] = {
                'artist': '',
                'title': ''
            }
        
        # Extraer metadatos mejorados
        handler = EnhancedMp3FileHandler(backup_dir=backup_dir)
        info = handler.get_file_info(file_path)
        
        enhanced_artist = info.get('artist', '')
        enhanced_title = info.get('title', '')
        
        result['enhanced'] = {
            'artist': enhanced_artist,
            'title': enhanced_title
        }
        
        # Determinar si necesitamos actualizar
        update_artist = force or not current_artist or current_artist == 'Unknown Artist'
        update_title = force or not current_title or current_title == 'Unknown Title'
        update_genre = force or not audio.get('TCON')  # Actualizar género si no existe o force=True

        # Añadir info de depuración
        result['debug_info']['update_artist'] = update_artist
        result['debug_info']['update_title'] = update_title
        result['debug_info']['update_genre'] = update_genre
        result['debug_info']['current_artist_empty'] = not current_artist
        result['debug_info']['current_title_empty'] = not current_title
        result['debug_info']['enhanced_artist_empty'] = not enhanced_artist
        result['debug_info']['enhanced_title_empty'] = not enhanced_title
        
        need_update = (update_artist and enhanced_artist) or (update_title and enhanced_title)
        result['debug_info']['need_update'] = need_update
        
        # Actualizar etiquetas si es necesario
        if need_update and not dry_run:
            try:
                if not audio:
                    audio = ID3()
                
                # Preserve existing metadata first
                preserved = handler._preserve_metadata(audio)
                
                # Update the main fields
                if update_artist and enhanced_artist:
                    audio['TPE1'] = TPE1(encoding=3, text=enhanced_artist)
                
                if update_title and enhanced_title:
                    audio['TIT2'] = TIT2(encoding=3, text=enhanced_title)
                    
                # Update genres (single string value for compatibility)
                if 'genres' in info and info['genres']:
                    from mutagen.id3 import TCON
                    genres = []
                    try:
                        # Convert any genre info to a list of strings
                        if isinstance(info['genres'], (list, tuple)):
                            genres = [str(g) for g in info['genres'] if g]
                        elif isinstance(info['genres'], dict):
                            # Handle genre dictionaries with confidence scores
                            genre_items = sorted(info['genres'].items(), key=lambda x: x[1], reverse=True)
                            genres = [str(g[0]) for g in genre_items if g[0]]
                        elif info['genres']:
                            genres = [str(info['genres'])]
                            
                        if genres:
                            audio['TCON'] = TCON(encoding=3, text=genres)
                    except Exception as e:
                        logger.error(f"Error al procesar géneros para {file_path}: {e}")
                
                # Restore preserved fields
                for field, value in preserved.items():
                    frame_id = None
                    for id, name in handler._preserve_metadata.__annotations__['return']['tag_fields'].items():
                        if name == field:
                            frame_id = id
                            break
                    if frame_id and frame_id not in ['TPE1', 'TIT2']:  # Don't overwrite main fields
                        audio[frame_id] = ID3._framespec[frame_id](encoding=3, text=value)
                
                # Save changes
                audio.save(file_path)
                result['updated'] = True
                result['preserved_fields'] = list(preserved.keys())
                logger.info(f"Updated: {file_path} (preserved fields: {', '.join(preserved.keys())})")
                
            except Exception as e:
                logger.error(f"Error saving ID3 tags: {e}")
                result['error'] = f"Error saving tags: {e}"
        elif need_update:
            # Simulación (dry run)
            result['updated'] = True
            logger.info(f"Actualización simulada: {file_path}")
        else:
            logger.debug(f"No se necesita actualizar: {file_path}")
            
    except Exception as e:
        logger.error(f"Error procesando {file_path}: {e}")
        result['error'] = str(e)
    
    return result

def batch_process(directory: str, dry_run: bool = True, force: bool = False, 
                  max_files: int = None, workers: int = 4, debug: bool = False) -> List[Dict]:
    """
    Procesa por lotes archivos MP3 en un directorio.
    
    Args:
        directory: Directorio a procesar
        dry_run: Si True, solo simula los cambios
        force: Si True, actualiza metadatos aunque ya existan
        max_files: Número máximo de archivos a procesar
        workers: Número de trabajadores paralelos
        debug: Si True, incluye información detallada de diagnóstico
        
    Returns:
        Lista con resultados del procesamiento
    """
    if not os.path.isdir(directory):
        logger.error(f"Directorio no válido: {directory}")
        return []
    
    # Encontrar archivos MP3
    mp3_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.mp3'):
                mp3_files.append(os.path.join(root, file))
                if max_files and len(mp3_files) >= max_files:
                    break
        if max_files and len(mp3_files) >= max_files:
            break
    
    if not mp3_files:
        logger.error(f"No se encontraron archivos MP3 en: {directory}")
        return []
    
    logger.info(f"Procesando {len(mp3_files)} archivos MP3 {'(simulación)' if dry_run else ''}...")
    
    # Procesar archivos en paralelo
    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(process_file, f, dry_run, force, debug) for f in mp3_files]
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Error en proceso paralelo: {e}")
    
    return results

def display_results(results: List[Dict]) -> None:
    """
    Muestra un resumen de los resultados del procesamiento.
    
    Args:
        results: Lista con resultados del procesamiento
    """
    if not results:
        print("No hay resultados para mostrar.")
        return
    
    print("\nRESUMEN DE PROCESAMIENTO")
    print("=" * 60)
    
    # Estadísticas
    total = len(results)
    updated = sum(1 for r in results if r['updated'])
    errors = sum(1 for r in results if r['error'])
    
    print(f"Total archivos procesados: {total}")
    print(f"Archivos actualizados: {updated} ({updated/total*100:.1f}%)")
    print(f"Errores: {errors} ({errors/total*100:.1f}%)")
    
    # Tabla con resultados
    table_data = []
    for r in results:
        if r['updated']:
            orig = f"{r['original'].get('artist', '')} - {r['original'].get('title', '')}"
            enhanced = f"{r['enhanced'].get('artist', '')} - {r['enhanced'].get('title', '')}"
            status = "ERROR" if r['error'] else "✓"
            table_data.append([r['filename'], orig, enhanced, status])
    
    if table_data:
        print("\nARCHIVOS ACTUALIZADOS:")
        headers = ["Archivo", "Original (Artist - Title)", "Actualizado (Artist - Title)", "Estado"]
        print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[30, 30, 30, 8]))
    
    # Mostrar errores si hay
    if errors:
        print("\nERRORES:")
        for r in results:
            if r['error']:
                print(f"  {r['filename']}: {r['error']}")
    
    # Mostrar info de debug si está disponible
    debug_info_available = any('debug_info' in r and r['debug_info'] for r in results)
    if debug_info_available:
        print("\nINFORMACIÓN DE DIAGNÓSTICO:")
        for r in results:
            if 'debug_info' in r and r['debug_info']:
                print(f"\nArchivo: {r['filename']}")
                for key, value in r['debug_info'].items():
                    print(f"  {key}: {value}")

def batch_process_mp3():
    """Process MP3 files in a directory."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', '-d', 
                    help='Directory containing MP3 files to process',
                    required=False)
    parser.add_argument('--file', '-f',
                    help='Single MP3 file to process',
                    required=False)
    parser.add_argument('--apply', '-a',
                    help='Apply changes to files', 
                    action='store_true')
    parser.add_argument('--force', 
                    help='Force metadata update even if already populated',
                    action='store_true')
    parser.add_argument('--limit',
                    help='Limit number of files to process',
                    type=int)
    parser.add_argument('--workers',
                    help='Number of worker processes',
                    type=int,
                    default=2)
    parser.add_argument('--verbose', '-v',
                    help='Enable verbose output',
                    action='store_true')
    parser.add_argument('--debug',
                    help='Enable debug output',
                    action='store_true')
    args = parser.parse_args()
    
    if not args.directory and not args.file:
        parser.error("Either --directory/-d or --file/-f is required")

    config = Config()
    config.apply_changes = args.apply 
    config.force_update = args.force
    config.file_limit = args.limit
    config.worker_processes = args.workers
    config.verbose = args.verbose
    config.debug = args.debug

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            return
            
        # Process single file
        files = [args.file]
        directory = os.path.dirname(args.file)
    else:
        # Process directory
        directory = args.directory
        files = get_mp3_files(directory, limit=config.file_limit)
    
    print(f"\nProcessing {len(files)} files...")
    print(f"{'Simulation only - ' if not config.apply_changes else ''}Changes {'will' if config.apply_changes else 'would'} be applied")
    
    results = process_files(files, config)
    display_results(results, config)

def display_results(results: List[Dict]):
    """
    Muestra un resumen de los resultados del procesamiento.
    
    Args:
        results: Lista con resultados del procesamiento
    """
    print("\nRESULTADOS DEL PROCESAMIENTO:")
    print("=" * 80)
    
    # Estadísticas
    total = len(results)
    updated = sum(1 for r in results if r['updated'])
    errors = sum(1 for r in results if r['error'])
    
    print(f"\nEstadísticas:")
    print(f"  Total archivos: {total}")
    print(f"  Actualizados: {updated} ({updated/total*100:.1f}%)")
    print(f"  Errores: {errors} ({errors/total*100:.1f}%)")
    
    # Mostrar actualizaciones
    if updated > 0:
        print("\nArchivos actualizados:")
        for r in results:
            if r['updated']:
                print(f"\n{r['filename']}")
                if 'original' in r and 'enhanced' in r:
                    print(f"  Original:  {r['original'].get('artist', '')} - {r['original'].get('title', '')}")
                    print(f"  Mejorado:  {r['enhanced'].get('artist', '')} - {r['enhanced'].get('title', '')}")
                if 'preserved_fields' in r:
                    print(f"  Campos preservados: {', '.join(r['preserved_fields'])}")
    
    # Mostrar errores
    if errors > 0:
        print("\nErrores encontrados:")
        for r in results:
            if r['error']:
                print(f"  {r['filename']}: {r['error']}")
    
    # Mostrar info de debug si está disponible
    debug_available = any('debug_info' in r and r['debug_info'] for r in results)
    if debug_available:
        print("\nInformación de diagnóstico:")
        for r in results:
            if 'debug_info' in r and r['debug_info']:
                print(f"\n{r['filename']}:")
                for key, value in r['debug_info'].items():
                    print(f"  {key}: {value}")

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='Procesar por lotes archivos MP3 con el extractor mejorado'
    )
    
    parser.add_argument('--directory', '-d', type=str, required=True,
                        help='Directorio con archivos MP3 a procesar')
    
    parser.add_argument('--apply', '-a', action='store_true',
                        help='Aplicar cambios (sin esto, solo es simulación)')
    
    parser.add_argument('--force', '-f', action='store_true',
                        help='Forzar actualización incluso si ya hay metadatos')
    
    parser.add_argument('--limit', '-l', type=int, default=None,
                        help='Límite de archivos a procesar (default: todos)')
    
    parser.add_argument('--workers', '-w', type=int, default=4,
                        help='Número de trabajadores paralelos (default: 4)')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Modo verboso con información detallada')
    
    parser.add_argument('--debug', '-D', action='store_true',
                        help='Incluir información de diagnóstico en los resultados')
    
    args = parser.parse_args()
    
    # Configurar nivel de logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    elif args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Ejecutar procesamiento
    dry_run = not args.apply
    results = batch_process(
        args.directory, 
        dry_run=dry_run,
        force=args.force,
        max_files=args.limit,
        workers=args.workers,
        debug=args.debug
    )
    
    # Mostrar resultados
    display_results(results)
    
    # Mensaje final
    if dry_run and results:
        print("\nEste fue un análisis de simulación. Para aplicar los cambios, utilice la opción --apply")

if __name__ == "__main__":
    main()

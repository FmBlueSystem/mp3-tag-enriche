#!/usr/bin/env python3
"""
📄 SCRIPT DE DEMOSTRACIÓN PARA IMPORT MANAGER - NUEVA BIBLIOTECA
==============================================================
Demuestra el uso de ImportManager para escanear, extraer, enriquecer
y guardar metadatos de archivos musicales en una base de datos.
"""

import sys
import os
import logging
import time
from pathlib import Path
from dataclasses import asdict # Para imprimir TrackMetadata

# Añadir la raíz del proyecto al PYTHONPATH para que 'src' sea un paquete de primer nivel
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    # Usar importaciones absolutas desde la raíz del proyecto (donde está 'src')
    from src.importers.import_manager import ImportManager, ImportProgress, TrackMetadata
    from src.core.database.db_manager import DBManager # Para verificación opcional
    from src.data import crud # Para verificación opcional
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    print("Asegúrate de que el script se ejecuta desde la raíz del proyecto.")
    print(f"PYTHONPATH actual: {sys.path}")
    sys.exit(1)

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def progress_callback(progress: ImportProgress):
    """Función de callback simple para mostrar el progreso de la importación."""
    if progress.total_files > 0:
        percentage = (progress.files_processed / progress.total_files) * 100
        progress_bar = '#' * int(percentage / 5) + '-' * (20 - int(percentage / 5))
        logger.info(
            f"Fase: {progress.phase} | {progress_bar} | "
            f"{progress.files_processed}/{progress.total_files} archivos | "
            f"Op: {progress.current_operation[:50]}... | "
            f"Errores: {progress.errors_count}"
        )
    else:
        logger.info(
            f"Fase: {progress.phase} | Op: {progress.current_operation[:50]}... | "
            f"Archivos Procesados: {progress.files_processed} | Errores: {progress.errors_count}"
        )

def print_import_summary(result):
    """Imprime un resumen detallado del resultado de la importación."""
    logger.info("\n--- RESUMEN DE LA IMPORTACIÓN ---")
    logger.info(f"Éxito general: {'Sí' if result.success else 'No'}")
    logger.info(f"Tiempo total transcurrido: {result.elapsed_time:.2f} segundos")
    logger.info(f"Archivos encontrados en escaneo: {result.total_files_found}")
    logger.info(f"Archivos procesados (intentados): {result.total_files_processed}")
    logger.info(f"Importaciones exitosas (guardadas en BD): {result.successful_imports}")
    logger.info(f"Importaciones fallidas (errores de extracción/BD): {result.failed_imports}")

    if result.errors:
        logger.warning("\n--- ERRORES DETALLADOS ---")
        for i, error_msg in enumerate(result.errors):
            logger.warning(f"  Error {i+1}: {error_msg}")
    else:
        logger.info("\nNo se reportaron errores detallados.")

    logger.info("\n--- ESTADÍSTICAS DEL ESCANER ---")
    for ext, count in result.scan_statistics.get('files_by_extension', {}).items():
        logger.info(f"  {ext}: {count} archivos")
    logger.info(f"  Total escaneado: {result.scan_statistics.get('total_scanned', 0)}")
    logger.info(f"  Errores de escaneo: {len(result.scan_statistics.get('scan_errors', []))}")
    
    if result.imported_tracks:
        logger.info("\n--- ALGUNOS TRACKS IMPORTADOS (hasta 5) ---")
        for i, track_metadata in enumerate(result.imported_tracks[:5]):
            # Convertir a dict para facilitar la impresión, ya que TrackMetadata es un dataclass
            track_dict = asdict(track_metadata)
            # Simplificar la info para la demo
            simplified_track = {
                "file_name": track_dict.get("file_name"),
                "title": track_dict.get("title"),
                "artist": track_dict.get("artist"),
                "album": track_dict.get("album"),
                "enriched_genres": track_dict.get("enriched_genres"),
                "enrichment_confidence": track_dict.get("enrichment_confidence")
            }
            logger.info(f"  Track {i+1}: {simplified_track}")
    else:
        logger.info("\nNo se importaron tracks o no se retornaron en el resultado.")

def verify_data_in_db(db_manager: DBManager, num_tracks_to_verify: int = 5):
    """Verifica algunos de los datos insertados directamente desde la BD."""
    if not db_manager.conn:
        logger.error("No hay conexión a la BD para verificación.")
        return

    logger.info(f"\n--- VERIFICANDO DATOS EN LA BASE DE DATOS (primeros {num_tracks_to_verify} tracks) ---")
    try:
        # crud.get_all_tracks espera una conexión, no un db_manager
        # y no existe tal cual en el crud.py que hemos visto.
        # Usaremos db_manager.fetch_query directamente.
        
        # Necesitamos obtener los tracks más recientes o hacer un select simple
        # Nota: el crud.py actual tiene get_all_tracks pero toma conn, limit, offset
        # y su estructura es diferente. Vamos a simplificar para la demo.
        
        # Vamos a usar el db_manager.fetch_query y construir el objeto Track si es necesario,
        # o simplemente imprimir los diccionarios de fila.
        
        query = f"SELECT id, filepath, title, artist, album, genre, enriched_genres, enrichment_confidence FROM tracks ORDER BY id DESC LIMIT {num_tracks_to_verify}"
        rows = db_manager.fetch_query(query)
        
        if not rows:
            logger.info("No se encontraron tracks en la base de datos para verificar.")
            return
            
        for i, row in enumerate(rows):
            # sqlite3.Row se puede acceder como un diccionario
            logger.info(f"  DB Track {i+1}: ID={row['id']}, Título='{row['title']}', Artista='{row['artist']}', "
                        f"Géneros Enriquecidos='{row['enriched_genres']}', Confianza='{row['enrichment_confidence']}'")
            if row['enriched_genres']:
                 logger.info(f"     Tipo de enriched_genres en BD: {type(row['enriched_genres'])}") # Debería ser str (JSON)

    except Exception as e:
        logger.error(f"Error durante la verificación en BD: {e}", exc_info=True)


def main():
    """Función principal del script de demostración."""
    if len(sys.argv) < 2:
        logger.error("Uso: python demo_importer.py <ruta_al_directorio_de_musica> [--no-enrich]")
        sys.exit(1)

    music_directory = sys.argv[1]
    if not os.path.isdir(music_directory):
        logger.error(f"El directorio proporcionado no existe o no es un directorio: {music_directory}")
        sys.exit(1)

    enable_enrichment_flag = True
    if "--no-enrich" in sys.argv:
        enable_enrichment_flag = False
        logger.info("Enriquecimiento de metadatos DESHABILITADO.")
    else:
        logger.info("Enriquecimiento de metadatos HABILITADO.")

    logger.info(f"Iniciando importación para el directorio: {music_directory}")

    # Crear instancia del ImportManager
    # El constructor de ImportManager ahora también instancia DBManager internamente.
    import_manager = ImportManager(enable_enrichment=enable_enrichment_flag, max_workers=4)
    
    # Establecer el callback de progreso
    import_manager.set_progress_callback(progress_callback)

    # Iniciar la importación
    start_overall_time = time.time()
    try:
        import_result = import_manager.import_directory(
            directory=music_directory,
            recursive=True,
            calculate_hashes=False # Poner a True si se quieren calcular hashes
        )
    except Exception as e:
        logger.error(f"Excepción crítica durante import_directory: {e}", exc_info=True)
        # Asegurarse de que el DBManager cierre la conexión si hubo un error muy temprano
        if hasattr(import_manager, 'db_manager') and import_manager.db_manager.conn:
            import_manager.db_manager.close()
        sys.exit(1)
        
    end_overall_time = time.time()
    logger.info(f"Tiempo total del script (incluyendo setup y resumen): {end_overall_time - start_overall_time:.2f} segundos")

    # Imprimir resumen
    if import_result:
        print_import_summary(import_result)
    else:
        logger.error("El resultado de la importación fue None, algo falló catastróficamente.")

    # Verificación opcional en BD (usando una nueva instancia de DBManager para no interferir si la otra se cerró)
    # O, si ImportManager no cierra su DBManager hasta un método close() explícito, podríamos reusarla.
    # Dado que ImportManager cierra su DBManager en el finally de _perform_import, creamos una nueva para verificar.
    logger.info("\nIntentando verificación en base de datos...")
    db_verifier = DBManager() # Crea su propia conexión
    if db_verifier.conn:
        verify_data_in_db(db_verifier)
        db_verifier.close()
    else:
        logger.error("No se pudo establecer conexión con DBManager para verificación.")

if __name__ == "__main__":
    main() 
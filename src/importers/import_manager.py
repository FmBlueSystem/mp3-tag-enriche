#!/usr/bin/env python3
"""
📥 GESTOR DE IMPORTACIÓN - NUEVA BIBLIOTECA v2.0
===============================================
Coordina el proceso completo de importación de bibliotecas musicales
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Callable, Generator, Tuple
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import logging

from .file_scanner import MusicFileScanner, ScanResult
from .metadata_extractor import MetadataExtractor, TrackMetadata

# Importaciones para la base de datos
from ..core.database.db_manager import DBManager
from ..data import crud

logger = logging.getLogger(__name__)

@dataclass
class ImportProgress:
    """Estado del progreso de importación."""
    phase: str  # 'scanning', 'extracting', 'processing', 'complete'
    current_file: str
    files_processed: int
    total_files: int
    elapsed_time: float
    estimated_remaining: float
    errors_count: int
    current_operation: str
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

@dataclass
class ImportResult:
    """Resultado completo de una importación."""
    success: bool
    total_files_found: int
    total_files_processed: int
    successful_imports: int
    failed_imports: int
    elapsed_time: float
    errors: List[str]
    imported_tracks: List[TrackMetadata]
    scan_statistics: Dict
    
class ImportManager:
    """
    Gestor principal del proceso de importación.
    """
    
    def __init__(self, max_workers: int = 4, enable_enrichment: bool = True):
        """
        Inicializar el gestor de importación.
        
        Args:
            max_workers: Número máximo de hilos para procesamiento paralelo
            enable_enrichment: Si habilitar la extracción y enriquecimiento de metadatos
        """
        self.scanner = MusicFileScanner()
        self.extractor = MetadataExtractor(enable_enrichment=enable_enrichment)
        self.max_workers = max_workers
        self.db_manager = DBManager()
        
        # Estado del progreso
        self.progress = ImportProgress(
            phase='idle',
            current_file='',
            files_processed=0,
            total_files=0,
            elapsed_time=0.0,
            estimated_remaining=0.0,
            errors_count=0,
            current_operation=''
        )
        
        # Callbacks
        self.progress_callback: Optional[Callable[[ImportProgress], None]] = None
        self.file_processed_callback: Optional[Callable[[TrackMetadata], None]] = None
        
        # Control de cancelación
        self._cancel_requested = False
        self._import_lock = threading.Lock()
        
    def set_progress_callback(self, callback: Callable[[ImportProgress], None]):
        """Establecer callback para reportar progreso."""
        self.progress_callback = callback
        
    def set_file_processed_callback(self, callback: Callable[[TrackMetadata], None]):
        """Establecer callback para cuando se procesa un archivo."""
        self.file_processed_callback = callback
        
    def cancel_import(self):
        """Cancelar importación en progreso."""
        self._cancel_requested = True
        
    def import_directory(self, 
                        directory: str, 
                        recursive: bool = True,
                        calculate_hashes: bool = False,
                        filter_extensions: Optional[List[str]] = None) -> ImportResult:
        """
        Importar todos los archivos de audio de un directorio.
        
        Args:
            directory: Directorio a importar
            recursive: Si escanear subdirectorios
            calculate_hashes: Si calcular hashes MD5
            filter_extensions: Lista de extensiones a incluir (None = todas)
            
        Returns:
            ImportResult con el resultado de la importación
        """
        with self._import_lock:
            return self._perform_import(
                directories=[directory],
                recursive=recursive,
                calculate_hashes=calculate_hashes,
                filter_extensions=filter_extensions
            )
            
    def import_multiple_directories(self,
                                  directories: List[str],
                                  recursive: bool = True,
                                  calculate_hashes: bool = False,
                                  filter_extensions: Optional[List[str]] = None) -> ImportResult:
        """
        Importar archivos de múltiples directorios.
        
        Args:
            directories: Lista de directorios a importar
            recursive: Si escanear subdirectorios
            calculate_hashes: Si calcular hashes MD5
            filter_extensions: Lista de extensiones a incluir
            
        Returns:
            ImportResult con el resultado de la importación
        """
        with self._import_lock:
            return self._perform_import(
                directories=directories,
                recursive=recursive,
                calculate_hashes=calculate_hashes,
                filter_extensions=filter_extensions
            )
            
    def _perform_import(self,
                       directories: List[str],
                       recursive: bool,
                       calculate_hashes: bool,
                       filter_extensions: Optional[List[str]]) -> ImportResult:
        """Realizar el proceso completo de importación."""
        start_time = time.time()
        self._cancel_requested = False
        
        # Inicializar resultado
        result = ImportResult(
            success=False,
            total_files_found=0,
            total_files_processed=0,
            successful_imports=0,
            failed_imports=0,
            elapsed_time=0.0,
            errors=[],
            imported_tracks=[],
            scan_statistics={}
        )
        
        try:
            # FASE 1: Escaneo de archivos
            self._update_progress('scanning', 'Escaneando directorios...', 0, 0)
            
            scan_results = list(self._scan_directories(directories, recursive))
            
            if self._cancel_requested:
                result.errors.append("Importación cancelada por el usuario")
                return result
                
            # Filtrar por extensiones si se especifica
            if filter_extensions:
                extensions_set = {ext.lower() for ext in filter_extensions}
                scan_results = self.scanner.filter_by_extension(scan_results, extensions_set)
                
            result.total_files_found = len(scan_results)
            result.scan_statistics = self.scanner.get_scan_statistics()
            
            if not scan_results:
                result.errors.append("No se encontraron archivos de audio")
                return result
                
            # FASE 2: Extracción de metadatos
            self._update_progress('extracting', 'Extrayendo metadatos...', 0, len(scan_results))
            
            imported_tracks = list(self._extract_metadata_batch(
                scan_results, calculate_hashes
            ))
            
            if self._cancel_requested:
                result.errors.append("Importación cancelada por el usuario")
                return result
                
            # FASE 3: Finalización
            self._update_progress('complete', 'Importación completada', len(imported_tracks), len(scan_results))
            
            # Compilar resultado final
            result.success = True
            result.total_files_processed = len(scan_results)
            result.successful_imports = len(imported_tracks)
            result.failed_imports = len(scan_results) - len(imported_tracks)
            result.imported_tracks = imported_tracks
            result.errors.extend(self.extractor.get_extraction_errors())
            result.elapsed_time = time.time() - start_time
            
            return result
            
        except Exception as e:
            logger.error(f"Error crítico durante la importación: {e}", exc_info=True)
            result.errors.append(f"Error crítico durante la importación: {e}")
            result.elapsed_time = time.time() - start_time
            return result
        finally:
            # Asegurarse de cerrar la conexión a la BD
            if self.db_manager and self.db_manager.conn:
                self.db_manager.close()
            
    def _scan_directories(self, directories: List[str], recursive: bool) -> Generator[ScanResult, None, None]:
        """Escanear directorios y reportar progreso."""
        def progress_callback(files_found: int, total_estimated: int, current_file: str):
            if self._cancel_requested:
                return
            self._update_progress('scanning', f'Escaneando: {current_file}', files_found, total_estimated)
            
        self.scanner.set_progress_callback(progress_callback)
        
        for directory in directories:
            if self._cancel_requested:
                break
            yield from self.scanner.scan_directory(directory, recursive)
            
    def _extract_metadata_batch(self, 
                               scan_results: List[ScanResult], 
                               calculate_hashes: bool) -> Generator[TrackMetadata, None, None]:
        """Extraer metadatos usando procesamiento paralelo."""
        
        def extract_single_file(scan_result: ScanResult) -> Optional[TrackMetadata]:
            """Extraer metadatos de un solo archivo."""
            if self._cancel_requested:
                return None
                
            metadata = self.extractor.extract_metadata(
                scan_result.file_path, 
                calculate_hashes
            )
            
            if metadata:
                # Reportar progreso
                with self.progress._lock:
                    self.progress.files_processed += 1
                    self.progress.current_file = scan_result.file_name
                    
                # Guardar en la base de datos
                try:
                    # Convertir TrackMetadata a dict para la función crud
                    track_data_dict = asdict(metadata)
                    
                    # Eliminar el campo 'id' si existe y es None, ya que la BD lo autogenera.
                    # crud.add_track lo espera como track_id si se pasa, pero TrackMetadata no tiene track_id.
                    # El modelo Track de la BD sí tiene 'id'.
                    # Si asdict(metadata) produce un campo 'id' (si TrackMetadata lo tuviera), y es None, está bien.
                    # Lo importante es que el mapeo de campos de TrackMetadata a columnas de la tabla 'tracks' sea correcto.

                    # Renombrar file_path a filepath para coincidir con el modelo de BD y crud.py
                    if 'file_path' in track_data_dict:
                        track_data_dict['filepath'] = track_data_dict.pop('file_path')
                    else:
                        # Esto sería inesperado si metadata.file_path es un campo obligatorio
                        logger.warning(f"El campo 'file_path' no está en track_data_dict para {scan_result.file_path}")
                        # Podríamos decidir no intentar guardarlo o manejarlo como un error.
                        # Por ahora, dejamos que crud.add_track falle si 'filepath' es obligatorio y falta.

                    # Los campos como enriched_genres (dict) y enrichment_sources (list)
                    # son serializados a JSON por crud.add_track.

                    track_id_from_db = crud.add_track(self.db_manager.conn, track_data_dict)
                    if track_id_from_db:
                        logger.info(f"Track '{metadata.title}' (Archivo: {metadata.file_name}) guardado en BD con ID: {track_id_from_db}")
                        # Actualizar el objeto metadata con el ID de la BD si es necesario y si TrackMetadata tiene un campo id.
                        # TrackMetadata no tiene un campo 'id' actualmente, pero sí lo tiene Track en models.py.
                        # Esto es más para el objeto que se retorna/usa internamente si se necesita el ID de BD.
                        # metadata.id = track_id_from_db # Descomentar si TrackMetadata añade un campo 'id'
                    else:
                        logger.warning(f"No se pudo guardar el track '{metadata.title}' (Archivo: {metadata.file_name}) en la BD. crud.add_track devolvió None.")
                        self.extractor.extraction_errors.append(f"Error BD (crud.add_track): {scan_result.file_path}")
                except Exception as db_error:
                    logger.error(f"Excepción al guardar track {metadata.file_name} en BD: {db_error}", exc_info=True)
                    self.extractor.extraction_errors.append(f"Excepción BD: {scan_result.file_path} - {db_error}")

                if self.file_processed_callback:
                    self.file_processed_callback(metadata)
                    
            return metadata
            
        # Procesar archivos en paralelo
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar tareas
            future_to_scan = {
                executor.submit(extract_single_file, scan_result): scan_result 
                for scan_result in scan_results
            }
            
            # Recoger resultados conforme se completan
            for future in as_completed(future_to_scan):
                if self._cancel_requested:
                    # Cancelar tareas pendientes
                    for f in future_to_scan:
                        f.cancel()
                    break
                    
                try:
                    metadata = future.result()
                    if metadata:
                        yield metadata
                except Exception as e:
                    scan_result = future_to_scan[future]
                    self.extractor.extraction_errors.append(
                        f"Error procesando {scan_result.file_path}: {e}"
                    )
                    
    def _update_progress(self, phase: str, operation: str, processed: int, total: int):
        """Actualizar estado del progreso."""
        current_time = time.time()
        
        # Calcular tiempo transcurrido
        if hasattr(self, '_start_time'):
            elapsed = current_time - self._start_time
        else:
            self._start_time = current_time
            elapsed = 0.0
            
        # Estimar tiempo restante
        if processed > 0 and total > 0:
            rate = processed / elapsed if elapsed > 0 else 0
            remaining_files = total - processed
            estimated_remaining = remaining_files / rate if rate > 0 else 0.0
        else:
            estimated_remaining = 0.0
            
        # Actualizar progreso
        self.progress.phase = phase
        self.progress.current_operation = operation
        self.progress.files_processed = processed
        self.progress.total_files = total
        self.progress.elapsed_time = elapsed
        self.progress.estimated_remaining = estimated_remaining
        self.progress.errors_count = len(self.extractor.get_extraction_errors())
        
        # Llamar callback si existe
        if self.progress_callback:
            self.progress_callback(self.progress)
            
    def quick_preview(self, directory: str, max_files: int = 20) -> List[TrackMetadata]:
        """
        Vista previa rápida de archivos en un directorio.
        
        Args:
            directory: Directorio a previsualizar
            max_files: Máximo número de archivos a procesar
            
        Returns:
            Lista de metadatos de archivos encontrados
        """
        try:
            # Escaneo rápido
            scan_results = self.scanner.quick_scan(directory, max_files)
            
            # Extraer metadatos de los primeros archivos
            preview_tracks = []
            for scan_result in scan_results[:max_files]:
                metadata = self.extractor.extract_metadata(scan_result.file_path)
                if metadata:
                    preview_tracks.append(metadata)
                    
            return preview_tracks
            
        except Exception as e:
            print(f"Error en preview: {e}")
            return []
            
    def get_import_statistics(self) -> Dict:
        """Obtener estadísticas del último proceso de importación."""
        return {
            'scanner_stats': self.scanner.get_scan_statistics(),
            'extraction_errors': len(self.extractor.get_extraction_errors()),
            'supported_formats': self.scanner.get_supported_formats(),
            'current_progress': {
                'phase': self.progress.phase,
                'files_processed': self.progress.files_processed,
                'total_files': self.progress.total_files,
                'elapsed_time': self.progress.elapsed_time,
                'errors_count': self.progress.errors_count
            }
        }
        
    def validate_directory(self, directory: str) -> Dict[str, any]:
        """
        Validar un directorio antes de importar.
        
        Args:
            directory: Directorio a validar
            
        Returns:
            Diccionario con información de validación
        """
        validation = {
            'exists': False,
            'readable': False,
            'has_audio_files': False,
            'estimated_files': 0,
            'estimated_size_mb': 0,
            'errors': []
        }
        
        try:
            path = Path(directory)
            
            # Verificar existencia
            if not path.exists():
                validation['errors'].append(f"Directorio no existe: {directory}")
                return validation
            validation['exists'] = True
            
            # Verificar permisos de lectura
            if not os.access(directory, os.R_OK):
                validation['errors'].append(f"Sin permisos de lectura: {directory}")
                return validation
            validation['readable'] = True
            
            # Escaneo rápido para estimar contenido
            try:
                quick_results = self.scanner.quick_scan(directory, 100)
                validation['estimated_files'] = len(quick_results)
                
                if quick_results:
                    validation['has_audio_files'] = True
                    total_size = sum(r.file_size for r in quick_results)
                    validation['estimated_size_mb'] = round(total_size / (1024 * 1024), 2)
                    
            except Exception as e:
                validation['errors'].append(f"Error escaneando directorio: {e}")
                
        except Exception as e:
            validation['errors'].append(f"Error validando directorio: {e}")
            
        return validation 

    def import_folder(self, folder: str, recursive: bool = True, calculate_hash: bool = False) -> List[TrackMetadata]:
        """
        Importa todos los archivos musicales de una carpeta, extrae y enriquece metadatos.
        Este método parece ser un helper simplificado y podría necesitar 
        integrarse mejor con el flujo principal de _perform_import o ser deprecado.
        Por ahora, lo adaptamos para usar self.scanner.
        
        Args:
            folder: Carpeta raíz a importar
            recursive: Si buscar recursivamente
            calculate_hash: Si calcular hash MD5 de los archivos
        
        Returns:
            Lista de objetos TrackMetadata enriquecidos
        """
        logger.info(f"Escaneando carpeta (vía import_folder): {folder}")
        
        # Usar self.scanner.scan_directory que devuelve ScanResult objects
        scan_results = list(self.scanner.scan_directory(folder, recursive=recursive))
        
        # Extraer solo las rutas de archivo para extract_batch, que espera List[str]
        file_paths = [sr.file_path for sr in scan_results]
        
        logger.info(f"Archivos musicales encontrados (vía import_folder): {len(file_paths)}")
        if not file_paths:
            return []
        
        logger.info("Extrayendo y enriqueciendo metadatos (vía import_folder)...")
        # self.extractor.extract_batch espera una lista de rutas de archivo (str)
        tracks = self.extractor.extract_batch(file_paths, calculate_hash=calculate_hash, enrich_metadata=True)
        logger.info(f"Tracks procesados exitosamente (vía import_folder): {len(tracks)}")
        
        # NOTA: Este método no guarda en la base de datos actualmente.
        # Debería integrarse con el flujo de _perform_import si se desea persistencia.
        return tracks

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python import_manager.py <carpeta>")
        sys.exit(1)
    folder = sys.argv[1]
    manager = ImportManager(enable_enrichment=True)
    tracks = manager.import_folder(folder)
    print(f"Tracks importados: {len(tracks)}")
    for t in tracks:
        print(f"{t.file_name} | {t.artist} - {t.title} | Géneros: {t.enriched_genres}") 
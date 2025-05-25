#!/usr/bin/env python3
"""
🎵 FILE SCANNER - NUEVA BIBLIOTECA
==================================
Escanea carpetas recursivamente y encuentra archivos musicales válidos.
"""

import os
import time # Para estadísticas de escaneo
from pathlib import Path
from typing import List, Set, Dict, Any, Callable, Optional, Generator
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS: Set[str] = {'.mp3', '.flac', '.m4a', '.wav', '.ogg'}

@dataclass
class ScanResult:
    """Representa un archivo encontrado durante el escaneo."""
    file_path: str
    file_name: str
    file_size: int
    file_extension: str

class MusicFileScanner:
    """
    Escanea directorios en busca de archivos musicales, 
    proporciona estadísticas y callbacks de progreso.
    """
    def __init__(self):
        self.supported_extensions: Set[str] = SUPPORTED_EXTENSIONS
        self.scan_errors: List[str] = []
        self.files_by_extension: Dict[str, int] = {ext: 0 for ext in self.supported_extensions}
        self.total_scanned: int = 0
        self.total_size_scanned: int = 0
        self.progress_callback: Optional[Callable[[int, int, str], None]] = None
        self._estimated_total_files: int = 0 # Estimación inicial

    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Establecer callback para reportar progreso del escaneo."""
        self.progress_callback = callback

    def _reset_stats(self):
        self.scan_errors = []
        self.files_by_extension = {ext: 0 for ext in self.supported_extensions}
        self.total_scanned = 0
        self.total_size_scanned = 0
        self._estimated_total_files = 0

    def _pre_scan_estimate(self, directory: Path, recursive: bool) -> int:
        """Estima el número total de archivos a ser potencialmente procesados."""
        count = 0
        try:
            if recursive:
                for _ in directory.rglob('*'): # Contar todos los items
                    count += 1
            else:
                for _ in directory.iterdir(): # Contar todos los items
                    count += 1
        except OSError as e:
            logger.warning(f"Error al pre-escanear {directory} para estimación: {e}")
            self.scan_errors.append(f"Error estimando {directory}: {e}")
        return count

    def scan_directory(self, directory: str, recursive: bool = True) -> Generator[ScanResult, None, None]:
        """Escanea un directorio y devuelve un generador de ScanResult."""
        self._reset_stats()
        root = Path(directory).expanduser().resolve()

        if not root.exists() or not root.is_dir():
            self.scan_errors.append(f"Directorio no encontrado o no es un directorio: {directory}")
            logger.error(f"Directorio no válido: {directory}")
            return

        self._estimated_total_files = self._pre_scan_estimate(root, recursive)
        files_processed_count = 0

        iterator = root.rglob('*') if recursive else root.iterdir()
        
        for path in iterator:
            files_processed_count +=1
            if path.is_file():
                self.total_scanned += 1
                ext = path.suffix.lower()
                if ext in self.supported_extensions:
                    self.files_by_extension[ext] += 1
                    self.total_size_scanned += path.stat().st_size
                    scan_result = ScanResult(
                        file_path=str(path.absolute()),
                        file_name=path.name,
                        file_size=path.stat().st_size,
                        file_extension=ext
                    )
                    yield scan_result
            
            if self.progress_callback:
                # Pasar el conteo actual de archivos procesados y el estimado total
                self.progress_callback(files_processed_count, self._estimated_total_files, str(path))

    def quick_scan(self, directory: str, max_files: int = 100) -> List[ScanResult]:
        """Realiza un escaneo rápido y limitado del directorio."""
        results = []
        count = 0
        try:
            for item in self.scan_directory(directory, recursive=True): # Usar scan_directory
                results.append(item)
                count += 1
                if count >= max_files:
                    break
        except Exception as e:
            logger.error(f"Error durante quick_scan en '{directory}': {e}")
            self.scan_errors.append(f"Error en quick_scan '{directory}': {e}")
        return results

    def filter_by_extension(self, scan_results: List[ScanResult], extensions: Set[str]) -> List[ScanResult]:
        """Filtra una lista de ScanResult por un conjunto de extensiones."""
        if not extensions: # Si el conjunto de extensiones está vacío, no filtrar
            return scan_results
        
        lowercase_extensions = {ext.lower() for ext in extensions}
        return [sr for sr in scan_results if sr.file_extension.lower() in lowercase_extensions]

    def get_scan_statistics(self) -> Dict[str, Any]:
        """Devuelve estadísticas del último escaneo."""
        return {
            'files_by_extension': self.files_by_extension.copy(),
            'total_scanned_matching_extensions': sum(self.files_by_extension.values()),
            'total_items_processed_in_scan': self.total_scanned, # Renombrado para claridad
            'total_size_scanned_mb': round(self.total_size_scanned / (1024 * 1024), 2),
            'scan_errors': self.scan_errors[:],
            'supported_formats': list(self.supported_extensions)
        }

    def get_supported_formats(self) -> List[str]:
        """Devuelve una lista de formatos de archivo soportados."""
        return list(self.supported_extensions)

# La función original, ahora puede ser un helper o eliminada si la clase la reemplaza completamente.
# Por ahora la dejo comentada por si ImportManager necesita una función simple también.
# def scan_music_files(directory: str, recursive: bool = True) -> List[str]:
#     music_files = []
#     # ... (implementación original)
#     return music_files

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) < 2:
        print("Uso: python file_scanner.py <carpeta>")
        sys.exit(1)
    
    scanner = MusicFileScanner()
    
    def demo_progress(processed_count, total_estimate, current_item):
        prog = (processed_count / total_estimate) * 100 if total_estimate > 0 else 0
        print(f"Escaneando: {current_item} - {processed_count}/{total_estimate} ({prog:.2f}%)", end='\r')

    scanner.set_progress_callback(demo_progress)
    
    folder = sys.argv[1]
    print(f"Escaneando directorio: {folder}")
    found_files = []
    for result in scanner.scan_directory(folder):
        found_files.append(result)
        # print(result)
    print("\nEscaneo completo.")
    
    print("\nEstadísticas del escaneo:")
    stats = scanner.get_scan_statistics()
    for key, value in stats.items():
        if key == 'scan_errors' and not value:
            continue
        print(f"  {key}: {value}")

    print(f"\nTotal de archivos musicales encontrados: {len(found_files)}")
    # for f_info in found_files:
    #     print(f_info.file_path)

    print("\nProbando quick_scan (max 10):")
    quick_results = scanner.quick_scan(folder, 10)
    print(f"Quick scan encontró: {len(quick_results)} archivos")
    for qr in quick_results:
        print(f"  {qr.file_name}")

    print("\nFormatos soportados:")
    print(scanner.get_supported_formats()) 
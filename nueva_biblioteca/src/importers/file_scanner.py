"""
Escáner de archivos musicales para importación masiva.
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Generator, Callable, Optional, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

@dataclass
class ScanResult:
    """
    Resultado del escaneo de un archivo.
    """
    file_path: str
    file_size: int
    file_format: str
    last_modified: float
    is_valid: bool
    error_message: Optional[str] = None

class MusicFileScanner:
    """
    Escáner optimizado para archivos musicales con soporte para importación masiva.
    """
    
    # Formatos de audio soportados
    SUPPORTED_FORMATS = {
        '.mp3', '.flac', '.m4a', '.aac', '.wav', '.ogg', 
        '.wma', '.aiff', '.ape', '.opus'
    }
    
    # Directorios a ignorar por defecto
    IGNORED_DIRS = {
        '__pycache__', '.git', '.svn', '.hg', 'node_modules',
        'Thumbs.db', '.DS_Store', 'desktop.ini'
    }
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._stop_scanning = threading.Event()
        self._progress_callback: Optional[Callable[[int, int], None]] = None
        self._file_callback: Optional[Callable[[ScanResult], None]] = None
    
    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """
        Establece un callback para reportar progreso.
        Args:
            callback: Función que recibe (archivos_procesados, total_archivos)
        """
        self._progress_callback = callback
    
    def set_file_callback(self, callback: Callable[[ScanResult], None]):
        """
        Establece un callback para procesar cada archivo encontrado.
        Args:
            callback: Función que recibe un ScanResult
        """
        self._file_callback = callback
    
    def stop_scan(self):
        """
        Detiene el escaneo en curso.
        """
        self._stop_scanning.set()
    
    def reset_stop_flag(self):
        """
        Reinicia la flag de detención.
        """
        self._stop_scanning.clear()
    
    def is_music_file(self, file_path: Path) -> bool:
        """
        Verifica si un archivo es un archivo musical soportado.
        """
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS
    
    def should_ignore_directory(self, dir_path: Path) -> bool:
        """
        Verifica si un directorio debe ser ignorado.
        """
        dir_name = dir_path.name.lower()
        return (
            dir_name in self.IGNORED_DIRS or
            dir_name.startswith('.') or
            dir_name.startswith('_')
        )
    
    def scan_file(self, file_path: Path) -> ScanResult:
        """
        Escanea un archivo individual y retorna información básica.
        """
        try:
            if not file_path.exists():
                return ScanResult(
                    file_path=str(file_path),
                    file_size=0,
                    file_format="",
                    last_modified=0,
                    is_valid=False,
                    error_message="Archivo no encontrado"
                )
            
            if not self.is_music_file(file_path):
                return ScanResult(
                    file_path=str(file_path),
                    file_size=0,
                    file_format="",
                    last_modified=0,
                    is_valid=False,
                    error_message="Formato no soportado"
                )
            
            stat = file_path.stat()
            file_format = file_path.suffix.lower().lstrip('.')
            
            return ScanResult(
                file_path=str(file_path.resolve()),
                file_size=stat.st_size,
                file_format=file_format,
                last_modified=stat.st_mtime,
                is_valid=True
            )
            
        except Exception as e:
            return ScanResult(
                file_path=str(file_path),
                file_size=0,
                file_format="",
                last_modified=0,
                is_valid=False,
                error_message=str(e)
            )
    
    def find_music_files(self, root_path: str) -> Generator[Path, None, None]:
        """
        Busca recursivamente archivos musicales en un directorio.
        """
        root = Path(root_path)
        
        if not root.exists():
            return
        
        if root.is_file():
            if self.is_music_file(root):
                yield root
            return
        
        try:
            for item in root.rglob("*"):
                if self._stop_scanning.is_set():
                    break
                
                if item.is_file() and self.is_music_file(item):
                    # Verificar si está en un directorio ignorado
                    should_skip = any(
                        self.should_ignore_directory(parent)
                        for parent in item.parents
                    )
                    
                    if not should_skip:
                        yield item
                        
        except PermissionError:
            # Ignorar directorios sin permisos
            pass
        except Exception as e:
            print(f"Error escaneando {root_path}: {e}")
    
    def count_music_files(self, root_path: str) -> int:
        """
        Cuenta el número total de archivos musicales en un directorio.
        Útil para calcular progreso antes del escaneo principal.
        """
        count = 0
        try:
            for _ in self.find_music_files(root_path):
                if self._stop_scanning.is_set():
                    break
                count += 1
        except Exception:
            pass
        return count
    
    def scan_directory(
        self, 
        root_path: str,
        recursive: bool = True
    ) -> Generator[ScanResult, None, None]:
        """
        Escanea un directorio y genera resultados de archivos musicales.
        """
        self.reset_stop_flag()
        
        if recursive:
            files = list(self.find_music_files(root_path))
        else:
            root = Path(root_path)
            files = [
                f for f in root.iterdir() 
                if f.is_file() and self.is_music_file(f)
            ]
        
        total_files = len(files)
        processed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar todas las tareas
            future_to_file = {
                executor.submit(self.scan_file, file_path): file_path
                for file_path in files
            }
            
            # Procesar resultados conforme se completan
            for future in as_completed(future_to_file):
                if self._stop_scanning.is_set():
                    break
                
                try:
                    result = future.result()
                    processed += 1
                    
                    # Callback de progreso
                    if self._progress_callback:
                        self._progress_callback(processed, total_files)
                    
                    # Callback de archivo
                    if self._file_callback:
                        self._file_callback(result)
                    
                    yield result
                    
                except Exception as e:
                    file_path = future_to_file[future]
                    error_result = ScanResult(
                        file_path=str(file_path),
                        file_size=0,
                        file_format="",
                        last_modified=0,
                        is_valid=False,
                        error_message=f"Error procesando: {e}"
                    )
                    yield error_result
    
    def scan_multiple_directories(
        self, 
        directories: List[str]
    ) -> Generator[ScanResult, None, None]:
        """
        Escanea múltiples directorios secuencialmente.
        """
        for directory in directories:
            if self._stop_scanning.is_set():
                break
            
            yield from self.scan_directory(directory)
    
    def get_scan_statistics(self, results: List[ScanResult]) -> Dict[str, any]:
        """
        Genera estadísticas del escaneo.
        """
        valid_files = [r for r in results if r.is_valid]
        invalid_files = [r for r in results if not r.is_valid]
        
        # Estadísticas por formato
        format_stats = {}
        total_size = 0
        
        for result in valid_files:
            format_stats[result.file_format] = format_stats.get(result.file_format, 0) + 1
            total_size += result.file_size
        
        # Errores más comunes
        error_stats = {}
        for result in invalid_files:
            if result.error_message:
                error_stats[result.error_message] = error_stats.get(result.error_message, 0) + 1
        
        return {
            'total_files_found': len(results),
            'valid_files': len(valid_files),
            'invalid_files': len(invalid_files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'formats_found': format_stats,
            'common_errors': error_stats,
            'most_common_format': max(format_stats.items(), key=lambda x: x[1])[0] if format_stats else None
        }
    
    def quick_scan(self, root_path: str, sample_size: int = 100) -> Dict[str, any]:
        """
        Realiza un escaneo rápido de muestra para estimar el contenido del directorio.
        """
        results = []
        count = 0
        
        for result in self.scan_directory(root_path):
            results.append(result)
            count += 1
            
            if count >= sample_size:
                break
        
        stats = self.get_scan_statistics(results)
        stats['is_sample'] = True
        stats['sample_size'] = count
        
        return stats
#!/usr/bin/env python3
"""
🎵 PROCESADOR SIMPLE Y SEGURO DE MP3
===================================

Procesador que evita el congelamiento con:
- Máximo 1 archivo a la vez (sin concurrencia)
- Rate limiting estricto 
- Gestión de memoria activa
- Progreso visible
- Timeouts configurables
"""

import os
import sys
import gc
import time
import signal
import logging
from pathlib import Path
from typing import Dict, List
from contextlib import contextmanager

# Configurar logging simple
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Agregar directorio del proyecto
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)

class SimpleTimeout:
    """Clase simple para manejar timeouts."""
    
    def __init__(self, seconds=30):
        self.seconds = seconds
    
    def __enter__(self):
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.seconds)
        return self
    
    def __exit__(self, type, value, traceback):
        signal.alarm(0)
    
    def _timeout_handler(self, signum, frame):
        raise TimeoutError(f"Operación tardó más de {self.seconds} segundos")

# Importar cliente API mejorado si está disponible
try:
    from improved_api_client import ImprovedAPIManager
    API_IMPROVEMENTS_AVAILABLE = True
except ImportError:
    API_IMPROVEMENTS_AVAILABLE = False

from src.core.file_handler import Mp3FileHandler

# Spotify API integration
try:
    from src.core.spotify_api import SpotifyAPI
    SPOTIFY_AVAILABLE = True
except ImportError:
    SPOTIFY_AVAILABLE = False
    print("⚠️ Spotify API no disponible")

class SimpleMP3Processor:
    """Procesador MP3 simple y ultra-seguro."""
    
    def __init__(self):
        """Inicializa procesador con configuración conservadora."""
        self.rate_limit = 0.5  # Medio segundo entre archivos
        self.timeout = 30      # 30 segundos máximo por archivo
        self.memory_cleanup_interval = 10  # Limpiar memoria cada 10 archivos
        self.start_time = time.time()
        self.processed = 0
        self.errors = 0
        
        # Configurar directorio de backup
        project_dir = os.path.dirname(os.path.abspath(__file__))
        backup_dir = os.path.join(project_dir, "mp3_backups")
        os.makedirs(backup_dir, exist_ok=True)
        self.handler = Mp3FileHandler(backup_dir=backup_dir, verbose=False)
    
    @contextmanager
    def safe_processing(self, file_path: str):
        """Context manager para procesamiento seguro."""
        logger.info(f"🔄 Procesando: {os.path.basename(file_path)}")
        start_time = time.time()
        
        try:
            # Rate limiting
            time.sleep(self.rate_limit)
            
            # Verificar archivo
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
            if not file_path.lower().endswith('.mp3'):
                raise ValueError(f"No es archivo MP3: {file_path}")
            
            yield
            
        except Exception as e:
            logger.error(f"❌ Error en {os.path.basename(file_path)}: {e}")
            self.errors += 1
            raise
        
        finally:
            # Cleanup
            gc.collect()
            process_time = time.time() - start_time
            logger.info(f"⏱️ Completado en {process_time:.1f}s")
            self.processed += 1
            
            # Mostrar progreso cada archivo
            self._show_progress()
    
    def process_single_file(self, file_path: str, dry_run: bool = True) -> Dict:
        """Procesa un archivo individual con máxima seguridad."""
        result = {
            'file': file_path,
            'filename': os.path.basename(file_path),
            'success': False,
            'error': None,
            'info': {}
        }
        
        try:
            with self.safe_processing(file_path):
                with SimpleTimeout(self.timeout):
                    # Usar handler básico (más estable)
                    info = self.handler.get_file_info(file_path)
                    
                    if info:
                        result['info'] = {
                            'artist': info.get('artist', ''),
                            'title': info.get('title', ''),
                            'album': info.get('album', ''),
                            'duration': info.get('duration', ''),
                            'has_metadata': bool(info.get('artist') or info.get('title'))
                        }
                        
                        if not dry_run:
                            # Aquí podrías aplicar cambios si es necesario
                            logger.info(f"📝 (Cambios se aplicarían aquí)")
                        
                        result['success'] = True
                        logger.info(f"✅ Exitoso: {result['info']['artist']} - {result['info']['title']}")
                    else:
                        result['error'] = 'No se pudo extraer información'
                        logger.warning(f"⚠️ Sin información: {os.path.basename(file_path)}")
        
        except TimeoutError as e:
            result['error'] = f'Timeout: {str(e)}'
            logger.error(f"⏰ Timeout en: {os.path.basename(file_path)}")
        
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"💥 Error procesando: {os.path.basename(file_path)} - {e}")
        
        return result
    
    def process_directory(self, directory: str, dry_run: bool = True, max_files: int = None) -> List[Dict]:
        """Procesa directorio de forma secuencial y segura."""
        
        logger.info(f"🎵 PROCESADOR SIMPLE MP3 - MODO SEGURO")
        logger.info(f"📁 Directorio: {directory}")
        logger.info(f"📋 Modo: {'SIMULACIÓN' if dry_run else 'APLICAR CAMBIOS'}")
        
        if not os.path.isdir(directory):
            logger.error(f"❌ Directorio no válido: {directory}")
            return []
        
        # Buscar archivos MP3
        logger.info("🔍 Buscando archivos MP3...")
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
            logger.error(f"❌ No se encontraron archivos MP3 en: {directory}")
            return []
        
        total = len(mp3_files)
        logger.info(f"🎵 Encontrados {total} archivos MP3")
        logger.info(f"⚙️ Rate limit: {self.rate_limit}s por archivo")
        logger.info(f"⏱️ Timeout: {self.timeout}s por archivo")
        logger.info(f"⏳ Tiempo estimado: {(total * self.rate_limit) / 60:.1f} minutos")
        logger.info(f"🔄 Iniciando procesamiento...")
        
        # Procesar secuencialmente (SIN CONCURRENCIA)
        results = []
        
        for i, file_path in enumerate(mp3_files, 1):
            logger.info(f"\n📊 Archivo {i}/{total} ({i/total*100:.1f}%)")
            
            try:
                result = self.process_single_file(file_path, dry_run)
                results.append(result)
                
                # Cleanup de memoria cada ciertos archivos
                if i % self.memory_cleanup_interval == 0:
                    logger.info("🧹 Limpiando memoria...")
                    gc.collect()
                    time.sleep(0.5)
                
            except KeyboardInterrupt:
                logger.info(f"\n🛑 Interrumpido por usuario en archivo {i}")
                break
            
            except Exception as e:
                logger.error(f"💥 Error crítico en archivo {i}: {e}")
                results.append({
                    'file': file_path,
                    'filename': os.path.basename(file_path),
                    'success': False,
                    'error': f'Error crítico: {str(e)}'
                })
                # Continuar con el siguiente archivo
                continue
        
        # Resumen final
        self._show_final_summary(results, total)
        
        return results
    
    def _show_progress(self):
        """Muestra progreso actual."""
        elapsed = time.time() - self.start_time
        if self.processed > 0:
            avg_time = elapsed / self.processed
            logger.info(f"📈 Progreso: {self.processed} procesados, {self.errors} errores, {avg_time:.1f}s/archivo promedio")
    
    def _show_final_summary(self, results: List[Dict], total: int):
        """Muestra resumen final."""
        elapsed = time.time() - self.start_time
        success_count = sum(1 for r in results if r.get('success', False))
        
        logger.info(f"\n🏁 RESUMEN FINAL")
        logger.info(f"=" * 40)
        logger.info(f"📁 Total archivos: {total}")
        logger.info(f"🔄 Procesados: {len(results)}")
        logger.info(f"✅ Exitosos: {success_count} ({success_count/len(results)*100:.1f}%)")
        logger.info(f"❌ Errores: {self.errors} ({self.errors/len(results)*100:.1f}%)")
        logger.info(f"⏱️ Tiempo total: {elapsed/60:.1f} minutos")
        logger.info(f"⚡ Promedio: {elapsed/len(results):.1f}s por archivo")
        
        # Mostrar algunos exitosos
        success_files = [r for r in results if r.get('success') and r.get('info', {}).get('has_metadata')]
        if success_files:
            logger.info(f"\n🎵 ARCHIVOS CON METADATA (primeros 5):")
            for result in success_files[:5]:
                info = result['info']
                logger.info(f"   🎤 {info['artist']} - {info['title']}")
        
        # Mostrar algunos errores
        error_files = [r for r in results if r.get('error')]
        if error_files:
            logger.info(f"\n❌ ERRORES (primeros 3):")
            for result in error_files[:3]:
                logger.info(f"   💥 {result['filename']}: {result['error']}")

def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🎵 Procesador MP3 simple y seguro (no se congela)"
    )
    parser.add_argument('--directory', '-d', required=True,
                       help='Directorio con archivos MP3')
    parser.add_argument('--apply', '-a', action='store_true',
                       help='Aplicar cambios (por defecto solo analiza)')
    parser.add_argument('--max-files', type=int,
                       help='Número máximo de archivos a procesar')
    
    args = parser.parse_args()
    
    # Crear procesador
    processor = SimpleMP3Processor()
    
    # Procesar
    try:
        results = processor.process_directory(
            directory=args.directory,
            dry_run=not args.apply,
            max_files=args.max_files
        )
        
        logger.info(f"\n🎉 Procesamiento completado sin congelamiento!")
        logger.info(f"📝 Ver detalles en: simple_processing.log")
        
    except KeyboardInterrupt:
        logger.info(f"\n👋 Detenido por usuario")
    except Exception as e:
        logger.error(f"💥 Error fatal: {e}")

if __name__ == "__main__":
    main() 
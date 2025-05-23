#!/usr/bin/env python3
"""
🎵 DETECTOR DE GÉNEROS MUSICALES - LAUNCHER UNIFICADO
====================================================

Punto de entrada único para todas las funcionalidades del sistema.
Auto-detecta el mejor modo de ejecución basado en el entorno.

Uso:
    python main.py                      # Auto-detect: GUI si disponible, CLI si no
    python main.py --gui                # Forzar modo GUI
    python main.py --cli [archivos]     # Forzar modo CLI
    python main.py --batch <directorio> # Modo procesamiento batch
    python main.py --analyze <archivos> # Solo análisis sin modificar
    python main.py --help               # Ayuda completa

Ejemplos:
    python main.py                                    # Modo automático
    python main.py --cli /ruta/a/archivo.mp3         # CLI directo
    python main.py --batch /ruta/a/directorio/       # Procesamiento masivo
    python main.py --analyze /ruta/*.mp3             # Solo análisis
"""

import sys
import os
import argparse
import logging
from typing import List, Optional
from pathlib import Path

# 🔧 PARCHE: Suprimir logs verbosos que causan congelamiento
import logging
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('musicbrainzngs').setLevel(logging.ERROR)
logging.getLogger('musicbrainzngs.musicbrainzngs').setLevel(logging.ERROR)
logging.getLogger('mutagen').setLevel(logging.WARNING)
logging.getLogger('spotipy').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('pylast').setLevel(logging.WARNING)


# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedLauncher:
    """Launcher unificado para todas las interfaces del sistema."""
    
    def __init__(self):
        self.gui_available = self._check_gui_availability()
        self.project_root = Path(__file__).parent
        
    def _check_gui_availability(self) -> bool:
        """Verifica si la GUI está disponible."""
        try:
            # Verificar dependencias GUI
            import PySide6
            from src.gui.main_window import MainWindow
            
            # Verificar entorno gráfico
            if sys.platform == 'darwin':  # macOS
                return True
            elif sys.platform.startswith('linux'):
                return bool(os.environ.get('DISPLAY'))
            elif sys.platform == 'win32':  # Windows
                return True
            
            return False
        except ImportError as e:
            logger.debug(f"GUI no disponible: {e}")
            return False
    
    def auto_detect_mode(self) -> str:
        """Auto-detecta el mejor modo basado en entorno y argumentos."""
        # Si hay argumentos específicos de CLI, usar CLI
        if len(sys.argv) > 1:
            if any(arg in sys.argv for arg in ['--cli', '--batch', '--analyze']):
                return 'cli'
        
        # Si GUI está disponible y no hay argumentos específicos de CLI
        if self.gui_available:
            return 'gui'
        
        return 'cli'
    
    def run_gui(self):
        """Ejecutar interfaz gráfica."""
        try:
            logger.info("🖥️  Iniciando interfaz gráfica...")
            from PySide6.QtWidgets import QApplication
            from src.gui.main_window import MainWindow
            from src.gui.style import apply_dark_theme
            
            app = QApplication(sys.argv)
            apply_dark_theme(app)
            window = MainWindow()
            window.show()
            
            logger.info("✅ GUI iniciada correctamente")
            sys.exit(app.exec())
            
        except ImportError as e:
            logger.error(f"❌ Error importando GUI: {e}")
            print("❌ GUI no disponible. Cambiando a modo CLI...")
            self.run_cli()
        except Exception as e:
            logger.error(f"❌ Error ejecutando GUI: {e}")
            print(f"❌ Error en GUI: {e}")
            print("🔄 Cambiando a modo CLI...")
            self.run_cli()
    
    def run_cli(self, paths: Optional[List[str]] = None, 
                analyze_only: bool = False, 
                batch_mode: bool = False,
                **kwargs):
        """Ejecutar interfaz de línea de comandos."""
        try:
            logger.info("💻 Iniciando interfaz CLI...")
            
            if batch_mode and paths:
                self._run_batch_mode(paths[0], **kwargs)
            else:
                self._run_standard_cli(paths, analyze_only, **kwargs)
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando CLI: {e}")
            print(f"❌ Error en CLI: {e}")
            sys.exit(1)
    
    def _run_standard_cli(self, paths: Optional[List[str]], analyze_only: bool, **kwargs):
        """Ejecutar CLI estándar usando el sistema moderno."""
        try:
            # Usar el CLI moderno de src/__main__.py
            from src.__main__ import main as cli_main
            from src.__main__ import create_detector, process_files
            
            if not paths:
                # Si no hay paths, usar directorio por defecto o pedir al usuario
                default_dir = "/Volumes/My Passport/Dj compilation 2025/DMS/DMS 80s"
                if os.path.exists(default_dir):
                    paths = [default_dir]
                else:
                    print("📁 No se especificaron archivos. Usando directorio actual...")
                    paths = ["."]
            
            # Crear detector con configuración unificada
            detector = create_detector(
                backup_dir=kwargs.get('backup_dir', "/Volumes/My Passport/Dj compilation 2025/Respados mp3"),
                use_spotify=not kwargs.get('no_spotify', False),
                verbose=kwargs.get('verbose', True)
            )
            
            # Procesar archivos
            results = process_files(
                detector=detector,
                paths=paths,
                recursive=kwargs.get('recursive', True),
                analyze_only=analyze_only,
                confidence=kwargs.get('confidence', 0.3),
                max_genres=kwargs.get('max_genres', 3)
            )
            
            # Mostrar resumen
            total_processed = len([r for r in results.values() if r])
            print(f"\n✅ Procesamiento completado: {total_processed} archivos")
            
        except ImportError:
            # Fallback al CLI legacy si el moderno no está disponible
            logger.warning("CLI moderno no disponible, usando legacy...")
            self._run_legacy_cli(paths, analyze_only, **kwargs)
    
    def _run_legacy_cli(self, paths: Optional[List[str]], analyze_only: bool, **kwargs):
        """Ejecutar CLI legacy como fallback."""
        print("⚠️  Usando CLI legacy...")
        
        # Importar y usar el CLI legacy
        import subprocess
        cmd = [sys.executable, "enriquecer_mp3_cli.py"]
        
        if paths:
            cmd.extend(["--directory", paths[0]])
        
        if kwargs.get('no_spotify'):
            cmd.append("--no-spotify")
        
        subprocess.run(cmd)
    
    def _run_batch_mode(self, directory: str, **kwargs):
        """Ejecutar modo batch especializado."""
        try:
            logger.info(f"🔄 Iniciando procesamiento batch: {directory}")
            
            # Usar el sistema batch especializado
            from batch_process_mp3 import batch_process, display_results
            
            results = batch_process(
                directory=directory,
                dry_run=kwargs.get('dry_run', False),
                force=kwargs.get('force', False),
                max_files=kwargs.get('max_files'),
                workers=kwargs.get('workers', 4),
                debug=kwargs.get('debug', False)
            )
            
            display_results(results)
            
        except ImportError as e:
            logger.error(f"Batch mode no disponible: {e}")
            print("❌ Modo batch no disponible, usando CLI estándar...")
            self._run_standard_cli([directory], False, **kwargs)

def create_parser() -> argparse.ArgumentParser:
    """Crear parser de argumentos unificado."""
    parser = argparse.ArgumentParser(
        description="🎵 Detector de Géneros Musicales - Launcher Unificado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Modo de ejecución
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--gui', action='store_true',
        help='Forzar modo GUI (interfaz gráfica)'
    )
    mode_group.add_argument(
        '--cli', action='store_true',
        help='Forzar modo CLI (línea de comandos)'
    )
    mode_group.add_argument(
        '--batch', action='store_true',
        help='Modo procesamiento batch especializado'
    )
    mode_group.add_argument(
        '--analyze', action='store_true',
        help='Solo análisis sin modificar archivos'
    )
    
    # Archivos y directorios
    parser.add_argument(
        'paths', nargs='*',
        help='Archivos MP3 o directorios a procesar'
    )
    
    # Configuración general
    parser.add_argument(
        '--recursive', '-r', action='store_true',
        help='Procesar directorios recursivamente'
    )
    parser.add_argument(
        '--backup-dir',
        default="/Volumes/My Passport/Dj compilation 2025/Respados mp3",
        help='Directorio para backups'
    )
    parser.add_argument(
        '--confidence', type=float, default=0.3,
        help='Umbral mínimo de confianza (0.0-1.0)'
    )
    parser.add_argument(
        '--max-genres', type=int, default=3,
        help='Número máximo de géneros a asignar'
    )
    parser.add_argument(
        '--no-spotify', action='store_true',
        help='Deshabilitar API de Spotify'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Salida detallada'
    )
    
    # Opciones específicas de batch
    parser.add_argument(
        '--dry-run', action='store_true',
        help='[BATCH] Solo simular cambios sin aplicar'
    )
    parser.add_argument(
        '--force', action='store_true',
        help='[BATCH] Forzar actualización aunque ya existan metadatos'
    )
    parser.add_argument(
        '--max-files', type=int,
        help='[BATCH] Máximo número de archivos a procesar'
    )
    parser.add_argument(
        '--workers', type=int, default=4,
        help='[BATCH] Número de procesos paralelos'
    )
    parser.add_argument(
        '--debug', action='store_true',
        help='[BATCH] Información detallada de debug'
    )
    
    return parser

def main():
    """Función principal del launcher unificado."""
    parser = create_parser()
    args = parser.parse_args()
    
    launcher = UnifiedLauncher()
    
    # Mostrar información del sistema
    print("🎵 DETECTOR DE GÉNEROS MUSICALES")
    print("=" * 40)
    print(f"GUI disponible: {'✅ Sí' if launcher.gui_available else '❌ No'}")
    
    try:
        # Determinar modo de ejecución
        if args.gui:
            if launcher.gui_available:
                launcher.run_gui()
            else:
                print("❌ GUI no disponible en este entorno. Usando CLI...")
                launcher.run_cli(args.paths, False, **vars(args))
        
        elif args.cli:
            launcher.run_cli(args.paths, False, **vars(args))
        
        elif args.batch:
            if not args.paths:
                print("❌ Modo batch requiere especificar un directorio")
                sys.exit(1)
            launcher.run_cli(args.paths, False, batch_mode=True, **vars(args))
        
        elif args.analyze:
            if not args.paths:
                print("❌ Modo análisis requiere especificar archivos")
                sys.exit(1)
            launcher.run_cli(args.paths, True, **vars(args))
        
        else:
            # Auto-detectar modo
            mode = launcher.auto_detect_mode()
            print(f"🔍 Modo auto-detectado: {mode.upper()}")
            
            if mode == 'gui':
                launcher.run_gui()
            else:
                launcher.run_cli(args.paths, False, **vars(args))
    
    except KeyboardInterrupt:
        print("\n🛑 Operación cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error crítico: {e}")
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
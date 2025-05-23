"""Script to run the Genre Detector GUI application."""
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow

def setup_logging():
    """Configura el sistema de registro."""
    log_file = Path("app.log")
    
    # Configuración básica del logger
    logging.basicConfig(
        level=logging.DEBUG,  # Set global level to DEBUG
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set debug level specifically for file_handler
    file_handler_logger = logging.getLogger('src.core.file_handler')
    file_handler_logger.setLevel(logging.DEBUG)
    
    # Configurar el nivel de logging para musicbrainzngs a WARNING para reducir el ruido
    logging.getLogger("musicbrainzngs").setLevel(logging.WARNING)
    # Configurar el nivel de logging para pylast a WARNING también
    logging.getLogger("pylast").setLevel(logging.WARNING)
    # Configurar el nivel de logging para la librería mpd a WARNING
    logging.getLogger("mpd").setLevel(logging.WARNING)

    # Log de inicio de aplicación
    logger = logging.getLogger(__name__)
    logger.info("Iniciando Genre Detector GUI...")

def main():
    """Función principal para ejecutar la aplicación."""
    # Configurar logging
    setup_logging()
    
    # Debug logging
    logger = logging.getLogger(__name__)
    logger.info(f"Python path: {sys.path}")
    logger.info(f"Current working directory: {Path.cwd()}")
    
    try:
        from src.gui.main_window import MainWindow
        logger.info("Successfully imported MainWindow")
    except ImportError as e:
        logger.error(f"Failed to import MainWindow: {e}")
        sys.exit(1)
    
    # Crear la aplicación Qt
    app = QApplication(sys.argv)
    
    # Crear y mostrar la ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar el loop principal
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

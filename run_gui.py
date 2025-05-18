"""Launch the GUI application."""
import sys
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.gui.style import apply_dark_theme
import logging # Importar logging

if __name__ == "__main__":
    # Configurar logging básico
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.StreamHandler(sys.stdout) # Asegurar que salga a stdout
                        ])
    logger = logging.getLogger(__name__)
    logger.info("Lanzando aplicación GUI...")

    app = QApplication(sys.argv)
    apply_dark_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

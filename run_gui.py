"""Launch the GUI application."""
import sys
from PySide6.QtWidgets import QApplication
# from src.gui.style import apply_dark_theme # Comentada ya que qt-material maneja el tema
from src.gui.main_window import MainWindow
# from src.utils.config_loader import AppConfig # Comentada, parece no existir o no usarse aquí
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

    # Cargar configuración (opcional, si es necesario antes de la GUI)
    # app_config = AppConfig()
    # settings = app_config.get_settings()

    app = QApplication(sys.argv)
    
    # Aplicar tema oscuro inicial (si se desea, o manejarlo dentro de MainWindow)
    # apply_dark_theme(app) # Comentada
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

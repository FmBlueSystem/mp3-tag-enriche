import sys
import os # Necesario para manipulación de paths
import logging

# Añadir el directorio raíz del proyecto (padre de 'src') a sys.path
# para que la importación 'from src.gui.main_window' funcione correctamente.
# __file__ es la ruta al script actual (src/run_gui.py)
# os.path.dirname(__file__) es el directorio del script actual (src)
# os.path.join(..., '..') va al directorio padre (la raíz del proyecto)
# os.path.abspath asegura que sea una ruta absoluta.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow

# Configurar el logging básico para la GUI
LOG_FILE = os.path.expanduser("~/GenreDetectorApp.log") # Usar ruta absoluta en el home del usuario

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w'), # Escribir a ~/GenreDetectorApp.log, sobrescribiendo
        logging.StreamHandler(sys.stdout) # Mantener logs en la salida estándar también
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("Iniciando la aplicación Genre Detector GUI...")
    app = QApplication(sys.argv)
    
    try:
        window = MainWindow()
        window.show()
        logger.info("Ventana principal mostrada.")
    except Exception as e:
        logger.error(f"Error al inicializar MainWindow: {e}", exc_info=True)
        # Opcional: Mostrar un diálogo de error al usuario si QApplication ya está corriendo
        # from PySide6.QtWidgets import QMessageBox
        # QMessageBox.critical(None, "Error de Aplicación", f"No se pudo iniciar la ventana principal: {e}")
        sys.exit(1) # Salir si la ventana no se puede crear

    sys.exit(app.exec())

if __name__ == '__main__':
    main() 
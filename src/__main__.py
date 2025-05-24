"""
Nueva Biblioteca - Sistema inteligente de gestión musical

Punto de entrada principal de la aplicación.
"""

from src.ui.main_window import MainWindow
from PySide6.QtWidgets import QApplication
import sys


def main():
    """Función principal de la aplicación."""
    app = QApplication(sys.argv)
    app.setApplicationName("Nueva Biblioteca")
    app.setApplicationVersion("1.0.0")
    
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

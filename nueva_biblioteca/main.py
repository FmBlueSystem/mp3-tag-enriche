#!/usr/bin/env python3
"""
Nueva Biblioteca - Sistema de Gestión Musical Inteligente
Aplicación principal con Material 3 Expressive
"""
import sys
from pathlib import Path

# Agregar el directorio src al path para importaciones
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication
from src.ui.main_window import MainWindow
from qt_material import apply_stylesheet

import src.config as config

def main():
    """Función principal de la aplicación."""
    try:
        # Configurar HiDPI
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
        
        # Configurar aplicación
        app = QApplication(sys.argv)
        
        # Aplicar estilo Material Design con ajustes para Retina
        theme_extras = {
            'density_scale': '2',  # Escala para Retina
            'font_size': config.MATERIAL_THEME['font_size']
        }
        apply_stylesheet(app, theme='dark_purple.xml', extra=theme_extras)
        
        # Crear ventana principal
        window = MainWindow()
        window.resize(config.WINDOW_CONFIG['default_width'], 
                     config.WINDOW_CONFIG['default_height'])
        window.show()
        
        # Centrar ventana
        window.center_on_screen()
        
        return app.exec()
        
    except Exception as e:
        print(f"Error fatal en la aplicación: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

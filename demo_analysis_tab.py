#!/usr/bin/env python3
"""
Demo del Tab de Análisis de Tracks - Nueva Biblioteca Musical
"""

import sys
import os

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # Cambiar automáticamente al tab de análisis (índice 2)
    window.tab_widget.setCurrentIndex(2)
    
    print('✅ Interfaz iniciada con el Tab de Análisis activo')
    print('📊 Puedes ver las estadísticas, usar las herramientas y explorar los datos')
    print('🔄 Presiona Ctrl+C para cerrar cuando termines de explorar')
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print('\n👋 Cerrando aplicación...')

if __name__ == "__main__":
    main() 
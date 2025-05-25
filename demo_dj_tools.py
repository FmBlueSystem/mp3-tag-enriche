#!/usr/bin/env python3
"""
Demo de Herramientas de DJ - v2.3
Demostración de las funcionalidades profesionales de DJ integradas en la aplicación.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.main_window import MainWindow

def demo_dj_tools():
    """Inicia la aplicación con el tab de DJ activo."""
    app = QApplication(sys.argv)
    
    # Crear ventana principal
    window = MainWindow()
    
    if not window.db_conn:
        print("❌ Error crítico con la base de datos. No se puede continuar.")
        sys.exit(1)
    
    # Cambiar al tab de DJ (índice 3)
    window.tab_widget.setCurrentIndex(3)
    
    print("🎧 ¡Herramientas de DJ iniciadas!")
    print("🎛️ Funcionalidades disponibles:")
    print("   • Crossfader virtual con control de volumen")
    print("   • Sincronización de BPM con cálculo de pitch")
    print("   • Sugerencias inteligentes de transición")
    print("   • Análisis de compatibilidad armónica")
    print("   • Análisis de flujo energético")
    print("")
    print("🎵 Datos cargados desde la base de datos real")
    print("🔄 Haz clic en las sugerencias para probar la funcionalidad")
    print("🎚️ Mueve el crossfader para ver los cambios de volumen")
    print("⚡ Usa los botones de sincronización para ajustar BPM")
    print("")
    print("🔄 Presiona Ctrl+C para cerrar cuando termines de explorar")
    
    window.show()
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n👋 ¡Gracias por probar las herramientas de DJ!")

if __name__ == "__main__":
    demo_dj_tools() 
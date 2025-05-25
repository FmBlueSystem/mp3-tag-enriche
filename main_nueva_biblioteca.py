#!/usr/bin/env python3
"""
🎵 NUEVA BIBLIOTECA - Sistema de Gestión Musical Inteligente
===========================================================

Aplicación moderna de gestión de bibliotecas musicales con:
- Interfaz Material 3 Expressive
- Motor de reglas inteligente
- Playlists dinámicas
- Búsqueda avanzada

Uso:
    python main_nueva_biblioteca.py
"""

import sys
import os
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Punto de entrada principal de Nueva Biblioteca."""
    try:
        print("🎵 NUEVA BIBLIOTECA - Iniciando...")
        print("=" * 50)
        
        # Importar dependencias
        from PySide6.QtWidgets import QApplication
        from qt_material import apply_stylesheet
        
        # Importar componentes de la aplicación
        from src.ui.main_window import MainWindow
        
        # Crear aplicación Qt
        app = QApplication(sys.argv)
        
        # Aplicar tema Material 3 Expressive
        apply_stylesheet(app, theme='dark_purple.xml', extra={
            'font_family': 'Roboto',
            'font_size': '11px',
            'primary_color': '#6750A4',
            'secondary_color': '#625B71',
            'surface_color': '#1C1B1F',
            'background_color': '#141218'
        })
        
        # Crear y mostrar ventana principal
        window = MainWindow()
        window.show()
        
        print("✅ Nueva Biblioteca iniciada correctamente")
        print("🎨 Tema Material 3 Expressive aplicado")
        print("🚀 ¡Disfruta gestionando tu música!")
        
        # Ejecutar aplicación
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("💡 Asegúrate de tener instaladas las dependencias:")
        print("   pip install PySide6 qt-material")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error ejecutando Nueva Biblioteca: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 
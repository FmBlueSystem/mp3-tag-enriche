#!/usr/bin/env python3
"""
Demo de la interfaz gráfica del optimizador de playlists.
Muestra cómo usar el optimizador con diferentes estrategias.
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication

from ..playlist_optimizer_window import PlaylistOptimizerWindow

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Punto de entrada principal de la demo."""
    try:
        # Crear aplicación Qt
        app = QApplication(sys.argv)
        
        # Configurar estilo
        app.setStyle('Fusion')
        
        # Crear y mostrar ventana
        window = PlaylistOptimizerWindow()
        window.show()
        
        # Ejecutar loop principal
        return app.exec()
        
    except Exception as e:
        logging.error(f"Error iniciando la demo: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())

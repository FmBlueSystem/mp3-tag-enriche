#!/usr/bin/env python3
"""Entry point for the MP3 Tag Enricher application."""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from .gui.main_window import MainWindow

def main():
    """Initialize and run the application."""
    app = QApplication(sys.argv)
    
    # Set default font
    default_font = QFont("Helvetica", 12)
    app.setFont(default_font)
    
    # Set application metadata
    app.setApplicationName("MP3 Tag Enricher")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("FMolina")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

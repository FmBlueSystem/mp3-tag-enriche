"""
Ventana principal de Nueva Biblioteca
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel,
    QPushButton, QStatusBar
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QScreen, QGuiApplication

from .dialogs import ImportDialog, PreferencesDialog
from ..services.music_service import MusicService

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.music_service = MusicService()
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        self.setWindowTitle("Nueva Biblioteca - Gestión Musical")
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Título
        title = QLabel("Nueva Biblioteca")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        # Barra de estado
        self.statusBar().showMessage("Listo")
        
    def center_on_screen(self):
        """Centra la ventana en la pantalla."""
        # Obtener la geometría de la pantalla principal
        screen = QGuiApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            frame = self.frameGeometry()
            frame.moveCenter(geometry.center())
            self.move(frame.topLeft())

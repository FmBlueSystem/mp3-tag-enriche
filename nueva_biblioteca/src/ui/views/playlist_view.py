"""
Vista de playlist con Material 3 Expressive.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class PlaylistView(QWidget):
    """Vista de playlist con diseño Material 3 Expressive."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        
        label = QLabel("Vista de Playlists")
        label.setStyleSheet("""
            QLabel {
                color: #E6E1E5;
                font-size: 24px;
                font-weight: 600;
                text-align: center;
                padding: 40px;
            }
        """)
        layout.addWidget(label) 
"""
Panel de playlists con Material 3 Expressive.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QFrame
from PySide6.QtCore import Signal


class PlaylistPanel(QWidget):
    """Panel de playlists con diseño Material 3 Expressive."""
    
    playlist_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Título
        title = QLabel("Playlists")
        title.setStyleSheet("""
            QLabel {
                color: #E6E1E5;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 0px;
            }
        """)
        layout.addWidget(title)
        
        # Lista de playlists
        self.playlist_list = QListWidget()
        self.playlist_list.setStyleSheet("""
            QListWidget {
                background: rgba(28, 27, 31, 0.4);
                border: 1px solid rgba(103, 80, 164, 0.2);
                border-radius: 12px;
                color: #E6E1E5;
                padding: 8px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 6px;
                margin: 1px 0px;
            }
            QListWidget::item:hover {
                background: rgba(103, 80, 164, 0.2);
            }
            QListWidget::item:selected {
                background: rgba(103, 80, 164, 0.3);
            }
        """)
        
        # Agregar playlists de ejemplo
        for playlist in ["Favoritos", "Rock Clásico", "Chill Out", "Workout"]:
            self.playlist_list.addItem(f"🎶 {playlist}")
            
        layout.addWidget(self.playlist_list, 1) 
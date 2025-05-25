"""
Panel de filtros con Material 3 Expressive.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QCheckBox
from PySide6.QtCore import Signal


class FilterPanel(QWidget):
    """Panel de filtros con diseño Material 3 Expressive."""
    
    filter_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Título
        title = QLabel("Filtros")
        title.setStyleSheet("""
            QLabel {
                color: #E6E1E5;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 0px;
            }
        """)
        layout.addWidget(title)
        
        # Filtro por género
        genre_label = QLabel("Género:")
        genre_label.setStyleSheet("color: #CAC4D0; font-size: 12px;")
        layout.addWidget(genre_label)
        
        self.genre_combo = QComboBox()
        self.genre_combo.addItems(["Todos", "Rock", "Pop", "Jazz", "Electronic", "Classical"])
        self.genre_combo.setStyleSheet("""
            QComboBox {
                background: rgba(28, 27, 31, 0.4);
                border: 1px solid rgba(103, 80, 164, 0.2);
                border-radius: 8px;
                color: #E6E1E5;
                padding: 8px 12px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(:/icons/expand_more.png);
            }
        """)
        layout.addWidget(self.genre_combo)
        
        # Filtros adicionales
        self.favorites_check = QCheckBox("Solo favoritos")
        self.favorites_check.setStyleSheet("""
            QCheckBox {
                color: #CAC4D0;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 2px solid rgba(103, 80, 164, 0.5);
                background: transparent;
            }
            QCheckBox::indicator:checked {
                background: #6750A4;
                border-color: #6750A4;
            }
        """)
        layout.addWidget(self.favorites_check)
        
        layout.addStretch() 
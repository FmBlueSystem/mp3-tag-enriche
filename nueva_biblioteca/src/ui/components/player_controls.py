"""
Controles de reproductor con Material 3 Expressive.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider
from PySide6.QtCore import Signal, Qt


class PlayerControls(QWidget):
    """Controles de reproductor con diseño Material 3 Expressive."""
    
    play_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Título
        title = QLabel("Reproductor")
        title.setStyleSheet("""
            QLabel {
                color: #E6E1E5;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 0px;
            }
        """)
        layout.addWidget(title)
        
        # Información de la pista actual
        self.track_info = QLabel("Sin reproducir")
        self.track_info.setStyleSheet("""
            QLabel {
                color: #CAC4D0;
                font-size: 12px;
                padding: 4px 8px;
                background: rgba(28, 27, 31, 0.4);
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.track_info)
        
        # Controles de reproducción
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        # Botones de control
        self.prev_btn = QPushButton("⏮")
        self.play_btn = QPushButton("▶")
        self.next_btn = QPushButton("⏭")
        
        for btn in [self.prev_btn, self.play_btn, self.next_btn]:
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(103, 80, 164, 0.3);
                    border: none;
                    border-radius: 20px;
                    color: #D0BCFF;
                    font-size: 16px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(103, 80, 164, 0.4);
                }
                QPushButton:pressed {
                    background: rgba(103, 80, 164, 0.5);
                }
            """)
            
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.next_btn)
        
        layout.addLayout(controls_layout)
        
        # Barra de progreso
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(103, 80, 164, 0.2);
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #6750A4;
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -6px 0;
            }
            QSlider::sub-page:horizontal {
                background: #6750A4;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_slider) 
"""Widget para configurar efectos de transición."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QComboBox, QSlider, QLabel, QPushButton,
                             QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QColor

class MaterialSlider(QSlider):
    """Slider con estilo Material Design."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #E0E0E0;
                margin: 2px 0;
            }
            
            QSlider::handle:horizontal {
                background: #6200EE;
                border: none;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            
            QSlider::sub-page:horizontal {
                background: #6200EE;
            }
        """)

class MaterialComboBox(QComboBox):
    """ComboBox con estilo Material Design."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QComboBox {
                border: 2px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
                min-width: 6em;
                background: white;
            }
            
            QComboBox:hover {
                border-color: #6200EE;
            }
            
            QComboBox::drop-down {
                border: none;
            }
            
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)

class TransitionEffectWidget(QWidget):
    """Widget para configurar efectos de transición."""
    
    effect_changed = Signal(str)  # Emitido cuando se cambia el efecto
    duration_changed = Signal(float)  # Emitido cuando cambia la duración
    preview_requested = Signal()  # Emitido cuando se solicita previsualizar
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configurar widget principal
        self.setObjectName("transitionEffectWidget")
        self.setStyleSheet("""
            #transitionEffectWidget {
                background: white;
                border-radius: 8px;
            }
        """)
        
        # Crear elementos
        self.effect_combo = MaterialComboBox()
        self.effect_combo.addItems(["CrossFade", "EQ Transition"])
        
        self.duration_slider = MaterialSlider(Qt.Horizontal)
        self.duration_slider.setRange(5, 100)  # 0.5s a 10s en steps de 0.1s
        self.duration_slider.setValue(20)  # 2s por defecto
        
        self.duration_label = QLabel("2.0s")
        self.duration_label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 14px;
            }
        """)
        
        self.preview_button = QPushButton("Previsualizar")
        self.preview_button.setStyleSheet("""
            QPushButton {
                background: #6200EE;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            
            QPushButton:hover {
                background: #3700B3;
            }
            
            QPushButton:pressed {
                background: #BB86FC;
            }
        """)
        
        # Crear layouts
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        effect_layout = QHBoxLayout()
        effect_layout.addWidget(QLabel("Efecto:"))
        effect_layout.addWidget(self.effect_combo)
        
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duración:"))
        duration_layout.addWidget(self.duration_slider)
        duration_layout.addWidget(self.duration_label)
        
        # Agregar layouts y widgets
        main_layout.addLayout(effect_layout)
        main_layout.addLayout(duration_layout)
        main_layout.addWidget(self.preview_button)
        
        self.setLayout(main_layout)
        
        # Conectar señales
        self.effect_combo.currentTextChanged.connect(
            lambda text: self.effect_changed.emit(text.lower().replace(" ", "_")))
        self.duration_slider.valueChanged.connect(self._update_duration)
        self.preview_button.clicked.connect(self.preview_requested)
        
    def _update_duration(self, value):
        """Actualiza la duración del efecto."""
        duration = value / 10.0  # Convertir a segundos
        self.duration_label.setText(f"{duration:.1f}s")
        self.duration_changed.emit(duration)
        
    def get_current_effect(self) -> str:
        """Retorna el nombre del efecto seleccionado."""
        return self.effect_combo.currentText().lower().replace(" ", "_")
        
    def get_current_duration(self) -> float:
        """Retorna la duración actual en segundos."""
        return self.duration_slider.value() / 10.0

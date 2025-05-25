"""Diálogo para configurar y previsualizar efectos de transición."""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFrame, QLabel)
from PySide6.QtCore import Qt, Signal

from ..widgets.transition_effect_widget import TransitionEffectWidget
from ...services.transition_effects import TransitionEffectManager

class TransitionEffectDialog(QDialog):
    """Diálogo para configurar efectos de transición."""
    
    effect_configured = Signal(str, float)  # nombre_efecto, duración
    
    def __init__(self, effect_manager: TransitionEffectManager, parent=None):
        """
        Inicializa el diálogo de efectos.
        
        Args:
            effect_manager: Gestor de efectos de transición
            parent: Widget padre
        """
        super().__init__(parent)
        
        self.effect_manager = effect_manager
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("Configurar Efecto de Transición")
        self.setStyleSheet("""
            QDialog {
                background: white;
            }
        """)
        self.resize(400, 300)
        
        # Layout principal
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Título
        title = QLabel("Configurar Efecto")
        title.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 20px;
                font-weight: 500;
            }
        """)
        layout.addWidget(title)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #E0E0E0;")
        layout.addWidget(separator)
        
        # Widget de configuración
        self.effect_widget = TransitionEffectWidget()
        layout.addWidget(self.effect_widget)
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #6200EE;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            
            QPushButton:hover {
                background: rgba(98, 0, 238, 0.04);
            }
            
            QPushButton:pressed {
                background: rgba(98, 0, 238, 0.12);
            }
        """)
        
        self.accept_button = QPushButton("Aceptar")
        self.accept_button.setStyleSheet("""
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
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.accept_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Conectar señales
        self.cancel_button.clicked.connect(self.reject)
        self.accept_button.clicked.connect(self._handle_accept)
        self.effect_widget.preview_requested.connect(self._preview_effect)
        
    def _handle_accept(self):
        """Maneja la aceptación del diálogo."""
        effect_name = self.effect_widget.get_current_effect()
        duration = self.effect_widget.get_current_duration()
        
        # Emitir señal con la configuración
        self.effect_configured.emit(effect_name, duration)
        self.accept()
        
    def _preview_effect(self):
        """Previsualiza el efecto actual."""
        effect_name = self.effect_widget.get_current_effect()
        duration = self.effect_widget.get_current_duration()
        
        # Obtener el efecto del manager
        effect = self.effect_manager.get_effect(effect_name)
        if effect:
            # Configurar duración
            effect.duration = duration
            # TODO: Implementar previsualización con audio de ejemplo

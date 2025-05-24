"""Control panel widget for genre detection settings."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QCheckBox, QSlider, QSpinBox, QLabel, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from typing import Dict
from PySide6.QtGui import QFont

from ..i18n import tr

class ControlPanel(QWidget):
    """Control panel for genre detection settings."""
    
    settings_changed = Signal(dict)  # Emite diccionario con configuración actualizada
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        # Emitir configuración inicial
        self.emit_settings()
        
    def setup_ui(self):
        """Set up the control panel interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)  # Reducir espaciado entre QGroupBoxes
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Grupo de opciones de análisis
        analysis_group = QGroupBox(tr("analysis_options"))
        analysis_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 2px solid #3E4451;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }
        """)
        analysis_layout = QVBoxLayout(analysis_group)
        analysis_layout.setSpacing(8)
        analysis_layout.setContentsMargins(12, 15, 12, 12)
        
        self.rename_files = QCheckBox(tr("rename_files_checkbox"))
        self.rename_files.setAccessibleName(tr("accessibility_rename_files"))
        self.rename_files.setToolTip(tr("tooltip_rename_files"))
        self.rename_files.setChecked(True)
        analysis_layout.addWidget(self.rename_files)
        
        self.organize_files = QCheckBox(tr("organize_files_checkbox"))
        self.organize_files.setAccessibleName(tr("accessibility_organize_files"))
        self.organize_files.setToolTip(tr("tooltip_organize_files"))
        self.organize_files.setChecked(False)  # Por defecto desactivado
        analysis_layout.addWidget(self.organize_files)
        
        layout.addWidget(analysis_group)
        
        # Grupo de parámetros de detección
        detection_params_group = QGroupBox(tr("detection_params"))
        detection_params_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 2px solid #3E4451;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }
        """)
        detection_params_layout = QVBoxLayout(detection_params_group)
        detection_params_layout.setSpacing(12)
        detection_params_layout.setContentsMargins(12, 15, 12, 12)

        # Control de umbral de confianza
        confidence_container = QVBoxLayout()
        confidence_container.setSpacing(6)
        
        # Etiqueta y valor en una fila
        confidence_header = QHBoxLayout()
        confidence_header.setSpacing(8)
        
        self.confidence_label = QLabel(tr("confidence_threshold"))
        self.confidence_label.setAccessibleName(tr("accessibility_confidence"))
        self.confidence_label.setFont(QFont("Arial", 9))
        confidence_header.addWidget(self.confidence_label)
        
        confidence_header.addStretch()
        
        self.confidence_value = QLabel("0.3")
        self.confidence_value.setAccessibleName(tr("accessibility_confidence_value"))
        self.confidence_value.setFont(QFont("Arial", 9, QFont.Bold))
        self.confidence_value.setStyleSheet("color: #61AFEF; background-color: #2C323C; padding: 2px 6px; border-radius: 3px;")
        self.confidence_value.setMinimumWidth(35)
        self.confidence_value.setAlignment(Qt.AlignCenter)
        confidence_header.addWidget(self.confidence_value)
        
        confidence_container.addLayout(confidence_header)
        
        # Slider en línea separada
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setAccessibleName(tr("accessibility_confidence_slider"))
        self.confidence_slider.setAccessibleDescription(tr("accessibility_confidence_desc"))
        self.confidence_slider.setMinimumHeight(25)
        self.confidence_slider.setMinimum(10)
        self.confidence_slider.setMaximum(90)
        self.confidence_slider.setValue(30)
        self.confidence_slider.setTickInterval(20)
        self.confidence_slider.setTickPosition(QSlider.TicksBelow)
        self.confidence_slider.valueChanged.connect(self.update_confidence_label)
        self.confidence_slider.setToolTip(tr("tooltip_confidence"))
        confidence_container.addWidget(self.confidence_slider)
        
        detection_params_layout.addLayout(confidence_container)
        
        # Control de géneros máximos
        max_genres_container = QVBoxLayout()
        max_genres_container.setSpacing(6)
        
        # Etiqueta y control en una fila
        max_genres_header = QHBoxLayout()
        max_genres_header.setSpacing(8)
        
        self.max_genres_label = QLabel(tr("max_genres"))
        self.max_genres_label.setAccessibleName(tr("accessibility_max_genres"))
        self.max_genres_label.setFont(QFont("Arial", 9))
        max_genres_header.addWidget(self.max_genres_label)
        
        max_genres_header.addStretch()
        
        self.max_genres_spinner = QSpinBox()
        self.max_genres_spinner.setAccessibleName(tr("accessibility_max_genres_control"))
        self.max_genres_spinner.setAccessibleDescription(tr("accessibility_max_genres_desc"))
        self.max_genres_spinner.setMinimumWidth(60)
        self.max_genres_spinner.setMinimumHeight(28)
        self.max_genres_spinner.setMinimum(1)
        self.max_genres_spinner.setMaximum(10)
        self.max_genres_spinner.setValue(3)
        self.max_genres_spinner.valueChanged.connect(self.emit_settings)
        self.max_genres_spinner.setToolTip(tr("tooltip_max_genres"))
        self.max_genres_spinner.setAlignment(Qt.AlignCenter)
        max_genres_header.addWidget(self.max_genres_spinner)
        
        max_genres_container.addLayout(max_genres_header)
        detection_params_layout.addLayout(max_genres_container)
        
        layout.addWidget(detection_params_group)
        
        # Conectar cambios
        self.rename_files.stateChanged.connect(self.emit_settings)
        self.organize_files.stateChanged.connect(self.emit_settings)
        self.confidence_slider.valueChanged.connect(self.emit_settings)
        self.max_genres_spinner.valueChanged.connect(self.emit_settings)
        
    def update_confidence_label(self, value: int) -> None:
        """Update the confidence value label."""
        confidence = value / 100
        self.confidence_value.setText(f"{confidence:.1f}")
        
    def emit_settings(self, *args) -> None:
        """Emit the current settings."""
        self.settings_changed.emit(self.get_settings())
        
    def get_settings(self) -> Dict:
        """Get the current settings."""
        return {
            'rename_files': self.rename_files.isChecked(),
            'organize_files': self.organize_files.isChecked(),
            'confidence': self.confidence_slider.value() / 100.0,
            'max_genres': self.max_genres_spinner.value()
        }

    def set_settings(self, settings: Dict) -> None:
        """Set the panel settings."""
        if 'rename_files' in settings:
            self.rename_files.setChecked(settings['rename_files'])
        if 'organize_files' in settings:
            self.organize_files.setChecked(settings['organize_files'])
        if 'confidence' in settings:
            self.confidence_slider.setValue(int(settings['confidence'] * 100))
        if 'max_genres' in settings:
            self.max_genres_spinner.setValue(settings['max_genres'])

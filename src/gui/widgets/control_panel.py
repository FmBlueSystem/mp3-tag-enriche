"""Control panel widget for genre detection settings."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QCheckBox, QSlider, QSpinBox, QLabel, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from typing import Dict

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
        layout.setSpacing(10) # Reducir espaciado entre QGroupBoxes
        
        # Grupo de opciones de análisis
        analysis_group = QGroupBox(tr("analysis_options"))
        analysis_layout = QVBoxLayout(analysis_group)
        analysis_layout.setSpacing(8)
        
        self.analyze_only = QCheckBox(tr("analyze_only_checkbox"))
        self.analyze_only.setAccessibleName(tr("accessibility_analyze_only"))
        self.analyze_only.setToolTip(tr("tooltip_analyze_only"))
        self.analyze_only.setChecked(True)
        analysis_layout.addWidget(self.analyze_only)
        
        self.rename_files = QCheckBox(tr("rename_files_checkbox"))
        self.rename_files.setAccessibleName(tr("accessibility_rename_files"))
        self.rename_files.setToolTip(tr("tooltip_rename_files"))
        self.rename_files.setChecked(True)
        analysis_layout.addWidget(self.rename_files)
        
        layout.addWidget(analysis_group)
        
        # Grupo de parámetros de detección
        detection_params_group = QGroupBox(tr("detection_params"))
        detection_params_layout = QVBoxLayout(detection_params_group)
        detection_params_layout.setSpacing(8)

        # Control de umbral de confianza
        confidence_row = QHBoxLayout()
        confidence_row.setSpacing(8)
        
        self.confidence_label = QLabel(tr("confidence_threshold"))
        self.confidence_label.setAccessibleName(tr("accessibility_confidence"))
        confidence_row.addWidget(self.confidence_label)
        
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setAccessibleName(tr("accessibility_confidence_slider"))
        self.confidence_slider.setAccessibleDescription(tr("accessibility_confidence_desc"))
        self.confidence_slider.setMinimumWidth(64)  # Material Design minimum width
        self.confidence_slider.setMinimum(10)
        self.confidence_slider.setMaximum(90)
        self.confidence_slider.setValue(30)
        self.confidence_slider.setTickInterval(10)
        self.confidence_slider.setTickPosition(QSlider.TicksBelow)
        self.confidence_slider.valueChanged.connect(self.update_confidence_label)
        self.confidence_slider.setToolTip(tr("tooltip_confidence"))
        confidence_row.addWidget(self.confidence_slider, 1) # Slider ocupa más espacio
        
        self.confidence_value = QLabel("0.3")
        self.confidence_value.setAccessibleName(tr("accessibility_confidence_value"))
        self.confidence_value.setMinimumWidth(30) # Ancho mínimo para el valor
        confidence_row.addWidget(self.confidence_value)
        
        detection_params_layout.addLayout(confidence_row)
        
        # Control de géneros máximos
        max_genres_row = QHBoxLayout()
        max_genres_row.setSpacing(8)
        
        self.max_genres_label = QLabel(tr("max_genres"))
        self.max_genres_label.setAccessibleName(tr("accessibility_max_genres"))
        max_genres_row.addWidget(self.max_genres_label)
        
        self.max_genres_spinner = QSpinBox()
        self.max_genres_spinner.setAccessibleName(tr("accessibility_max_genres_control"))
        self.max_genres_spinner.setAccessibleDescription(tr("accessibility_max_genres_desc"))
        self.max_genres_spinner.setMinimumWidth(64)  # Material Design minimum width
        self.max_genres_spinner.setMinimum(1)
        self.max_genres_spinner.setMaximum(10)
        self.max_genres_spinner.setValue(3)
        self.max_genres_spinner.valueChanged.connect(self.update_max_genres_label)
        self.max_genres_spinner.setToolTip(tr("tooltip_max_genres"))
        max_genres_row.addWidget(self.max_genres_spinner)
        
        self.max_genres_value = QLabel("3") # Este QLabel podría ser redundante si el QSpinBox ya muestra el valor
        self.max_genres_value.setAccessibleName(tr("accessibility_max_genres_value"))
        self.max_genres_value.setMinimumWidth(30) # Ancho mínimo
        # max_genres_row.addWidget(self.max_genres_value) # Opcional, QSpinBox ya muestra el valor
        max_genres_row.addStretch() # Empujar el spinner a la izquierda si no se usa el label de valor

        detection_params_layout.addLayout(max_genres_row)
        layout.addWidget(detection_params_group)
        
        # Conectar cambios
        self.analyze_only.stateChanged.connect(self.emit_settings)
        self.rename_files.stateChanged.connect(self.emit_settings)
        self.confidence_slider.valueChanged.connect(self.emit_settings)
        self.max_genres_spinner.valueChanged.connect(self.emit_settings)
        
    def update_confidence_label(self, value: int) -> None:
        """Update the confidence value label."""
        confidence = value / 100
        self.confidence_value.setText(f"{confidence:.1f}")
        
    def update_max_genres_label(self, value: int) -> None:
        """Update the maximum genres value label."""
        self.max_genres_value.setText(str(value))
        
    def emit_settings(self, *args) -> None:
        """Emit the current settings."""
        self.settings_changed.emit(self.get_settings())
        
    def get_settings(self) -> Dict:
        """Get the current settings."""
        return {
            'analyze_only': self.analyze_only.isChecked(),
            'rename_files': self.rename_files.isChecked(),
            'confidence': self.confidence_slider.value() / 100.0,
            'max_genres': self.max_genres_spinner.value()
        }

    def set_settings(self, settings: Dict) -> None:
        """Set the panel settings."""
        if 'analyze_only' in settings:
            self.analyze_only.setChecked(settings['analyze_only'])
        if 'rename_files' in settings:
            self.rename_files.setChecked(settings['rename_files'])
        if 'confidence' in settings:
            self.confidence_slider.setValue(int(settings['confidence'] * 100))
        if 'max_genres' in settings:
            self.max_genres_spinner.setValue(settings['max_genres'])

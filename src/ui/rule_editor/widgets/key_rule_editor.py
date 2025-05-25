from typing import Optional, List, Set
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QComboBox, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal

from .camelot_wheel import CamelotWheelWidget
from ....core.camelot import CamelotWheel, CompatibilityMode

class KeyRuleEditor(QWidget):
    """
    Editor especializado para reglas que involucran claves musicales.
    Integra la rueda Camelot para selección visual de claves y
    modos de compatibilidad.
    """
    
    # Señales
    ruleChanged = pyqtSignal(str)  # Emite la regla como texto
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Componentes
        self.wheel = CamelotWheelWidget()
        self.camelot = CamelotWheel()
        
        # Estado
        self.selected_key: Optional[str] = None
        self.compatible_keys: Set[str] = set()
        self.current_mode = CompatibilityMode.PERFECT
        
        self.initUI()
        
    def initUI(self):
        """Inicializa la interfaz del editor."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Panel superior con controles
        controls = QHBoxLayout()
        
        # Selector de modo de compatibilidad
        mode_label = QLabel("Modo:")
        mode_label.setStyleSheet("font-weight: bold;")
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Igual (Perfect Match)",
            "Energía ↑ (Energy Up)",
            "Energía ↓ (Energy Down)",
            "Armónico (Harmonic)"
        ])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        
        # Botones de acción
        self.clear_button = QPushButton("🗑️ Limpiar")
        self.clear_button.clicked.connect(self.clear_selection)
        
        self.rotate_button = QPushButton("🔄 Rotar")
        self.rotate_button.clicked.connect(lambda: self.wheel.rotate(30))
        
        # Agregar widgets al layout de controles
        controls.addWidget(mode_label)
        controls.addWidget(self.mode_combo)
        controls.addStretch()
        controls.addWidget(self.clear_button)
        controls.addWidget(self.rotate_button)
        
        # Panel de preview
        preview = QWidget()
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        
        preview_label = QLabel("Vista Previa de Regla:")
        preview_label.setStyleSheet("font-weight: bold;")
        
        self.preview_text = QLabel()
        self.preview_text.setWordWrap(True)
        self.preview_text.setStyleSheet("""
            QLabel {
                color: #666666;
                background-color: #f5f5f5;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.preview_text)
        
        # Descripción
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setStyleSheet("""
            QLabel {
                color: #666666;
                font-style: italic;
            }
        """)
        self._update_description()
        
        # Agregar todo al layout principal
        layout.addLayout(controls)
        layout.addWidget(self.wheel)
        layout.addWidget(preview)
        layout.addWidget(self.description)
        
        # Conectar señales
        self.wheel.keySelected.connect(self._on_key_selected)
        self.wheel.compatibilityChanged.connect(self._on_compatibility_changed)
        
    def _on_key_selected(self, key: str):
        """
        Maneja la selección de una clave.
        
        Args:
            key: Clave seleccionada en notación Camelot
        """
        self.selected_key = key
        self._update_rule()
        self._update_description()
        
    def _on_compatibility_changed(self, compatible_keys: List[str]):
        """
        Maneja cambios en la compatibilidad.
        
        Args:
            compatible_keys: Lista de claves compatibles
        """
        self.compatible_keys = set(compatible_keys)
        self._update_rule()
        
    def _on_mode_changed(self, index: int):
        """
        Maneja cambios en el modo de compatibilidad.
        
        Args:
            index: Índice seleccionado en el combo
        """
        modes = [
            CompatibilityMode.PERFECT,
            CompatibilityMode.ENERGY_UP,
            CompatibilityMode.ENERGY_DOWN,
            CompatibilityMode.HARMONIC
        ]
        
        if 0 <= index < len(modes):
            self.current_mode = modes[index]
            self.wheel.set_compatibility_mode(self.current_mode)
            self._update_description()
            
    def _update_rule(self):
        """Actualiza la regla basada en la selección actual."""
        if not self.selected_key:
            self.preview_text.setText("")
            self.ruleChanged.emit("")
            return
            
        # Obtener clave musical
        musical_key = self.camelot.get_musical_key(self.selected_key)
        if not musical_key:
            return
            
        # Construir regla
        rule = f"key COMPATIBLE_WITH '{musical_key}'"
        
        # Actualizar preview
        self.preview_text.setText(rule)
        self.ruleChanged.emit(rule)
        
    def _update_description(self):
        """Actualiza el texto descriptivo según el modo actual."""
        if not self.selected_key:
            desc = (
                "Selecciona una clave en la rueda para crear una regla. "
                "Las claves mayores están en el anillo exterior y las menores "
                "en el interior."
            )
        else:
            key_info = self.camelot.get_key_info(self.selected_key)
            mode_desc = {
                CompatibilityMode.PERFECT: "misma clave",
                CompatibilityMode.ENERGY_UP: "energía creciente",
                CompatibilityMode.ENERGY_DOWN: "energía decreciente",
                CompatibilityMode.HARMONIC: "armonía paralela"
            }
            
            desc = (
                f"Clave seleccionada: {key_info['musical_key']} "
                f"({key_info['camelot_key']})\n"
                f"Modo: {mode_desc.get(self.current_mode, '')}\n"
                f"Claves compatibles: {len(self.compatible_keys)}"
            )
            
        self.description.setText(desc)
        
    def clear_selection(self):
        """Limpia la selección actual."""
        self.selected_key = None
        self.compatible_keys.clear()
        self.wheel.select_key(None)
        self._update_rule()
        self._update_description()
        
    def get_rule(self) -> str:
        """
        Retorna la regla actual como texto.
        
        Returns:
            str: Regla en formato texto o vacío si no hay selección
        """
        if self.selected_key:
            musical_key = self.camelot.get_musical_key(self.selected_key)
            return f"key COMPATIBLE_WITH '{musical_key}'"
        return ""

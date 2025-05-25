"""
Panel de filtros avanzados con Material 3 Expressive.
Integrado con RuleService para filtrado inteligente.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QCheckBox, QPushButton, QLineEdit, QSlider, QFrame,
    QTextEdit, QGroupBox, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, List, Any


class FilterPanel(QWidget):
    """Panel de filtros avanzados con diseño Material 3 Expressive."""
    
    # Señales
    filter_applied = Signal(dict)  # filter_data
    filter_cleared = Signal()
    rule_validated = Signal(bool, str)  # is_valid, message
    quick_rule_applied = Signal(str)  # rule_expression
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_filters = {}
        self._setup_ui()
        self._setup_connections()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(16)
        
        # Título del panel
        header = self._create_header()
        layout.addWidget(header)
        
        # Sección de filtros rápidos
        quick_filters = self._create_quick_filters_section()
        layout.addWidget(quick_filters)
        
        # Sección de filtros básicos
        basic_filters = self._create_basic_filters_section()
        layout.addWidget(basic_filters)
        
        # Sección de filtros numéricos
        numeric_filters = self._create_numeric_filters_section()
        layout.addWidget(numeric_filters)
        
        # Sección de reglas personalizadas
        custom_rules = self._create_custom_rules_section()
        layout.addWidget(custom_rules)
        
        # Botones de acción
        actions = self._create_actions_section()
        layout.addWidget(actions)
        
        layout.addStretch()
        
    def _create_header(self) -> QWidget:
        """Crea el encabezado del panel."""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: rgba(103, 80, 164, 0.1);
                border-radius: 8px;
                padding: 4px;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 8, 12, 8)
        
        title = QLabel("Filtros Avanzados")
        title.setStyleSheet("""
            QLabel {
                color: #E6E1E5;
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Botón de ayuda
        help_btn = QPushButton("?")
        help_btn.setFixedSize(24, 24)
        help_btn.setToolTip("Ayuda de filtros")
        help_btn.setStyleSheet("""
            QPushButton {
                background: rgba(103, 80, 164, 0.2);
                border: none;
                border-radius: 12px;
                color: #CAC4D0;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(103, 80, 164, 0.3);
            }
        """)
        help_btn.clicked.connect(self._show_filter_help)
        layout.addWidget(help_btn)
        
        return header
    
    def _create_quick_filters_section(self) -> QWidget:
        """Crea la sección de filtros rápidos."""
        section = QGroupBox("Filtros Rápidos")
        section.setStyleSheet("""
            QGroupBox {
                color: #D0BCFF;
                font-size: 12px;
                font-weight: 600;
                border: 1px solid rgba(103, 80, 164, 0.3);
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px 0 8px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(8)
        
        # Crear botones de filtros rápidos
        quick_filters_data = [
            ("⚡ Alta Energía", "energy > 0.8"),
            ("🔥 Populares", "play_count > 30"),
            ("⭐ Favoritos", "rating >= 4"),
            ("🆕 Recientes", "year > 2015"),
            ("💪 Workout", "energy > 0.8 AND bpm > 120"),
            ("😌 Chill", "energy < 0.5 AND valence > 0.4")
        ]
        
        for i in range(0, len(quick_filters_data), 2):
            row_layout = QHBoxLayout()
            
            # Botón izquierdo
            name, rule = quick_filters_data[i]
            btn_left = self._create_quick_filter_button(name, rule)
            row_layout.addWidget(btn_left)
            
            # Botón derecho (si existe)
            if i + 1 < len(quick_filters_data):
                name, rule = quick_filters_data[i + 1]
                btn_right = self._create_quick_filter_button(name, rule)
                row_layout.addWidget(btn_right)
            else:
                row_layout.addStretch()
            
            layout.addLayout(row_layout)
        
        return section
    
    def _create_quick_filter_button(self, name: str, rule: str) -> QPushButton:
        """Crea un botón de filtro rápido."""
        btn = QPushButton(name)
        btn.setStyleSheet("""
            QPushButton {
                background: rgba(103, 80, 164, 0.2);
                border: 1px solid rgba(103, 80, 164, 0.3);
                border-radius: 6px;
                color: #D0BCFF;
                font-size: 10px;
                padding: 6px 8px;
                text-align: center;
            }
            QPushButton:hover {
                background: rgba(103, 80, 164, 0.3);
                border-color: rgba(103, 80, 164, 0.5);
            }
            QPushButton:pressed {
                background: rgba(103, 80, 164, 0.4);
            }
        """)
        btn.clicked.connect(lambda: self.quick_rule_applied.emit(rule))
        return btn
    
    def _create_basic_filters_section(self) -> QWidget:
        """Crea la sección de filtros básicos."""
        section = QGroupBox("Filtros Básicos")
        section.setStyleSheet("""
            QGroupBox {
                color: #D0BCFF;
                font-size: 12px;
                font-weight: 600;
                border: 1px solid rgba(103, 80, 164, 0.3);
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px 0 8px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        
        # Filtro por género
        genre_layout = QVBoxLayout()
        genre_label = QLabel("Género:")
        genre_label.setStyleSheet("color: #CAC4D0; font-size: 11px;")
        genre_layout.addWidget(genre_label)
        
        self.genre_combo = QComboBox()
        self.genre_combo.addItems(["Todos", "Rock", "Pop", "Jazz", "Electronic", "Classical", "Hip Hop", "House", "Techno"])
        self.genre_combo.setStyleSheet(self._get_combo_style())
        genre_layout.addWidget(self.genre_combo)
        layout.addLayout(genre_layout)
        
        # Filtro por artista
        artist_layout = QVBoxLayout()
        artist_label = QLabel("Artista:")
        artist_label.setStyleSheet("color: #CAC4D0; font-size: 11px;")
        artist_layout.addWidget(artist_label)
        
        self.artist_combo = QComboBox()
        self.artist_combo.addItems(["Todos"])
        self.artist_combo.setStyleSheet(self._get_combo_style())
        artist_layout.addWidget(self.artist_combo)
        layout.addLayout(artist_layout)
        
        # Checkboxes para filtros especiales
        self.favorites_check = QCheckBox("Solo favoritos (rating ≥ 4)")
        self.favorites_check.setStyleSheet(self._get_checkbox_style())
        layout.addWidget(self.favorites_check)
        
        self.recent_check = QCheckBox("Solo tracks recientes (> 2015)")
        self.recent_check.setStyleSheet(self._get_checkbox_style())
        layout.addWidget(self.recent_check)
        
        return section
    
    def _create_numeric_filters_section(self) -> QWidget:
        """Crea la sección de filtros numéricos."""
        section = QGroupBox("Filtros Numéricos")
        section.setStyleSheet("""
            QGroupBox {
                color: #D0BCFF;
                font-size: 12px;
                font-weight: 600;
                border: 1px solid rgba(103, 80, 164, 0.3);
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px 0 8px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        
        # Filtro de BPM
        bpm_layout = QVBoxLayout()
        bpm_label = QLabel("BPM:")
        bpm_label.setStyleSheet("color: #CAC4D0; font-size: 11px;")
        bpm_layout.addWidget(bpm_label)
        
        bpm_range_layout = QHBoxLayout()
        self.bpm_min = QSpinBox()
        self.bpm_min.setRange(0, 300)
        self.bpm_min.setValue(0)
        self.bpm_min.setSuffix(" min")
        self.bpm_min.setStyleSheet(self._get_spinbox_style())
        
        self.bpm_max = QSpinBox()
        self.bpm_max.setRange(0, 300)
        self.bpm_max.setValue(200)
        self.bpm_max.setSuffix(" max")
        self.bpm_max.setStyleSheet(self._get_spinbox_style())
        
        bpm_range_layout.addWidget(self.bpm_min)
        bpm_range_layout.addWidget(QLabel("-"))
        bpm_range_layout.addWidget(self.bpm_max)
        bpm_layout.addLayout(bpm_range_layout)
        layout.addLayout(bpm_layout)
        
        # Filtro de energía
        energy_layout = QVBoxLayout()
        energy_label = QLabel("Energía:")
        energy_label.setStyleSheet("color: #CAC4D0; font-size: 11px;")
        energy_layout.addWidget(energy_label)
        
        energy_range_layout = QHBoxLayout()
        self.energy_min = QDoubleSpinBox()
        self.energy_min.setRange(0.0, 1.0)
        self.energy_min.setValue(0.0)
        self.energy_min.setSingleStep(0.1)
        self.energy_min.setDecimals(1)
        self.energy_min.setSuffix(" min")
        self.energy_min.setStyleSheet(self._get_spinbox_style())
        
        self.energy_max = QDoubleSpinBox()
        self.energy_max.setRange(0.0, 1.0)
        self.energy_max.setValue(1.0)
        self.energy_max.setSingleStep(0.1)
        self.energy_max.setDecimals(1)
        self.energy_max.setSuffix(" max")
        self.energy_max.setStyleSheet(self._get_spinbox_style())
        
        energy_range_layout.addWidget(self.energy_min)
        energy_range_layout.addWidget(QLabel("-"))
        energy_range_layout.addWidget(self.energy_max)
        energy_layout.addLayout(energy_range_layout)
        layout.addLayout(energy_layout)
        
        # Filtro de año
        year_layout = QVBoxLayout()
        year_label = QLabel("Año:")
        year_label.setStyleSheet("color: #CAC4D0; font-size: 11px;")
        year_layout.addWidget(year_label)
        
        year_range_layout = QHBoxLayout()
        self.year_min = QSpinBox()
        self.year_min.setRange(1900, 2030)
        self.year_min.setValue(1980)
        self.year_min.setSuffix(" min")
        self.year_min.setStyleSheet(self._get_spinbox_style())
        
        self.year_max = QSpinBox()
        self.year_max.setRange(1900, 2030)
        self.year_max.setValue(2024)
        self.year_max.setSuffix(" max")
        self.year_max.setStyleSheet(self._get_spinbox_style())
        
        year_range_layout.addWidget(self.year_min)
        year_range_layout.addWidget(QLabel("-"))
        year_range_layout.addWidget(self.year_max)
        year_layout.addLayout(year_range_layout)
        layout.addLayout(year_layout)
        
        return section
    
    def _create_custom_rules_section(self) -> QWidget:
        """Crea la sección de reglas personalizadas."""
        section = QGroupBox("Regla Personalizada")
        section.setStyleSheet("""
            QGroupBox {
                color: #D0BCFF;
                font-size: 12px;
                font-weight: 600;
                border: 1px solid rgba(103, 80, 164, 0.3);
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px 0 8px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(8)
        
        # Campo de entrada de regla
        rule_label = QLabel("Expresión de regla:")
        rule_label.setStyleSheet("color: #CAC4D0; font-size: 11px;")
        layout.addWidget(rule_label)
        
        self.rule_input = QTextEdit()
        self.rule_input.setMaximumHeight(80)
        self.rule_input.setPlaceholderText("Ejemplo: genre = 'House' AND bpm > 120")
        self.rule_input.setStyleSheet("""
            QTextEdit {
                background: rgba(28, 27, 31, 0.6);
                border: 1px solid rgba(103, 80, 164, 0.3);
                border-radius: 6px;
                color: #E6E1E5;
                font-size: 11px;
                padding: 8px;
            }
            QTextEdit:focus {
                border-color: #6750A4;
            }
        """)
        layout.addWidget(self.rule_input)
        
        # Botones de regla
        rule_buttons = QHBoxLayout()
        
        validate_btn = QPushButton("Validar")
        validate_btn.setStyleSheet(self._get_button_style("#2196F3"))
        validate_btn.clicked.connect(self._validate_rule)
        rule_buttons.addWidget(validate_btn)
        
        apply_rule_btn = QPushButton("Aplicar Regla")
        apply_rule_btn.setStyleSheet(self._get_button_style("#6750A4"))
        apply_rule_btn.clicked.connect(self._apply_custom_rule)
        rule_buttons.addWidget(apply_rule_btn)
        
        layout.addLayout(rule_buttons)
        
        # Estado de validación
        self.validation_label = QLabel("Escriba una regla para validar")
        self.validation_label.setStyleSheet("""
            QLabel {
                color: #938F99;
                font-size: 10px;
                padding: 4px;
            }
        """)
        layout.addWidget(self.validation_label)
        
        return section
    
    def _create_actions_section(self) -> QWidget:
        """Crea la sección de botones de acción."""
        actions = QFrame()
        layout = QHBoxLayout(actions)
        layout.setSpacing(8)
        
        # Botón aplicar filtros
        apply_btn = QPushButton("Aplicar Filtros")
        apply_btn.setStyleSheet(self._get_button_style("#4CAF50"))
        apply_btn.clicked.connect(self._apply_filters)
        layout.addWidget(apply_btn)
        
        # Botón limpiar
        clear_btn = QPushButton("Limpiar")
        clear_btn.setStyleSheet(self._get_button_style("#F44336"))
        clear_btn.clicked.connect(self._clear_filters)
        layout.addWidget(clear_btn)
        
        return actions
    
    def _setup_connections(self):
        """Configura las conexiones de señales."""
        # Conectar cambios en controles para actualización automática
        self.genre_combo.currentTextChanged.connect(self._on_basic_filter_changed)
        self.artist_combo.currentTextChanged.connect(self._on_basic_filter_changed)
        self.favorites_check.toggled.connect(self._on_basic_filter_changed)
        self.recent_check.toggled.connect(self._on_basic_filter_changed)
        
        # Conectar controles numéricos
        self.bpm_min.valueChanged.connect(self._on_numeric_filter_changed)
        self.bpm_max.valueChanged.connect(self._on_numeric_filter_changed)
        self.energy_min.valueChanged.connect(self._on_numeric_filter_changed)
        self.energy_max.valueChanged.connect(self._on_numeric_filter_changed)
        self.year_min.valueChanged.connect(self._on_numeric_filter_changed)
        self.year_max.valueChanged.connect(self._on_numeric_filter_changed)
        
        # Conectar entrada de regla
        self.rule_input.textChanged.connect(self._on_rule_text_changed)
    
    def _on_basic_filter_changed(self):
        """Maneja cambios en filtros básicos."""
        self._update_current_filters()
    
    def _on_numeric_filter_changed(self):
        """Maneja cambios en filtros numéricos."""
        self._update_current_filters()
    
    def _on_rule_text_changed(self):
        """Maneja cambios en el texto de regla."""
        self.validation_label.setText("Regla modificada - validar para aplicar")
        self.validation_label.setStyleSheet("color: #938F99; font-size: 10px; padding: 4px;")
    
    def _update_current_filters(self):
        """Actualiza los filtros actuales."""
        self._current_filters = {
            'genre': self.genre_combo.currentText(),
            'artist': self.artist_combo.currentText(),
            'favorites': self.favorites_check.isChecked(),
            'recent': self.recent_check.isChecked(),
            'bpm_min': self.bpm_min.value(),
            'bpm_max': self.bpm_max.value(),
            'energy_min': self.energy_min.value(),
            'energy_max': self.energy_max.value(),
            'year_min': self.year_min.value(),
            'year_max': self.year_max.value()
        }
    
    def _apply_filters(self):
        """Aplica todos los filtros seleccionados."""
        self._update_current_filters()
        
        # Construir regla desde filtros
        rule_parts = []
        
        # Filtro de género
        if self._current_filters['genre'] != "Todos":
            rule_parts.append(f"genre = '{self._current_filters['genre']}'")
        
        # Filtro de artista
        if self._current_filters['artist'] != "Todos":
            rule_parts.append(f"artist = '{self._current_filters['artist']}'")
        
        # Filtros checkbox
        if self._current_filters['favorites']:
            rule_parts.append("rating >= 4")
        
        if self._current_filters['recent']:
            rule_parts.append("year > 2015")
        
        # Filtros numéricos
        if self._current_filters['bpm_min'] > 0 or self._current_filters['bpm_max'] < 200:
            rule_parts.append(f"bpm BETWEEN {self._current_filters['bpm_min']} AND {self._current_filters['bpm_max']}")
        
        if self._current_filters['energy_min'] > 0.0 or self._current_filters['energy_max'] < 1.0:
            rule_parts.append(f"energy BETWEEN {self._current_filters['energy_min']} AND {self._current_filters['energy_max']}")
        
        if self._current_filters['year_min'] > 1980 or self._current_filters['year_max'] < 2024:
            rule_parts.append(f"year BETWEEN {self._current_filters['year_min']} AND {self._current_filters['year_max']}")
        
        # Combinar reglas con AND
        if rule_parts:
            rule = " AND ".join(rule_parts)
            filter_data = {'rule': rule, 'filters': self._current_filters}
            self.filter_applied.emit(filter_data)
        else:
            # Sin filtros, limpiar
            self.filter_cleared.emit()
    
    def _clear_filters(self):
        """Limpia todos los filtros."""
        # Resetear controles
        self.genre_combo.setCurrentText("Todos")
        self.artist_combo.setCurrentText("Todos")
        self.favorites_check.setChecked(False)
        self.recent_check.setChecked(False)
        
        self.bpm_min.setValue(0)
        self.bpm_max.setValue(200)
        self.energy_min.setValue(0.0)
        self.energy_max.setValue(1.0)
        self.year_min.setValue(1980)
        self.year_max.setValue(2024)
        
        self.rule_input.clear()
        self.validation_label.setText("Filtros limpiados")
        
        # Emitir señal
        self.filter_cleared.emit()
    
    def _validate_rule(self):
        """Valida la regla personalizada."""
        rule_text = self.rule_input.toPlainText().strip()
        if not rule_text:
            self.validation_label.setText("Ingrese una regla para validar")
            self.validation_label.setStyleSheet("color: #938F99; font-size: 10px; padding: 4px;")
            return
        
        # Emitir señal de validación (será manejada por MainWindow -> RuleService)
        self.rule_validated.emit(True, rule_text)  # Temporal, se actualizará con respuesta real
    
    def _apply_custom_rule(self):
        """Aplica la regla personalizada."""
        rule_text = self.rule_input.toPlainText().strip()
        if rule_text:
            filter_data = {'rule': rule_text, 'custom': True}
            self.filter_applied.emit(filter_data)
    
    def _show_filter_help(self):
        """Muestra ayuda de filtros."""
        # TODO: Implementar diálogo de ayuda detallada
        pass
    
    def update_artists(self, artists: List[str]):
        """Actualiza la lista de artistas disponibles."""
        current = self.artist_combo.currentText()
        self.artist_combo.clear()
        self.artist_combo.addItem("Todos")
        self.artist_combo.addItems(artists)
        
        # Restaurar selección si existe
        index = self.artist_combo.findText(current)
        if index >= 0:
            self.artist_combo.setCurrentIndex(index)
    
    def update_genres(self, genres: List[str]):
        """Actualiza la lista de géneros disponibles."""
        current = self.genre_combo.currentText()
        self.genre_combo.clear()
        self.genre_combo.addItem("Todos")
        self.genre_combo.addItems(genres)
        
        # Restaurar selección si existe
        index = self.genre_combo.findText(current)
        if index >= 0:
            self.genre_combo.setCurrentIndex(index)
    
    def set_validation_result(self, is_valid: bool, message: str):
        """Establece el resultado de validación de regla."""
        if is_valid:
            self.validation_label.setText(f"✓ {message}")
            self.validation_label.setStyleSheet("color: #4CAF50; font-size: 10px; padding: 4px;")
        else:
            self.validation_label.setText(f"✗ {message}")
            self.validation_label.setStyleSheet("color: #F44336; font-size: 10px; padding: 4px;")
    
    # === Métodos de utilidad para estilos ===
    
    def _get_combo_style(self) -> str:
        return """
            QComboBox {
                background: rgba(28, 27, 31, 0.6);
                border: 1px solid rgba(103, 80, 164, 0.3);
                border-radius: 6px;
                color: #E6E1E5;
                font-size: 11px;
                padding: 6px 8px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background: #2B2930;
                border: 1px solid #6750A4;
                color: #E6E1E5;
                selection-background-color: rgba(103, 80, 164, 0.3);
            }
        """
    
    def _get_checkbox_style(self) -> str:
        return """
            QCheckBox {
                color: #CAC4D0;
                font-size: 11px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border-radius: 3px;
                border: 2px solid rgba(103, 80, 164, 0.5);
                background: transparent;
            }
            QCheckBox::indicator:checked {
                background: #6750A4;
                border-color: #6750A4;
            }
            QCheckBox::indicator:hover {
                border-color: rgba(103, 80, 164, 0.7);
            }
        """
    
    def _get_spinbox_style(self) -> str:
        return """
            QSpinBox, QDoubleSpinBox {
                background: rgba(28, 27, 31, 0.6);
                border: 1px solid rgba(103, 80, 164, 0.3);
                border-radius: 4px;
                color: #E6E1E5;
                font-size: 10px;
                padding: 4px 6px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #6750A4;
            }
        """
    
    def _get_button_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background: {color};
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 11px;
                font-weight: 600;
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                background: {color}E6;
            }}
            QPushButton:pressed {{
                background: {color}CC;
            }}
        """
"""
Barra de búsqueda con Material 3 Expressive.
Integrada con motor de reglas para búsquedas inteligentes.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, 
    QCompleter, QLabel, QFrame, QMenu, QToolTip
)
from PySide6.QtCore import Qt, Signal, QTimer, QStringListModel, QPoint
from PySide6.QtGui import QIcon, QFont


class SearchBar(QWidget):
    """
    Barra de búsqueda expresiva con autocompletado y filtros rápidos.
    
    Características Material 3 Expressive:
    - Diseño redondeado y elevado
    - Animaciones suaves
    - Autocompletado inteligente
    - Filtros rápidos visuales
    """
    
    # Señales
    search_changed = Signal(str)
    rule_applied = Signal(str)  # rule_expression
    quick_filter_applied = Signal(str)  # rule_expression
    search_cleared = Signal()
    rule_help_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self._setup_ui()
        self._setup_connections()
        self._setup_completer()
        
        # Timer para búsqueda con delay
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._emit_search)
        
        # Estado de modo de reglas
        self._rule_mode = False
        self._current_rule = ""
        
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Contenedor principal con estilo
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background: rgba(103, 80, 164, 0.1);
                border: 2px solid transparent;
                border-radius: 24px;
                padding: 4px;
            }
            QFrame:focus-within {
                border-color: #6750A4;
                background: rgba(103, 80, 164, 0.15);
            }
        """)
        
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(16, 8, 16, 8)
        container_layout.setSpacing(12)
        
        # Icono de búsqueda
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("""
            QLabel {
                color: #CAC4D0;
                font-size: 16px;
                background: transparent;
                border: none;
            }
        """)
        container_layout.addWidget(search_icon)
        
        # Campo de búsqueda
        self.search_input = QLineEdit()
        self._update_search_placeholder()
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #E6E1E5;
                font-size: 14px;
                font-weight: 400;
                padding: 4px 0px;
            }
            QLineEdit::placeholder {
                color: #938F99;
            }
        """)
        container_layout.addWidget(self.search_input, 1)
        
        # Botón de modo reglas
        self.rule_mode_btn = QPushButton("🔍")
        self.rule_mode_btn.setFixedSize(32, 32)
        self.rule_mode_btn.setCheckable(True)
        self.rule_mode_btn.setToolTip("Alternar modo de reglas")
        self.rule_mode_btn.setStyleSheet("""
            QPushButton {
                background: rgba(103, 80, 164, 0.2);
                border: none;
                border-radius: 16px;
                color: #D0BCFF;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(103, 80, 164, 0.3);
            }
            QPushButton:checked {
                background: rgba(103, 80, 164, 0.5);
                color: #FFFFFF;
            }
        """)
        container_layout.addWidget(self.rule_mode_btn)
        
        # Botón de filtros rápidos
        self.filter_btn = QPushButton("⚡")
        self.filter_btn.setFixedSize(32, 32)
        self.filter_btn.setToolTip("Filtros rápidos")
        self.filter_btn.setStyleSheet("""
            QPushButton {
                background: rgba(103, 80, 164, 0.2);
                border: none;
                border-radius: 16px;
                color: #D0BCFF;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(103, 80, 164, 0.3);
            }
            QPushButton:pressed {
                background: rgba(103, 80, 164, 0.4);
            }
        """)
        container_layout.addWidget(self.filter_btn)
        
        # Botón de ayuda de reglas
        self.help_btn = QPushButton("?")
        self.help_btn.setFixedSize(24, 24)
        self.help_btn.setToolTip("Ayuda de reglas")
        self.help_btn.setStyleSheet("""
            QPushButton {
                background: rgba(103, 80, 164, 0.15);
                border: none;
                border-radius: 12px;
                color: #CAC4D0;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(103, 80, 164, 0.25);
            }
        """)
        container_layout.addWidget(self.help_btn)
        
        # Botón de limpiar
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFixedSize(24, 24)
        self.clear_btn.setVisible(False)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(242, 184, 181, 0.2);
                border: none;
                border-radius: 12px;
                color: #F2B8B5;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(242, 184, 181, 0.3);
            }
        """)
        container_layout.addWidget(self.clear_btn)
        
        layout.addWidget(container)
        
    def _setup_connections(self):
        """Configura las conexiones de señales."""
        self.search_input.textChanged.connect(self._on_text_changed)
        self.clear_btn.clicked.connect(self._clear_search)
        self.rule_mode_btn.toggled.connect(self._toggle_rule_mode)
        self.filter_btn.clicked.connect(self._show_quick_filters)
        self.help_btn.clicked.connect(self._show_rule_help)
        
    def _setup_completer(self):
        """Configura el autocompletado."""
        # Lista de sugerencias (se puede cargar dinámicamente)
        suggestions = [
            "Rock", "Pop", "Jazz", "Classical", "Electronic",
            "Hip Hop", "Country", "Blues", "Reggae", "Folk",
            "Metal", "Punk", "Indie", "Alternative", "R&B"
        ]
        
        model = QStringListModel(suggestions)
        completer = QCompleter(model, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        
        # Estilo del popup de autocompletado
        completer.popup().setStyleSheet("""
            QListView {
                background: #2B2930;
                border: 1px solid #6750A4;
                border-radius: 8px;
                color: #E6E1E5;
                selection-background-color: rgba(103, 80, 164, 0.3);
                padding: 4px;
            }
            QListView::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QListView::item:hover {
                background: rgba(103, 80, 164, 0.2);
            }
        """)
        
        self.search_input.setCompleter(completer)
        
    def _on_text_changed(self, text: str):
        """Maneja cambios en el texto de búsqueda."""
        # Mostrar/ocultar botón de limpiar
        self.clear_btn.setVisible(bool(text))
        
        # Iniciar timer para búsqueda con delay
        self.search_timer.stop()
        if text:
            self.search_timer.start(300)  # 300ms delay
        else:
            self._emit_search()
            
    def _emit_search(self):
        """Emite la señal de búsqueda."""
        query = self.search_input.text().strip()
        
        if self._rule_mode:
            # En modo reglas, emitir como regla
            self.rule_applied.emit(query)
        else:
            # En modo búsqueda normal
            self.search_changed.emit(query)
        
    def _clear_search(self):
        """Limpia la búsqueda."""
        self.search_input.clear()
        self._current_rule = ""
        self.search_cleared.emit()
        
    def _toggle_rule_mode(self, enabled: bool):
        """Alterna entre modo búsqueda y modo reglas."""
        self._rule_mode = enabled
        self._update_search_placeholder()
        
        if enabled:
            self.rule_mode_btn.setText("📝")
            self.rule_mode_btn.setToolTip("Modo reglas activo")
        else:
            self.rule_mode_btn.setText("🔍")
            self.rule_mode_btn.setToolTip("Alternar modo de reglas")
        
        # Re-emitir búsqueda actual en el nuevo modo
        if self.search_input.text().strip():
            self._emit_search()
    
    def _update_search_placeholder(self):
        """Actualiza el placeholder según el modo."""
        if self._rule_mode:
            self.search_input.setPlaceholderText("Escribir regla: genre = 'House' AND bpm > 120...")
        else:
            self.search_input.setPlaceholderText("Buscar música, artistas, álbumes...")
    
    def _show_quick_filters(self):
        """Muestra menú de filtros rápidos."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #2B2930;
                border: 1px solid #6750A4;
                border-radius: 8px;
                color: #E6E1E5;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:hover {
                background: rgba(103, 80, 164, 0.3);
            }
        """)
        
        # Filtros rápidos predefinidos
        quick_filters = [
            ("⚡ Alta Energía", "energy > 0.8"),
            ("🏠 House Music", "genre CONTAINS 'House'"),
            ("🆕 Tracks Recientes", "year > 2015"),
            ("🎵 BPM Medio", "bpm BETWEEN 120 AND 140"),
            ("⭐ Favoritos", "rating >= 4"),
            ("🔥 Muy Reproducidos", "play_count > 30"),
            ("😌 Chill Vibes", "energy < 0.5 AND valence > 0.4"),
            ("💪 Workout", "energy > 0.8 AND bpm BETWEEN 120 AND 140"),
        ]
        
        for name, rule in quick_filters:
            action = menu.addAction(name)
            action.triggered.connect(lambda checked, r=rule: self._apply_quick_filter(r))
        
        # Mostrar menú
        button_pos = self.filter_btn.mapToGlobal(QPoint(0, self.filter_btn.height()))
        menu.exec(button_pos)
    
    def _apply_quick_filter(self, rule: str):
        """Aplica un filtro rápido."""
        self.search_input.setText(rule)
        self._rule_mode = True
        self.rule_mode_btn.setChecked(True)
        self._update_search_placeholder()
        self.quick_filter_applied.emit(rule)
    
    def _show_rule_help(self):
        """Muestra ayuda de reglas."""
        self.rule_help_requested.emit()
        
    def set_suggestions(self, suggestions: list):
        """Actualiza las sugerencias de autocompletado."""
        model = QStringListModel(suggestions)
        self.search_input.completer().setModel(model)
        
    def get_query(self) -> str:
        """Obtiene la consulta actual."""
        return self.search_input.text().strip()
        
    def set_query(self, query: str):
        """Establece la consulta."""
        self.search_input.setText(query)
        
    def focus_search(self):
        """Enfoca el campo de búsqueda."""
        self.search_input.setFocus()
        self.search_input.selectAll() 
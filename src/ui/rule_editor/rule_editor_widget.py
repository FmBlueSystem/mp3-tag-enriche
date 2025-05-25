from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, 
                                    QPushButton, QLabel, QSpacerItem,
                                    QSizePolicy, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal

from .widgets.rule_canvas import RuleCanvas
from .widgets.field_palette import FieldPalette
from .widgets.rule_chip import RuleChip
from ...core.parser import Parser
from ...core.evaluator import Evaluator

class RuleEditorWidget(QWidget):
    """
    Widget principal del editor de reglas que integra:
    - Paleta de campos (izquierda)
    - Canvas de reglas (centro)
    - Controles y preview (derecha)
    """
    
    ruleChanged = pyqtSignal(str)  # Emitida cuando cambia la regla
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Componentes core
        self.parser = Parser()
        self.evaluator = Evaluator()
        
        self.initUI()
        
    def initUI(self):
        """Inicializa la interfaz del editor"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Panel izquierdo: Paleta de campos
        self.field_palette = FieldPalette()
        main_layout.addWidget(self.field_palette)
        
        # Panel central: Canvas y controles
        central_panel = QWidget()
        central_layout = QVBoxLayout(central_panel)
        central_layout.setContentsMargins(16, 16, 16, 16)
        
        # Toolbar superior
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 8)
        
        # Título
        title = QLabel("Editor de Reglas")
        title.setStyleSheet("""
            QLabel {
                color: #1976D2;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        
        # Botones de acción
        self.validateButton = QPushButton("✓ Validar")
        self.validateButton.clicked.connect(self.validateRule)
        self.validateButton.setStyleSheet(self._getButtonStyle("primary"))
        
        self.clearButton = QPushButton("🗑️ Limpiar")
        self.clearButton.clicked.connect(self.clearCanvas)
        self.clearButton.setStyleSheet(self._getButtonStyle("secondary"))
        
        toolbar_layout.addWidget(title)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.validateButton)
        toolbar_layout.addWidget(self.clearButton)
        
        # Canvas de reglas
        self.canvas = RuleCanvas()
        
        # Panel de preview
        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        
        preview_title = QLabel("Vista Previa")
        preview_title.setStyleSheet("font-weight: bold;")
        
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
        
        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(self.preview_text)
        
        # Agregar todo al layout central
        central_layout.addWidget(toolbar)
        central_layout.addWidget(self.canvas)
        central_layout.addWidget(preview_panel)
        
        main_layout.addWidget(central_panel)
        
        # Configuración del widget
        self.setMinimumSize(800, 600)
        
    def _getButtonStyle(self, style: str) -> str:
        """Retorna el estilo CSS para botones según el tipo"""
        base_style = """
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
        """
        
        if style == "primary":
            return base_style + """
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:pressed {
                    background-color: #0D47A1;
                }
            """
        else:
            return base_style + """
                QPushButton {
                    background-color: white;
                    color: #666666;
                    border: 1px solid #e0e0e0;
                }
                QPushButton:hover {
                    background-color: #f5f5f5;
                    border-color: #bdbdbd;
                }
                QPushButton:pressed {
                    background-color: #eeeeee;
                }
            """
            
    def validateRule(self):
        """Valida la regla actual usando el parser y evaluador"""
        try:
            # Convertir el estado visual a texto
            rule_text = self._buildRuleText()
            
            # Intentar parsear
            ast = self.parser.parse(rule_text)
            
            # Actualizar preview
            self.preview_text.setText(rule_text)
            self.preview_text.setStyleSheet("""
                QLabel {
                    color: #2E7D32;
                    background-color: #E8F5E9;
                    padding: 8px;
                    border-radius: 4px;
                }
            """)
            
            # Emitir cambio
            self.ruleChanged.emit(rule_text)
            
        except Exception as e:
            self.preview_text.setText(f"Error: {str(e)}")
            self.preview_text.setStyleSheet("""
                QLabel {
                    color: #C62828;
                    background-color: #FFEBEE;
                    padding: 8px;
                    border-radius: 4px;
                }
            """)
            
            QMessageBox.warning(
                self,
                "Error de Validación",
                f"La regla contiene errores:\n\n{str(e)}"
            )
            
    def clearCanvas(self):
        """Limpia todas las reglas del canvas"""
        reply = QMessageBox.question(
            self,
            "Confirmar Limpiar",
            "¿Estás seguro de que quieres eliminar todas las reglas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.canvas.rules.clear()
            self.canvas.connections.clear()
            self.canvas.update()
            self.preview_text.setText("")
            self.preview_text.setStyleSheet("""
                QLabel {
                    color: #666666;
                    background-color: #f5f5f5;
                    padding: 8px;
                    border-radius: 4px;
                }
            """)
            
    def _buildRuleText(self) -> str:
        """
        Construye el texto de la regla basado en el estado visual del canvas.
        Por ahora retorna un placeholder - se implementará cuando
        tengamos la lógica completa de conexiones.
        """
        # TODO: Implementar construcción real de regla
        return "(BPM > 120) AND (genre = 'House')"  # Placeholder

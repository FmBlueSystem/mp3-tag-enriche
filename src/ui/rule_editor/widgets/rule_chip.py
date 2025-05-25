from typing import Optional
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, 
                           QPushButton, QMenu, QVBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

from .key_rule_dialog import KeyRuleDialog

class RuleChip(QFrame):
    """
    Widget que representa una regla individual en el canvas.
    
    Ejemplo de visualización:
    ┌──────────────────────────┐
    │ BPM > 120                │
    └──────────────────────────┘
    """
    
    # Señales
    ruleChanged = pyqtSignal()  # Emitida cuando cambia la regla
    ruleDeleted = pyqtSignal()  # Emitida cuando se elimina la regla
    
    def __init__(self, field_name: str, parent=None):
        super().__init__(parent)
        
        # Estado
        self.field_name = field_name
        self.operator = None
        self.value = None
        
        # Configuración del frame
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setMinimumWidth(150)
        
        # Permitir drops para conexiones
        self.setAcceptDrops(True)
        
        # UI
        self.initUI()
        
    def initUI(self):
        """Inicializa la interfaz del chip."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 4, 8, 4)
        self.layout.setSpacing(2)
        
        # Layout superior con campo y botón de eliminar
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        self.field_label = QLabel(self.field_name)
        self.field_label.setStyleSheet("""
            QLabel {
                color: #1976D2;
                font-weight: bold;
            }
        """)
        
        self.delete_button = QPushButton("×")
        self.delete_button.setFixedSize(16, 16)
        self.delete_button.clicked.connect(self.delete)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: none;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                color: #f44336;
            }
        """)
        
        top_layout.addWidget(self.field_label)
        top_layout.addStretch()
        top_layout.addWidget(self.delete_button)
        
        # Layout inferior con operador y valor
        self.rule_label = QLabel()
        self.rule_label.setStyleSheet("color: #424242;")
        
        # Agregar sublayouts
        self.layout.addLayout(top_layout)
        self.layout.addWidget(self.rule_label)
        
        # Estilo del frame
        self.setStyleSheet("""
            RuleChip {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            
            RuleChip:hover {
                border-color: #2196F3;
            }
        """)
        
        # Menú contextual
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        
        # Si es un campo de clave, mostrar editor directamente
        if self.field_name.lower() == "key":
            self.showKeyEditor()
            
    def showContextMenu(self, pos: QPoint):
        """
        Muestra el menú contextual del chip.
        
        Args:
            pos: Posición donde mostrar el menú
        """
        menu = QMenu(self)
        
        edit_action = menu.addAction("📝 Editar")
        edit_action.triggered.connect(self.showEditor)
        
        delete_action = menu.addAction("🗑️ Eliminar")
        delete_action.triggered.connect(self.delete)
        
        menu.exec(self.mapToGlobal(pos))
        
    def showEditor(self):
        """Muestra el editor apropiado según el tipo de campo."""
        if self.field_name.lower() == "key":
            self.showKeyEditor()
        else:
            # TODO: Mostrar editor genérico
            pass
            
    def showKeyEditor(self):
        """Muestra el editor de reglas de clave musical."""
        # Obtener regla actual si existe
        current_rule = None
        if self.operator and self.value:
            current_rule = f"{self.field_name} {self.operator} {self.value}"
            
        # Mostrar diálogo
        rule = KeyRuleDialog.get_rule(current_rule, self)
        
        if rule:
            # Parsear regla generada
            # Formato esperado: "key COMPATIBLE_WITH 'G maj'"
            parts = rule.split(" ", 2)
            if len(parts) == 3:
                self.operator = parts[1]
                self.value = parts[2]
                self.updateDisplay()
                self.ruleChanged.emit()
                
    def updateDisplay(self):
        """Actualiza la visualización de la regla."""
        if self.operator and self.value:
            # Formatear según el tipo de regla
            if self.field_name.lower() == "key":
                self.rule_label.setText(f"compatible con {self.value}")
            else:
                self.rule_label.setText(f"{self.operator} {self.value}")
        else:
            self.rule_label.setText("(Click para editar)")
            
    def delete(self):
        """Elimina el chip."""
        self.ruleDeleted.emit()
        self.deleteLater()
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Maneja el inicio de un drop sobre el chip.
        
        Args:
            event: Evento de drag & drop
        """
        if event.mimeData().hasFormat("application/x-rule-connection"):
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        """
        Maneja el drop sobre el chip.
        
        Args:
            event: Evento de drag & drop
        """
        # TODO: Implementar conexión entre chips
        event.accept()
        
    def mousePressEvent(self, event):
        """
        Maneja clicks del mouse.
        
        Args:
            event: Evento del mouse
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.showEditor()
            
    def getRuleText(self) -> str:
        """
        Retorna el texto de la regla completa.
        
        Returns:
            str con la regla formateada
        """
        if self.operator and self.value:
            return f"{self.field_name} {self.operator} {self.value}"
        return ""

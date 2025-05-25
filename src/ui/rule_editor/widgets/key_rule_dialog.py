from typing import Optional
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                          QPushButton, QFrame, QLabel)
from PyQt6.QtCore import Qt

from .key_rule_editor import KeyRuleEditor

class KeyRuleDialog(QDialog):
    """
    Diálogo modal para edición de reglas de clave musical.
    Integra el KeyRuleEditor en una interfaz de diálogo.
    """
    
    def __init__(self, initial_rule: Optional[str] = None, parent=None):
        super().__init__(parent)
        
        self.rule_text = initial_rule
        self.result_rule = None  # Regla resultante al aceptar
        
        self.initUI()
        
    def initUI(self):
        """Inicializa la interfaz del diálogo."""
        self.setWindowTitle("Editor de Regla de Clave Musical")
        self.setMinimumSize(600, 800)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Descripción
        desc = QLabel(
            "Selecciona una clave musical y un modo de compatibilidad "
            "para crear una regla. La regla filtrará canciones cuya clave "
            "sea compatible con la seleccionada según el modo elegido."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666666;")
        
        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #e0e0e0;")
        
        # Editor de claves
        self.editor = KeyRuleEditor()
        
        # Cargar regla inicial si existe
        if self.rule_text:
            self._load_rule(self.rule_text)
            
        # Panel de preview
        preview_panel = QFrame()
        preview_panel.setFrameStyle(QFrame.Shape.Box)
        preview_panel.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        
        preview_title = QLabel("Vista Previa de Regla:")
        preview_title.setStyleSheet("font-weight: bold;")
        
        self.preview_label = QLabel()
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("color: #666666;")
        
        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(self.preview_label)
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet(self._get_button_style("secondary"))
        
        self.accept_button = QPushButton("Aceptar")
        self.accept_button.clicked.connect(self.accept)
        self.accept_button.setEnabled(False)  # Habilitado al tener regla válida
        self.accept_button.setStyleSheet(self._get_button_style("primary"))
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.accept_button)
        
        # Agregar todo al layout principal
        layout.addWidget(desc)
        layout.addWidget(line)
        layout.addWidget(self.editor)
        layout.addWidget(preview_panel)
        layout.addLayout(button_layout)
        
        # Conectar señales
        self.editor.ruleChanged.connect(self._on_rule_changed)
        
    def _load_rule(self, rule_text: str):
        """
        Carga una regla existente en el editor.
        
        Args:
            rule_text: Texto de la regla a cargar
        """
        # TODO: Implementar parsing de regla existente
        # Por ahora solo actualizamos el preview
        self.preview_label.setText(rule_text)
        self.accept_button.setEnabled(bool(rule_text))
        
    def _on_rule_changed(self, rule: str):
        """
        Maneja cambios en la regla.
        
        Args:
            rule: Nueva regla generada
        """
        self.preview_label.setText(rule)
        self.accept_button.setEnabled(bool(rule))
        self.result_rule = rule
        
    @staticmethod
    def _get_button_style(style: str) -> str:
        """
        Retorna el estilo CSS para botones.
        
        Args:
            style: Tipo de estilo ('primary' o 'secondary')
            
        Returns:
            str con el CSS del botón
        """
        base_style = """
            QPushButton {
                padding: 8px 16px;
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
                QPushButton:disabled {
                    background-color: #BDBDBD;
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
            
    @classmethod
    def get_rule(cls, initial_rule: Optional[str] = None, parent=None) -> Optional[str]:
        """
        Método de conveniencia para obtener una regla mediante el diálogo.
        
        Args:
            initial_rule: Regla inicial a cargar
            parent: Widget padre
            
        Returns:
            Regla generada o None si se cancela
        """
        dialog = cls(initial_rule, parent)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            return dialog.result_rule
        return None

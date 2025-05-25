#!/usr/bin/env python3
"""
Demostración del editor de reglas con rueda Camelot.
Muestra la creación visual de reglas de compatibilidad de claves musicales.
"""

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                           QVBoxLayout, QLabel, QFrame)
from PyQt6.QtCore import Qt

from ..widgets.key_rule_editor import KeyRuleEditor
from ....core.camelot import CamelotWheel, CompatibilityMode

class KeyRuleDemoWindow(QMainWindow):
    """Ventana principal de la demostración."""
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        """Inicializa la interfaz de usuario."""
        self.setWindowTitle('Editor de Reglas de Clave Musical - Demo')
        self.setGeometry(100, 100, 800, 800)
        
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        
        # Layout principal
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Título
        title = QLabel("Editor de Reglas de Clave Musical")
        title.setStyleSheet("""
            QLabel {
                color: #1976D2;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        
        # Descripción
        description = QLabel(
            "Usa la rueda Camelot para crear reglas de compatibilidad "
            "entre claves musicales. Selecciona una clave y un modo de "
            "compatibilidad para generar la regla automáticamente."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #666666;")
        
        # Editor de reglas
        self.rule_editor = KeyRuleEditor()
        
        # Panel de información
        info_panel = QFrame()
        info_panel.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        info_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        
        info_layout = QVBoxLayout(info_panel)
        
        # Información de la rueda Camelot
        wheel = CamelotWheel()
        wheel_info = QLabel(
            "Rueda Camelot:\n\n" + str(wheel)
        )
        wheel_info.setStyleSheet("""
            QLabel {
                font-family: monospace;
                padding: 8px;
            }
        """)
        
        # Información de compatibilidad
        compatibility_info = QLabel(
            "\nModos de Compatibilidad:\n"
            "- Perfect Match: Misma clave\n"
            "- Energy Up: Siguiente clave (+1)\n"
            "- Energy Down: Clave anterior (-1)\n"
            "- Harmonic: Clave relativa (+7)\n"
        )
        compatibility_info.setStyleSheet("padding: 8px;")
        
        info_layout.addWidget(wheel_info)
        info_layout.addWidget(compatibility_info)
        
        # Estado actual
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-style: italic;
                padding: 8px;
            }
        """)
        
        # Agregar widgets al layout principal
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.rule_editor)
        layout.addWidget(info_panel)
        layout.addWidget(self.status_label)
        
        # Conectar señales
        self.rule_editor.ruleChanged.connect(self._on_rule_changed)
        
    def _on_rule_changed(self, rule: str):
        """
        Maneja cambios en la regla.
        
        Args:
            rule: Nueva regla generada
        """
        if rule:
            self.status_label.setText(
                f"Regla actual: {rule}\n\n"
                "Esta regla filtrará canciones cuya clave sea "
                "compatible con la seleccionada según el modo elegido."
            )
        else:
            self.status_label.setText(
                "No hay regla definida. Selecciona una clave en la rueda "
                "para comenzar."
            )

def main():
    """Punto de entrada principal de la demo."""
    try:
        app = QApplication(sys.argv)
        
        # Configurar estilo
        app.setStyle('Fusion')
        
        # Crear y mostrar ventana
        window = KeyRuleDemoWindow()
        window.show()
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Error iniciando la demo: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

# Importar el editor de reglas
from ..rule_editor_widget import RuleEditorWidget

class RuleEditorDemo(QMainWindow):
    """Ventana de demostración del editor visual de reglas"""
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        """Inicializa la interfaz de la demo"""
        self.setWindowTitle('Editor Visual de Reglas - Demo')
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Crear y agregar el editor de reglas
        self.rule_editor = RuleEditorWidget()
        layout.addWidget(self.rule_editor)
        
        # Conectar señal de cambio de regla
        self.rule_editor.ruleChanged.connect(self.onRuleChanged)
        
        # Estilo de la ventana
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
        """)
        
    def onRuleChanged(self, rule_text: str):
        """Manejador de cambios en la regla"""
        print(f"\nRegla actualizada:")
        print(f"Text: {rule_text}")
        
        # Aquí podrías hacer más cosas con la regla,
        # como evaluarla contra una biblioteca de prueba

def main():
    """Punto de entrada principal de la demo"""
    try:
        # Crear la aplicación Qt
        app = QApplication(sys.argv)
        
        # Configurar estilo global
        app.setStyle('Fusion')
        
        # Crear y mostrar la ventana principal
        demo = RuleEditorDemo()
        demo.show()
        
        # Ejecutar el loop de eventos
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Error iniciando la demo: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()

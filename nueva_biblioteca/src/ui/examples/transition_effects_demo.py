"""Demo de efectos de transición."""

import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

from ...services.transition_effects import TransitionEffectManager
from ..dialogs.transition_effect_dialog import TransitionEffectDialog

class TransitionEffectsDemo(QMainWindow):
    """Ventana de demo para efectos de transición."""
    
    def __init__(self):
        super().__init__()
        
        # Configurar ventana
        self.setWindowTitle("Demo de Efectos de Transición")
        self.resize(500, 400)
        
        # Crear gestor de efectos
        self.effect_manager = TransitionEffectManager()
        
        # Configurar widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Configurar tema Material Design
        self.setStyleSheet("""
            QMainWindow {
                background: white;
            }
        """)
        
        # Abrir diálogo de configuración
        self.show_dialog()
        
    def show_dialog(self):
        """Muestra el diálogo de configuración de efectos."""
        dialog = TransitionEffectDialog(self.effect_manager, self)
        dialog.effect_configured.connect(self._apply_effect)
        dialog.show()
        
    def _apply_effect(self, effect_name: str, duration: float):
        """
        Aplica el efecto seleccionado.
        
        Args:
            effect_name: Nombre del efecto a aplicar
            duration: Duración de la transición en segundos
        """
        # Obtener efecto
        effect = self.effect_manager.get_effect(effect_name)
        if not effect:
            return
            
        # Configurar duración
        effect.duration = duration
        
        # Crear tonos de ejemplo
        sr = 44100  # Sample rate
        t = np.linspace(0, 3, int(sr * 3))  # 3 segundos
        
        # Audio 1: Tono de 440 Hz (La4)
        audio1 = np.sin(2 * np.pi * 440 * t)
        
        # Audio 2: Tono de 880 Hz (La5)
        audio2 = np.sin(2 * np.pi * 880 * t)
        
        # Aplicar efecto
        transition = effect.apply(audio1, audio2, sr)
        
        # TODO: Implementar reproducción de audio cuando se resuelva el problema de espacio
        print(f"Efecto {effect_name} aplicado con duración {duration}s")

def main():
    """Función principal de la demo."""
    app = QApplication(sys.argv)
    window = TransitionEffectsDemo()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

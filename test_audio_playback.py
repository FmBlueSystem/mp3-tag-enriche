#!/usr/bin/env python3
"""
Test de Reproducción de Audio - v3.0
Script de prueba para las funcionalidades de reproducción de audio.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.audio_player_widgets import AudioPlayerWidget, DualDeckWidget
from core.audio_engine import AudioEngine, is_audio_file, get_supported_formats

class AudioTestWindow(QMainWindow):
    """Ventana de prueba para reproducción de audio."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎵 Test de Reproducción de Audio v3.0")
        self.setGeometry(100, 100, 1000, 700)
        
        self._setup_ui()
        self._create_test_files()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Título
        title = QLabel("🎧 Test de Reproducción de Audio")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB; padding: 10px;")
        layout.addWidget(title)
        
        # Información de formatos soportados
        formats_info = QLabel(f"Formatos soportados: {', '.join(get_supported_formats())}")
        formats_info.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(formats_info)
        
        # Widget de dual deck
        self.dual_deck = DualDeckWidget()
        layout.addWidget(self.dual_deck)
        
        # Botones de prueba
        test_layout = QVBoxLayout()
        
        self.test_engine_btn = QPushButton("🔧 Test Motor de Audio")
        self.test_engine_btn.clicked.connect(self._test_audio_engine)
        test_layout.addWidget(self.test_engine_btn)
        
        self.load_sample_btn = QPushButton("📁 Cargar Archivos de Ejemplo")
        self.load_sample_btn.clicked.connect(self._load_sample_files)
        test_layout.addWidget(self.load_sample_btn)
        
        layout.addLayout(test_layout)
        
        # Información de estado
        self.status_label = QLabel("✅ Listo para pruebas de audio")
        self.status_label.setStyleSheet("padding: 10px; background-color: #f0f8ff; border-radius: 5px;")
        layout.addWidget(self.status_label)
    
    def _create_test_files(self):
        """Crea información sobre archivos de prueba."""
        self.test_files = []
        
        # Buscar archivos de audio en directorios comunes
        test_dirs = [
            os.path.expanduser("~/Music"),
            os.path.expanduser("~/Downloads"),
            "/System/Library/Sounds",  # macOS
            ".",  # Directorio actual
        ]
        
        for test_dir in test_dirs:
            if os.path.exists(test_dir):
                for file in os.listdir(test_dir):
                    file_path = os.path.join(test_dir, file)
                    if os.path.isfile(file_path) and is_audio_file(file_path):
                        self.test_files.append(file_path)
                        if len(self.test_files) >= 5:  # Limitar a 5 archivos
                            break
            if len(self.test_files) >= 5:
                break
        
        if self.test_files:
            self.status_label.setText(f"✅ Encontrados {len(self.test_files)} archivos de audio para pruebas")
        else:
            self.status_label.setText("⚠️ No se encontraron archivos de audio. Usa 'Cargar Audio' manualmente.")
    
    def _test_audio_engine(self):
        """Prueba el motor de audio básico."""
        try:
            engine = AudioEngine()
            
            if engine.is_initialized:
                self.status_label.setText("✅ Motor de audio inicializado correctamente")
                
                # Probar funciones básicas
                engine.set_volume(0.5)
                position = engine.get_position()
                duration = engine.get_duration()
                
                self.status_label.setText(
                    f"✅ Motor de audio OK - Pos: {position:.1f}s, Dur: {duration:.1f}s"
                )
            else:
                self.status_label.setText("❌ Error: Motor de audio no se pudo inicializar")
                
            engine.cleanup()
            
        except Exception as e:
            self.status_label.setText(f"❌ Error en test de motor: {e}")
    
    def _load_sample_files(self):
        """Carga archivos de ejemplo en los decks."""
        if len(self.test_files) >= 2:
            deck_a = self.dual_deck.get_deck_a()
            deck_b = self.dual_deck.get_deck_b()
            
            # Cargar primer archivo en Deck A
            if deck_a.load_audio_file(self.test_files[0]):
                self.status_label.setText(f"✅ Deck A: {os.path.basename(self.test_files[0])}")
            
            # Cargar segundo archivo en Deck B
            if len(self.test_files) > 1 and deck_b.load_audio_file(self.test_files[1]):
                current_text = self.status_label.text()
                self.status_label.setText(f"{current_text} | Deck B: {os.path.basename(self.test_files[1])}")
        else:
            self.status_label.setText("⚠️ No hay suficientes archivos de audio. Usa los botones 'Cargar Audio' manualmente.")
    
    def closeEvent(self, event):
        """Limpia recursos al cerrar."""
        if hasattr(self, 'dual_deck'):
            self.dual_deck.cleanup()
        super().closeEvent(event)

def main():
    """Función principal de prueba."""
    print("🎵 Iniciando test de reproducción de audio...")
    
    app = QApplication(sys.argv)
    
    # Verificar dependencias
    try:
        import pygame
        print("✅ pygame disponible")
    except ImportError:
        print("❌ pygame no disponible. Instala con: pip install pygame")
        return
    
    # Crear ventana de prueba
    window = AudioTestWindow()
    window.show()
    
    print("🎧 Ventana de prueba abierta")
    print("🎛️ Funcionalidades disponibles:")
    print("   • Reproductores duales con controles completos")
    print("   • Carga de archivos de audio (WAV, OGG, MP3)")
    print("   • Control de volumen independiente")
    print("   • Barras de progreso y tiempo")
    print("   • Estados de reproducción en tiempo real")
    print("")
    print("🔄 Usa los controles para probar la funcionalidad")
    print("📁 Haz clic en 'Cargar Audio' para seleccionar archivos")
    print("▶️ Usa Play/Pause/Stop para controlar la reproducción")
    print("")
    print("🔄 Presiona Ctrl+C para cerrar cuando termines")
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n👋 ¡Gracias por probar la reproducción de audio!")

if __name__ == "__main__":
    main() 
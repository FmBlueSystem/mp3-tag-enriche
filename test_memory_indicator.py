#!/usr/bin/env python3
"""
Script de prueba para el indicador visual de memoria.
Verifica que el indicador funcione correctamente con diferentes estados.
"""

import sys
import os
import time
import psutil
from pathlib import Path

# Agregar el directorio src al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer, Qt
from src.gui.widgets.memory_indicator import MemoryIndicator
from src.core.memory_optimizer import get_memory_optimizer

class MemoryIndicatorTest(QWidget):
    """Widget de prueba para el indicador de memoria."""
    
    def __init__(self):
        super().__init__()
        self.memory_optimizer = get_memory_optimizer()
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de prueba."""
        self.setWindowTitle("Prueba del Indicador de Memoria")
        self.setMinimumSize(600, 300)
        
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("Prueba del Indicador Visual de Memoria")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Indicador de memoria
        self.memory_indicator = MemoryIndicator()
        layout.addWidget(self.memory_indicator)
        
        # Información del sistema
        info_layout = QVBoxLayout()
        
        system_info = f"Sistema: {psutil.virtual_memory().total / (1024**3):.1f}GB RAM, {psutil.cpu_count()} CPUs"
        self.system_label = QLabel(system_info)
        info_layout.addWidget(self.system_label)
        
        self.status_label = QLabel("Estado: Iniciando...")
        info_layout.addWidget(self.status_label)
        
        layout.addLayout(info_layout)
        
        # Botones de prueba
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Iniciar Monitoreo")
        self.start_btn.clicked.connect(self.start_monitoring)
        buttons_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Detener Monitoreo")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        buttons_layout.addWidget(self.stop_btn)
        
        self.force_update_btn = QPushButton("Actualizar Ahora")
        self.force_update_btn.clicked.connect(self.force_update)
        buttons_layout.addWidget(self.force_update_btn)
        
        self.simulate_load_btn = QPushButton("Simular Carga")
        self.simulate_load_btn.clicked.connect(self.simulate_memory_load)
        buttons_layout.addWidget(self.simulate_load_btn)
        
        layout.addLayout(buttons_layout)
        
        # Conectar señales del indicador
        self.memory_indicator.memory_critical.connect(self.on_memory_critical)
        self.memory_indicator.memory_high.connect(self.on_memory_high)
        self.memory_indicator.memory_normal.connect(self.on_memory_normal)
        
        # Timer para actualizar información
        self.info_timer = QTimer()
        self.info_timer.timeout.connect(self.update_info)
        self.info_timer.start(1000)
        
    def start_monitoring(self):
        """Inicia el monitoreo activo."""
        self.memory_indicator.start_monitoring()
        self.status_label.setText("Estado: Monitoreo activo iniciado")
        
    def stop_monitoring(self):
        """Detiene el monitoreo activo."""
        self.memory_indicator.stop_monitoring()
        self.status_label.setText("Estado: Monitoreo detenido")
        
    def force_update(self):
        """Fuerza una actualización inmediata."""
        self.memory_indicator.force_update()
        self.status_label.setText("Estado: Actualización forzada")
        
    def simulate_memory_load(self):
        """Simula carga de memoria para probar los diferentes estados."""
        try:
            # Crear algunas listas grandes para simular uso de memoria
            data = []
            for i in range(5):
                data.append([0] * (1024 * 1024))  # ~4MB por lista
                time.sleep(0.1)
            
            self.status_label.setText("Estado: Simulación de carga completada")
            
            # Limpiar después de un momento
            QTimer.singleShot(2000, lambda: self.cleanup_simulation(data))
            
        except Exception as e:
            self.status_label.setText(f"Estado: Error en simulación - {e}")
            
    def cleanup_simulation(self, data):
        """Limpia la simulación de carga."""
        del data
        import gc
        gc.collect()
        self.status_label.setText("Estado: Simulación limpiada")
        
    def update_info(self):
        """Actualiza la información del sistema."""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            
            pressure_level = self.memory_indicator.get_current_pressure_level()
            
            info_text = (
                f"Memoria Sistema: {memory.percent:.1f}% "
                f"({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)\n"
                f"Proceso: {process.memory_info().rss / (1024**2):.1f}MB\n"
                f"Presión: {pressure_level}"
            )
            
            self.system_label.setText(info_text)
            
        except Exception as e:
            self.system_label.setText(f"Error obteniendo información: {e}")
    
    def on_memory_critical(self):
        """Maneja estado crítico de memoria."""
        self.status_label.setText("🔴 Estado: MEMORIA CRÍTICA detectada")
        self.status_label.setStyleSheet("color: #FF4444; font-weight: bold;")
        
    def on_memory_high(self):
        """Maneja estado alto de memoria."""
        self.status_label.setText("🟠 Estado: MEMORIA ALTA detectada")
        self.status_label.setStyleSheet("color: #FF8800; font-weight: bold;")
        
    def on_memory_normal(self):
        """Maneja estado normal de memoria."""
        self.status_label.setText("🟢 Estado: Memoria en niveles normales")
        self.status_label.setStyleSheet("color: #44AA44; font-weight: bold;")

def main():
    """Función principal del test."""
    print("🧪 Iniciando prueba del indicador visual de memoria...")
    
    app = QApplication(sys.argv)
    
    # Configurar aplicación
    app.setApplicationName("Test Indicador Memoria")
    app.setApplicationVersion("1.0")
    
    # Crear y mostrar ventana de prueba
    test_window = MemoryIndicatorTest()
    test_window.show()
    
    print("✅ Ventana de prueba mostrada")
    print("📊 Información del sistema:")
    print(f"   - RAM Total: {psutil.virtual_memory().total / (1024**3):.1f}GB")
    print(f"   - CPUs: {psutil.cpu_count()}")
    print(f"   - Uso actual: {psutil.virtual_memory().percent:.1f}%")
    
    # Ejecutar aplicación
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
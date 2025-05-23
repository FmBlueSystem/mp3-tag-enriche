#!/usr/bin/env python3
"""
Script de prueba para el indicador visual de CPU.
Verifica que el indicador funcione correctamente con diferentes estados.
"""

import sys
import os
import time
import threading
import psutil
from pathlib import Path

# Agregar el directorio src al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer, Qt
from src.gui.widgets.cpu_indicator import CPUIndicator

class CPUIndicatorTest(QWidget):
    """Widget de prueba para el indicador de CPU."""
    
    def __init__(self):
        super().__init__()
        self.load_threads = []
        self.is_loading = False
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de prueba."""
        self.setWindowTitle("Prueba del Indicador de CPU")
        self.setMinimumSize(700, 350)
        
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("Prueba del Indicador Visual de CPU")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Indicador de CPU
        self.cpu_indicator = CPUIndicator()
        layout.addWidget(self.cpu_indicator)
        
        # Información del sistema
        info_layout = QVBoxLayout()
        
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        freq_info = f" @ {cpu_freq.current:.0f}MHz" if cpu_freq else ""
        
        system_info = f"Sistema: {cpu_count} CPUs{freq_info}"
        self.system_label = QLabel(system_info)
        info_layout.addWidget(self.system_label)
        
        self.status_label = QLabel("Estado: Iniciando...")
        info_layout.addWidget(self.status_label)
        
        self.detailed_label = QLabel("")
        self.detailed_label.setFont(self.detailed_label.font())
        self.detailed_label.setStyleSheet("color: #555555; font-size: 10px;")
        info_layout.addWidget(self.detailed_label)
        
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
        
        layout.addLayout(buttons_layout)
        
        # Botones de carga de CPU
        load_buttons_layout = QHBoxLayout()
        
        self.light_load_btn = QPushButton("Carga Ligera")
        self.light_load_btn.clicked.connect(self.simulate_light_load)
        load_buttons_layout.addWidget(self.light_load_btn)
        
        self.moderate_load_btn = QPushButton("Carga Moderada")
        self.moderate_load_btn.clicked.connect(self.simulate_moderate_load)
        load_buttons_layout.addWidget(self.moderate_load_btn)
        
        self.heavy_load_btn = QPushButton("Carga Pesada")
        self.heavy_load_btn.clicked.connect(self.simulate_heavy_load)
        load_buttons_layout.addWidget(self.heavy_load_btn)
        
        self.stop_load_btn = QPushButton("Detener Carga")
        self.stop_load_btn.clicked.connect(self.stop_load)
        self.stop_load_btn.setStyleSheet("background-color: #FF6666; color: white; font-weight: bold;")
        load_buttons_layout.addWidget(self.stop_load_btn)
        
        layout.addLayout(load_buttons_layout)
        
        # Conectar señales del indicador
        self.cpu_indicator.cpu_critical.connect(self.on_cpu_critical)
        self.cpu_indicator.cpu_high.connect(self.on_cpu_high)
        self.cpu_indicator.cpu_normal.connect(self.on_cpu_normal)
        
        # Timer para actualizar información
        self.info_timer = QTimer()
        self.info_timer.timeout.connect(self.update_info)
        self.info_timer.start(1000)
        
    def start_monitoring(self):
        """Inicia el monitoreo activo."""
        self.cpu_indicator.start_monitoring()
        self.status_label.setText("Estado: Monitoreo activo iniciado")
        
    def stop_monitoring(self):
        """Detiene el monitoreo activo."""
        self.cpu_indicator.stop_monitoring()
        self.status_label.setText("Estado: Monitoreo detenido")
        
    def force_update(self):
        """Fuerza una actualización inmediata."""
        self.cpu_indicator.force_update()
        self.status_label.setText("Estado: Actualización forzada")
        
    def cpu_intensive_task(self, duration: int = 5, intensity: float = 1.0):
        """Tarea intensiva de CPU para simular carga."""
        end_time = time.time() + duration
        while time.time() < end_time and self.is_loading:
            # Operaciones matemáticas intensivas
            for _ in range(int(100000 * intensity)):
                _ = sum(i**2 for i in range(100))
            time.sleep(0.001)  # Pequeña pausa para no saturar completamente
    
    def simulate_light_load(self):
        """Simula carga ligera de CPU (~30%)."""
        if self.is_loading:
            self.stop_load()
            
        self.is_loading = True
        self.status_label.setText("Estado: Simulando carga ligera...")
        
        # 2 threads con baja intensidad
        for _ in range(2):
            thread = threading.Thread(target=self.cpu_intensive_task, args=(10, 0.3))
            thread.daemon = True
            thread.start()
            self.load_threads.append(thread)
    
    def simulate_moderate_load(self):
        """Simula carga moderada de CPU (~60%)."""
        if self.is_loading:
            self.stop_load()
            
        self.is_loading = True
        self.status_label.setText("Estado: Simulando carga moderada...")
        
        # 4 threads con intensidad media
        for _ in range(4):
            thread = threading.Thread(target=self.cpu_intensive_task, args=(10, 0.6))
            thread.daemon = True
            thread.start()
            self.load_threads.append(thread)
    
    def simulate_heavy_load(self):
        """Simula carga pesada de CPU (~90%)."""
        if self.is_loading:
            self.stop_load()
            
        self.is_loading = True
        self.status_label.setText("Estado: Simulando carga pesada...")
        
        # Threads según número de CPUs con alta intensidad
        cpu_count = psutil.cpu_count()
        for _ in range(cpu_count):
            thread = threading.Thread(target=self.cpu_intensive_task, args=(10, 0.9))
            thread.daemon = True
            thread.start()
            self.load_threads.append(thread)
    
    def stop_load(self):
        """Detiene la simulación de carga."""
        self.is_loading = False
        self.load_threads.clear()
        self.status_label.setText("Estado: Carga detenida")
        
    def update_info(self):
        """Actualiza la información del sistema."""
        try:
            # Información básica de CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            
            pressure_level = self.cpu_indicator.get_current_pressure_level()
            
            # Información detallada
            detailed_info = self.cpu_indicator.get_detailed_info()
            active_cores = detailed_info.get("active_cores", 0)
            total_cores = detailed_info.get("total_cores", 0)
            max_core = detailed_info.get("max_core_usage", 0)
            
            info_text = (
                f"CPU Total: {cpu_percent:.1f}% | "
                f"Cores Activos: {active_cores}/{total_cores} | "
                f"Max Core: {max_core:.1f}% | "
                f"Presión: {pressure_level}"
            )
            
            self.system_label.setText(info_text)
            
            # Información de cores individuales
            if cpu_per_core:
                cores_text = "Cores: " + " | ".join([f"C{i}:{usage:.0f}%" for i, usage in enumerate(cpu_per_core)])
                if len(cores_text) > 100:  # Truncar si es muy largo
                    cores_text = cores_text[:100] + "..."
                self.detailed_label.setText(cores_text)
            
        except Exception as e:
            self.system_label.setText(f"Error obteniendo información: {e}")
    
    def on_cpu_critical(self):
        """Maneja estado crítico de CPU."""
        self.status_label.setText("🔴 Estado: CPU CRÍTICA detectada")
        self.status_label.setStyleSheet("color: #FF4444; font-weight: bold;")
        
    def on_cpu_high(self):
        """Maneja estado alto de CPU."""
        self.status_label.setText("🟠 Estado: CPU ALTA detectada")
        self.status_label.setStyleSheet("color: #FF8800; font-weight: bold;")
        
    def on_cpu_normal(self):
        """Maneja estado normal de CPU."""
        self.status_label.setText("🟢 Estado: CPU en niveles normales")
        self.status_label.setStyleSheet("color: #44AA44; font-weight: bold;")
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana."""
        self.stop_load()
        super().closeEvent(event)

def main():
    """Función principal del test."""
    print("🧪 Iniciando prueba del indicador visual de CPU...")
    
    app = QApplication(sys.argv)
    
    # Configurar aplicación
    app.setApplicationName("Test Indicador CPU")
    app.setApplicationVersion("1.0")
    
    # Crear y mostrar ventana de prueba
    test_window = CPUIndicatorTest()
    test_window.show()
    
    print("✅ Ventana de prueba mostrada")
    print("📊 Información del sistema:")
    print(f"   - CPUs: {psutil.cpu_count()}")
    
    cpu_freq = psutil.cpu_freq()
    if cpu_freq:
        print(f"   - Frecuencia: {cpu_freq.current:.0f}MHz (min: {cpu_freq.min:.0f}, max: {cpu_freq.max:.0f})")
    
    print(f"   - Uso actual: {psutil.cpu_percent(interval=1):.1f}%")
    
    print("\n🎛️ Controles disponibles:")
    print("   - Carga Ligera: ~30% CPU")
    print("   - Carga Moderada: ~60% CPU") 
    print("   - Carga Pesada: ~90% CPU")
    print("   - Detener Carga: Para todas las simulaciones")
    
    # Ejecutar aplicación
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
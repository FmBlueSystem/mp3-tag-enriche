#!/usr/bin/env python3
"""
Script de prueba para los indicadores visuales de sistema (Memoria + CPU).
Verifica que ambos indicadores funcionen correctamente en conjunto.
"""

import sys
import os
import time
import threading
import psutil
from pathlib import Path

# Agregar el directorio src al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox
from PySide6.QtCore import QTimer, Qt
from src.gui.widgets.memory_indicator import MemoryIndicator
from src.gui.widgets.cpu_indicator import CPUIndicator

class SystemIndicatorsTest(QWidget):
    """Widget de prueba para ambos indicadores de sistema."""
    
    def __init__(self):
        super().__init__()
        self.load_threads = []
        self.memory_data = []
        self.is_loading = False
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de prueba."""
        self.setWindowTitle("Prueba de Indicadores de Sistema - Memoria + CPU")
        self.setMinimumSize(900, 500)
        
        layout = QVBoxLayout(self)
        
        # Título principal
        title = QLabel("🖥️ Prueba de Indicadores Visuales de Sistema")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 15px; color: #2E3440;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Contenedor de indicadores
        indicators_group = QGroupBox("Indicadores en Tiempo Real")
        indicators_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        indicators_layout = QHBoxLayout(indicators_group)
        
        # Indicador de Memoria
        memory_container = QWidget()
        memory_layout = QVBoxLayout(memory_container)
        memory_label = QLabel("Memoria del Sistema")
        memory_label.setAlignment(Qt.AlignCenter)
        memory_label.setStyleSheet("font-weight: bold; color: #5E81AC;")
        memory_layout.addWidget(memory_label)
        
        self.memory_indicator = MemoryIndicator()
        memory_layout.addWidget(self.memory_indicator)
        indicators_layout.addWidget(memory_container)
        
        # Indicador de CPU
        cpu_container = QWidget()
        cpu_layout = QVBoxLayout(cpu_container)
        cpu_label = QLabel("CPU del Sistema")
        cpu_label.setAlignment(Qt.AlignCenter)
        cpu_label.setStyleSheet("font-weight: bold; color: #D08770;")
        cpu_layout.addWidget(cpu_label)
        
        self.cpu_indicator = CPUIndicator()
        cpu_layout.addWidget(self.cpu_indicator)
        indicators_layout.addWidget(cpu_container)
        
        layout.addWidget(indicators_group)
        
        # Información del sistema
        info_group = QGroupBox("Información del Sistema")
        info_layout = QVBoxLayout(info_group)
        
        # Info básica del sistema
        system_memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        freq_info = f" @ {cpu_freq.current:.0f}MHz" if cpu_freq else ""
        
        system_info = (
            f"💾 RAM Total: {system_memory.total / (1024**3):.1f}GB | "
            f"🖥️ CPUs: {cpu_count}{freq_info}"
        )
        
        self.system_label = QLabel(system_info)
        self.system_label.setStyleSheet("font-size: 11px; color: #4C566A;")
        info_layout.addWidget(self.system_label)
        
        # Status de indicadores
        self.status_label = QLabel("Estado: Iniciando monitoreo...")
        self.status_label.setStyleSheet("font-size: 12px; color: #2E3440;")
        info_layout.addWidget(self.status_label)
        
        # Info detallada en tiempo real
        self.detailed_label = QLabel("")
        self.detailed_label.setStyleSheet("font-size: 10px; color: #5E81AC;")
        info_layout.addWidget(self.detailed_label)
        
        layout.addWidget(info_group)
        
        # Controles de monitoreo
        monitor_group = QGroupBox("Controles de Monitoreo")
        monitor_layout = QHBoxLayout(monitor_group)
        
        self.start_monitor_btn = QPushButton("▶️ Iniciar Monitoreo")
        self.start_monitor_btn.clicked.connect(self.start_monitoring)
        self.start_monitor_btn.setStyleSheet("background-color: #A3BE8C; color: white; font-weight: bold;")
        monitor_layout.addWidget(self.start_monitor_btn)
        
        self.stop_monitor_btn = QPushButton("⏸️ Pausar Monitoreo")
        self.stop_monitor_btn.clicked.connect(self.stop_monitoring)
        monitor_layout.addWidget(self.stop_monitor_btn)
        
        self.force_update_btn = QPushButton("🔄 Actualizar Ahora")
        self.force_update_btn.clicked.connect(self.force_update)
        monitor_layout.addWidget(self.force_update_btn)
        
        self.processing_mode_btn = QPushButton("⚡ Modo Procesamiento")
        self.processing_mode_btn.clicked.connect(self.toggle_processing_mode)
        self.processing_mode_btn.setStyleSheet("background-color: #EBCB8B; color: #2E3440; font-weight: bold;")
        monitor_layout.addWidget(self.processing_mode_btn)
        
        layout.addWidget(monitor_group)
        
        # Controles de simulación de carga
        load_group = QGroupBox("Simulación de Carga del Sistema")
        load_layout = QVBoxLayout(load_group)
        
        # Botones de CPU
        cpu_buttons = QHBoxLayout()
        cpu_buttons.addWidget(QLabel("CPU:"))
        
        self.cpu_light_btn = QPushButton("Ligera (30%)")
        self.cpu_light_btn.clicked.connect(lambda: self.simulate_cpu_load("light"))
        cpu_buttons.addWidget(self.cpu_light_btn)
        
        self.cpu_moderate_btn = QPushButton("Moderada (60%)")
        self.cpu_moderate_btn.clicked.connect(lambda: self.simulate_cpu_load("moderate"))
        cpu_buttons.addWidget(self.cpu_moderate_btn)
        
        self.cpu_heavy_btn = QPushButton("Pesada (90%)")
        self.cpu_heavy_btn.clicked.connect(lambda: self.simulate_cpu_load("heavy"))
        cpu_buttons.addWidget(self.cpu_heavy_btn)
        
        load_layout.addLayout(cpu_buttons)
        
        # Botones de memoria
        memory_buttons = QHBoxLayout()
        memory_buttons.addWidget(QLabel("Memoria:"))
        
        self.mem_light_btn = QPushButton("Consumir 500MB")
        self.mem_light_btn.clicked.connect(lambda: self.simulate_memory_load(500))
        memory_buttons.addWidget(self.mem_light_btn)
        
        self.mem_moderate_btn = QPushButton("Consumir 1GB")
        self.mem_moderate_btn.clicked.connect(lambda: self.simulate_memory_load(1024))
        memory_buttons.addWidget(self.mem_moderate_btn)
        
        self.mem_heavy_btn = QPushButton("Consumir 2GB")
        self.mem_heavy_btn.clicked.connect(lambda: self.simulate_memory_load(2048))
        memory_buttons.addWidget(self.mem_heavy_btn)
        
        load_layout.addLayout(memory_buttons)
        
        # Botón de limpiar
        stop_layout = QHBoxLayout()
        self.stop_all_btn = QPushButton("🛑 Detener Todas las Simulaciones")
        self.stop_all_btn.clicked.connect(self.stop_all_simulations)
        self.stop_all_btn.setStyleSheet("background-color: #BF616A; color: white; font-weight: bold;")
        stop_layout.addWidget(self.stop_all_btn)
        
        load_layout.addLayout(stop_layout)
        layout.addWidget(load_group)
        
        # Conectar señales de los indicadores
        self.memory_indicator.memory_critical.connect(self.on_memory_critical)
        self.memory_indicator.memory_high.connect(self.on_memory_high)
        self.memory_indicator.memory_normal.connect(self.on_memory_normal)
        
        self.cpu_indicator.cpu_critical.connect(self.on_cpu_critical)
        self.cpu_indicator.cpu_high.connect(self.on_cpu_high)
        self.cpu_indicator.cpu_normal.connect(self.on_cpu_normal)
        
        # Timer para actualizar información
        self.info_timer = QTimer()
        self.info_timer.timeout.connect(self.update_info)
        self.info_timer.start(1000)
        
        # Variables de estado
        self.processing_mode = False
        
    def start_monitoring(self):
        """Inicia el monitoreo activo."""
        self.memory_indicator.start_monitoring()
        self.cpu_indicator.start_monitoring()
        self.status_label.setText("Estado: ✅ Monitoreo activo")
        
    def stop_monitoring(self):
        """Detiene el monitoreo activo."""
        self.memory_indicator.stop_monitoring()
        self.cpu_indicator.stop_monitoring()
        self.status_label.setText("Estado: ⏸️ Monitoreo pausado")
        
    def force_update(self):
        """Fuerza una actualización inmediata."""
        self.memory_indicator.force_update()
        self.cpu_indicator.force_update()
        self.status_label.setText("Estado: 🔄 Actualización forzada")
        
    def toggle_processing_mode(self):
        """Alterna el modo de procesamiento."""
        self.processing_mode = not self.processing_mode
        self.memory_indicator.set_processing_mode(self.processing_mode)
        self.cpu_indicator.set_processing_mode(self.processing_mode)
        
        mode_text = "ACTIVO" if self.processing_mode else "NORMAL"
        self.status_label.setText(f"Estado: ⚡ Modo procesamiento {mode_text}")
        
        # Actualizar botón
        if self.processing_mode:
            self.processing_mode_btn.setText("🔄 Modo Normal")
        else:
            self.processing_mode_btn.setText("⚡ Modo Procesamiento")
    
    def simulate_cpu_load(self, intensity: str):
        """Simula carga de CPU."""
        if self.is_loading:
            self.stop_all_simulations()
            
        self.is_loading = True
        
        # Configurar según intensidad
        if intensity == "light":
            threads_count = 2
            work_intensity = 0.3
            duration = 10
        elif intensity == "moderate":
            threads_count = 4
            work_intensity = 0.6
            duration = 10
        else:  # heavy
            threads_count = psutil.cpu_count()
            work_intensity = 0.9
            duration = 10
            
        self.status_label.setText(f"Estado: 🔥 Simulando carga CPU {intensity.upper()}")
        
        # Crear threads de trabajo
        for _ in range(threads_count):
            thread = threading.Thread(
                target=self._cpu_intensive_task, 
                args=(duration, work_intensity)
            )
            thread.daemon = True
            thread.start()
            self.load_threads.append(thread)
    
    def simulate_memory_load(self, mb_to_consume: int):
        """Simula consumo de memoria."""
        try:
            # Crear datos en memoria
            data_chunk = [0] * (1024 * 1024)  # 1MB chunk
            for _ in range(mb_to_consume):
                self.memory_data.append(data_chunk.copy())
                
            self.status_label.setText(f"Estado: 💾 Consumiendo ~{mb_to_consume}MB de memoria")
            
        except Exception as e:
            self.status_label.setText(f"Estado: ❌ Error simulando memoria: {e}")
    
    def stop_all_simulations(self):
        """Detiene todas las simulaciones."""
        self.is_loading = False
        self.load_threads.clear()
        self.memory_data.clear()
        
        # Forzar garbage collection
        import gc
        gc.collect()
        
        self.status_label.setText("Estado: 🛑 Todas las simulaciones detenidas")
    
    def _cpu_intensive_task(self, duration: int, intensity: float):
        """Tarea intensiva de CPU."""
        end_time = time.time() + duration
        while time.time() < end_time and self.is_loading:
            for _ in range(int(100000 * intensity)):
                _ = sum(i**2 for i in range(100))
            time.sleep(0.001)
    
    def update_info(self):
        """Actualiza la información del sistema."""
        try:
            # Obtener datos actuales
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Estados de presión
            memory_pressure = self.memory_indicator.get_current_pressure_level()
            cpu_pressure = self.cpu_indicator.get_current_pressure_level()
            
            # Información detallada
            detailed_text = (
                f"📊 Memoria: {memory.percent:.1f}% ({memory_pressure}) | "
                f"CPU: {cpu_percent:.1f}% ({cpu_pressure}) | "
                f"Disponible: {memory.available / (1024**3):.1f}GB"
            )
            
            self.detailed_label.setText(detailed_text)
            
        except Exception as e:
            self.detailed_label.setText(f"Error: {e}")
    
    # Manejadores de eventos de memoria
    def on_memory_critical(self):
        self.status_label.setText("🔴 ALERTA: Memoria CRÍTICA detectada")
        self.status_label.setStyleSheet("color: #BF616A; font-weight: bold;")
        
    def on_memory_high(self):
        self.status_label.setText("🟠 ATENCIÓN: Memoria ALTA detectada")
        self.status_label.setStyleSheet("color: #D08770; font-weight: bold;")
        
    def on_memory_normal(self):
        self.status_label.setText("🟢 Memoria en niveles normales")
        self.status_label.setStyleSheet("color: #A3BE8C; font-weight: bold;")
    
    # Manejadores de eventos de CPU
    def on_cpu_critical(self):
        self.status_label.setText("🔴 ALERTA: CPU CRÍTICA detectada")
        self.status_label.setStyleSheet("color: #BF616A; font-weight: bold;")
        
    def on_cpu_high(self):
        self.status_label.setText("🟠 ATENCIÓN: CPU ALTA detectada")
        self.status_label.setStyleSheet("color: #D08770; font-weight: bold;")
        
    def on_cpu_normal(self):
        self.status_label.setText("🟢 CPU en niveles normales")
        self.status_label.setStyleSheet("color: #A3BE8C; font-weight: bold;")
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana."""
        self.stop_all_simulations()
        super().closeEvent(event)

def main():
    """Función principal del test."""
    print("🧪 Iniciando prueba de indicadores de sistema...")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Test Indicadores Sistema")
    app.setApplicationVersion("1.0")
    
    # Crear y mostrar ventana de prueba
    test_window = SystemIndicatorsTest()
    test_window.show()
    
    print("✅ Ventana de prueba mostrada")
    print("📊 Información del sistema:")
    
    memory = psutil.virtual_memory()
    print(f"   💾 RAM: {memory.total / (1024**3):.1f}GB total, {memory.percent:.1f}% en uso")
    print(f"   🖥️ CPUs: {psutil.cpu_count()}")
    
    cpu_freq = psutil.cpu_freq()
    if cpu_freq:
        print(f"   ⚡ Frecuencia: {cpu_freq.current:.0f}MHz")
    
    print(f"   📈 CPU actual: {psutil.cpu_percent(interval=1):.1f}%")
    
    print("\n🎛️ Funcionalidades de prueba:")
    print("   • Monitoreo en tiempo real de memoria y CPU")
    print("   • Modo procesamiento (actualización cada 1s)")
    print("   • Simulación de cargas de CPU (ligera/moderada/pesada)")
    print("   • Simulación de consumo de memoria (500MB/1GB/2GB)")
    print("   • Alertas visuales por cambios de estado")
    
    # Ejecutar aplicación
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
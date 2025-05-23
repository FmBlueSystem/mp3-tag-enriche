"""
Widget indicador de memoria visual para monitoreo en tiempo real.
Muestra el estado de memoria mediante colores sin interrumpir el flujo de la aplicación.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtGui import QFont, QPalette
import logging
from typing import Dict, Any

from ...core.memory_optimizer import get_memory_optimizer

logger = logging.getLogger(__name__)

class MemoryIndicator(QWidget):
    """Widget que muestra el estado de memoria mediante colores e información visual."""
    
    # Señales para comunicar cambios de estado
    memory_critical = Signal()  # Memoria crítica detectada
    memory_high = Signal()      # Memoria alta detectada
    memory_normal = Signal()    # Memoria normal
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.memory_optimizer = get_memory_optimizer()
        self.setup_ui()
        self.setup_timer()
        self.last_pressure_level = "NORMAL"
        
    def setup_ui(self):
        """Configura la interfaz del indicador."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # Etiqueta de memoria más compacta
        self.memory_label = QLabel("Memoria:")
        self.memory_label.setFont(QFont("Arial", 8, QFont.Bold))
        self.memory_label.setMinimumWidth(45)
        layout.addWidget(self.memory_label)
        
        # Barra de progreso optimizada
        self.memory_bar = QProgressBar()
        self.memory_bar.setMaximum(100)
        self.memory_bar.setMinimumWidth(80)
        self.memory_bar.setMaximumWidth(120)
        self.memory_bar.setMinimumHeight(18)
        self.memory_bar.setMaximumHeight(22)
        self.memory_bar.setTextVisible(True)
        layout.addWidget(self.memory_bar)
        
        # Indicador de estado más pequeño
        self.status_label = QLabel("●")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.status_label.setMinimumWidth(15)
        layout.addWidget(self.status_label)
        
        # Texto de estado compacto
        self.status_text = QLabel("Normal")
        self.status_text.setFont(QFont("Arial", 8))
        self.status_text.setMinimumWidth(50)
        layout.addWidget(self.status_text)
        
        # Información del proceso más pequeña
        self.process_label = QLabel("")
        self.process_label.setFont(QFont("Arial", 7))
        self.process_label.setStyleSheet("color: #666666;")
        self.process_label.setMinimumWidth(40)
        layout.addWidget(self.process_label)
        
        # Establecer estado inicial
        self.update_display("NORMAL", {"system_percent": 0, "process_rss_mb": 0})
        
    def setup_timer(self):
        """Configura el timer para actualización automática."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_memory_status)
        self.update_timer.start(2000)  # Actualizar cada 2 segundos
        
    def update_memory_status(self):
        """Actualiza el estado de memoria desde el optimizador."""
        try:
            memory_status = self.memory_optimizer.monitor_memory_pressure()
            pressure_level = memory_status.get("pressure_level", "NORMAL")
            memory_info = memory_status.get("memory_info", {})
            
            self.update_display(pressure_level, memory_info)
            
            # Emitir señales según el cambio de estado
            if pressure_level != self.last_pressure_level:
                if pressure_level == "CRÍTICO":
                    self.memory_critical.emit()
                elif pressure_level == "ALTO":
                    self.memory_high.emit()
                else:
                    self.memory_normal.emit()
                
                self.last_pressure_level = pressure_level
                
        except Exception as e:
            logger.error(f"Error actualizando estado de memoria: {e}")
    
    def update_display(self, pressure_level: str, memory_info: Dict[str, float]):
        """Actualiza la visualización del indicador."""
        system_percent = memory_info.get("system_percent", 0)
        process_mb = memory_info.get("process_rss_mb", 0)
        
        # Actualizar barra de progreso
        self.memory_bar.setValue(int(system_percent))
        self.memory_bar.setFormat(f"{system_percent:.1f}%")
        
        # Configurar colores y texto según el nivel de presión
        if pressure_level == "CRÍTICO":
            self._set_critical_style()
            status_text = "Crítico"
        elif pressure_level == "ALTO":
            self._set_high_style()
            status_text = "Alto"
        elif pressure_level == "MODERADO":
            self._set_moderate_style()
            status_text = "Moderado"
        else:
            self._set_normal_style()
            status_text = "Normal"
        
        self.status_text.setText(status_text)
        self.process_label.setText(f"Proceso: {process_mb:.0f}MB")
        
    def _set_critical_style(self):
        """Estilo para memoria crítica - Rojo."""
        self.status_label.setText("●")
        self.status_label.setStyleSheet("color: #FF4444; font-weight: bold;")
        self.memory_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #FF4444;
                border-radius: 5px;
                background-color: #FFE6E6;
            }
            QProgressBar::chunk {
                background-color: #FF4444;
                border-radius: 3px;
            }
        """)
        self.status_text.setStyleSheet("color: #FF4444; font-weight: bold;")
        
    def _set_high_style(self):
        """Estilo para memoria alta - Naranja."""
        self.status_label.setText("●")
        self.status_label.setStyleSheet("color: #FF8800; font-weight: bold;")
        self.memory_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #FF8800;
                border-radius: 5px;
                background-color: #FFF2E6;
            }
            QProgressBar::chunk {
                background-color: #FF8800;
                border-radius: 3px;
            }
        """)
        self.status_text.setStyleSheet("color: #FF8800; font-weight: bold;")
        
    def _set_moderate_style(self):
        """Estilo para memoria moderada - Amarillo."""
        self.status_label.setText("●")
        self.status_label.setStyleSheet("color: #FFAA00; font-weight: bold;")
        self.memory_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #FFAA00;
                border-radius: 5px;
                background-color: #FFFAED;
            }
            QProgressBar::chunk {
                background-color: #FFAA00;
                border-radius: 3px;
            }
        """)
        self.status_text.setStyleSheet("color: #FFAA00; font-weight: bold;")
        
    def _set_normal_style(self):
        """Estilo para memoria normal - Verde."""
        self.status_label.setText("●")
        self.status_label.setStyleSheet("color: #44AA44; font-weight: bold;")
        self.memory_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #44AA44;
                border-radius: 5px;
                background-color: #F0F8F0;
            }
            QProgressBar::chunk {
                background-color: #44AA44;
                border-radius: 3px;
            }
        """)
        self.status_text.setStyleSheet("color: #44AA44; font-weight: bold;")
    
    def start_monitoring(self):
        """Inicia el monitoreo activo (útil durante procesamiento)."""
        if not self.update_timer.isActive():
            self.update_timer.start(1000)  # Más frecuente durante procesamiento
            
    def stop_monitoring(self):
        """Detiene el monitoreo activo."""
        if self.update_timer.isActive():
            self.update_timer.stop()
            
    def set_processing_mode(self, is_processing: bool):
        """Ajusta el modo de monitoreo según si se está procesando."""
        if is_processing:
            self.update_timer.start(1000)  # Actualizar cada segundo
        else:
            self.update_timer.start(2000)  # Actualizar cada 2 segundos
            
    def get_current_pressure_level(self) -> str:
        """Obtiene el nivel actual de presión de memoria."""
        return self.last_pressure_level
    
    def force_update(self):
        """Fuerza una actualización inmediata del estado."""
        self.update_memory_status() 
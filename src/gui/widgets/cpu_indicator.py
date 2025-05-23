"""
Widget indicador de CPU visual para monitoreo en tiempo real.
Muestra el estado de CPU mediante colores sin interrumpir el flujo de la aplicación.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtGui import QFont
import psutil
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CPUIndicator(QWidget):
    """Widget que muestra el estado de CPU mediante colores e información visual."""
    
    # Señales para comunicar cambios de estado
    cpu_critical = Signal()  # CPU crítica detectada
    cpu_high = Signal()      # CPU alta detectada
    cpu_normal = Signal()    # CPU normal
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Inicializar variables antes de setup_ui
        self.last_pressure_level = "NORMAL"
        self.cpu_count = psutil.cpu_count()
        
        # Ahora configurar UI (que necesita cpu_count)
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """Configura la interfaz del indicador."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # Etiqueta de CPU más compacta
        self.cpu_label = QLabel("CPU:")
        self.cpu_label.setFont(QFont("Arial", 8, QFont.Bold))
        self.cpu_label.setMinimumWidth(30)
        layout.addWidget(self.cpu_label)
        
        # Barra de progreso optimizada
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximum(100)
        self.cpu_bar.setMinimumWidth(80)
        self.cpu_bar.setMaximumWidth(120)
        self.cpu_bar.setMinimumHeight(18)
        self.cpu_bar.setMaximumHeight(22)
        self.cpu_bar.setTextVisible(True)
        layout.addWidget(self.cpu_bar)
        
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
        
        # Información de cores más pequeña
        self.cores_label = QLabel("")
        self.cores_label.setFont(QFont("Arial", 7))
        self.cores_label.setStyleSheet("color: #666666;")
        self.cores_label.setMinimumWidth(40)
        layout.addWidget(self.cores_label)
        
        # Establecer estado inicial
        self.update_display("NORMAL", {"cpu_percent": 0, "active_cores": 0})
        
    def setup_timer(self):
        """Configura el timer para actualización automática."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_cpu_status)
        self.update_timer.start(2000)  # Actualizar cada 2 segundos
        
    def get_cpu_info(self) -> Dict[str, Any]:
        """Obtiene información actual del CPU."""
        try:
            # Usar interval=1 para obtener una medición más precisa
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # Contar cores activos (>5% de uso)
            active_cores = sum(1 for core_usage in cpu_per_core if core_usage > 5.0)
            
            # Determinar nivel de presión
            pressure_level = self._determine_pressure_level(cpu_percent)
            
            return {
                "cpu_percent": cpu_percent,
                "cpu_per_core": cpu_per_core,
                "active_cores": active_cores,
                "total_cores": self.cpu_count,
                "pressure_level": pressure_level,
                "max_core_usage": max(cpu_per_core) if cpu_per_core else 0
            }
        except Exception as e:
            logger.error(f"Error obteniendo información de CPU: {e}")
            return {
                "cpu_percent": 0,
                "cpu_per_core": [],
                "active_cores": 0,
                "total_cores": self.cpu_count,
                "pressure_level": "NORMAL",
                "max_core_usage": 0
            }
    
    def _determine_pressure_level(self, cpu_percent: float) -> str:
        """Determina el nivel de presión basado en el uso de CPU."""
        if cpu_percent >= 85:
            return "CRÍTICO"
        elif cpu_percent >= 60:
            return "ALTO"
        elif cpu_percent >= 30:
            return "MODERADO"
        else:
            return "NORMAL"
        
    def update_cpu_status(self):
        """Actualiza el estado de CPU."""
        try:
            cpu_info = self.get_cpu_info()
            pressure_level = cpu_info.get("pressure_level", "NORMAL")
            
            self.update_display(pressure_level, cpu_info)
            
            # Emitir señales según el cambio de estado
            if pressure_level != self.last_pressure_level:
                if pressure_level == "CRÍTICO":
                    self.cpu_critical.emit()
                elif pressure_level == "ALTO":
                    self.cpu_high.emit()
                else:
                    self.cpu_normal.emit()
                
                self.last_pressure_level = pressure_level
                
        except Exception as e:
            logger.error(f"Error actualizando estado de CPU: {e}")
    
    def update_display(self, pressure_level: str, cpu_info: Dict[str, Any]):
        """Actualiza la visualización del indicador."""
        cpu_percent = cpu_info.get("cpu_percent", 0)
        active_cores = cpu_info.get("active_cores", 0)
        total_cores = cpu_info.get("total_cores", self.cpu_count)
        
        # Actualizar barra de progreso
        self.cpu_bar.setValue(int(cpu_percent))
        self.cpu_bar.setFormat(f"{cpu_percent:.1f}%")
        
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
        self.cores_label.setText(f"Cores: {active_cores}/{total_cores}")
        
    def _set_critical_style(self):
        """Estilo para CPU crítica - Rojo."""
        self.status_label.setText("●")
        self.status_label.setStyleSheet("color: #FF4444; font-weight: bold;")
        self.cpu_bar.setStyleSheet("""
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
        """Estilo para CPU alta - Naranja."""
        self.status_label.setText("●")
        self.status_label.setStyleSheet("color: #FF8800; font-weight: bold;")
        self.cpu_bar.setStyleSheet("""
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
        """Estilo para CPU moderada - Amarillo."""
        self.status_label.setText("●")
        self.status_label.setStyleSheet("color: #FFAA00; font-weight: bold;")
        self.cpu_bar.setStyleSheet("""
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
        """Estilo para CPU normal - Verde."""
        self.status_label.setText("●")
        self.status_label.setStyleSheet("color: #44AA44; font-weight: bold;")
        self.cpu_bar.setStyleSheet("""
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
        """Obtiene el nivel actual de presión de CPU."""
        return self.last_pressure_level
    
    def force_update(self):
        """Fuerza una actualización inmediata del estado."""
        self.update_cpu_status()
        
    def get_detailed_info(self) -> Dict[str, Any]:
        """Obtiene información detallada del CPU para debugging."""
        return self.get_cpu_info() 
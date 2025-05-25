"""
Widget para visualizar análisis de audio en tiempo real
"""
from typing import List, Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QPen,
    QLinearGradient, QGradient
)

from ...services.audio_analyzer import AudioAnalyzer

class WaveformWidget(QWidget):
    """Widget para visualizar forma de onda."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.waveform_data: Optional[List[float]] = None
        self.setMinimumHeight(100)
        self.setStyleSheet("""
            background-color: #1A1A1A;
            border-radius: 4px;
        """)
        
    def set_data(self, data: List[float]):
        """Actualiza los datos de la forma de onda."""
        self.waveform_data = data
        self.update()
        
    def paintEvent(self, event):
        """Dibuja la forma de onda."""
        if not self.waveform_data:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Configurar gradiente
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#6200EE"))
        gradient.setColorAt(1, QColor("#03DAC5"))
        gradient.setSpread(QGradient.PadSpread)
        
        # Dibujar forma de onda
        path = QPainterPath()
        center_y = self.height() / 2
        width = self.width()
        points_per_pixel = len(self.waveform_data) / width
        
        for x in range(width):
            index = int(x * points_per_pixel)
            if index < len(self.waveform_data):
                y = center_y - self.waveform_data[index]
                if x == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
                    
        # Reflejar para forma simétrica
        for x in range(width - 1, -1, -1):
            index = int(x * points_per_pixel)
            if index < len(self.waveform_data):
                y = center_y + self.waveform_data[index]
                path.lineTo(x, y)
                
        path.closeSubpath()
        
        # Dibujar path con gradiente
        painter.fillPath(path, gradient)
        
        # Dibujar borde
        pen = QPen(QColor("#9F45ED"))
        pen.setWidth(1)
        painter.strokePath(path, pen)

class SpectrumWidget(QWidget):
    """Widget para visualizar espectro de frecuencias."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.spectrum_data: Optional[List[float]] = None
        self.setMinimumHeight(100)
        self.setStyleSheet("""
            background-color: #1A1A1A;
            border-radius: 4px;
        """)
        
    def set_data(self, data: List[float]):
        """Actualiza los datos del espectro."""
        self.spectrum_data = data
        self.update()
        
    def paintEvent(self, event):
        """Dibuja el espectro."""
        if not self.spectrum_data:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        bar_count = min(128, len(self.spectrum_data))
        bar_width = width / bar_count
        
        for i in range(bar_count):
            # Normalizar valor entre 0 y 1
            value = (self.spectrum_data[i] + 80) / 80  # dB scale offset
            value = max(0, min(1, value))
            
            # Calcular altura y posición de la barra
            bar_height = value * height
            x = i * bar_width
            y = height - bar_height
            
            # Crear gradiente para cada barra
            gradient = QLinearGradient(x, y, x, height)
            gradient.setColorAt(0, QColor("#6200EE"))
            gradient.setColorAt(1, QColor("#03DAC5"))
            
            # Dibujar barra
            painter.fillRect(
                x, y,
                bar_width * 0.8,  # Dejar espacio entre barras
                bar_height,
                gradient
            )

class MetricWidget(QFrame):
    """Widget para mostrar una métrica individual."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setup_ui(title)
        
    def setup_ui(self, title: str):
        """Configura la interfaz del widget."""
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 8px;
                padding: 8px;
            }
            QLabel {
                color: #000000;
            }
            QLabel[title="true"] {
                font-size: 12px;
                color: #666666;
            }
            QLabel[value="true"] {
                font-size: 24px;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        
        self.title_label = QLabel(title)
        self.title_label.setProperty("title", True)
        
        self.value_label = QLabel("--")
        self.value_label.setProperty("value", True)
        self.value_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        
    def set_value(self, value: Any):
        """Actualiza el valor mostrado."""
        if isinstance(value, float):
            text = f"{value:.2f}"
        else:
            text = str(value)
        self.value_label.setText(text)

class AudioAnalyzerWidget(QWidget):
    """Widget principal para análisis de audio."""
    
    def __init__(self, analyzer: AudioAnalyzer, parent=None):
        super().__init__(parent)
        self.analyzer = analyzer
        self.current_time = 0.0
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_analysis)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Visualizaciones
        self.waveform = WaveformWidget()
        self.spectrum = SpectrumWidget()
        
        # Métricas
        metrics_layout = QHBoxLayout()
        
        self.bpm_metric = MetricWidget("BPM")
        self.key_metric = MetricWidget("Tonalidad")
        self.energy_metric = MetricWidget("Energía")
        self.volume_metric = MetricWidget("Volumen")
        
        metrics_layout.addWidget(self.bpm_metric)
        metrics_layout.addWidget(self.key_metric)
        metrics_layout.addWidget(self.energy_metric)
        metrics_layout.addWidget(self.volume_metric)
        
        # Añadir todo al layout principal
        layout.addWidget(self.waveform)
        layout.addWidget(self.spectrum)
        layout.addLayout(metrics_layout)
        
    def start_analysis(self, update_interval: int = 100):
        """
        Inicia el análisis en tiempo real.
        
        Args:
            update_interval: Intervalo de actualización en ms
        """
        self.update_timer.start(update_interval)
        
        # Obtener forma de onda inicial
        if waveform := self.analyzer.get_waveform(
            width=self.waveform.width(),
            height=self.waveform.height()
        ):
            self.waveform.set_data(waveform)
            
    def stop_analysis(self):
        """Detiene el análisis en tiempo real."""
        self.update_timer.stop()
        
    def set_current_time(self, time: float):
        """
        Actualiza el tiempo actual de reproducción.
        
        Args:
            time: Tiempo en segundos
        """
        self.current_time = time
        
    def update_analysis(self):
        """Actualiza el análisis con los datos más recientes."""
        # Analizar segmento actual
        segment_size = 0.1  # 100ms
        results = self.analyzer.analyze_segment(
            self.current_time,
            self.current_time + segment_size
        )
        
        # Actualizar visualizaciones y métricas
        if results:
            if 'spectrum' in results:
                self.spectrum.set_data(results['spectrum'])
                
            if 'bpm' in results:
                self.bpm_metric.set_value(results['bpm'])
                
            if 'key' in results:
                self.key_metric.set_value(results['key'])
                
            if 'energy' in results:
                self.energy_metric.set_value(results['energy'])
                
            if 'volume' in results:
                self.volume_metric.set_value(results['volume'])

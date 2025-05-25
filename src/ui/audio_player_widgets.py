#!/usr/bin/env python3
"""
Widgets de Reproducción de Audio - v3.0
Componentes de interfaz para reproducción de audio en aplicaciones de DJ.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel,
    QFileDialog, QProgressBar, QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPalette, QIcon
from typing import Optional, Callable

from core.audio_engine import AudioEngine, PlaybackState, format_time, is_audio_file

class AudioPlayerWidget(QWidget):
    """Widget principal de reproducción de audio."""
    
    # Señales
    track_loaded = pyqtSignal(str)  # Archivo cargado
    playback_started = pyqtSignal()
    playback_paused = pyqtSignal()
    playback_stopped = pyqtSignal()
    position_changed = pyqtSignal(float)  # Posición en segundos
    volume_changed = pyqtSignal(float)  # Volumen 0.0-1.0
    
    def __init__(self, deck_name: str = "Deck", parent=None):
        super().__init__(parent)
        self.deck_name = deck_name
        self.audio_engine = AudioEngine()
        self.current_file = None
        
        # Timer para actualizar UI
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_position)
        self.update_timer.setInterval(100)  # Actualizar cada 100ms
        
        self._setup_ui()
        self._connect_signals()
        self._setup_audio_callbacks()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header con nombre del deck
        header_layout = QHBoxLayout()
        self.deck_label = QLabel(f"🎵 {self.deck_name}")
        self.deck_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.deck_label.setStyleSheet("color: #2E86AB; padding: 5px;")
        header_layout.addWidget(self.deck_label)
        header_layout.addStretch()
        
        # Botón de carga de archivo
        self.load_button = QPushButton("📁 Cargar Audio")
        self.load_button.clicked.connect(self._load_file)
        self.load_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        header_layout.addWidget(self.load_button)
        
        layout.addLayout(header_layout)
        
        # Información del archivo
        self.file_info_label = QLabel("No hay archivo cargado")
        self.file_info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.file_info_label)
        
        # Controles de reproducción
        controls_layout = QHBoxLayout()
        
        # Botones de control
        self.play_button = QPushButton("▶️")
        self.play_button.setFixedSize(50, 50)
        self.play_button.clicked.connect(self._toggle_playback)
        self.play_button.setEnabled(False)
        
        self.stop_button = QPushButton("⏹️")
        self.stop_button.setFixedSize(50, 50)
        self.stop_button.clicked.connect(self._stop_playback)
        self.stop_button.setEnabled(False)
        
        # Estilo para botones de control
        button_style = """
            QPushButton {
                background-color: #2E86AB;
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1F5F8B;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """
        self.play_button.setStyleSheet(button_style)
        self.stop_button.setStyleSheet(button_style)
        
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Barra de progreso y posición
        progress_layout = QVBoxLayout()
        
        # Etiquetas de tiempo
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        progress_layout.addLayout(time_layout)
        
        # Barra de progreso
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(1000)  # Usamos 1000 para mejor precisión
        self.progress_slider.setValue(0)
        self.progress_slider.sliderPressed.connect(self._on_seek_start)
        self.progress_slider.sliderReleased.connect(self._on_seek_end)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #d4d4d4, stop:1 #afafaf);
            }
        """)
        progress_layout.addWidget(self.progress_slider)
        
        layout.addLayout(progress_layout)
        
        # Control de volumen
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("🔊"))
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.volume_slider.setStyleSheet(self.progress_slider.styleSheet())
        
        self.volume_label = QLabel("100%")
        self.volume_label.setMinimumWidth(40)
        
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        
        layout.addLayout(volume_layout)
        
        # Estado de reproducción
        self.state_label = QLabel("⏹️ Detenido")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.state_label)
        
        # Configurar layout principal
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
        """)
    
    def _connect_signals(self):
        """Conecta las señales internas."""
        pass
    
    def _setup_audio_callbacks(self):
        """Configura los callbacks del motor de audio."""
        self.audio_engine.on_state_changed = self._on_audio_state_changed
        self.audio_engine.on_position_changed = self._on_audio_position_changed
        self.audio_engine.on_track_finished = self._on_track_finished
    
    def _load_file(self):
        """Abre diálogo para cargar archivo de audio."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Cargar audio para {self.deck_name}",
            "",
            "Archivos de Audio (*.wav *.ogg *.mp3);;Todos los archivos (*)"
        )
        
        if file_path and is_audio_file(file_path):
            self.load_audio_file(file_path)
    
    def load_audio_file(self, file_path: str) -> bool:
        """
        Carga un archivo de audio específico.
        
        Args:
            file_path: Ruta al archivo de audio
            
        Returns:
            True si se cargó correctamente
        """
        if self.audio_engine.load_file(file_path):
            self.current_file = file_path
            filename = os.path.basename(file_path)
            self.file_info_label.setText(f"📄 {filename}")
            
            # Habilitar controles
            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            
            # Actualizar duración
            duration = self.audio_engine.get_duration()
            self.total_time_label.setText(format_time(duration))
            
            # Emitir señal
            self.track_loaded.emit(file_path)
            
            return True
        return False
    
    def _toggle_playback(self):
        """Alterna entre play y pause."""
        state = self.audio_engine.get_state()
        
        if state == PlaybackState.STOPPED:
            self._start_playback()
        elif state == PlaybackState.PLAYING:
            self._pause_playback()
        elif state == PlaybackState.PAUSED:
            self._resume_playback()
    
    def _start_playback(self):
        """Inicia la reproducción."""
        if self.audio_engine.play():
            self.update_timer.start()
    
    def _pause_playback(self):
        """Pausa la reproducción."""
        self.audio_engine.pause()
        self.update_timer.stop()
    
    def _resume_playback(self):
        """Reanuda la reproducción."""
        if self.audio_engine.play():
            self.update_timer.start()
    
    def _stop_playback(self):
        """Detiene la reproducción."""
        self.audio_engine.stop()
        self.update_timer.stop()
        self.progress_slider.setValue(0)
        self.current_time_label.setText("00:00")
    
    def _on_volume_changed(self, value: int):
        """Maneja cambios en el volumen."""
        volume = value / 100.0
        self.audio_engine.set_volume(volume)
        self.volume_label.setText(f"{value}%")
        self.volume_changed.emit(volume)
    
    def _on_seek_start(self):
        """Inicia el proceso de seek."""
        self.update_timer.stop()
    
    def _on_seek_end(self):
        """Finaliza el proceso de seek."""
        if self.audio_engine.get_duration() > 0:
            position = (self.progress_slider.value() / 1000.0) * self.audio_engine.get_duration()
            self.audio_engine.seek(position)
        
        if self.audio_engine.is_playing():
            self.update_timer.start()
    
    def _update_position(self):
        """Actualiza la posición en la interfaz."""
        position = self.audio_engine.get_position()
        duration = self.audio_engine.get_duration()
        
        # Actualizar etiqueta de tiempo
        self.current_time_label.setText(format_time(position))
        
        # Actualizar barra de progreso
        if duration > 0:
            progress = int((position / duration) * 1000)
            self.progress_slider.setValue(progress)
    
    @pyqtSlot(object)
    def _on_audio_state_changed(self, state: PlaybackState):
        """Maneja cambios en el estado de reproducción."""
        if state == PlaybackState.PLAYING:
            self.play_button.setText("⏸️")
            self.state_label.setText("▶️ Reproduciendo")
            self.state_label.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 4px;
                    padding: 5px;
                    font-weight: bold;
                    color: #155724;
                }
            """)
            self.playback_started.emit()
            
        elif state == PlaybackState.PAUSED:
            self.play_button.setText("▶️")
            self.state_label.setText("⏸️ Pausado")
            self.state_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 4px;
                    padding: 5px;
                    font-weight: bold;
                    color: #856404;
                }
            """)
            self.playback_paused.emit()
            
        elif state == PlaybackState.STOPPED:
            self.play_button.setText("▶️")
            self.state_label.setText("⏹️ Detenido")
            self.state_label.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 4px;
                    padding: 5px;
                    font-weight: bold;
                    color: #721c24;
                }
            """)
            self.playback_stopped.emit()
            
        elif state == PlaybackState.LOADING:
            self.state_label.setText("⏳ Cargando...")
            self.state_label.setStyleSheet("""
                QLabel {
                    background-color: #d1ecf1;
                    border: 1px solid #bee5eb;
                    border-radius: 4px;
                    padding: 5px;
                    font-weight: bold;
                    color: #0c5460;
                }
            """)
    
    @pyqtSlot(float)
    def _on_audio_position_changed(self, position: float):
        """Maneja cambios en la posición de reproducción."""
        self.position_changed.emit(position)
    
    @pyqtSlot()
    def _on_track_finished(self):
        """Maneja el final de la reproducción."""
        self.update_timer.stop()
        self.progress_slider.setValue(0)
        self.current_time_label.setText("00:00")
    
    def get_current_file(self) -> Optional[str]:
        """Obtiene el archivo actualmente cargado."""
        return self.current_file
    
    def get_position(self) -> float:
        """Obtiene la posición actual en segundos."""
        return self.audio_engine.get_position()
    
    def get_duration(self) -> float:
        """Obtiene la duración total en segundos."""
        return self.audio_engine.get_duration()
    
    def get_volume(self) -> float:
        """Obtiene el volumen actual (0.0-1.0)."""
        return self.audio_engine.volume
    
    def set_volume(self, volume: float):
        """Establece el volumen (0.0-1.0)."""
        volume_percent = int(volume * 100)
        self.volume_slider.setValue(volume_percent)
    
    def is_playing(self) -> bool:
        """Verifica si está reproduciendo."""
        return self.audio_engine.is_playing()
    
    def cleanup(self):
        """Limpia recursos del widget."""
        self.update_timer.stop()
        self.audio_engine.cleanup()

class DualDeckWidget(QWidget):
    """Widget con dos decks de audio para DJ."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz con dos decks."""
        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        
        # Deck A
        self.deck_a = AudioPlayerWidget("Deck A", self)
        layout.addWidget(self.deck_a)
        
        # Separador visual
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #ddd;")
        layout.addWidget(separator)
        
        # Deck B
        self.deck_b = AudioPlayerWidget("Deck B", self)
        layout.addWidget(self.deck_b)
    
    def get_deck_a(self) -> AudioPlayerWidget:
        """Obtiene el deck A."""
        return self.deck_a
    
    def get_deck_b(self) -> AudioPlayerWidget:
        """Obtiene el deck B."""
        return self.deck_b
    
    def cleanup(self):
        """Limpia recursos de ambos decks."""
        self.deck_a.cleanup()
        self.deck_b.cleanup() 
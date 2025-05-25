"""
Controles de reproductor con Material 3 Expressive.
Incluye funcionalidades completas de reproducción y visualización.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSlider, QFrame, QProgressBar
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QFont, QPixmap
from typing import Dict, Any, Optional


class PlayerControls(QWidget):
    """Controles de reproductor con diseño Material 3 Expressive."""
    
    # Señales
    play_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()
    next_requested = Signal()
    previous_requested = Signal()
    volume_changed = Signal(int)  # volume (0-100)
    position_changed = Signal(int)  # position in seconds
    shuffle_toggled = Signal(bool)  # shuffle_enabled
    repeat_toggled = Signal(bool)   # repeat_enabled
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Estado del reproductor
        self._is_playing = False
        self._current_track = None
        self._duration = 0
        self._position = 0
        self._volume = 70
        self._shuffle = False
        self._repeat = False
        
        # Timer para actualizar progreso (simulado)
        self._progress_timer = QTimer()
        self._progress_timer.timeout.connect(self._update_progress)
        
        self._setup_ui()
        self._setup_connections()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Contenedor principal con fondo
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background: rgba(28, 27, 31, 0.6);
                border: 1px solid rgba(103, 80, 164, 0.2);
                border-radius: 16px;
                padding: 12px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(12)
        
        # Información de track actual
        track_info_section = self._create_track_info_section()
        container_layout.addWidget(track_info_section)
        
        # Controles de progreso
        progress_section = self._create_progress_section()
        container_layout.addWidget(progress_section)
        
        # Controles principales de reproducción
        main_controls = self._create_main_controls_section()
        container_layout.addWidget(main_controls)
        
        # Controles secundarios
        secondary_controls = self._create_secondary_controls_section()
        container_layout.addWidget(secondary_controls)
        
        layout.addWidget(container)
        
    def _create_track_info_section(self) -> QWidget:
        """Crea la sección de información del track."""
        section = QFrame()
        layout = QHBoxLayout(section)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)
        
        # Artwork placeholder (miniatura del album)
        self.artwork_label = QLabel()
        self.artwork_label.setFixedSize(48, 48)
        self.artwork_label.setStyleSheet("""
            QLabel {
                background: rgba(103, 80, 164, 0.3);
                border-radius: 8px;
                color: #D0BCFF;
                font-size: 20px;
            }
        """)
        self.artwork_label.setAlignment(Qt.AlignCenter)
        self.artwork_label.setText("🎵")
        layout.addWidget(self.artwork_label)
        
        # Información del track
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        self.track_title = QLabel("Sin reproducir")
        self.track_title.setStyleSheet("""
            QLabel {
                color: #E6E1E5;
                font-size: 14px;
                font-weight: 600;
            }
        """)
        info_layout.addWidget(self.track_title)
        
        self.track_artist = QLabel("Selecciona una pista")
        self.track_artist.setStyleSheet("""
            QLabel {
                color: #CAC4D0;
                font-size: 12px;
            }
        """)
        info_layout.addWidget(self.track_artist)
        
        self.track_details = QLabel("")
        self.track_details.setStyleSheet("""
            QLabel {
                color: #938F99;
                font-size: 10px;
            }
        """)
        info_layout.addWidget(self.track_details)
        
        layout.addLayout(info_layout, 1)
        
        return section
    
    def _create_progress_section(self) -> QWidget:
        """Crea la sección de progreso."""
        section = QFrame()
        layout = QVBoxLayout(section)
        layout.setSpacing(6)
        
        # Tiempos
        time_layout = QHBoxLayout()
        
        self.current_time_label = QLabel("0:00")
        self.current_time_label.setStyleSheet("""
            QLabel {
                color: #CAC4D0;
                font-size: 11px;
                font-weight: 500;
            }
        """)
        time_layout.addWidget(self.current_time_label)
        
        time_layout.addStretch()
        
        self.total_time_label = QLabel("0:00")
        self.total_time_label.setStyleSheet("""
            QLabel {
                color: #CAC4D0;
                font-size: 11px;
                font-weight: 500;
            }
        """)
        time_layout.addWidget(self.total_time_label)
        
        layout.addLayout(time_layout)
        
        # Barra de progreso
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(100)
        self.progress_slider.setValue(0)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(103, 80, 164, 0.2);
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #6750A4;
                width: 18px;
                height: 18px;
                border-radius: 9px;
                margin: -6px 0;
                border: 2px solid #D0BCFF;
            }
            QSlider::handle:horizontal:hover {
                background: #8A7FD9;
                border-color: #E6E1E5;
            }
            QSlider::sub-page:horizontal {
                background: #6750A4;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_slider)
        
        return section
    
    def _create_main_controls_section(self) -> QWidget:
        """Crea la sección de controles principales."""
        section = QFrame()
        layout = QHBoxLayout(section)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        
        # Botón anterior
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setFixedSize(44, 44)
        self.prev_btn.setToolTip("Anterior")
        self.prev_btn.setStyleSheet(self._get_control_button_style())
        layout.addWidget(self.prev_btn)
        
        # Botón play/pause principal
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(56, 56)
        self.play_btn.setToolTip("Reproducir")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: #6750A4;
                border: none;
                border-radius: 28px;
                color: white;
                font-size: 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #8A7FD9;
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background: #5A4A8A;
                transform: scale(0.95);
            }
        """)
        layout.addWidget(self.play_btn)
        
        # Botón siguiente
        self.next_btn = QPushButton("⏭")
        self.next_btn.setFixedSize(44, 44)
        self.next_btn.setToolTip("Siguiente")
        self.next_btn.setStyleSheet(self._get_control_button_style())
        layout.addWidget(self.next_btn)
        
        return section
    
    def _create_secondary_controls_section(self) -> QWidget:
        """Crea la sección de controles secundarios."""
        section = QFrame()
        layout = QHBoxLayout(section)
        layout.setSpacing(12)
        
        # Botón shuffle
        self.shuffle_btn = QPushButton("🔀")
        self.shuffle_btn.setFixedSize(32, 32)
        self.shuffle_btn.setCheckable(True)
        self.shuffle_btn.setToolTip("Reproducción aleatoria")
        self.shuffle_btn.setStyleSheet(self._get_toggle_button_style())
        layout.addWidget(self.shuffle_btn)
        
        # Control de volumen
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(6)
        
        volume_icon = QLabel("🔊")
        volume_icon.setStyleSheet("""
            QLabel {
                color: #CAC4D0;
                font-size: 14px;
            }
        """)
        volume_layout.addWidget(volume_icon)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(self._volume)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(103, 80, 164, 0.2);
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #6750A4;
                width: 14px;
                height: 14px;
                border-radius: 7px;
                margin: -5px 0;
            }
            QSlider::sub-page:horizontal {
                background: #6750A4;
                border-radius: 2px;
            }
        """)
        volume_layout.addWidget(self.volume_slider)
        
        layout.addLayout(volume_layout, 1)
        
        # Botón stop
        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setFixedSize(32, 32)
        self.stop_btn.setToolTip("Detener")
        self.stop_btn.setStyleSheet(self._get_secondary_button_style())
        layout.addWidget(self.stop_btn)
        
        # Botón repeat
        self.repeat_btn = QPushButton("🔁")
        self.repeat_btn.setFixedSize(32, 32)
        self.repeat_btn.setCheckable(True)
        self.repeat_btn.setToolTip("Repetir")
        self.repeat_btn.setStyleSheet(self._get_toggle_button_style())
        layout.addWidget(self.repeat_btn)
        
        return section
    
    def _setup_connections(self):
        """Configura las conexiones de señales."""
        # Controles principales
        self.play_btn.clicked.connect(self._toggle_play_pause)
        self.prev_btn.clicked.connect(self.previous_requested.emit)
        self.next_btn.clicked.connect(self.next_requested.emit)
        self.stop_btn.clicked.connect(self._stop_playback)
        
        # Controles secundarios
        self.shuffle_btn.toggled.connect(self._toggle_shuffle)
        self.repeat_btn.toggled.connect(self._toggle_repeat)
        
        # Controles de progreso y volumen
        self.progress_slider.sliderPressed.connect(self._on_progress_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_progress_slider_released)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
    
    def _toggle_play_pause(self):
        """Alterna entre reproducir y pausar."""
        if self._is_playing:
            self.pause_requested.emit()
            self._set_playing_state(False)
        else:
            self.play_requested.emit()
            self._set_playing_state(True)
    
    def _stop_playback(self):
        """Detiene la reproducción."""
        self.stop_requested.emit()
        self._set_playing_state(False)
        self._set_position(0)
    
    def _toggle_shuffle(self, enabled: bool):
        """Alterna reproducción aleatoria."""
        self._shuffle = enabled
        self.shuffle_toggled.emit(enabled)
    
    def _toggle_repeat(self, enabled: bool):
        """Alterna repetición."""
        self._repeat = enabled
        self.repeat_toggled.emit(enabled)
    
    def _on_progress_slider_pressed(self):
        """Maneja cuando se presiona el slider de progreso."""
        self._progress_timer.stop()
    
    def _on_progress_slider_released(self):
        """Maneja cuando se suelta el slider de progreso."""
        if self._duration > 0:
            new_position = int((self.progress_slider.value() / 100.0) * self._duration)
            self._set_position(new_position)
            self.position_changed.emit(new_position)
        
        if self._is_playing:
            self._progress_timer.start(1000)  # Actualizar cada segundo
    
    def _on_volume_changed(self, volume: int):
        """Maneja cambios en el volumen."""
        self._volume = volume
        self.volume_changed.emit(volume)
    
    def _update_progress(self):
        """Actualiza el progreso de reproducción (simulado)."""
        if self._is_playing and self._duration > 0:
            self._position += 1
            if self._position >= self._duration:
                self._position = 0
                if not self._repeat:
                    self._set_playing_state(False)
                    self.next_requested.emit()
            
            self._update_progress_display()
    
    def _update_progress_display(self):
        """Actualiza la visualización del progreso."""
        if self._duration > 0:
            progress_percent = (self._position / self._duration) * 100
            self.progress_slider.setValue(int(progress_percent))
        
        self.current_time_label.setText(self._format_time(self._position))
        self.total_time_label.setText(self._format_time(self._duration))
    
    def _format_time(self, seconds: int) -> str:
        """Formatea tiempo en MM:SS."""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def _set_playing_state(self, playing: bool):
        """Establece el estado de reproducción."""
        self._is_playing = playing
        
        if playing:
            self.play_btn.setText("⏸")
            self.play_btn.setToolTip("Pausar")
            self._progress_timer.start(1000)
        else:
            self.play_btn.setText("▶")
            self.play_btn.setToolTip("Reproducir")
            self._progress_timer.stop()
    
    def _set_position(self, position: int):
        """Establece la posición de reproducción."""
        self._position = position
        self._update_progress_display()
    
    # === Métodos públicos para control externo ===
    
    def set_current_track(self, track_data: Dict[str, Any]):
        """Establece el track actual."""
        self._current_track = track_data
        
        # Actualizar información mostrada
        title = track_data.get('title', 'Desconocido')
        artist = track_data.get('artist', 'Desconocido')
        album = track_data.get('album', '')
        
        self.track_title.setText(title)
        self.track_artist.setText(artist)
        
        # Detalles adicionales
        details = []
        if album:
            details.append(album)
        
        bpm = track_data.get('bpm')
        if bpm:
            details.append(f"{bpm} BPM")
        
        key = track_data.get('key')
        if key:
            details.append(key)
        
        self.track_details.setText(" • ".join(details))
        
        # Establecer duración (simulada si no está disponible)
        self._duration = track_data.get('duration', 180)  # 3 minutos por defecto
        self._position = 0
        self._update_progress_display()
    
    def play(self):
        """Inicia reproducción."""
        self._set_playing_state(True)
    
    def pause(self):
        """Pausa reproducción."""
        self._set_playing_state(False)
    
    def stop(self):
        """Detiene reproducción."""
        self._set_playing_state(False)
        self._set_position(0)
    
    def set_volume(self, volume: int):
        """Establece el volumen."""
        self._volume = max(0, min(100, volume))
        self.volume_slider.setValue(self._volume)
    
    def get_volume(self) -> int:
        """Obtiene el volumen actual."""
        return self._volume
    
    def is_playing(self) -> bool:
        """Verifica si está reproduciendo."""
        return self._is_playing
    
    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """Obtiene el track actual."""
        return self._current_track
    
    # === Métodos de utilidad para estilos ===
    
    def _get_control_button_style(self) -> str:
        return """
            QPushButton {
                background: rgba(103, 80, 164, 0.3);
                border: none;
                border-radius: 22px;
                color: #D0BCFF;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(103, 80, 164, 0.4);
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background: rgba(103, 80, 164, 0.5);
                transform: scale(0.95);
            }
        """
    
    def _get_secondary_button_style(self) -> str:
        return """
            QPushButton {
                background: rgba(103, 80, 164, 0.2);
                border: none;
                border-radius: 16px;
                color: #CAC4D0;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(103, 80, 164, 0.3);
                color: #D0BCFF;
            }
            QPushButton:pressed {
                background: rgba(103, 80, 164, 0.4);
            }
        """
    
    def _get_toggle_button_style(self) -> str:
        return """
            QPushButton {
                background: rgba(103, 80, 164, 0.2);
                border: none;
                border-radius: 16px;
                color: #CAC4D0;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(103, 80, 164, 0.3);
                color: #D0BCFF;
            }
            QPushButton:checked {
                background: rgba(103, 80, 164, 0.5);
                color: #D0BCFF;
            }
            QPushButton:pressed {
                background: rgba(103, 80, 164, 0.4);
            }
        """
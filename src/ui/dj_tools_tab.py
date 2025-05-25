#!/usr/bin/env python3
"""
Tab de Herramientas de DJ - Interfaz para funcionalidades profesionales de mezcla
"""

import sys
import os
from typing import List, Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QSlider, QPushButton, QListWidget, QListWidgetItem,
    QProgressBar, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit,
    QSplitter, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

# Importar el motor de DJ y widgets de audio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.dj_engine import DJEngine, TrackInfo, TransitionAnalysis, TransitionQuality, get_transition_color
from ui.audio_player_widgets import DualDeckWidget, AudioPlayerWidget

class CrossfaderWidget(QWidget):
    """Widget de crossfader para mezcla entre dos tracks."""
    
    position_changed = pyqtSignal(float)  # Señal cuando cambia la posición
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Crossfader")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Etiquetas de tracks
        labels_layout = QHBoxLayout()
        self.track_a_label = QLabel("Track A")
        self.track_a_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.track_b_label = QLabel("Track B")
        self.track_b_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        labels_layout.addWidget(self.track_a_label)
        labels_layout.addStretch()
        labels_layout.addWidget(self.track_b_label)
        layout.addLayout(labels_layout)
        
        # Slider del crossfader
        self.crossfader_slider = QSlider(Qt.Orientation.Horizontal)
        self.crossfader_slider.setMinimum(-100)
        self.crossfader_slider.setMaximum(100)
        self.crossfader_slider.setValue(0)  # Posición central
        self.crossfader_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.crossfader_slider.setTickInterval(25)
        self.crossfader_slider.valueChanged.connect(self.on_position_changed)
        layout.addWidget(self.crossfader_slider)
        
        # Indicadores de volumen
        volume_layout = QHBoxLayout()
        
        # Volumen Track A
        self.volume_a_bar = QProgressBar()
        self.volume_a_bar.setMaximum(100)
        self.volume_a_bar.setValue(50)
        self.volume_a_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
        
        # Volumen Track B
        self.volume_b_bar = QProgressBar()
        self.volume_b_bar.setMaximum(100)
        self.volume_b_bar.setValue(50)
        self.volume_b_bar.setStyleSheet("QProgressBar::chunk { background-color: #2196F3; }")
        
        volume_layout.addWidget(QLabel("A:"))
        volume_layout.addWidget(self.volume_a_bar)
        volume_layout.addWidget(QLabel("B:"))
        volume_layout.addWidget(self.volume_b_bar)
        
        layout.addLayout(volume_layout)
        
        # Posición actual
        self.position_label = QLabel("Posición: Centro (50/50)")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.position_label)
        
        self.setLayout(layout)
        
    def on_position_changed(self, value):
        """Maneja el cambio de posición del crossfader."""
        # Convertir de -100/100 a -1.0/1.0
        position = value / 100.0
        
        # Calcular volúmenes
        volume_a = int((1.0 - (position + 1.0) / 2.0) * 100)
        volume_b = int(((position + 1.0) / 2.0) * 100)
        
        # Actualizar barras de volumen
        self.volume_a_bar.setValue(volume_a)
        self.volume_b_bar.setValue(volume_b)
        
        # Actualizar etiqueta
        if value < -10:
            self.position_label.setText(f"Posición: Track A ({volume_a}%)")
        elif value > 10:
            self.position_label.setText(f"Posición: Track B ({volume_b}%)")
        else:
            self.position_label.setText(f"Posición: Centro ({volume_a}/{volume_b})")
        
        # Emitir señal
        self.position_changed.emit(position)
        
    def set_track_names(self, track_a: str, track_b: str):
        """Establece los nombres de los tracks."""
        self.track_a_label.setText(f"A: {track_a}")
        self.track_b_label.setText(f"B: {track_b}")

class BPMSyncWidget(QWidget):
    """Widget para sincronización de BPM entre tracks."""
    
    def __init__(self):
        super().__init__()
        self.dj_engine = DJEngine()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Sincronización de BPM")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Grid para información de tracks
        grid = QGridLayout()
        
        # Headers
        grid.addWidget(QLabel(""), 0, 0)
        grid.addWidget(QLabel("Track A"), 0, 1)
        grid.addWidget(QLabel("Track B"), 0, 2)
        
        # BPM Original
        grid.addWidget(QLabel("BPM Original:"), 1, 0)
        self.bpm_a_label = QLabel("---")
        self.bpm_b_label = QLabel("---")
        grid.addWidget(self.bpm_a_label, 1, 1)
        grid.addWidget(self.bpm_b_label, 1, 2)
        
        # Pitch Adjustment
        grid.addWidget(QLabel("Ajuste Pitch:"), 2, 0)
        self.pitch_a_label = QLabel("0.0%")
        self.pitch_b_label = QLabel("0.0%")
        grid.addWidget(self.pitch_a_label, 2, 1)
        grid.addWidget(self.pitch_b_label, 2, 2)
        
        # BPM Sincronizado
        grid.addWidget(QLabel("BPM Sincronizado:"), 3, 0)
        self.synced_a_label = QLabel("---")
        self.synced_b_label = QLabel("---")
        grid.addWidget(self.synced_a_label, 3, 1)
        grid.addWidget(self.synced_b_label, 3, 2)
        
        layout.addLayout(grid)
        
        # Controles de sincronización
        sync_layout = QHBoxLayout()
        
        self.sync_to_a_btn = QPushButton("Sincronizar a A")
        self.sync_to_b_btn = QPushButton("Sincronizar a B")
        self.reset_sync_btn = QPushButton("Reset")
        
        self.sync_to_a_btn.clicked.connect(self.sync_to_track_a)
        self.sync_to_b_btn.clicked.connect(self.sync_to_track_b)
        self.reset_sync_btn.clicked.connect(self.reset_sync)
        
        sync_layout.addWidget(self.sync_to_a_btn)
        sync_layout.addWidget(self.sync_to_b_btn)
        sync_layout.addWidget(self.reset_sync_btn)
        
        layout.addLayout(sync_layout)
        
        # Información de compatibilidad
        self.compatibility_label = QLabel("Selecciona dos tracks para ver compatibilidad")
        self.compatibility_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.compatibility_label.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px;")
        layout.addWidget(self.compatibility_label)
        
        self.setLayout(layout)
        
        # Variables para tracks actuales
        self.current_track_a = None
        self.current_track_b = None
        
    def set_tracks(self, track_a: TrackInfo, track_b: TrackInfo):
        """Establece los tracks para sincronización."""
        self.current_track_a = track_a
        self.current_track_b = track_b
        
        # Actualizar información
        self.bpm_a_label.setText(f"{track_a.bpm:.1f}")
        self.bpm_b_label.setText(f"{track_b.bpm:.1f}")
        
        # Calcular compatibilidad
        compatibility = self.dj_engine.analyze_bpm_compatibility(track_a.bpm, track_b.bpm)
        
        self.compatibility_label.setText(
            f"Diferencia: {compatibility['bpm_difference']} BPM | "
            f"Compatibilidad: {compatibility['compatibility']} | "
            f"Score: {compatibility['score']}/100"
        )
        
        # Colorear según compatibilidad
        if compatibility['score'] >= 80:
            color = "#4CAF50"  # Verde
        elif compatibility['score'] >= 60:
            color = "#FF9800"  # Naranja
        else:
            color = "#F44336"  # Rojo
            
        self.compatibility_label.setStyleSheet(
            f"padding: 10px; border: 2px solid {color}; border-radius: 5px; background-color: {color}20;"
        )
        
        # Reset pitch adjustments
        self.reset_sync()
        
    def sync_to_track_a(self):
        """Sincroniza Track B al BPM de Track A."""
        if not self.current_track_a or not self.current_track_b:
            return
            
        pitch_b = self.dj_engine.calculate_pitch_adjustment(
            self.current_track_b.bpm, self.current_track_a.bpm
        )
        synced_bpm_b = self.dj_engine.calculate_synced_bpm(
            self.current_track_b.bpm, pitch_b
        )
        
        self.pitch_a_label.setText("0.0%")
        self.pitch_b_label.setText(f"{pitch_b:+.1f}%")
        self.synced_a_label.setText(f"{self.current_track_a.bpm:.1f}")
        self.synced_b_label.setText(f"{synced_bpm_b:.1f}")
        
    def sync_to_track_b(self):
        """Sincroniza Track A al BPM de Track B."""
        if not self.current_track_a or not self.current_track_b:
            return
            
        pitch_a = self.dj_engine.calculate_pitch_adjustment(
            self.current_track_a.bpm, self.current_track_b.bpm
        )
        synced_bpm_a = self.dj_engine.calculate_synced_bpm(
            self.current_track_a.bpm, pitch_a
        )
        
        self.pitch_a_label.setText(f"{pitch_a:+.1f}%")
        self.pitch_b_label.setText("0.0%")
        self.synced_a_label.setText(f"{synced_bpm_a:.1f}")
        self.synced_b_label.setText(f"{self.current_track_b.bpm:.1f}")
        
    def reset_sync(self):
        """Resetea la sincronización."""
        self.pitch_a_label.setText("0.0%")
        self.pitch_b_label.setText("0.0%")
        
        if self.current_track_a and self.current_track_b:
            self.synced_a_label.setText(f"{self.current_track_a.bpm:.1f}")
            self.synced_b_label.setText(f"{self.current_track_b.bpm:.1f}")

class TransitionSuggestionsWidget(QWidget):
    """Widget para mostrar sugerencias de transición."""
    
    track_selected = pyqtSignal(int)  # Señal cuando se selecciona un track
    
    def __init__(self):
        super().__init__()
        self.dj_engine = DJEngine()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Sugerencias de Transición")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Track actual
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("Track Actual:"))
        self.current_track_label = QLabel("Ninguno seleccionado")
        self.current_track_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        current_layout.addWidget(self.current_track_label)
        current_layout.addStretch()
        layout.addLayout(current_layout)
        
        # Lista de sugerencias
        self.suggestions_list = QListWidget()
        self.suggestions_list.itemClicked.connect(self.on_suggestion_clicked)
        layout.addWidget(self.suggestions_list)
        
        # Botón para actualizar sugerencias
        self.refresh_btn = QPushButton("Actualizar Sugerencias")
        self.refresh_btn.clicked.connect(self.refresh_suggestions)
        layout.addWidget(self.refresh_btn)
        
        self.setLayout(layout)
        
        # Variables
        self.current_track = None
        self.available_tracks = []
        
    def set_current_track(self, track: TrackInfo):
        """Establece el track actual."""
        self.current_track = track
        self.current_track_label.setText(f"{track.title} - {track.artist}")
        self.refresh_suggestions()
        
    def set_available_tracks(self, tracks: List[TrackInfo]):
        """Establece la lista de tracks disponibles."""
        self.available_tracks = tracks
        if self.current_track:
            self.refresh_suggestions()
            
    def refresh_suggestions(self):
        """Actualiza las sugerencias de transición."""
        if not self.current_track or not self.available_tracks:
            self.suggestions_list.clear()
            return
            
        # Obtener sugerencias del motor de DJ
        suggestions = self.dj_engine.suggest_transitions(
            self.current_track, self.available_tracks, max_suggestions=10
        )
        
        # Limpiar lista
        self.suggestions_list.clear()
        
        # Añadir sugerencias
        for analysis in suggestions:
            item_text = (
                f"{analysis.track_b.title} - {analysis.track_b.artist}\n"
                f"BPM: {analysis.track_b.bpm} ({analysis.bpm_difference:+.1f}) | "
                f"Key: {analysis.track_b.camelot_key} | "
                f"Score: {analysis.compatibility_score:.0f}/100"
            )
            
            item = QListWidgetItem(item_text)
            
            # Colorear según calidad
            color = get_transition_color(analysis.transition_quality)
            item.setBackground(QColor(color + "40"))  # Transparencia
            
            # Guardar análisis en el item
            item.setData(Qt.ItemDataRole.UserRole, analysis)
            
            self.suggestions_list.addItem(item)
            
    def on_suggestion_clicked(self, item):
        """Maneja el clic en una sugerencia."""
        analysis = item.data(Qt.ItemDataRole.UserRole)
        if analysis:
            self.track_selected.emit(analysis.track_b.track_id)

class DJToolsTab(QWidget):
    """Tab principal de herramientas de DJ."""
    
    def __init__(self, db_connection):
        super().__init__()
        self.db_connection = db_connection
        self.dj_engine = DJEngine()
        self.init_ui()
        
    def init_ui(self):
        # Layout principal vertical
        main_layout = QVBoxLayout()
        
        # Título del tab
        title_label = QLabel("🎧 Herramientas de DJ Profesionales v3.0")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2E86AB; padding: 10px; background-color: #f0f8ff; border-radius: 5px;")
        main_layout.addWidget(title_label)
        
        # Reproductores de audio (Dual Deck)
        audio_group = QGroupBox("🎵 Reproductores de Audio")
        audio_layout = QVBoxLayout()
        self.dual_deck_widget = DualDeckWidget()
        audio_layout.addWidget(self.dual_deck_widget)
        audio_group.setLayout(audio_layout)
        main_layout.addWidget(audio_group)
        
        # Splitter para controles y sugerencias
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo - Controles de DJ
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Crossfader mejorado
        crossfader_group = QGroupBox("🎛️ Crossfader Virtual")
        crossfader_layout = QVBoxLayout()
        self.crossfader_widget = CrossfaderWidget()
        crossfader_layout.addWidget(self.crossfader_widget)
        crossfader_group.setLayout(crossfader_layout)
        left_layout.addWidget(crossfader_group)
        
        # Sincronización BPM
        bpm_sync_group = QGroupBox("⚡ Sincronización BPM")
        bpm_sync_layout = QVBoxLayout()
        self.bpm_sync_widget = BPMSyncWidget()
        bpm_sync_layout.addWidget(self.bpm_sync_widget)
        bpm_sync_group.setLayout(bpm_sync_layout)
        left_layout.addWidget(bpm_sync_group)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        
        # Panel derecho - Sugerencias y análisis
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Sugerencias de transición
        suggestions_group = QGroupBox("🎯 Sugerencias de Transición")
        suggestions_layout = QVBoxLayout()
        self.suggestions_widget = TransitionSuggestionsWidget()
        suggestions_layout.addWidget(self.suggestions_widget)
        suggestions_group.setLayout(suggestions_layout)
        right_layout.addWidget(suggestions_group)
        
        # Información detallada
        details_group = QGroupBox("📊 Análisis Detallado")
        details_layout = QVBoxLayout()
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(200)
        self.details_text.setPlainText("Selecciona una transición para ver análisis detallado...")
        details_layout.addWidget(self.details_text)
        details_group.setLayout(details_layout)
        right_layout.addWidget(details_group)
        
        right_panel.setLayout(right_layout)
        
        # Añadir paneles al splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])  # Proporción inicial
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
        # Conectar señales
        self.suggestions_widget.track_selected.connect(self.on_track_selected)
        self._connect_audio_signals()
        
        # Cargar datos iniciales
        self.load_sample_data()
        
    def _connect_audio_signals(self):
        """Conecta las señales de los reproductores de audio."""
        deck_a = self.dual_deck_widget.get_deck_a()
        deck_b = self.dual_deck_widget.get_deck_b()
        
        # Conectar señales de carga de tracks
        deck_a.track_loaded.connect(lambda path: self._on_track_loaded("A", path))
        deck_b.track_loaded.connect(lambda path: self._on_track_loaded("B", path))
        
        # Conectar crossfader con volúmenes de los decks
        self.crossfader_widget.position_changed.connect(self._on_crossfader_changed)
        
        # Conectar cambios de volumen
        deck_a.volume_changed.connect(lambda vol: self._on_volume_changed("A", vol))
        deck_b.volume_changed.connect(lambda vol: self._on_volume_changed("B", vol))
    
    def _on_track_loaded(self, deck: str, file_path: str):
        """Maneja la carga de un track en un deck."""
        print(f"🎵 Track cargado en Deck {deck}: {file_path}")
        
        # Actualizar nombres en crossfader
        deck_a = self.dual_deck_widget.get_deck_a()
        deck_b = self.dual_deck_widget.get_deck_b()
        
        file_a = deck_a.get_current_file()
        file_b = deck_b.get_current_file()
        
        name_a = os.path.basename(file_a) if file_a else "Sin cargar"
        name_b = os.path.basename(file_b) if file_b else "Sin cargar"
        
        self.crossfader_widget.set_track_names(name_a, name_b)
        
        # TODO: Crear TrackInfo desde archivo y actualizar BPM sync
        # Por ahora usamos valores por defecto
        if file_a and file_b:
            track_a = TrackInfo(1, name_a, "Artista", 128.0, "C", "1A", 5, 4.0, 180)
            track_b = TrackInfo(2, name_b, "Artista", 132.0, "D", "2A", 6, 4.0, 200)
            self.bpm_sync_widget.set_tracks(track_a, track_b)
    
    def _on_crossfader_changed(self, position: float):
        """Maneja cambios en el crossfader."""
        # Calcular volúmenes para cada deck
        volume_a = (1.0 - (position + 1.0) / 2.0)
        volume_b = (position + 1.0) / 2.0
        
        # Aplicar volúmenes a los decks
        deck_a = self.dual_deck_widget.get_deck_a()
        deck_b = self.dual_deck_widget.get_deck_b()
        
        deck_a.set_volume(volume_a)
        deck_b.set_volume(volume_b)
        
        print(f"🎛️ Crossfader: A={volume_a:.2f}, B={volume_b:.2f}")
    
    def _on_volume_changed(self, deck: str, volume: float):
        """Maneja cambios de volumen en los decks."""
        print(f"🔊 Volumen Deck {deck}: {volume:.2f}")
    
    def cleanup(self):
        """Limpia recursos del tab."""
        if hasattr(self, 'dual_deck_widget'):
            self.dual_deck_widget.cleanup()
        
    def load_sample_data(self):
        """Carga datos reales desde la base de datos."""
        if not self.db_connection:
            return
            
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT track_id, title, artist, bpm, key, camelot_key, energy, rating, duration_seconds
                FROM tracks 
                WHERE bpm IS NOT NULL AND bpm > 0
                ORDER BY rating DESC, title
                LIMIT 10
            """)
            
            rows = cursor.fetchall()
            tracks = []
            
            for row in rows:
                track_id, title, artist, bpm, key, camelot_key, energy, rating, duration = row
                
                # Valores por defecto si faltan datos
                energy = energy or 5
                rating = rating or 3.0
                duration = duration or 180
                key = key or "C"
                camelot_key = camelot_key or "1A"
                
                track = TrackInfo(
                    track_id=track_id,
                    title=title or "Sin título",
                    artist=artist or "Artista desconocido",
                    bpm=float(bpm),
                    key=key,
                    camelot_key=camelot_key,
                    energy=energy,
                    rating=float(rating),
                    duration=int(duration)
                )
                tracks.append(track)
            
            # Establecer track actual y disponibles
            if tracks:
                self.suggestions_widget.set_current_track(tracks[0])
                self.suggestions_widget.set_available_tracks(tracks[1:])
                
                # Configurar crossfader con primeros dos tracks
                if len(tracks) >= 2:
                    self.crossfader_widget.set_track_names(
                        tracks[0].title, tracks[1].title
                    )
                    self.bpm_sync_widget.set_tracks(tracks[0], tracks[1])
                    
        except Exception as e:
            print(f"Error cargando datos de DJ: {e}")
            # Fallback a datos de ejemplo si hay error
            self.load_fallback_data()
            
    def load_fallback_data(self):
        """Carga datos de ejemplo como fallback."""
        sample_tracks = [
            TrackInfo(1, "Song A", "Artist 1", 128.0, "Am", "8A", 7, 4.5, 240),
            TrackInfo(2, "Song B", "Artist 2", 132.0, "Em", "9A", 8, 4.0, 210),
            TrackInfo(3, "Song C", "Artist 3", 125.0, "Dm", "7A", 6, 3.8, 195),
            TrackInfo(4, "Song D", "Artist 4", 140.0, "F", "7B", 9, 4.2, 220),
        ]
        
        # Establecer track actual y disponibles
        if sample_tracks:
            self.suggestions_widget.set_current_track(sample_tracks[0])
            self.suggestions_widget.set_available_tracks(sample_tracks[1:])
            
            # Configurar crossfader con primeros dos tracks
            if len(sample_tracks) >= 2:
                self.crossfader_widget.set_track_names(
                    sample_tracks[0].title, sample_tracks[1].title
                )
                self.bpm_sync_widget.set_tracks(sample_tracks[0], sample_tracks[1])
                
    def on_track_selected(self, track_id: int):
        """Maneja la selección de un track desde las sugerencias."""
        # En implementación real, cargaría el track desde la BD
        print(f"Track seleccionado: {track_id}")
        
        # Actualizar análisis detallado
        self.details_text.setPlainText(
            f"Track ID: {track_id}\n"
            f"Análisis de transición cargado...\n"
            f"Compatibilidad armónica: Verificada\n"
            f"Flujo energético: Analizado\n"
            f"Recomendación: Transición sugerida"
        )

# Función de prueba
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Crear tab de DJ tools
    dj_tab = DJToolsTab(None)  # Sin conexión DB para prueba
    dj_tab.show()
    
    sys.exit(app.exec()) 
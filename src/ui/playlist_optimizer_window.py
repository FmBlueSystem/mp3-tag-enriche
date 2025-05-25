"""
Interfaz gráfica para el optimizador de playlists.
Permite visualizar y probar diferentes estrategias de optimización.
"""

from typing import List, Dict, Any
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                          QLabel, QComboBox, QPushButton, QListWidget, 
                          QGroupBox, QTextEdit, QProgressBar, QTableWidget,
                          QTableWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal

from ..core.playlist_optimizer import (
    PlaylistOptimizer, OptimizationStrategy, OptimizationResult
)

class PlaylistOptimizerWindow(QMainWindow):
    """Ventana principal del optimizador de playlists."""
    
    def __init__(self):
        super().__init__()
        self.optimizer = PlaylistOptimizer()
        
        # Estado
        self.current_tracks: List[Dict[str, Any]] = []
        self.result: OptimizationResult = None
        
        self.initUI()
        
    def initUI(self):
        """Inicializa la interfaz de usuario."""
        self.setWindowTitle("Optimizador de Playlists")
        self.setMinimumSize(800, 600)
        
        # Widget central
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        self.setCentralWidget(central)
        
        # Panel superior
        top_panel = QHBoxLayout()
        
        # Lista de tracks
        tracks_group = QGroupBox("Tracks")
        tracks_layout = QVBoxLayout(tracks_group)
        
        self.tracks_list = QListWidget()
        tracks_layout.addWidget(self.tracks_list)
        
        # Botones de control de tracks
        track_buttons = QHBoxLayout()
        
        self.add_button = QPushButton("Agregar")
        self.add_button.clicked.connect(self._add_demo_tracks)
        
        self.clear_button = QPushButton("Limpiar")
        self.clear_button.clicked.connect(self._clear_tracks)
        
        track_buttons.addWidget(self.add_button)
        track_buttons.addWidget(self.clear_button)
        tracks_layout.addLayout(track_buttons)
        
        # Panel de optimización
        optimize_group = QGroupBox("Optimización")
        optimize_layout = QVBoxLayout(optimize_group)
        
        # Selector de estrategia
        strategy_layout = QHBoxLayout()
        strategy_layout.addWidget(QLabel("Estrategia:"))
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "Progresión de Claves",
            "Flujo de Energía",
            "Híbrido"
        ])
        strategy_layout.addWidget(self.strategy_combo)
        optimize_layout.addLayout(strategy_layout)
        
        # Botón optimizar
        self.optimize_button = QPushButton("Optimizar")
        self.optimize_button.clicked.connect(self._optimize)
        optimize_layout.addWidget(self.optimize_button)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        optimize_layout.addWidget(self.progress)
        
        # Agregar paneles al layout superior
        top_panel.addWidget(tracks_group, stretch=2)
        top_panel.addWidget(optimize_group, stretch=1)
        
        # Panel de resultados
        results_group = QGroupBox("Resultados")
        results_layout = QVBoxLayout(results_group)
        
        # Tabla de transiciones
        self.transitions_table = QTableWidget()
        self.transitions_table.setColumnCount(3)
        self.transitions_table.setHorizontalHeaderLabels([
            "Desde", "Hasta", "Score"
        ])
        results_layout.addWidget(self.transitions_table)
        
        # Panel de estadísticas
        stats_layout = QHBoxLayout()
        
        # Estadísticas generales
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(100)
        stats_layout.addWidget(self.stats_text)
        
        # Problemas y sugerencias
        self.problems_text = QTextEdit()
        self.problems_text.setReadOnly(True)
        self.problems_text.setMaximumHeight(100)
        stats_layout.addWidget(self.problems_text)
        
        results_layout.addLayout(stats_layout)
        
        # Agregar todo al layout principal
        layout.addLayout(top_panel)
        layout.addWidget(results_group)
        
        # Estado inicial
        self.optimize_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        
    def _add_demo_tracks(self):
        """Agrega tracks de demostración."""
        demo_tracks = [
            {
                'title': 'Track 1',
                'key': 'G maj',      # 8A
                'bpm': 126,
                'energy': 0.7,
                'danceability': 0.8
            },
            {
                'title': 'Track 2',
                'key': 'D min',      # 7B
                'bpm': 124,
                'energy': 0.6,
                'danceability': 0.7
            },
            {
                'title': 'Track 3',
                'key': 'A maj',      # 11A
                'bpm': 128,
                'energy': 0.9,
                'danceability': 0.8
            },
            {
                'title': 'Track 4',
                'key': 'F min',      # 4B
                'bpm': 122,
                'energy': 0.5,
                'danceability': 0.6
            },
            {
                'title': 'Track 5',
                'key': 'C maj',      # 8B
                'bpm': 130,
                'energy': 0.8,
                'danceability': 0.9
            }
        ]
        
        self.current_tracks = demo_tracks
        self._update_tracks_list()
        
        self.optimize_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        
    def _clear_tracks(self):
        """Limpia la lista de tracks."""
        self.current_tracks.clear()
        self.tracks_list.clear()
        self.transitions_table.setRowCount(0)
        self.stats_text.clear()
        self.problems_text.clear()
        self.result = None
        
        self.optimize_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        
    def _update_tracks_list(self):
        """Actualiza la lista visual de tracks."""
        self.tracks_list.clear()
        
        for track in self.current_tracks:
            text = (
                f"{track['title']}\n"
                f"Key: {track['key']} | BPM: {track['bpm']} | "
                f"Energy: {track['energy']:.2f}"
            )
            self.tracks_list.addItem(text)
            
    def _optimize(self):
        """Optimiza la playlist usando la estrategia seleccionada."""
        self.progress.setVisible(True)
        self.optimize_button.setEnabled(False)
        
        try:
            # Determinar estrategia
            strategy_map = {
                0: OptimizationStrategy.KEY_PROGRESSION,
                1: OptimizationStrategy.ENERGY_FLOW,
                2: OptimizationStrategy.HYBRID
            }
            strategy = strategy_map[self.strategy_combo.currentIndex()]
            
            # Optimizar
            self.result = self.optimizer.optimize(
                self.current_tracks,
                strategy=strategy
            )
            
            # Actualizar UI con resultados
            self._update_results()
            
        finally:
            self.progress.setVisible(False)
            self.optimize_button.setEnabled(True)
            
    def _update_results(self):
        """Actualiza la UI con los resultados de la optimización."""
        if not self.result or not self.result.success:
            return
            
        # Actualizar lista de tracks
        self.current_tracks = self.result.tracks
        self._update_tracks_list()
        
        # Actualizar tabla de transiciones
        self.transitions_table.setRowCount(len(self.result.stats['transitions']))
        
        for i, trans in enumerate(self.result.stats['transitions']):
            self.transitions_table.setItem(i, 0, QTableWidgetItem(trans['from']))
            self.transitions_table.setItem(i, 1, QTableWidgetItem(trans['to']))
            self.transitions_table.setItem(
                i, 2,
                QTableWidgetItem(f"{trans['score']:.2f}")
            )
            
        self.transitions_table.resizeColumnsToContents()
        
        # Actualizar estadísticas
        stats_text = (
            f"Score Final: {self.result.score:.2f}\n"
            f"Transiciones: {len(self.result.stats['transitions'])}\n"
        )
        
        if 'key_score' in self.result.stats:
            stats_text += f"Score Claves: {self.result.stats['key_score']:.2f}\n"
        if 'energy_score' in self.result.stats:
            stats_text += f"Score Energía: {self.result.stats['energy_score']:.2f}\n"
            
        self.stats_text.setText(stats_text)
        
        # Actualizar problemas
        if self.result.warnings:
            problems_text = "Advertencias:\n"
            problems_text += "\n".join(f"- {w}" for w in self.result.warnings)
            self.problems_text.setText(problems_text)
        else:
            self.problems_text.clear()

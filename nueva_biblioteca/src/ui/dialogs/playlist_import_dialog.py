"""
Diálogo para importar playlists
"""
from typing import List, Dict, Any
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal

from ...services.music_service import MusicService

class PlaylistImporter(QThread):
    """Worker para importar playlists en segundo plano."""
    
    progress = Signal(dict)  # Señal de progreso
    finished = Signal(dict)  # Señal de finalización
    
    def __init__(self, playlist_path: str, music_service: MusicService):
        super().__init__()
        self.playlist_path = playlist_path
        self.music_service = music_service
        
    def run(self):
        """Ejecuta la importación."""
        try:
            results = {
                'tracks': [],
                'errors': []
            }
            
            # Leer archivo de playlist
            with open(self.playlist_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_track = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('#EXTINF:'):
                    # Línea de metadata
                    meta = line.split(',', 1)[1]
                    if ' - ' in meta:
                        artist, title = meta.split(' - ', 1)
                        current_track = {
                            'artist': artist.strip(),
                            'title': title.strip()
                        }
                    else:
                        current_track = {'title': meta.strip()}
                        
                elif line.startswith('#'):
                    # Otra línea de comentario/metadata
                    continue
                    
                else:
                    # Línea de archivo
                    path = line
                    if current_track:
                        current_track['path'] = path
                    else:
                        current_track = {'path': path}
                    
                    # Intentar importar track
                    if current_track.get('path'):
                        track_path = current_track['path']
                        if not Path(track_path).is_absolute():
                            # Intentar resolver path relativo
                            base_dir = Path(self.playlist_path).parent
                            track_path = str(base_dir / track_path)
                        
                        # Solo importar si el archivo existe
                        if Path(track_path).exists():
                            try:
                                # Extraer metadata y añadir a biblioteca
                                track = self.music_service.import_tracks(
                                    str(Path(track_path).parent),
                                    recursive=False
                                )
                                if track and track['success'] > 0:
                                    results['tracks'].append(current_track)
                                else:
                                    results['errors'].append(
                                        f"Error importando: {track_path}"
                                    )
                            except Exception as e:
                                results['errors'].append(str(e))
                        else:
                            results['errors'].append(
                                f"Archivo no encontrado: {track_path}"
                            )
                    
                    current_track = {}
                    
            self.finished.emit(results)
            
        except Exception as e:
            self.finished.emit({
                'tracks': [],
                'errors': [str(e)]
            })

class PlaylistImportDialog(QDialog):
    """Diálogo para importar playlists."""
    
    def __init__(self, music_service: MusicService, parent=None):
        super().__init__(parent)
        self.music_service = music_service
        self.importer: PlaylistImporter = None
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("Importar Playlist")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setStyleSheet("""
            QDialog {
                background: #F5F5F5;
            }
            QFrame {
                background: #FFFFFF;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #6200EE;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3700B3;
            }
            QPushButton:pressed {
                background-color: #6200EE;
            }
            QPushButton:disabled {
                background-color: #E0E0E0;
                color: #9E9E9E;
            }
            QTableWidget {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background: white;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #E0E0E0;
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #6200EE;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Área superior
        top_layout = QHBoxLayout()
        
        self.select_btn = QPushButton("Seleccionar Playlist")
        self.select_btn.clicked.connect(self.select_playlist)
        top_layout.addWidget(self.select_btn)
        
        self.path_label = QLabel("Ningún archivo seleccionado")
        self.path_label.setStyleSheet("""
            QLabel {
                color: #666666;
                padding: 8px;
            }
        """)
        top_layout.addWidget(self.path_label, stretch=1)
        
        layout.addLayout(top_layout)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Área de resultados
        results_frame = QFrame()
        results_frame.setFrameShape(QFrame.StyledPanel)
        results_layout = QVBoxLayout(results_frame)
        
        # Tabla de tracks
        self.tracks_table = QTableWidget()
        self.tracks_table.setColumnCount(3)
        self.tracks_table.setHorizontalHeaderLabels(["Título", "Artista", "Ruta"])
        header = self.tracks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        results_layout.addWidget(self.tracks_table)
        
        # Tabla de errores
        self.errors_table = QTableWidget()
        self.errors_table.setColumnCount(1)
        self.errors_table.setHorizontalHeaderLabels(["Error"])
        self.errors_table.horizontalHeader().setStretchLastSection(True)
        self.errors_table.setVisible(False)
        results_layout.addWidget(self.errors_table)
        
        layout.addWidget(results_frame)
        
        # Botones inferiores
        buttons_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("Importar")
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self.start_import)
        
        self.close_btn = QPushButton("Cerrar")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6200EE;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
            }
        """)
        
        buttons_layout.addWidget(self.import_btn)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
    def select_playlist(self):
        """Abre diálogo para seleccionar archivo de playlist."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Playlist",
            str(Path.home()),
            "Playlists (*.m3u *.m3u8)"
        )
        
        if file_path:
            self.path_label.setText(file_path)
            self.import_btn.setEnabled(True)
            
    def start_import(self):
        """Inicia la importación de la playlist."""
        playlist_path = self.path_label.text()
        if playlist_path == "Ningún archivo seleccionado":
            return
            
        # Deshabilitar controles
        self.select_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        
        # Mostrar progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # Crear y configurar importer
        self.importer = PlaylistImporter(playlist_path, self.music_service)
        self.importer.finished.connect(self.import_finished)
        self.importer.start()
        
    def import_finished(self, results: Dict[str, Any]):
        """
        Maneja la finalización de la importación.
        
        Args:
            results: Diccionario con resultados
        """
        # Detener progreso
        self.progress_bar.setVisible(False)
        
        # Mostrar tracks importados
        tracks = results.get('tracks', [])
        self.tracks_table.setRowCount(len(tracks))
        for i, track in enumerate(tracks):
            self.tracks_table.setItem(i, 0, QTableWidgetItem(track.get('title', '')))
            self.tracks_table.setItem(i, 1, QTableWidgetItem(track.get('artist', '')))
            self.tracks_table.setItem(i, 2, QTableWidgetItem(track.get('path', '')))
            
        # Mostrar errores si hay
        errors = results.get('errors', [])
        if errors:
            self.errors_table.setVisible(True)
            self.errors_table.setRowCount(len(errors))
            for i, error in enumerate(errors):
                self.errors_table.setItem(i, 0, QTableWidgetItem(str(error)))
                
        # Rehabilitar controles
        self.select_btn.setEnabled(True)
        self.import_btn.setEnabled(True)

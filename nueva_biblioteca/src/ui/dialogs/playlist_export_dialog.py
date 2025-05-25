"""
Diálogo para exportar playlists
"""
from typing import List, Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QComboBox, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import Qt

from ...services.music_service import MusicService

class PlaylistExportDialog(QDialog):
    """Diálogo para exportar playlists."""
    
    def __init__(self, music_service: MusicService, track_ids: List[str], parent=None):
        """
        Inicializa el diálogo.
        
        Args:
            music_service: Servicio de música
            track_ids: Lista de IDs de tracks a exportar
            parent: Widget padre
        """
        super().__init__(parent)
        self.music_service = music_service
        self.track_ids = track_ids
        self.setup_ui()
        self.load_tracks()
        
    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("Exportar Playlist")
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
            QComboBox {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
                background: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(:/icons/arrow_down.png);
                width: 12px;
                height: 12px;
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
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Área de tracks
        tracks_frame = QFrame()
        tracks_frame.setFrameShape(QFrame.StyledPanel)
        tracks_layout = QVBoxLayout(tracks_frame)
        
        # Etiqueta de tracks
        tracks_label = QLabel("Tracks a Exportar")
        tracks_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #000000;
            }
        """)
        tracks_layout.addWidget(tracks_label)
        
        # Tabla de tracks
        self.tracks_table = QTableWidget()
        self.tracks_table.setColumnCount(4)
        self.tracks_table.setHorizontalHeaderLabels(["Título", "Artista", "Álbum", "Género"])
        header = self.tracks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        tracks_layout.addWidget(self.tracks_table)
        
        layout.addWidget(tracks_frame)
        
        # Área de opciones
        options_frame = QFrame()
        options_frame.setFrameShape(QFrame.StyledPanel)
        options_layout = QVBoxLayout(options_frame)
        
        # Formato
        format_layout = QHBoxLayout()
        format_label = QLabel("Formato:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(['m3u', 'm3u8'])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo, stretch=1)
        options_layout.addLayout(format_layout)
        
        layout.addWidget(options_frame)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("Exportar")
        self.export_btn.clicked.connect(self.export_playlist)
        
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
        
        buttons_layout.addWidget(self.export_btn)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
    def load_tracks(self):
        """Carga los tracks en la tabla."""
        self.tracks_table.setRowCount(len(self.track_ids))
        
        for i, track_id in enumerate(self.track_ids):
            track = self.music_service.get_track(track_id)
            if track:
                self.tracks_table.setItem(i, 0, QTableWidgetItem(track['title']))
                self.tracks_table.setItem(i, 1, QTableWidgetItem(track['artist']))
                self.tracks_table.setItem(i, 2, QTableWidgetItem(track['album']))
                self.tracks_table.setItem(i, 3, QTableWidgetItem(track.get('genre', '')))
                
    def export_playlist(self):
        """Exporta la playlist al archivo seleccionado."""
        format = self.format_combo.currentText()
        file_filter = f"Playlist (*.{format})"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Playlist",
            str(Path.home()),
            file_filter
        )
        
        if file_path:
            # Asegurar extensión correcta
            if not file_path.lower().endswith(f'.{format}'):
                file_path += f'.{format}'
            
            # Generar contenido
            content = self.music_service.export_playlist(
                self.track_ids,
                format=format
            )
            
            if content:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.accept()
                except Exception as e:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Error guardando playlist: {str(e)}"
                    )

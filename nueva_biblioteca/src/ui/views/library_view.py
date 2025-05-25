"""
Vista de biblioteca con Material 3 Expressive.
Integrada con servicios de datos y motor de reglas.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QLabel, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal
from typing import List, Dict, Any


class LibraryView(QWidget):
    """Vista de biblioteca con diseño Material 3 Expressive."""
    
    # Señales
    track_selected = Signal(dict)  # track_data
    track_double_clicked = Signal(dict)  # track_data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks = []
        self._filtered_tracks = []
        self._setup_ui()
        self._setup_connections()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header con información
        header_layout = QHBoxLayout()
        
        self.info_label = QLabel("Biblioteca Musical")
        self.info_label.setStyleSheet("""
            QLabel {
                color: #E6E1E5;
                font-size: 16px;
                font-weight: 600;
                padding: 8px 0px;
            }
        """)
        header_layout.addWidget(self.info_label)
        
        self.stats_label = QLabel("0 tracks")
        self.stats_label.setStyleSheet("""
            QLabel {
                color: #CAC4D0;
                font-size: 12px;
                padding: 8px 0px;
            }
        """)
        header_layout.addStretch()
        header_layout.addWidget(self.stats_label)
        
        layout.addLayout(header_layout)
        
        # Tabla de música
        self.music_table = QTableWidget()
        self.music_table.setColumnCount(8)
        self.music_table.setHorizontalHeaderLabels([
            "Título", "Artista", "Álbum", "Género", "BPM", "Clave", "Energía", "Duración"
        ])
        
        # Configurar encabezados
        header = self.music_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Título se estira
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Artista
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Álbum
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Género
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # BPM
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Clave
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Energía
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Duración
        
        # Estilo de la tabla
        self.music_table.setStyleSheet("""
            QTableWidget {
                background: rgba(28, 27, 31, 0.6);
                border: 1px solid rgba(103, 80, 164, 0.2);
                border-radius: 12px;
                color: #E6E1E5;
                gridline-color: rgba(103, 80, 164, 0.1);
                selection-background-color: rgba(103, 80, 164, 0.3);
            }
            QTableWidget::item {
                padding: 8px 12px;
                border: none;
            }
            QTableWidget::item:hover {
                background: rgba(103, 80, 164, 0.2);
            }
            QHeaderView::section {
                background: rgba(103, 80, 164, 0.2);
                color: #D0BCFF;
                border: none;
                padding: 8px 12px;
                font-weight: 600;
            }
        """)
        
        self.music_table.setAlternatingRowColors(True)
        self.music_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.music_table)
        
    def _setup_connections(self):
        """Configura las conexiones de señales."""
        self.music_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.music_table.itemDoubleClicked.connect(self._on_double_click)
        
    def _on_selection_changed(self):
        """Maneja cambios en la selección."""
        current_row = self.music_table.currentRow()
        if current_row >= 0 and current_row < len(self._filtered_tracks):
            track = self._filtered_tracks[current_row]
            self.track_selected.emit(track)
    
    def _on_double_click(self, item):
        """Maneja doble clic en un track."""
        row = item.row()
        if row >= 0 and row < len(self._filtered_tracks):
            track = self._filtered_tracks[row]
            self.track_double_clicked.emit(track)
    
    def update_tracks(self, tracks: List[Dict[str, Any]]):
        """Actualiza la lista de tracks mostrados."""
        self._filtered_tracks = tracks
        self._populate_table()
        self._update_stats()
    
    def _populate_table(self):
        """Puebla la tabla con los tracks actuales."""
        self.music_table.setRowCount(len(self._filtered_tracks))
        
        for row, track in enumerate(self._filtered_tracks):
            # Título
            item = QTableWidgetItem(track.get("title", ""))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.music_table.setItem(row, 0, item)
            
            # Artista
            item = QTableWidgetItem(track.get("artist", ""))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.music_table.setItem(row, 1, item)
            
            # Álbum
            item = QTableWidgetItem(track.get("album", ""))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.music_table.setItem(row, 2, item)
            
            # Género
            item = QTableWidgetItem(track.get("genre", ""))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.music_table.setItem(row, 3, item)
            
            # BPM
            bpm = track.get("bpm", 0)
            item = QTableWidgetItem(str(bpm) if bpm else "")
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.music_table.setItem(row, 4, item)
            
            # Clave
            item = QTableWidgetItem(track.get("key", ""))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.music_table.setItem(row, 5, item)
            
            # Energía
            energy = track.get("energy", 0)
            energy_text = f"{energy:.1f}" if energy else ""
            item = QTableWidgetItem(energy_text)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.music_table.setItem(row, 6, item)
            
            # Duración
            duration_formatted = track.get("duration_formatted", "")
            item = QTableWidgetItem(duration_formatted)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.music_table.setItem(row, 7, item)
    
    def _update_stats(self):
        """Actualiza las estadísticas mostradas."""
        count = len(self._filtered_tracks)
        if count == 1:
            self.stats_label.setText("1 track")
        else:
            self.stats_label.setText(f"{count} tracks")
    
    def get_selected_track(self) -> Dict[str, Any]:
        """Obtiene el track seleccionado."""
        current_row = self.music_table.currentRow()
        if current_row >= 0 and current_row < len(self._filtered_tracks):
            return self._filtered_tracks[current_row]
        return {}
    
    def clear_selection(self):
        """Limpia la selección."""
        self.music_table.clearSelection() 
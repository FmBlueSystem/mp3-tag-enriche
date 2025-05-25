"""
Diálogo para importar música a la biblioteca
"""
from typing import Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QProgressBar, QTableWidget, QTableWidgetItem,
    QFrame, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, QThread, Signal

from ...services.music_service import MusicService

class ImportWorker(QThread):
    """Worker thread para importar música."""
    progress = Signal(dict)
    finished = Signal(dict)
    
    def __init__(self, music_service: MusicService, directory: str):
        super().__init__()
        self.music_service = music_service
        self.directory = directory
        
    def run(self):
        """Ejecuta la importación en segundo plano."""
        try:
            results = self.music_service.import_tracks(self.directory)
            self.finished.emit(results)
        except Exception as e:
            self.finished.emit({
                'total': 0,
                'success': 0,
                'failed': 0,
                'errors': [str(e)],
                'imported_tracks': []
            })

class ResultsWidget(QFrame):
    """Widget para mostrar resultados de importación."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget de resultados."""
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            ResultsWidget {
                background: #FFFFFF;
                border-radius: 8px;
                padding: 16px;
            }
            QLabel {
                color: #000000;
                font-size: 14px;
            }
            QLabel#statsLabel {
                font-weight: bold;
                font-size: 16px;
                margin-bottom: 8px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Etiquetas para estadísticas
        self.stats_label = QLabel("Resultados de Importación")
        self.stats_label.setObjectName("statsLabel")
        layout.addWidget(self.stats_label)
        
        # Grid para estadísticas detalladas
        stats_layout = QHBoxLayout()
        
        self.total_label = QLabel("Total: 0")
        self.success_label = QLabel("Exitosos: 0")
        self.failed_label = QLabel("Fallidos: 0")
        
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.success_label)
        stats_layout.addWidget(self.failed_label)
        
        layout.addLayout(stats_layout)
        
        # Tabla de errores
        self.errors_table = QTableWidget()
        self.errors_table.setColumnCount(1)
        self.errors_table.setHorizontalHeaderLabels(["Error"])
        self.errors_table.horizontalHeader().setStretchLastSection(True)
        self.errors_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.errors_table)
        
        self.setLayout(layout)
        
    def update_results(self, results: dict):
        """
        Actualiza el widget con nuevos resultados.
        
        Args:
            results: Diccionario con resultados de importación
        """
        self.total_label.setText(f"Total: {results['total']}")
        self.success_label.setText(f"Exitosos: {results['success']}")
        self.failed_label.setText(f"Fallidos: {results['failed']}")
        
        # Actualizar tabla de errores
        self.errors_table.setRowCount(len(results['errors']))
        for i, error in enumerate(results['errors']):
            self.errors_table.setItem(i, 0, QTableWidgetItem(str(error)))

class ImportDialog(QDialog):
    """Diálogo para importar música a la biblioteca."""
    
    def __init__(self, music_service: MusicService, parent=None):
        super().__init__(parent)
        self.music_service = music_service
        self.worker: Optional[ImportWorker] = None
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("Importar Música")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setStyleSheet("""
            QDialog {
                background: #F5F5F5;
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
        
        # Botón de selección
        self.select_btn = QPushButton("Seleccionar Directorio")
        self.select_btn.setMinimumHeight(36)
        self.select_btn.clicked.connect(self.select_directory)
        top_layout.addWidget(self.select_btn)
        
        # Etiqueta de directorio
        self.dir_label = QLabel("Ningún directorio seleccionado")
        self.dir_label.setStyleSheet("""
            QLabel {
                color: #666666;
                padding: 8px;
            }
        """)
        top_layout.addWidget(self.dir_label, stretch=1)
        
        layout.addLayout(top_layout)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Área de resultados
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        self.results_widget = ResultsWidget()
        self.results_widget.setVisible(False)
        
        scroll.setWidget(self.results_widget)
        layout.addWidget(scroll)
        
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
        
    def select_directory(self):
        """Abre diálogo para seleccionar directorio."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Directorio de Música",
            str(Path.home()),
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            self.dir_label.setText(directory)
            self.import_btn.setEnabled(True)
            
    def start_import(self):
        """Inicia el proceso de importación."""
        directory = self.dir_label.text()
        if directory == "Ningún directorio seleccionado":
            return
            
        # Deshabilitar controles
        self.select_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        
        # Mostrar progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Modo indeterminado
        
        # Crear y configurar worker
        self.worker = ImportWorker(self.music_service, directory)
        self.worker.finished.connect(self.import_finished)
        self.worker.start()
        
    def import_finished(self, results: dict):
        """
        Maneja la finalización de la importación.
        
        Args:
            results: Diccionario con resultados
        """
        # Detener progreso
        self.progress_bar.setVisible(False)
        
        # Mostrar resultados
        self.results_widget.setVisible(True)
        self.results_widget.update_results(results)
        
        # Rehabilitar controles
        self.select_btn.setEnabled(True)
        self.import_btn.setEnabled(True)

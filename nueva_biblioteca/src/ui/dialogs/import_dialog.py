"""
Diálogo para importar música a la biblioteca
"""
from typing import Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QProgressBar, QTableWidget, QTableWidgetItem,
    QFrame, QScrollArea, QWidget, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal

from ...services.music_service import MusicService
from ...importers.import_manager import ImportManager, ImportProgress, ImportResult

class ImportWorker(QThread):
    """Worker thread para importar música usando MusicService integrado con ImportManager."""
    progress = Signal(dict)
    finished = Signal(dict)
    
    def __init__(self, directory: str, music_service: MusicService):
        super().__init__()
        self.directory = directory
        self.music_service = music_service
        self.import_manager = ImportManager()
        
    def run(self):
        """Ejecuta la importación en segundo plano usando MusicService."""
        try:
            # Configurar callbacks del ImportManager para recibir actualizaciones
            self.import_manager.add_progress_callback(self._on_progress)
            
            # Utilizar método integrado de MusicService para importación
            result = self.music_service.import_files_with_manager(
                self.directory,
                recursive=True
            )
            
            # Emitir resultado ya procesado por MusicService
            self.finished.emit(result)
            
        except Exception as e:
            self.finished.emit({
                'total': 0,
                'success': 0,
                'failed': 1,
                'duplicates': 0,
                'errors': [str(e)],
                'imported_tracks': [],
                'duration': 0
            })
    
    def _on_progress(self, progress: ImportProgress):
        """Callback para progreso de importación."""
        progress_data = {
            'total_files': progress.total_files,
            'processed_files': progress.processed_files,
            'successful_imports': progress.successful_imports,
            'failed_imports': progress.failed_imports,
            'duplicate_files': progress.duplicate_files,
            'current_file': progress.current_file,
            'completion_percentage': progress.completion_percentage,
            'processing_rate': progress.processing_rate,
            'estimated_time_remaining': progress.estimated_time_remaining
        }
        self.progress.emit(progress_data)
    
    def cancel_import(self):
        """Cancela la importación en progreso."""
        if self.import_manager:
            self.import_manager.cancel_import()

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
        self.duplicates_label = QLabel("Duplicados: 0")
        
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.success_label)
        stats_layout.addWidget(self.failed_label)
        stats_layout.addWidget(self.duplicates_label)
        
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
        self.duplicates_label.setText(f"Duplicados: {results.get('duplicates', 0)}")
        
        # Actualizar tabla de errores
        self.errors_table.setRowCount(len(results['errors']))
        for i, error in enumerate(results['errors']):
            self.errors_table.setItem(i, 0, QTableWidgetItem(str(error)))

class ImportDialog(QDialog):
    """Diálogo para importar música a la biblioteca."""
    
    def __init__(self, music_service: MusicService, parent=None):
        super().__init__(parent)
        self.music_service = music_service  # Mantenemos para compatibilidad
        self.worker: Optional[ImportWorker] = None
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("Importar Música")
        self.setMinimumWidth(650)
        self.setMinimumHeight(450)
        
        # Crear barra de estado
        self.status_bar = QLabel("Seleccione un directorio para comenzar")
        self.status_bar.setStyleSheet("color: #666666; padding: 5px;")
        
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
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self.cancel_import)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC3545;
                color: white;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
        """)
        
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
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
        
        # Añadir barra de estado al fondo
        layout.addWidget(self.status_bar)
        
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
        
        # Mostrar botón cancelar y ocultar cerrar
        self.cancel_btn.setVisible(True)
        self.close_btn.setVisible(False)
        
        # Mostrar progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Modo indeterminado
        
        # Crear y configurar worker con MusicService
        self.worker = ImportWorker(directory, self.music_service)
        self.worker.finished.connect(self.import_finished)
        self.worker.progress.connect(self.update_progress)
        self.worker.start()
    
    def update_progress(self, progress_data: dict):
        """Actualiza la barra de progreso con datos en tiempo real."""
        if progress_data.get('total_files', 0) > 0:
            # Cambiar a modo determinado
            self.progress_bar.setRange(0, progress_data['total_files'])
            self.progress_bar.setValue(progress_data['processed_files'])
            
            # Actualizar texto de estado
            current_file = progress_data.get('current_file', '')
            if current_file:
                percentage = progress_data.get('completion_percentage', 0)
                self.progress_bar.setFormat(f"{percentage:.1f}% - {current_file}")
        else:
            # Mantener modo indeterminado
            self.progress_bar.setRange(0, 0)
        
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
        
        # Rehabilitar controles y cambiar visibilidad
        self.select_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        self.close_btn.setVisible(True)
        
        # Mostrar información resumen
        duration = results.get('duration', 0)
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        # Añadimos mensaje detallado
        success = results.get('success', 0)
        failed = results.get('failed', 0)
        duplicates = results.get('duplicates', 0)
        
        info_text = f"Importación completada en {minutes}min {seconds}s.\n\n"
        
        if success > 0:
            info_text += f"• {success} archivos importados correctamente.\n"
        if duplicates > 0:
            info_text += f"• {duplicates} archivos duplicados omitidos.\n"
        if failed > 0:
            info_text += f"• {failed} archivos fallidos (ver detalles).\n"
            
        QMessageBox.information(
            self,
            "Importación Completada",
            info_text
        )
        
        # Si hay nuevas pistas, marcar para actualizar la biblioteca
        if success > 0:
            self.setResult(QDialog.Accepted)
    
    def set_import_path(self, folder_path: str):
        """Establece la ruta de importación preseleccionada."""
        if folder_path and Path(folder_path).exists():
            self.dir_label.setText(folder_path)
            self.import_btn.setEnabled(True)
            
    def cancel_import(self):
        """Cancela la importación en progreso."""
        if self.worker and self.worker.isRunning():
            # Cancelar importación en el ImportManager
            self.worker.cancel_import()
            
            # Actualizar UI
            self.status_bar.showMessage("Importación cancelada")
            self.progress_bar.setFormat("Cancelando...")
            
            # No terminamos el thread forzosamente, dejamos que termine limpiamente
            # El callback import_finished se llamará cuando termine

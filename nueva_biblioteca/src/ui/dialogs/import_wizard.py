"""
Wizard de importación de archivos musicales.
"""

import os
from pathlib import Path
from typing import Optional, List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QFileDialog, QCheckBox, QSpinBox,
    QGroupBox, QListWidget, QListWidgetItem, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QComboBox, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QThread, pyqtSignal
from PySide6.QtGui import QFont, QIcon, QPixmap
import logging

from ...importers import ImportManager, ImportProgress, ImportResult

class ImportWorkerThread(QThread):
    """
    Hilo de trabajo para la importación que no bloquea la UI.
    """
    progress_updated = pyqtSignal(ImportProgress)
    import_completed = pyqtSignal(ImportResult)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, import_manager: ImportManager):
        super().__init__()
        self.import_manager = import_manager
        self.directories: List[str] = []
        self.files: List[str] = []
        self.options = {
            'recursive': True,
            'check_duplicates': True,
            'extract_metadata': True
        }
        
        # Conectar callbacks del import manager
        self.import_manager.add_progress_callback(self.progress_updated.emit)
        self.import_manager.add_completion_callback(self.import_completed.emit)
        self.import_manager.add_error_callback(self.error_occurred.emit)
    
    def set_directories(self, directories: List[str]):
        """Establece los directorios a importar."""
        self.directories = directories
        self.files = []
    
    def set_files(self, files: List[str]):
        """Establece los archivos específicos a importar."""
        self.files = files
        self.directories = []
    
    def set_options(self, options: dict):
        """Establece las opciones de importación."""
        self.options.update(options)
    
    def run(self):
        """Ejecuta la importación."""
        try:
            if self.directories:
                # Importar directorios
                for directory in self.directories:
                    if not self.import_manager.is_importing:
                        result = self.import_manager.import_directory(
                            directory,
                            recursive=self.options.get('recursive', True),
                            check_duplicates=self.options.get('check_duplicates', True),
                            extract_metadata=self.options.get('extract_metadata', True)
                        )
                        if not self.directories[:-1]:  # Si es el último directorio
                            self.import_completed.emit(result)
            
            elif self.files:
                # Importar archivos específicos
                result = self.import_manager.import_files(
                    self.files,
                    check_duplicates=self.options.get('check_duplicates', True),
                    extract_metadata=self.options.get('extract_metadata', True)
                )
                self.import_completed.emit(result)
                
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def cancel_import(self):
        """Cancela la importación."""
        self.import_manager.cancel_import()

class ImportWizard(QDialog):
    """
    Wizard para importación de archivos musicales con interfaz paso a paso.
    """
    
    # Señales
    import_completed = Signal(ImportResult)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Configuración del diálogo
        self.setWindowTitle("Asistente de Importación - Nueva Biblioteca")
        self.setModal(True)
        self.resize(700, 500)
        
        # Componentes
        self.import_manager = ImportManager(max_workers=4)
        self.worker_thread: Optional[ImportWorkerThread] = None
        
        # Estado del wizard
        self.current_step = 0
        self.selected_paths: List[str] = []
        self.import_options = {
            'recursive': True,
            'check_duplicates': True,
            'extract_metadata': True,
            'max_workers': 4
        }
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Título y descripción
        title_label = QLabel("Importar Música")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        description_label = QLabel(
            "Importe archivos musicales a su biblioteca. "
            "El asistente le guiará paso a paso."
        )
        description_label.setWordWrap(True)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addSpacing(20)
        
        # Stack de pasos
        self.steps_stack = QStackedWidget()
        layout.addWidget(self.steps_stack)
        
        # Paso 1: Selección de archivos/directorios
        self.step1_widget = self.create_selection_step()
        self.steps_stack.addWidget(self.step1_widget)
        
        # Paso 2: Opciones de importación
        self.step2_widget = self.create_options_step()
        self.steps_stack.addWidget(self.step2_widget)
        
        # Paso 3: Proceso de importación
        self.step3_widget = self.create_import_step()
        self.steps_stack.addWidget(self.step3_widget)
        
        # Paso 4: Resultado
        self.step4_widget = self.create_results_step()
        self.steps_stack.addWidget(self.step4_widget)
        
        # Botones de navegación
        button_layout = QHBoxLayout()
        
        self.back_button = QPushButton("< Anterior")
        self.next_button = QPushButton("Siguiente >")
        self.cancel_button = QPushButton("Cancelar")
        self.finish_button = QPushButton("Finalizar")
        
        self.back_button.setEnabled(False)
        self.finish_button.setVisible(False)
        
        button_layout.addWidget(self.back_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.finish_button)
        
        layout.addLayout(button_layout)
        
        # Referencias a botones para fácil acceso
        self.buttons = {
            'back': self.back_button,
            'next': self.next_button,
            'cancel': self.cancel_button,
            'finish': self.finish_button
        }
    
    def create_selection_step(self) -> QWidget:
        """Crea el paso de selección de archivos/directorios."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instrucciones
        instructions = QLabel(
            "Seleccione los directorios o archivos que desea importar:"
        )
        layout.addWidget(instructions)
        
        # Botones de selección
        button_layout = QHBoxLayout()
        
        self.select_directory_btn = QPushButton("Agregar Directorio")
        self.select_files_btn = QPushButton("Agregar Archivos")
        self.clear_selection_btn = QPushButton("Limpiar")
        
        button_layout.addWidget(self.select_directory_btn)
        button_layout.addWidget(self.select_files_btn)
        button_layout.addWidget(self.clear_selection_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Lista de archivos/directorios seleccionados
        self.selection_list = QListWidget()
        self.selection_list.setMinimumHeight(200)
        layout.addWidget(QLabel("Elementos seleccionados:"))
        layout.addWidget(self.selection_list)
        
        # Información de selección
        self.selection_info = QLabel("No hay elementos seleccionados")
        layout.addWidget(self.selection_info)
        
        return widget
    
    def create_options_step(self) -> QWidget:
        """Crea el paso de opciones de importación."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instrucciones
        instructions = QLabel(
            "Configure las opciones de importación:"
        )
        layout.addWidget(instructions)
        
        # Opciones principales
        main_group = QGroupBox("Opciones Principales")
        main_layout = QFormLayout(main_group)
        
        self.recursive_check = QCheckBox()
        self.recursive_check.setChecked(True)
        main_layout.addRow("Buscar en subdirectorios:", self.recursive_check)
        
        self.duplicates_check = QCheckBox()
        self.duplicates_check.setChecked(True)
        main_layout.addRow("Verificar archivos duplicados:", self.duplicates_check)
        
        self.metadata_check = QCheckBox()
        self.metadata_check.setChecked(True)
        main_layout.addRow("Extraer metadatos:", self.metadata_check)
        
        layout.addWidget(main_group)
        
        # Opciones avanzadas
        advanced_group = QGroupBox("Opciones Avanzadas")
        advanced_layout = QFormLayout(advanced_group)
        
        self.workers_spin = QSpinBox()
        self.workers_spin.setMinimum(1)
        self.workers_spin.setMaximum(8)
        self.workers_spin.setValue(4)
        advanced_layout.addRow("Hilos de procesamiento:", self.workers_spin)
        
        layout.addWidget(advanced_group)
        
        layout.addStretch()
        
        return widget
    
    def create_import_step(self) -> QWidget:
        """Crea el paso del proceso de importación."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Estado actual
        self.import_status_label = QLabel("Preparando importación...")
        layout.addWidget(self.import_status_label)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # Información detallada
        info_group = QGroupBox("Información del Proceso")
        info_layout = QFormLayout(info_group)
        
        self.total_files_label = QLabel("0")
        self.processed_files_label = QLabel("0")
        self.successful_label = QLabel("0")
        self.failed_label = QLabel("0")
        self.duplicates_label = QLabel("0")
        self.current_file_label = QLabel("")
        
        info_layout.addRow("Total de archivos:", self.total_files_label)
        info_layout.addRow("Procesados:", self.processed_files_label)
        info_layout.addRow("Exitosos:", self.successful_label)
        info_layout.addRow("Fallidos:", self.failed_label)
        info_layout.addRow("Duplicados:", self.duplicates_label)
        info_layout.addRow("Archivo actual:", self.current_file_label)
        
        layout.addWidget(info_group)
        
        # Log de proceso
        self.import_log = QTextEdit()
        self.import_log.setMaximumHeight(150)
        self.import_log.setReadOnly(True)
        layout.addWidget(QLabel("Log del proceso:"))
        layout.addWidget(self.import_log)
        
        return widget
    
    def create_results_step(self) -> QWidget:
        """Crea el paso de resultados."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Título de resultado
        self.result_title = QLabel()
        result_font = QFont()
        result_font.setPointSize(14)
        result_font.setBold(True)
        self.result_title.setFont(result_font)
        layout.addWidget(self.result_title)
        
        # Resumen de resultados
        self.result_summary = QLabel()
        self.result_summary.setWordWrap(True)
        layout.addWidget(self.result_summary)
        
        # Estadísticas detalladas
        stats_group = QGroupBox("Estadísticas Detalladas")
        stats_layout = QFormLayout(stats_group)
        
        self.stats_total = QLabel()
        self.stats_successful = QLabel()
        self.stats_failed = QLabel()
        self.stats_duplicates = QLabel()
        self.stats_duration = QLabel()
        
        stats_layout.addRow("Total procesado:", self.stats_total)
        stats_layout.addRow("Importaciones exitosas:", self.stats_successful)
        stats_layout.addRow("Importaciones fallidas:", self.stats_failed)
        stats_layout.addRow("Archivos duplicados:", self.stats_duplicates)
        stats_layout.addRow("Duración:", self.stats_duration)
        
        layout.addWidget(stats_group)
        
        # Log de errores (si los hay)
        self.error_log = QTextEdit()
        self.error_log.setMaximumHeight(150)
        self.error_log.setReadOnly(True)
        self.error_log.setVisible(False)
        
        self.error_label = QLabel("Errores encontrados:")
        self.error_label.setVisible(False)
        
        layout.addWidget(self.error_label)
        layout.addWidget(self.error_log)
        
        layout.addStretch()
        
        return widget
    
    def setup_connections(self):
        """Configura las conexiones de señales."""
        # Botones de navegación
        self.back_button.clicked.connect(self.go_back)
        self.next_button.clicked.connect(self.go_next)
        self.cancel_button.clicked.connect(self.cancel_import)
        self.finish_button.clicked.connect(self.accept)
        
        # Botones de selección
        self.select_directory_btn.clicked.connect(self.select_directory)
        self.select_files_btn.clicked.connect(self.select_files)
        self.clear_selection_btn.clicked.connect(self.clear_selection)
    
    def go_next(self):
        """Avanza al siguiente paso."""
        if self.current_step == 0:
            # Validar selección
            if not self.selected_paths:
                self.show_error("Debe seleccionar al menos un directorio o archivo")
                return
            self.update_options()
        
        elif self.current_step == 1:
            # Iniciar importación
            self.start_import()
        
        elif self.current_step == 2:
            # En proceso - no debería estar habilitado
            return
        
        self.current_step += 1
        self.update_step()
    
    def go_back(self):
        """Retrocede al paso anterior."""
        if self.current_step > 0:
            self.current_step -= 1
            self.update_step()
    
    def update_step(self):
        """Actualiza la interfaz según el paso actual."""
        self.steps_stack.setCurrentIndex(self.current_step)
        
        # Botones
        self.back_button.setEnabled(self.current_step > 0)
        
        if self.current_step == 0:
            self.next_button.setText("Siguiente >")
            self.next_button.setEnabled(len(self.selected_paths) > 0)
        elif self.current_step == 1:
            self.next_button.setText("Iniciar Importación")
            self.next_button.setEnabled(True)
        elif self.current_step == 2:
            self.next_button.setEnabled(False)
            self.cancel_button.setText("Cancelar Importación")
        elif self.current_step == 3:
            self.next_button.setVisible(False)
            self.cancel_button.setVisible(False)
            self.finish_button.setVisible(True)
            self.back_button.setEnabled(False)
    
    def select_directory(self):
        """Selecciona un directorio para importar."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Directorio de Música",
            str(Path.home() / "Music")
        )
        
        if directory and directory not in self.selected_paths:
            self.selected_paths.append(directory)
            self.update_selection_list()
    
    def select_files(self):
        """Selecciona archivos específicos para importar."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar Archivos de Música",
            str(Path.home() / "Music"),
            "Archivos de Audio (*.mp3 *.flac *.m4a *.wav *.ogg);;Todos los archivos (*)"
        )
        
        for file in files:
            if file not in self.selected_paths:
                self.selected_paths.append(file)
        
        self.update_selection_list()
    
    def clear_selection(self):
        """Limpia la selección."""
        self.selected_paths.clear()
        self.update_selection_list()
    
    def update_selection_list(self):
        """Actualiza la lista de selección."""
        self.selection_list.clear()
        
        for path in self.selected_paths:
            item = QListWidgetItem(path)
            if Path(path).is_dir():
                item.setText(f"📁 {path}")
            else:
                item.setText(f"🎵 {Path(path).name}")
            self.selection_list.addItem(item)
        
        # Actualizar información
        count = len(self.selected_paths)
        if count == 0:
            self.selection_info.setText("No hay elementos seleccionados")
        else:
            dirs = sum(1 for p in self.selected_paths if Path(p).is_dir())
            files = count - dirs
            self.selection_info.setText(
                f"Seleccionados: {dirs} directorio(s) y {files} archivo(s)"
            )
        
        # Habilitar botón siguiente
        if hasattr(self, 'next_button'):
            self.next_button.setEnabled(count > 0)
    
    def update_options(self):
        """Actualiza las opciones de importación."""
        self.import_options.update({
            'recursive': self.recursive_check.isChecked(),
            'check_duplicates': self.duplicates_check.isChecked(),
            'extract_metadata': self.metadata_check.isChecked(),
            'max_workers': self.workers_spin.value()
        })
    
    def start_import(self):
        """Inicia el proceso de importación."""
        # Actualizar manager con nuevas opciones
        self.import_manager.max_workers = self.import_options['max_workers']
        
        # Crear y configurar worker thread
        self.worker_thread = ImportWorkerThread(self.import_manager)
        
        # Conectar señales
        self.worker_thread.progress_updated.connect(self.update_import_progress)
        self.worker_thread.import_completed.connect(self.import_finished)
        self.worker_thread.error_occurred.connect(self.import_error)
        
        # Configurar datos
        directories = [p for p in self.selected_paths if Path(p).is_dir()]
        files = [p for p in self.selected_paths if Path(p).is_file()]
        
        if directories:
            self.worker_thread.set_directories(directories)
        else:
            self.worker_thread.set_files(files)
        
        self.worker_thread.set_options(self.import_options)
        
        # Iniciar
        self.worker_thread.start()
        
        # Log inicial
        self.import_log.append("Iniciando importación...")
        self.import_log.append(f"Directorios: {len(directories)}")
        self.import_log.append(f"Archivos: {len(files)}")
    
    def update_import_progress(self, progress: ImportProgress):
        """Actualiza el progreso de importación."""
        # Barra de progreso
        self.progress_bar.setValue(int(progress.completion_percentage))
        
        # Etiquetas de información
        self.total_files_label.setText(str(progress.total_files))
        self.processed_files_label.setText(str(progress.processed_files))
        self.successful_label.setText(str(progress.successful_imports))
        self.failed_label.setText(str(progress.failed_imports))
        self.duplicates_label.setText(str(progress.duplicate_files))
        self.current_file_label.setText(progress.current_file)
        
        # Estado
        if progress.total_files > 0:
            self.import_status_label.setText(
                f"Procesando... {progress.processed_files}/{progress.total_files} "
                f"({progress.completion_percentage:.1f}%)"
            )
        
        # Log si hay cambios significativos
        if progress.processed_files % 10 == 0 or progress.current_file:
            self.import_log.append(f"Procesado: {progress.current_file}")
    
    def import_finished(self, result: ImportResult):
        """Maneja la finalización de la importación."""
        self.current_step = 3
        self.update_step()
        
        # Actualizar resultado
        if result.successful_imports > 0:
            self.result_title.setText("✅ Importación Completada")
            self.result_title.setStyleSheet("color: green;")
        else:
            self.result_title.setText("⚠️ Importación con Problemas")
            self.result_title.setStyleSheet("color: orange;")
        
        # Resumen
        self.result_summary.setText(
            f"Se procesaron {result.total_processed} archivos. "
            f"{result.successful_imports} se importaron exitosamente, "
            f"{result.failed_imports} fallaron y "
            f"{result.duplicate_files} eran duplicados."
        )
        
        # Estadísticas
        self.stats_total.setText(str(result.total_processed))
        self.stats_successful.setText(str(result.successful_imports))
        self.stats_failed.setText(str(result.failed_imports))
        self.stats_duplicates.setText(str(result.duplicate_files))
        self.stats_duration.setText(f"{result.duration_seconds:.1f} segundos")
        
        # Errores si los hay
        if result.errors:
            self.error_label.setVisible(True)
            self.error_log.setVisible(True)
            self.error_log.setPlainText("\n".join(result.errors))
        
        # Emitir señal de completar
        self.import_completed.emit(result)
        
        # Log final
        self.import_log.append("¡Importación finalizada!")
    
    def import_error(self, error_message: str):
        """Maneja errores de importación."""
        self.import_log.append(f"ERROR: {error_message}")
        self.show_error(f"Error durante la importación: {error_message}")
    
    def cancel_import(self):
        """Cancela la importación o cierra el diálogo."""
        if self.current_step == 2 and self.worker_thread:
            # Cancelar importación en progreso
            self.worker_thread.cancel_import()
            self.worker_thread.wait(5000)  # Esperar hasta 5 segundos
            self.import_log.append("Importación cancelada por el usuario")
        
        self.reject()
    
    def show_error(self, message: str):
        """Muestra un mensaje de error."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Error", message)
    
    def closeEvent(self, event):
        """Maneja el cierre del diálogo."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.cancel_import()
            self.worker_thread.wait(3000)
        
        super().closeEvent(event)
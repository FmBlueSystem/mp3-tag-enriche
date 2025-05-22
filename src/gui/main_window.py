"""Main window implementation for the Genre Detector application."""
import os
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QStatusBar, QComboBox, QSplitter, QProgressBar,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon, QColor
from typing import Optional
from pathlib import Path

from .i18n import tr, set_language

from ..core.genre_detector import GenreDetector
from .models.genre_model import GenreModel
from .widgets.control_panel import ControlPanel
from .widgets.backup_panel import BackupPanel
from .widgets.file_results_table_widget import FileResultsTableWidget
from .threads.processing_thread import ProcessingThread
from .style import apply_dark_theme, apply_light_theme

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación."""

    def __init__(self):
        # Limpiar el log al iniciar la app
        try:
            open('app.log', 'w').close()
            logging.info('app.log limpiado al iniciar la aplicación.')
        except Exception as e:
            logging.error(f'No se pudo limpiar app.log al iniciar: {e}')
        logger.info("Iniciando MainWindow de la aplicación Genre Detector.")
        super().__init__()
        self.setWindowTitle(tr("ui.window.title"))
        self.setGeometry(100, 100, 1200, 800)  # Increased width to accommodate side panel
        self.backup_dir: Optional[str] = None
        default_backup_path = '/Volumes/My Passport/Dj compilation 2025/Respados mp3'
        
        try:
            if os.path.exists(default_backup_path):
                if os.path.isdir(default_backup_path):
                    self.backup_dir = default_backup_path
                    logger.info(f"Usando dir de respaldo existente: {self.backup_dir}")
                else:
                    logger.warning(f"Ruta de respaldo '{default_backup_path}' no es un dir. Seleccione manualmente.")
                    self.backup_dir = None
            else:
                os.makedirs(default_backup_path, exist_ok=True)
                self.backup_dir = default_backup_path
                logger.info(f"Dir de respaldo creado: {self.backup_dir}")
        except OSError as e:
            logger.error(f"Error con dir de respaldo '{default_backup_path}': {e}. Seleccione manualmente.")
            self.backup_dir = None

        self.model = GenreModel(backup_dir=self.backup_dir)
        self.is_dark_theme = True
        self.setup_ui()
        self.apply_current_theme()

    def _ensure_model_backup_dir_updated(self):
        """Asegura que el modelo esté inicializado y su directorio de respaldo actualizado."""
        # Comprobación básica para evitar errores si el modelo no está completamente inicializado
        if not hasattr(self, 'model') or self.model is None:
            logger.warning("El modelo no está inicializado. Creando una nueva instancia.")
            # Crear el modelo si no existe
            self.model = GenreModel(backup_dir=self.backup_dir)
        
        # Actualizar el directorio de respaldo del modelo solo si ha cambiado
        if self.model.backup_dir != self.backup_dir:
            self.model.update_backup_dir(self.backup_dir)
            logger.info(f"Directorio de respaldo del modelo actualizado a: {self.backup_dir}")


    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(tr("ui.window.title"))
        self.setMinimumSize(1100, 650)

        central_widget = QWidget()
        central_widget.setAccessibleName(tr("accessibility_main_window"))
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        top_controls = QHBoxLayout()

        self.lang_selector = QComboBox()
        self.lang_selector.addItem("English", "en")
        self.lang_selector.addItem("Español", "es")
        self.lang_selector.setMinimumWidth(120)
        self.lang_selector.currentIndexChanged.connect(self.change_language)
        top_controls.addWidget(self.lang_selector)

        self.theme_btn = QPushButton()
        self.theme_btn.setAccessibleName(tr("accessibility.buttons.theme.name"))
        self.theme_btn.setAccessibleDescription(tr("accessibility.buttons.theme.desc"))
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setToolTip(tr("tooltips.theme"))
        self.theme_btn.setShortcut("Ctrl+T")
        self.theme_btn.setMinimumWidth(64)
        self.update_theme_button()
        top_controls.addStretch()
        top_controls.addWidget(self.theme_btn)
        layout.addLayout(top_controls)

        buttons_layout = QHBoxLayout()

        self.add_files_btn = QPushButton(tr("ui.buttons.add_files"))
        self.add_files_btn.setAccessibleName(tr("accessibility.buttons.add_files.name"))
        self.add_files_btn.setAccessibleDescription(tr("accessibility.buttons.add_files.desc"))
        self.add_files_btn.clicked.connect(self.browse_files)
        self.add_files_btn.setToolTip(tr("tooltips.add_files"))
        self.add_files_btn.setShortcut("Ctrl+O")
        self.add_files_btn.setMinimumWidth(64)
        buttons_layout.addWidget(self.add_files_btn)

        self.add_folder_btn = QPushButton(tr("ui.buttons.add_folder"))
        self.add_folder_btn.setAccessibleName(tr("accessibility.buttons.add_folder.name"))
        self.add_folder_btn.setAccessibleDescription(tr("accessibility.buttons.add_folder.desc"))
        self.add_folder_btn.clicked.connect(self.browse_folder)
        self.add_folder_btn.setToolTip(tr("tooltips.add_folder"))
        self.add_folder_btn.setShortcut("Ctrl+D")
        self.add_folder_btn.setMinimumWidth(64)
        buttons_layout.addWidget(self.add_folder_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Usar el nuevo FileResultsTableWidget
        self.file_results_table = FileResultsTableWidget()
        self.file_results_table.files_added.connect(self.on_files_added)
        layout.addWidget(self.file_results_table, 1)

        side_panel = QWidget()
        side_layout = QVBoxLayout(side_panel)
        side_layout.setSpacing(10)

        self.control_panel = ControlPanel()
        self.control_panel.settings_changed.connect(self.on_settings_changed)
        side_layout.addWidget(self.control_panel)

        self.backup_panel = BackupPanel()
        self.backup_panel.backup_dir_changed.connect(self.on_backup_dir_changed)
        self.backup_panel.select_backup_dir_btn.clicked.connect(self.select_backup_directory)
        if self.backup_dir:
            self.backup_panel.set_backup_dir(self.backup_dir)
        side_layout.addWidget(self.backup_panel)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v/%m archivos - %p%")
        self.progress_bar.hide()
        side_layout.addWidget(self.progress_bar)

        # Botones de proceso
        process_buttons = QHBoxLayout()
        
        self.process_btn = QPushButton(tr("ui.buttons.process"))
        self.process_btn.setAccessibleName(tr("accessibility.buttons.process.name"))
        self.process_btn.setAccessibleDescription(tr("accessibility.buttons.process.desc"))
        self.process_btn.clicked.connect(self.process_files)
        self.process_btn.setEnabled(False)
        self.process_btn.setToolTip(tr("tooltips.process"))
        self.process_btn.setShortcut("Ctrl+P")
        self.process_btn.setMinimumWidth(100)
        process_buttons.addWidget(self.process_btn)

        self.cancel_btn = QPushButton(tr("ui.buttons.cancel"))
        self.cancel_btn.setAccessibleName(tr("accessibility.buttons.cancel"))
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setToolTip(tr("tooltips.cancel"))
        self.cancel_btn.setMinimumWidth(100)
        process_buttons.addWidget(self.cancel_btn)
        
        side_layout.addLayout(process_buttons)

        layout.addWidget(side_panel)

        status_bar = self.statusBar()
        status_bar.setAccessibleName(tr("accessibility.controls.status"))
        status_bar.showMessage(tr("general.status.ready"))

    def select_backup_directory(self):
        """Permite al usuario seleccionar el directorio de respaldo."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            tr("dialogs.select_backup"),
            self.backup_dir or os.path.expanduser("~")
        )
        if dir_path:
            self.backup_dir = dir_path
            self.backup_panel.set_backup_dir(dir_path)
            self._ensure_model_backup_dir_updated()

    def on_files_added(self, count: int):
        """Maneja la adición de archivos a la tabla."""
        if self.file_results_table.rowCount() > 0:
            self.process_btn.setEnabled(True)
        else:
            self.process_btn.setEnabled(False)
        self.statusBar().showMessage(tr("general.status.files_added", {"count": count}), 3000)

    def on_settings_changed(self, settings: dict):
        """Maneja cambios en la configuración."""
        # Aquí podemos implementar lógica adicional cuando cambian las configuraciones
        pass

    def on_backup_dir_changed(self, dir_path: str):
        """Maneja cambios en el directorio de respaldo."""
        self.backup_dir = dir_path
        self._ensure_model_backup_dir_updated()

    def process_files(self):
        logger.info("Intentando iniciar procesamiento de archivos.")
        files_to_process = self.file_results_table.get_all_files()
        logger.info(f"Archivos a procesar: {files_to_process}")
        if not files_to_process:
            logger.warning("No hay archivos para procesar.")
            self.statusBar().showMessage(tr("general.status.no_files"), 3000)
            return
        logger.info("Configurando modelo y UI para procesamiento.")
        self._ensure_model_backup_dir_updated()
        settings = self.control_panel.get_settings()
        logger.info(f"Configuración de procesamiento: {settings}")

        # Configurar UI para procesamiento
        self.progress_bar.setMaximum(len(files_to_process))
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.statusBar().showMessage(tr("general.status.processing"))
        
        for file_path in files_to_process:
            self.file_results_table.update_status(file_path, "Pendiente...")

        # Iniciar thread de procesamiento
        self.processing_thread = ProcessingThread(
            file_paths=files_to_process,
            model=self.model,
            analyze_only=settings['analyze_only'],
            confidence=settings['confidence'],
            max_genres=settings['max_genres'],
            rename_files=settings['rename_files'],
            backup_dir=self.backup_dir
        )
        
        # Conectar señales
        self.processing_thread.finished.connect(self.processing_complete)
        self.processing_thread.file_processed.connect(
            lambda filepath, message, is_error: self.update_table_on_file_processed(filepath, message, is_error)
        )
        self.processing_thread.progress.connect(self.update_progress)
        self.processing_thread.circuit_breaker_opened.connect(self.on_circuit_breaker_opened)
        self.processing_thread.circuit_breaker_closed.connect(self.on_circuit_breaker_closed)
        self.processing_thread.task_state_changed.connect(self.on_task_state_changed)

        # Deshabilitar controles
        self.process_btn.setEnabled(False)
        self.control_panel.setEnabled(False)
        self.backup_panel.select_backup_dir_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        
        logger.info("Iniciando hilo de procesamiento.")
        self.processing_thread.start()

    def update_table_on_file_processed(self, file_path: str, result_message: str, is_error: bool = False):
        logger.info(f"Archivo procesado: {file_path}, Mensaje: {result_message}, Error: {is_error}")
        try:
            if not isinstance(file_path, str):
                logger.error(f"TypeError: file_path debe ser str, no {type(file_path)}")
                return
            if not isinstance(result_message, str):
                logger.error(f"TypeError: result_message debe ser str, no {type(result_message)}")
                result_message = str(result_message)
            
            status = "Error" if is_error else "Completado"
            logger.debug(f"Actualizando tabla para {file_path}: estado={status}, mensaje={result_message}")
            
            self.file_results_table.update_status(file_path, status)
            self.file_results_table.update_result(file_path, result_message, is_error)
        except Exception as e:
            logger.error(f"Error al actualizar tabla GUI: {str(e)}", exc_info=True)


    def update_progress(self, message: str):
        """Actualiza la barra de progreso y mensajes de estado."""
        if "Procesado:" in message:
            try:
                parts = message.split(":")
                if len(parts) != 2:
                    logger.warning(f"Formato de mensaje incorrecto: {message}")
                    return
                    
                numbers = parts[1].strip().split("/")
                if len(numbers) != 2:
                    logger.warning(f"Formato de números incorrecto: {parts[1]}")
                    return
                    
                try:
                    current = int(numbers[0].strip())
                    total = int(numbers[1].strip())
                    self.progress_bar.setValue(current)
                except ValueError:
                    logger.warning(f"No se pudieron convertir a números: {numbers}")
                    return
                    
            except Exception as e:
                logger.error(f"Error parseando mensaje de progreso: {message} - {str(e)}")
        
    def on_circuit_breaker_opened(self):
        """Maneja la apertura del circuit breaker."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(tr("dialogs.circuit_breaker.title"))
        msg.setText(tr("dialogs.circuit_breaker.opened"))
        msg.setInformativeText(tr("dialogs.circuit_breaker.info"))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
        
    def on_circuit_breaker_closed(self):
        """Maneja el cierre del circuit breaker."""
        self.statusBar().showMessage(tr("dialogs.circuit_breaker.closed"), 5000)
        
    def on_task_state_changed(self, task_id: str, state: str):
        """Actualiza la UI según el estado de las tareas."""
        logger.debug(f"Tarea {task_id} cambió a estado: {state}")

    def cancel_processing(self):
        logger.info("Intentando cancelar procesamiento actual.")
        if hasattr(self, "processing_thread") and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self,
                tr("dialogs.confirm_cancel.title"),
                tr("dialogs.confirm_cancel.message"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                logger.info("Procesamiento cancelado por el usuario.")
                self.processing_thread.stop()
                self.statusBar().showMessage(tr("general.status.cancelled"), 5000)
            else:
                logger.info("El usuario decidió no cancelar el procesamiento.")
        
    def processing_complete(self, results: dict):
        logger.info(f"Procesamiento completado. Resultados: {results}")
        # Obtener contadores del resultado
        successful = results.get("success", 0)
        errors = results.get("errors", 0)
        renamed = results.get("renamed", 0)
        
        # Calcular total basado en archivos procesados
        total = successful + errors
        
        # Log de contadores finales para debugging
        logger.debug(
            f"Contadores finales - "
            f"Total: {total}, "
            f"Exitosos: {successful}, "
            f"Errores: {errors}, "
            f"Renombrados: {renamed}"
        )

        # Reactivar controles
        self.process_btn.setEnabled(True)
        self.control_panel.setEnabled(True)
        self.backup_panel.select_backup_dir_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.hide()

        if total == 0:
            self.statusBar().showMessage(tr("general.status.no_selection"), 7000)
        elif errors == 0:
            self.statusBar().showMessage(
                tr("general.status.complete.success", {
                    "success": successful,
                    "renamed": renamed
                }),
                7000
            )
        else:
            QMessageBox.warning(
                self,
                tr("dialogs.processing_errors.title"),
                tr("general.status.complete.with_errors", {
                    "success": successful,
                    "errors": errors,
                    "renamed": renamed
                })
            )
            
        logger.info(f"Procesamiento GUI completado. Total: {total}, Exitosos: {successful}, Errores: {errors}, Renombrados: {renamed}")

    def browse_files(self):
        logger.info("Abriendo diálogo para seleccionar archivos MP3.")
        files, _ = QFileDialog.getOpenFileNames(
            self,
            tr("dialogs.select_files"),
            os.path.expanduser("~"),
            tr("ui.filters.mp3")
        )
        if files:
            logger.info(f"Archivos seleccionados: {files}")
            self.file_results_table.add_files(files)
        else:
            logger.info("No se seleccionaron archivos.")

    def browse_folder(self):
        logger.info("Abriendo diálogo para seleccionar carpeta.")
        folder = QFileDialog.getExistingDirectory(
            self,
            tr("dialogs.select_folder"),
            os.path.expanduser("~")
        )
        if folder:
            logger.info(f"Carpeta seleccionada: {folder}")
            self.file_results_table.add_folder(folder)
        else:
            logger.info("No se seleccionó carpeta.")

    def toggle_theme(self):
        """Alterna entre tema claro y oscuro."""
        self.is_dark_theme = not self.is_dark_theme
        self.apply_current_theme()
        self.update_theme_button()
        theme_key = "ui.theme.dark.name" if self.is_dark_theme else "ui.theme.light.name"
        theme_name = tr(theme_key)
        logger.info(f"Theme changed to {theme_name} mode")
        self.statusBar().showMessage(tr("ui.theme.changed", {"mode": theme_name}), 2000)

    def change_language(self, index: int):
        """Change the application language."""
        lang_code = self.lang_selector.itemData(index)
        set_language(lang_code)
        # Update all UI text
        self.setWindowTitle(tr("ui.window.title"))
        self.add_files_btn.setText(tr("ui.buttons.add_files"))
        self.add_folder_btn.setText(tr("ui.buttons.add_folder"))
        self.process_btn.setText(tr("ui.buttons.process"))
        self.update_theme_button()
        # Update accessibility text
        central_widget = self.centralWidget()
        central_widget.setAccessibleName(tr("accessibility.main_window"))
        self.theme_btn.setAccessibleName(tr("accessibility.buttons.theme.name"))
        self.theme_btn.setAccessibleDescription(tr("accessibility.buttons.theme.desc"))
        self.add_files_btn.setAccessibleName(tr("accessibility.buttons.add_files.name"))
        self.add_files_btn.setAccessibleDescription(tr("accessibility.buttons.add_files.desc"))
        self.add_folder_btn.setAccessibleName(tr("accessibility.buttons.add_folder.name"))
        self.add_folder_btn.setAccessibleDescription(tr("accessibility.buttons.add_folder.desc"))
        self.process_btn.setAccessibleName(tr("accessibility.buttons.process.name"))
        self.process_btn.setAccessibleDescription(tr("accessibility.buttons.process.desc"))
        # Update tooltips
        self.theme_btn.setToolTip(tr("tooltips.theme"))
        self.add_files_btn.setToolTip(tr("tooltips.add_files"))
        self.add_folder_btn.setToolTip(tr("tooltips.add_folder"))
        self.process_btn.setToolTip(tr("tooltips.process"))
        # Update status bar
        self.statusBar().showMessage(tr("general.status.ready"))

    def apply_current_theme(self):
        """Aplica el tema actual (claro u oscuro)."""
        if self.is_dark_theme:
            apply_dark_theme(self)
        else:
            apply_light_theme(self)

    def update_theme_button(self):
        """Actualiza el texto e ícono del botón de tema."""
        if self.is_dark_theme:
            self.theme_btn.setText(tr("ui.theme.light.label"))
        else:
            self.theme_btn.setText(tr("ui.theme.dark.label"))

    def closeEvent(self, event):
        logger.info("Cerrando la ventana principal. Deteniendo hilos si es necesario.")
        if hasattr(self, "processing_thread") and self.processing_thread is not None:
            if self.processing_thread.isRunning():
                logger.info("Deteniendo hilo de procesamiento antes de cerrar.")
                self.processing_thread.stop()
                self.processing_thread.quit()
                self.processing_thread.wait()
        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        # Eliminar la carga automática de la carpeta y el procesamiento
        # (No hacer nada especial al iniciar)

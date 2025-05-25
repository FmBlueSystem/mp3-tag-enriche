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

from qt_material import apply_stylesheet # Importar qt-material

from .i18n import tr, set_language

from ..core.genre_detector import GenreDetector
from ..core.database.db_manager import DBManager # Importar DBManager
from ..core.rule_engine import RuleEngine # Importar RuleEngine
from ..core.folder_organizer import FolderOrganizer # Importar FolderOrganizer

from .models.genre_model import GenreModel
from .widgets.control_panel import ControlPanel
from .widgets.backup_panel import BackupPanel
from .widgets.file_results_table_widget import FileResultsTableWidget
from .widgets.memory_indicator import MemoryIndicator
from .widgets.cpu_indicator import CPUIndicator
from .threads.processing_thread import ProcessingThread
# from .style import apply_dark_theme, apply_light_theme # Comentada
# from .style import ThemeManager # Comentada si existe

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
        
        # Aplicar tema de qt-material
        apply_stylesheet(self, theme='dark_blue.xml')

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

        # Inicializar DBManager aquí y pasarlo a los componentes que lo necesiten
        self.db_manager = DBManager()
        self.model = GenreModel(backup_dir=self.backup_dir, db_manager=self.db_manager) # Pasar db_manager al modelo
        self.rule_engine = RuleEngine(self.db_manager) # Pasar db_manager posicionalmente
        self.folder_organizer = FolderOrganizer(db_manager=self.db_manager) # Inicializar FolderOrganizer

        # self.is_dark_theme = True # Comentado - qt-material maneja el tema
        self.setup_ui()
        # self.apply_current_theme() # Comentado - qt-material maneja el tema

    def _ensure_model_backup_dir_updated(self):
        """Asegura que el modelo esté inicializado y su directorio de respaldo actualizado."""
        # Comprobación básica para evitar errores si el modelo no está completamente inicializado
        if not hasattr(self, 'model') or self.model is None:
            logger.warning("El modelo no está inicializado. Creando una nueva instancia.")
            # Crear el modelo si no existe, pasando el db_manager
            self.model = GenreModel(backup_dir=self.backup_dir, db_manager=self.db_manager)
        
        # Actualizar el directorio de respaldo del modelo solo si ha cambiado
        if self.model.backup_dir != self.backup_dir:
            self.model.update_backup_dir(self.backup_dir)
            logger.info(f"Directorio de respaldo del modelo actualizado a: {self.backup_dir}")
        
        # Asegurar que el db_manager del modelo sea el mismo
        if self.model.db_manager != self.db_manager:
            self.model.db_manager = self.db_manager
            logger.info("DBManager del modelo actualizado.")


    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(tr("ui.window.title"))
        self.setMinimumSize(1200, 700)  # Aumentar tamaño mínimo

        central_widget = QWidget()
        central_widget.setAccessibleName(tr("accessibility_main_window"))
        self.setCentralWidget(central_widget)

        # Layout principal horizontal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Crear splitter principal horizontal
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(6)
        main_splitter.setChildrenCollapsible(False)

        # === PANEL IZQUIERDO: Área principal ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Barra superior con indicadores y controles
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        # Selector de idioma
        self.lang_selector = QComboBox()
        self.lang_selector.addItem("English", "en")
        self.lang_selector.addItem("Español", "es")
        self.lang_selector.setMinimumWidth(120)
        self.lang_selector.setMaximumWidth(150)
        self.lang_selector.currentIndexChanged.connect(self.change_language)
        top_bar.addWidget(self.lang_selector)

        # Separador visual
        top_bar.addSpacing(20)

        # Indicadores de sistema
        indicators_layout = QHBoxLayout()
        indicators_layout.setSpacing(15)

        self.memory_indicator = MemoryIndicator()
        self.memory_indicator.memory_critical.connect(self.on_memory_critical)
        self.memory_indicator.memory_high.connect(self.on_memory_high)
        self.memory_indicator.memory_normal.connect(self.on_memory_normal)
        indicators_layout.addWidget(self.memory_indicator)

        self.cpu_indicator = CPUIndicator()
        self.cpu_indicator.cpu_critical.connect(self.on_cpu_critical)
        self.cpu_indicator.cpu_high.connect(self.on_cpu_high)
        self.cpu_indicator.cpu_normal.connect(self.on_cpu_normal)
        indicators_layout.addWidget(self.cpu_indicator)

        top_bar.addLayout(indicators_layout)
        top_bar.addStretch()  # Empujar botón tema a la derecha

        # Botón de tema
        self.theme_btn = QPushButton()
        self.theme_btn.setAccessibleName(tr("accessibility.buttons.theme.name"))
        self.theme_btn.setAccessibleDescription(tr("accessibility.buttons.theme.desc"))
        # self.theme_btn.clicked.connect(self.toggle_theme) # Comentado
        self.theme_btn.setToolTip(tr("tooltips.theme"))
        self.theme_btn.setShortcut("Ctrl+T")
        self.theme_btn.setMinimumWidth(100)
        self.theme_btn.setMaximumWidth(120)
        # self.update_theme_button() # Comentado
        self.theme_btn.setVisible(False) # Ocultar el botón de tema por ahora
        top_bar.addWidget(self.theme_btn)

        left_layout.addLayout(top_bar)

        # Botones de archivos
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.add_files_btn = QPushButton(tr("ui.buttons.add_files"))
        self.add_files_btn.setAccessibleName(tr("accessibility.buttons.add_files.name"))
        self.add_files_btn.setAccessibleDescription(tr("accessibility.buttons.add_files.desc"))
        self.add_files_btn.clicked.connect(self.browse_files)
        self.add_files_btn.setToolTip(tr("tooltips.add_files"))
        self.add_files_btn.setShortcut("Ctrl+O")
        self.add_files_btn.setMinimumHeight(40)
        buttons_layout.addWidget(self.add_files_btn)

        self.add_folder_btn = QPushButton(tr("ui.buttons.add_folder"))
        self.add_folder_btn.setAccessibleName(tr("accessibility.buttons.add_folder.name"))
        self.add_folder_btn.setAccessibleDescription(tr("accessibility.buttons.add_folder.desc"))
        self.add_folder_btn.clicked.connect(self.browse_folder)
        self.add_folder_btn.setToolTip(tr("tooltips.add_folder"))
        self.add_folder_btn.setShortcut("Ctrl+D")
        self.add_folder_btn.setMinimumHeight(40)
        buttons_layout.addWidget(self.add_folder_btn)

        buttons_layout.addStretch()  # Empujar botones hacia la izquierda
        left_layout.addLayout(buttons_layout)

        # Tabla de archivos (ocupa la mayor parte del espacio)
        self.file_results_table = FileResultsTableWidget()
        self.file_results_table.files_added.connect(self.on_files_added)
        left_layout.addWidget(self.file_results_table, 1)  # Factor de estiramiento 1

        # === PANEL DERECHO: Panel de control ===
        right_panel = QWidget()
        right_panel.setMaximumWidth(350)  # Limitar ancho del panel derecho
        right_panel.setMinimumWidth(280)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(12)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Panel de control
        self.control_panel = ControlPanel()
        self.control_panel.settings_changed.connect(self.on_settings_changed)
        right_layout.addWidget(self.control_panel)

        # Panel de respaldo
        self.backup_panel = BackupPanel()
        self.backup_panel.backup_dir_changed.connect(self.on_backup_dir_changed)
        self.backup_panel.select_backup_dir_btn.clicked.connect(self.select_backup_directory)
        if self.backup_dir:
            self.backup_panel.set_backup_dir(self.backup_dir)
        right_layout.addWidget(self.backup_panel)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v/%m archivos - %p%")
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.hide()
        right_layout.addWidget(self.progress_bar)

        # Espaciador flexible
        right_layout.addStretch()

        # Botones de proceso en la parte inferior
        process_buttons = QVBoxLayout()
        process_buttons.setSpacing(8)
        
        self.process_btn = QPushButton(tr("ui.buttons.process"))
        self.process_btn.setAccessibleName(tr("accessibility.buttons.process.name"))
        self.process_btn.setAccessibleDescription(tr("accessibility.buttons.process.desc"))
        self.process_btn.clicked.connect(self.process_files)
        self.process_btn.setEnabled(False)
        self.process_btn.setToolTip(tr("tooltips.process"))
        self.process_btn.setShortcut("Ctrl+P")
        self.process_btn.setMinimumHeight(45)
        process_buttons.addWidget(self.process_btn)

        self.cancel_btn = QPushButton(tr("ui.buttons.cancel"))
        self.cancel_btn.setAccessibleName(tr("accessibility.buttons.cancel"))
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setToolTip(tr("tooltips.cancel"))
        self.cancel_btn.setMinimumHeight(35)
        process_buttons.addWidget(self.cancel_btn)
        
        right_layout.addLayout(process_buttons)

        # Agregar paneles al splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        
        # Configurar proporciones del splitter (70% izquierda, 30% derecha)
        main_splitter.setSizes([800, 350])
        main_splitter.setStretchFactor(0, 1)  # Panel izquierdo se estira
        main_splitter.setStretchFactor(1, 0)  # Panel derecho mantiene tamaño fijo

        # Agregar splitter al layout principal
        main_layout.addWidget(main_splitter)

        # Barra de estado
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
            confidence=settings['confidence'],
            max_genres=settings['max_genres'],
            rename_files=settings['rename_files'],
            backup_dir=self.backup_dir,
            db_manager=self.db_manager, # Pasar DBManager
            rule_engine=self.rule_engine, # Pasar RuleEngine
            folder_organizer=self.folder_organizer, # Pasar FolderOrganizer
            organize_files=settings['organize_files'] # Nueva opción para organizar
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
        # **NUEVO: Configurar indicadores de sistema para modo procesamiento**
        self.memory_indicator.set_processing_mode(True)
        self.cpu_indicator.set_processing_mode(True)

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

        # **NUEVO: Reestablecer indicadores de sistema a modo normal**
        self.memory_indicator.set_processing_mode(False)
        self.cpu_indicator.set_processing_mode(False)

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
        """Browse for a folder to add to the file list."""
        # Asegurar que el modelo esté actualizado antes de cualquier operación
        self._ensure_model_backup_dir_updated() 

        folder_path = QFileDialog.getExistingDirectory(
            self, 
            tr("ui.dialogs.select_folder"), 
            str(Path.home() / "Music") # Directorio inicial más genérico
        )
        if folder_path:
            self.file_results_table.add_folder(folder_path)
            logger.info(f"Carpeta añadida: {folder_path}")

    def change_language(self, index: int):
        """Change the application language."""
        lang_code = self.lang_selector.itemData(index)
        set_language(lang_code)
        # Update all UI text
        self.setWindowTitle(tr("ui.window.title"))
        self.add_files_btn.setText(tr("ui.buttons.add_files"))
        self.add_folder_btn.setText(tr("ui.buttons.add_folder"))
        self.process_btn.setText(tr("ui.buttons.process"))
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
        self.theme_btn.setIcon(QIcon.fromTheme("weather-clear-night") if self.is_dark_theme else QIcon.fromTheme("weather-sunny"))
        self.theme_btn.setText(tr("ui.buttons.theme.light") if self.is_dark_theme else tr("ui.buttons.theme.dark"))

    def closeEvent(self, event):
        """Handle the close event of the window."""
        logger.info("Cerrando MainWindow.")
        if hasattr(self, 'processing_thread') and self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(self,
                                         tr("ui.dialogs.confirm_exit.title"),
                                         tr("ui.dialogs.confirm_exit.message"),
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.cancel_processing() # Intenta cancelar de forma segura
                # Espera un poco para que el hilo termine si es posible, pero no indefinidamente
                if self.processing_thread.wait(3000): # Espera 3 segundos
                    logger.info("Hilo de procesamiento terminado correctamente antes de cerrar.")
                else:
                    logger.warning("Hilo de procesamiento no terminó a tiempo, forzando cierre.")
                event.accept()
            else:
                event.ignore()
                return
        
        # Guardar estado de la base de datos antes de cerrar, si es necesario
        if hasattr(self, 'db_manager') and self.db_manager:
            logger.info("Cerrando conexión con la base de datos.")
            self.db_manager.close() # Asegúrate de que este método exista y haga lo necesario

        # Guardar la configuración de idioma
        if hasattr(self, 'lang_selector'):
            current_lang_code = self.lang_selector.currentData()
            # Aquí podrías guardar current_lang_code en un archivo de configuración
            logger.info(f"Idioma actual al cerrar: {current_lang_code}")

        super().closeEvent(event)

    def showEvent(self, event):
        """Cargar el idioma al mostrar la ventana."""
        # Aquí podrías cargar el idioma desde un archivo de configuración
        # y establecerlo en self.lang_selector
        # Por ahora, establecemos un idioma por defecto si es necesario
        # (asumiendo que ya se maneja en setup_ui o __init__)
        super().showEvent(event)
        # Ejemplo: si quieres forzar un idioma al inicio desde una config:
        # saved_lang = self.config.get("language", "en") # Suponiendo que tienes un self.config
        # index = self.lang_selector.findData(saved_lang)
        # if index >= 0:
        #     self.lang_selector.setCurrentIndex(index)
        # else:
        #     self.lang_selector.setCurrentIndex(self.lang_selector.findData("en")) # Fallback a inglés

    def on_memory_critical(self):
        self.statusBar().showMessage(tr("status.memory.critical"), 5000)
        self.statusBar().setStyleSheet("background-color: red; color: white;")

    def on_memory_high(self):
        self.statusBar().showMessage(tr("status.memory.high"), 3000)
        self.statusBar().setStyleSheet("background-color: orange; color: black;")

    def on_memory_normal(self):
        # Limpiar el mensaje y el estilo si es necesario, o dejar que se borre solo
        # self.statusBar().clearMessage()
        self.statusBar().setStyleSheet("") # Restablecer estilo de la barra de estado
    
    def on_memory_warning(self, message: str):
        QMessageBox.warning(self, tr("ui.dialogs.memory_warning.title"), message)

    def on_cpu_critical(self):
        self.statusBar().showMessage(tr("status.cpu.critical"), 5000)
        # Actualizar estilo si es diferente del de memoria crítica para distinguirlos
        self.statusBar().setStyleSheet("background-color: darkred; color: white;") 

    def on_cpu_high(self):
        self.statusBar().showMessage(tr("status.cpu.high"), 3000)
        self.statusBar().setStyleSheet("background-color: darkorange; color: black;")

    def on_cpu_normal(self):
        # self.statusBar().clearMessage()
        self.statusBar().setStyleSheet("") # Restablecer estilo

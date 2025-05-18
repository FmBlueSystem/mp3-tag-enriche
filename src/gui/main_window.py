"""Main window implementation for the Genre Detector application."""
from pathlib import Path
import os
import re
import time
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QProgressBar, QStatusBar, QListWidget,
    QCheckBox, QSlider, QSpinBox
)
from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtGui import QDropEvent, QDragEnterEvent, QFont
from typing import Optional
import logging

from ..core.genre_detector import GenreDetector
from ..core.file_handler import Mp3FileHandler
from ..core.music_apis import MusicBrainzAPI
from src.gui.style import apply_dark_theme

logger = logging.getLogger(__name__)

# MODELO: Encapsula la lógica de negocio y datos
class GenreModel:
    def __init__(self, backup_dir: Optional[str] = None):
        # Crear primero el file_handler con el backup_dir
        file_handler_instance = Mp3FileHandler(backup_dir=backup_dir)
        # Pasar el file_handler al GenreDetector
        self.detector = GenreDetector(apis=[MusicBrainzAPI()], verbose=True, file_handler=file_handler_instance)
        self.min_confidence = 0.2
        self.max_api_tags = 100
        self.rename_after_update = True
        self.spam_terms = [
            "http", "fix", "tag", "mess", "error", "todo", "check", 
            "wrong", "unknown", "unclassifiable", "other", "others", 
            "delete", "seen live", "favorites", "favourite", "test", 
            "misc", "checked", "need", "spotify", "lastfm", "indy", 
            "artist", "artists", "video", "title"
        ]
        
    def filter_noise_genres(self, genres_dict):
        """Filtra géneros ruidosos o irrelevantes.
        
        Args:
            genres_dict: Diccionario de géneros con sus valores de confianza
            
        Returns:
            Diccionario filtrado de géneros
        """
        if not genres_dict:
            return {}
            
        filtered = {}
        
        for genre, conf in genres_dict.items():
            # Verificar longitud y contenido
            if (len(genre) < 30 and  # No demasiado largo
                not any(term in genre.lower() for term in self.spam_terms) and  # Sin términos de spam
                len(genre.strip()) > 1 and  # No demasiado corto
                not genre.isdigit() and  # No solo dígitos
                not all(c in "!@#$%^&*()[]{};:,./<>?\\|`~-=_+" for c in genre)):  # No solo símbolos
                filtered[genre] = conf
        
        return filtered

    def analyze(self, filepath):
        try:
            # Verificación exhaustiva para archivos, especialmente en volúmenes externos
            exists = False
            error_msg = ""
            
            # Intentar múltiples métodos para verificar la existencia del archivo
            try:
                # Método 1: Usando Path
                path_obj = Path(filepath)
                if path_obj.exists():
                    exists = True
            except Exception as e:
                error_msg = f"Error con Path.exists(): {str(e)}"
            
            # Método 2: Usando os.path si el método 1 falló
            if not exists:
                try:
                    if os.path.exists(filepath):
                        exists = True
                    else:
                        error_msg = f"os.path.exists() reporta que el archivo no existe"
                except Exception as e:
                    error_msg += f", Error con os.path.exists(): {str(e)}"
            
            # Método 3: Intentar abrir el archivo directamente
            if not exists:
                try:
                    with open(filepath, 'rb') as f:
                        # Si llegamos aquí, el archivo existe y se puede leer
                        exists = True
                except Exception as e:
                    error_msg += f", Error al intentar abrir archivo: {str(e)}"
            
            if not exists:
                return {"error": f"Archivo inaccesible: {filepath}. {error_msg}"}
            
            # Verificar si es un MP3 válido
            if not self.detector.file_handler.is_valid_mp3(filepath):
                return {"error": f"Archivo MP3 inválido: {filepath}"}
                
            # Proceder con el análisis
            result = self.detector.analyze_file(filepath)
            
            # Filtrar etiquetas de género para resultados más limpios
            if "detected_genres" in result:
                # Usar la función dedicada para filtrar géneros
                filtered_genres = self.filter_noise_genres(result["detected_genres"])
                
                # Tomar solo los más relevantes ordenados por confianza
                sorted_genres = dict(sorted(
                    filtered_genres.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:self.max_api_tags])
                
                result["detected_genres"] = sorted_genres
            
            return result
        except Exception as e:
            return {"error": f"Error al analizar: {str(e)}"}

    def process(self, filepath, confidence, max_genres):
        try:
            # Verificación exhaustiva para archivos, especialmente en volúmenes externos
            exists = False
            error_msg = ""
            
            # Intentar múltiples métodos para verificar la existencia del archivo
            try:
                # Método 1: Usando Path
                path_obj = Path(filepath)
                if path_obj.exists():
                    exists = True
            except Exception as e:
                error_msg = f"Error con Path.exists(): {str(e)}"
            
            # Método 2: Usando os.path si el método 1 falló
            if not exists:
                try:
                    if os.path.exists(filepath):
                        exists = True
                    else:
                        error_msg = f"os.path.exists() reporta que el archivo no existe"
                except Exception as e:
                    error_msg += f", Error con os.path.exists(): {str(e)}"
            
            # Método 3: Intentar abrir el archivo directamente
            if not exists:
                try:
                    with open(filepath, 'rb') as f:
                        # Si llegamos aquí, el archivo existe y se puede leer
                        exists = True
                except Exception as e:
                    error_msg += f", Error al intentar abrir archivo: {str(e)}"
            
            if not exists:
                return {"error": f"Archivo inaccesible: {filepath}. {error_msg}", "written": False}
                
            if not self.detector.file_handler.is_valid_mp3(filepath):
                return {"error": f"Archivo MP3 inválido: {filepath}", "written": False}
            
            # Detectar primero para obtener información de géneros
            analysis = self.detector.analyze_file(filepath)
            
            # Extraer géneros con confianza suficiente
            genres = analysis.get("detected_genres", {})
            
            # Filtrar géneros ruidosos o irrelevantes
            filtered_genres = self.filter_noise_genres(genres)
            
            # Verificar si quedan géneros después del filtrado estricto
            if not filtered_genres:
                # Si no hay géneros filtrados, hacer filtrado menos estricto
                for genre, conf in genres.items():
                    if len(genre) < 50 and len(genre.strip()) > 1:
                        filtered_genres[genre] = conf
            
            # Si aún no hay géneros, reportar el problema
            if not filtered_genres:
                return {
                    "error": f"No se detectaron géneros válidos para este archivo",
                    "written": False,
                    "detected_genres": genres
                }
            
            # Usar un umbral de confianza adaptativo
            adaptive_confidence = confidence
            if not any(conf >= confidence for conf in filtered_genres.values()):
                # Usar un umbral adaptativo (mínimo configurado o 20% menos que el umbral original)
                adaptive_confidence = min(self.min_confidence, max(0.1, confidence - 0.2))
            
            selected_genres = []
            for genre, conf in sorted(filtered_genres.items(), key=lambda x: x[1], reverse=True):
                if conf >= adaptive_confidence:
                    # Preservar géneros actuales que puedan ser válidos
                    # Normalizar género para evitar duplicados con diferente formato (ej: "Rock" vs "rock")
                    normalized = genre[0].upper() + genre[1:] if genre else ""
                    
                    # Verificar duplicados de manera más inteligente comparando en minúsculas
                    if normalized.lower() not in [g.lower() for g in selected_genres]:
                        selected_genres.append(normalized)
                        if len(selected_genres) >= max_genres:
                            break
            
            if not selected_genres:
                # Si aún no hay géneros seleccionados, tomar el género con mayor confianza
                if filtered_genres:
                    top_genre = max(filtered_genres.items(), key=lambda x: x[1])
                    normalized = top_genre[0][0].upper() + top_genre[0][1:] if top_genre[0] else ""
                    selected_genres.append(normalized)
                    adaptive_confidence = top_genre[1]  # Usar la confianza de este género como umbral
                else:
                    return {
                        "error": f"No se detectaron géneros con confianza suficiente",
                        "written": False,
                        "detected_genres": filtered_genres,
                        "threshold_used": adaptive_confidence
                    }
            
            # Escribir géneros con manejo de errores mejorado
            try:
                # Intentar hacer una copia de seguridad primero, ANTES de cualquier escritura
                backup_success = self.detector.file_handler._create_backup(filepath)
                if not backup_success:
                    # Si la copia de seguridad falla, seguir pero notificar
                    # Idealmente, esto se registraría o se mostraría al usuario de alguna manera.
                    logger.warning(f"Advertencia: No se pudo crear copia de seguridad para {filepath}")
                
                # Si se va a renombrar, rename_file_by_genre se encarga de todos los tags y el nombre.
                if self.rename_after_update:
                    current_filepath_for_rename = filepath 
                    rename_result = self.detector.file_handler.rename_file_by_genre(
                        current_filepath_for_rename, 
                        genres_to_write=selected_genres
                    )
                    # Actualizar el resultado con la información de rename_result
                    current_error = rename_result.get("error") # Obtener el error potencial
                    result = {
                        "written": rename_result.get("success", False),
                        "renamed": rename_result.get("success", False) and rename_result.get("new_path") != filepath,
                        "new_filepath": rename_result.get("new_path"),
                        "message": rename_result.get("message", ""),
                        # Solo incluir la clave "error" si current_error no es None
                        # "error": current_error, <--- Se manejará más abajo
                        "current_genre": ";".join(selected_genres) # Reflejar los géneros que intentamos escribir
                    }
                    if current_error:
                        result["error"] = current_error
                    
                    if "tag_update_error" in rename_result:
                         result["tag_update_error"] = rename_result["tag_update_error"]

                else: # Si no se renombra, solo escribir géneros (Artista/Título no se tocan aquí)
                    success = self.detector.file_handler.write_genre(filepath, selected_genres, backup=False) # Backup ya hecho
                    result = {"written": success}
                    if success:
                        time.sleep(0.2)  # Esperar un momento para que el sistema de archivos se actualice
                        info_after_write = self.detector.file_handler.get_file_info(filepath)
                        result["current_genre"] = info_after_write.get("current_genre", "")
                        result["selected_genres"] = selected_genres
                        result["threshold_used"] = adaptive_confidence
                    else:
                        result["error"] = f"Error al escribir géneros en {filepath}"
            
                return result
            except Exception as write_error:
                return {
                    "error": f"Error al escribir en el archivo: {str(write_error)}",
                    "written": False,
                    "selected_genres": selected_genres
                }
                
        except Exception as e:
            return {"error": f"Error al procesar: {str(e)}", "written": False}

# PROCESO: Hilo para tareas asíncronas
class ProcessingThread(QThread):
    progress = Signal(str)
    finished = Signal(dict)
    file_processed = Signal(str, str) # file path, status (e.g., "Success", "Error: ...")

    def __init__(self, file_paths, model, analyze_only=True, confidence=0.3, max_genres=3, rename_files=False, backup_dir: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.analyze_only = analyze_only
        self.confidence = confidence
        self.max_genres = max_genres
        self.rename_files = rename_files
        self.backup_dir = backup_dir # Este es el backup_dir de MainWindow
        self.model = model # Este es el GenreModel

        # Actualizar el backup_dir del file_handler existente en el modelo
        if self.model and self.model.detector and self.model.detector.file_handler:
            if hasattr(self.model.detector.file_handler, 'set_backup_dir'):
                self.model.detector.file_handler.set_backup_dir(self.backup_dir)
                logger.info(f"ProcessingThread: backup_dir en Mp3FileHandler (modelo) configurado/actualizado a: {self.backup_dir}")
            else:
                # Fallback si set_backup_dir no existe por alguna razón (no debería pasar)
                logger.warning("ProcessingThread: Mp3FileHandler no tiene set_backup_dir. Recreando con nueva ruta.")
                self.model.detector.file_handler = Mp3FileHandler(backup_dir=self.backup_dir)
        else:
            logger.error("ProcessingThread: No se pudo acceder a model.detector.file_handler para configurar backup_dir.")

    def run(self):
        total_files = len(self.file_paths)
        if total_files == 0:
            self.progress.emit("No hay archivos seleccionados para procesar.")
            self.finished.emit({"total": 0, "success": 0, "errors": 0, "renamed": 0, "details": []})
            return

        processed_count = 0
        success_count = 0
        error_count = 0
        renamed_count = 0
        results_details = []

        for filepath in self.file_paths:
            self.progress.emit(f"Processing {Path(filepath).name}")
            try:
                if self.analyze_only:
                    result = self.model.analyze(filepath)
                else:
                    result = self.model.process(filepath, self.confidence, self.max_genres)
                
                # Comprobar si hay un error real en el resultado
                actual_error = result.get("error")
                if actual_error: # Esto es True si actual_error no es None y no es una cadena vacía
                    error_count += 1
                    logger.error(f"Error al procesar {filepath}: {actual_error}")
                    self.file_processed.emit(filepath, f"Error: {actual_error}")
                elif "written" in result: # Si no hay error, ver si se escribió (caso de no análisis)
                    if result["written"]:
                        success_count += 1
                        # No emitir aquí si el renombrado va a emitir su propio mensaje
                        if not ("renamed" in result and result["renamed"]):
                             self.file_processed.emit(filepath, result.get("message", "Éxito en escritura de metadatos."))
                    else:
                        error_count += 1
                        # Este caso puede ocurrir si written=False pero no hay un result["error"] explícito (ej. write_genre falla silenciosamente)
                        err_msg_write = result.get('error', 'Error desconocido durante escritura de metadatos')
                        logger.error(f"Error al escribir metadatos para {filepath}: {err_msg_write}")
                        self.file_processed.emit(filepath, f"Error al escribir metadatos: {err_msg_write}")
                elif not self.analyze_only: # Caso donde 'written' no está pero no es análisis (inesperado)
                    error_count += 1
                    logger.error(f"Resultado inesperado para {filepath} (ni error ni written): {result}")
                    self.file_processed.emit(filepath, "Error: Resultado inesperado del procesamiento")
                else: # Éxito en el modo 'analyze_only'
                    success_count += 1
                    genres = result.get("detected_genres", {})
                    if genres:
                        genre_str = ", ".join(f"{g} ({c:.2f})" for g, c in 
                                           sorted(genres.items(), key=lambda x: x[1], reverse=True))
                        self.file_processed.emit(filepath, f"Éxito en análisis. Géneros detectados: {genre_str}")
                    else:
                        self.file_processed.emit(filepath, "No se detectaron géneros")
                
                processed_count += 1
                self.progress.emit(f"Procesado: {processed_count}/{total_files} - {os.path.basename(filepath)}")

                if "renamed" in result:                    
                    if result["renamed"]: # Si el renombrado fue exitoso (y hubo cambio)
                        renamed_count += 1
                        new_filepath_val = result.get('new_filepath')
                        # El mensaje de éxito del renombrado ya lo da rename_file_by_genre, no es necesario emitir otro.
                        # self.file_processed.emit(filepath, f"Éxito en renombrado. Renombrado a: {os.path.basename(new_filepath_val)}")
                        if result.get("message"):
                             self.file_processed.emit(filepath, result.get("message"))
                        elif new_filepath_val: # Backup
                             self.file_processed.emit(filepath, f"Renombrado a: {os.path.basename(new_filepath_val)}")

                    elif result.get("success") and result.get("new_path") == filepath: # Tags actualizados, sin renombrado
                        # success_count ya se incrementó si written fue True
                        if result.get("message"):
                            self.file_processed.emit(filepath, result.get("message"))
                        else:
                            self.file_processed.emit(filepath, "Tags actualizados (nombre sin cambios).")
                    else: 
                        # Si 'renamed' es False, o no está, pero SÍ hubo un error específico del renombrado 
                        # (distinto del error general de procesamiento)
                        rename_specific_error = result.get("error") # O la clave que use rename_file_by_genre para sus errores internos
                        if rename_specific_error and not actual_error: # Si no contamos ya este error
                            # No incrementar error_count aquí si el error ya se contó arriba (actual_error)
                            # Esto es para errores que SOLO ocurren en la fase de renombrado Y NO SON el 'actual_error'
                            # del procesamiento general.
                            # El problema es que 'error' es la misma clave.
                            # Lo importante es que el mensaje se emita.
                            self.file_processed.emit(filepath, f"Fallo al renombrar/actualizar tags: {rename_specific_error}")
                        elif not actual_error and not result.get("success"):
                             self.file_processed.emit(filepath, f"Fallo al renombrar/actualizar tags: {result.get('message', 'Razón desconocida')}")

                results_details.append({
                    "filepath": filepath,
                    "written_metadata_success": result.get("written", False),
                    "current_genre": result.get("current_genre", ""),
                    "selected_genres": result.get("selected_genres", []),
                    "threshold_used": result.get("threshold_used", 0.3),
                    "renamed_to": result.get("new_filepath", ""),
                    "error": result.get("error", ""),
                    "rename_error": result.get("error", ""),
                    "rename_message": result.get("message", ""),
                    "detected_genres": result.get("detected_genres", {})
                })
            except Exception as e:
                error_count += 1
                logger.error(f"Error al procesar {filepath}: {str(e)}")
                self.file_processed.emit(filepath, f"Error: {str(e)}")

        # Simular finalización
        # self.progress.emit(f"Completado: {processed_count} archivos procesados.")
        self.finished.emit({
            "total": total_files, 
            "success": success_count, 
            "errors": error_count, 
            "renamed": renamed_count,
            "details": results_details
        })

# CONTROL: Interfaz y eventos
class MainWindow(QMainWindow):
    browse_files_triggered = Signal()
    browse_folder_triggered = Signal()
    process_files_triggered = Signal()

    def __init__(self):
        super().__init__()
        self.mp3_files = []
        self.processing_thread = None
        # Establecer la ruta de backup predeterminada ANTES de inicializar GenreModel
        self.backup_dir_path = "/Volumes/My Passport/Dj compilation 2025/Respados mp3"
        self.model = GenreModel(backup_dir=self.backup_dir_path)
        
        self.setup_ui()
        apply_dark_theme(self)
        
        # Actualizar la etiqueta del directorio de backup después de setup_ui
        if self.backup_dir_path:
            self.backup_dir_label.setText(f"Backup Directory: {self.backup_dir_path}")
        else:
            self.backup_dir_label.setText("Backup Directory: Not Set (Error creating default)")

    def setup_ui(self):
        """Set up the user interface following Material Design guidelines."""
        self.setWindowTitle("Genre Detector - Dark AI")
        self.setMinimumSize(900, 650)
        # Use Segoe UI or Roboto font for Material Design consistency
        font = QFont("Segoe UI", 11)
        self.setFont(font)
        
        # Enable keyboard focus and tab navigation for accessibility
        self.setFocusPolicy(Qt.StrongFocus)
        
        central_widget = QWidget()
        central_widget.setAccessibleName("Main Window")
        self.setCentralWidget(central_widget)
        
        # Use consistent spacing from Material Design (8dp grid)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(16)  # 16dp spacing between sections
        layout.setContentsMargins(16, 16, 16, 16)  # 16dp margins
        # File selection section
        file_section = QWidget()
        file_section.setAccessibleName("File Selection Section")
        file_list_layout = QVBoxLayout(file_section)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)  # 8dp between buttons
        
        add_file_btn = QPushButton("Add Files")
        add_file_btn.setAccessibleName("Add Files Button")
        add_file_btn.setToolTip("Select MP3 files to process")
        add_file_btn.clicked.connect(self.browse_files)
        add_file_btn.setShortcut("Ctrl+O")  # Keyboard shortcut
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.setAccessibleName("Add Folder Button")
        add_folder_btn.setToolTip("Select a folder containing MP3 files")
        add_folder_btn.clicked.connect(self.browse_folder)
        add_folder_btn.setShortcut("Ctrl+Shift+O")  # Keyboard shortcut
        
        button_layout.addWidget(add_file_btn)
        button_layout.addWidget(add_folder_btn)
        button_layout.addStretch()  # Right-align buttons
        file_list_layout.addLayout(button_layout)
        
        # File list with enhanced accessibility
        self.file_list = QListWidget()
        self.file_list.setAccessibleName("File List")
        self.file_list.setAccessibleDescription("List of MP3 files to process")
        self.file_list.setAcceptDrops(True)
        self.file_list.setMinimumHeight(200)
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)  # Allow multiple selection
        self.file_list.setToolTip("Drag and drop MP3 files here or use the buttons above")
        file_list_layout.addWidget(self.file_list)
        
        layout.addWidget(file_section)
        # Options section with improved accessibility
        options_section = QWidget()
        options_section.setAccessibleName("Options Section")
        options_layout = QVBoxLayout(options_section)
        options_layout.setSpacing(16)
        
        # Analysis mode options
        analyze_row = QHBoxLayout()
        analyze_row.setSpacing(16)
        
        self.analyze_only = QCheckBox("Analysis Only")
        self.analyze_only.setAccessibleName("Analysis Only Checkbox")
        self.analyze_only.setToolTip("Only analyze files without making changes")
        self.analyze_only.setChecked(True)
        analyze_row.addWidget(self.analyze_only)
        
        self.rename_files = QCheckBox("Rename Files After Update")
        self.rename_files.setAccessibleName("Rename Files Checkbox")
        self.rename_files.setToolTip("Rename files using format: 'Artist - Title [Genre]'")
        self.rename_files.setChecked(True)
        analyze_row.addWidget(self.rename_files)
        
        analyze_row.addStretch()
        options_layout.addLayout(analyze_row)
        
        # Confidence threshold control with enhanced accessibility
        confidence_row = QHBoxLayout()
        confidence_row.setSpacing(16)
        
        self.confidence_label = QLabel("Confidence Threshold:")
        self.confidence_label.setAccessibleName("Confidence Threshold Label")
        confidence_row.addWidget(self.confidence_label)
        
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setAccessibleName("Confidence Threshold Slider")
        self.confidence_slider.setAccessibleDescription("Set minimum confidence level for genre detection")
        self.confidence_slider.setMinimum(10)
        self.confidence_slider.setMaximum(90)
        self.confidence_slider.setValue(30)
        self.confidence_slider.setTickInterval(10)
        self.confidence_slider.setTickPosition(QSlider.TicksBelow)
        self.confidence_slider.valueChanged.connect(self.update_confidence_label)
        self.confidence_slider.setToolTip("Adjust minimum confidence level for genre detection")
        confidence_row.addWidget(self.confidence_slider)
        
        self.confidence_input = QLabel("0.3")
        self.confidence_input.setAccessibleName("Confidence Value Label")
        confidence_row.addWidget(self.confidence_input)
        
        options_layout.addLayout(confidence_row)
        
        # Maximum genres control with enhanced accessibility
        max_genres_row = QHBoxLayout()
        max_genres_row.setSpacing(16)
        
        self.max_genres_label = QLabel("Max Genres:")
        self.max_genres_label.setAccessibleName("Maximum Genres Label")
        max_genres_row.addWidget(self.max_genres_label)
        
        self.max_genres_spinner = QSpinBox()
        self.max_genres_spinner.setAccessibleName("Maximum Genres Spinner")
        self.max_genres_spinner.setAccessibleDescription("Set maximum number of genres to detect")
        self.max_genres_spinner.setMinimum(1)
        self.max_genres_spinner.setMaximum(10)
        self.max_genres_spinner.setValue(3)
        self.max_genres_spinner.valueChanged.connect(self.update_max_genres_label)
        self.max_genres_spinner.setToolTip("Maximum number of genres to detect per file")
        max_genres_row.addWidget(self.max_genres_spinner)
        
        self.max_genres_input = QLabel("3")
        self.max_genres_input.setAccessibleName("Maximum Genres Value Label")
        max_genres_row.addWidget(self.max_genres_input)
        
        options_layout.addLayout(max_genres_row)
        
        # Backup directory selection
        backup_dir_row = QHBoxLayout()
        backup_dir_row.setSpacing(8) 
        
        self.backup_dir_label = QLabel("Backup Directory: Not Set") # El texto se actualizará en __init__
        self.backup_dir_label.setAccessibleName("Backup Directory Label")
        backup_dir_row.addWidget(self.backup_dir_label, 1) 
        
        self.select_backup_dir_btn = QPushButton("Select Backup Dir")
        self.select_backup_dir_btn.setAccessibleName("Select Backup Directory Button")
        self.select_backup_dir_btn.setToolTip("Select a folder to store backups of modified MP3 files")
        self.select_backup_dir_btn.clicked.connect(self.select_backup_directory)
        backup_dir_row.addWidget(self.select_backup_dir_btn)
        
        options_layout.addLayout(backup_dir_row) # Añadir la fila de backup al layout de opciones

        layout.addWidget(options_section)
        # Process button with enhanced accessibility
        self.process_btn = QPushButton("Process Files")
        self.process_btn.setAccessibleName("Process Files Button")
        self.process_btn.setAccessibleDescription("Start processing the selected files")
        self.process_btn.clicked.connect(self.process_files)
        self.process_btn.setEnabled(False)
        self.process_btn.setToolTip("Process the selected files (Ctrl+P)")
        self.process_btn.setShortcut("Ctrl+P")  # Keyboard shortcut
        layout.addWidget(self.process_btn, 0, Qt.AlignCenter)
        # Progress section with enhanced accessibility
        self.progress_label = QLabel()
        self.progress_label.setAccessibleName("Progress Label")
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)
        
        # Results section with enhanced accessibility
        results_section = QWidget()
        results_section.setAccessibleName("Results Section")
        results_layout = QVBoxLayout(results_section)
        
        # Results list with enhanced accessibility
        self.results_list = QListWidget()
        self.results_list.setAccessibleName("Results List")
        self.results_list.setAccessibleDescription("List of processing results for each file")
        self.results_list.setToolTip("Results of file processing")
        results_layout.addWidget(self.results_list)
        
        layout.addWidget(results_section)
        
        # Status bar with enhanced accessibility
        status_bar = self.statusBar()
        status_bar.setAccessibleName("Status Bar")
        status_bar.showMessage("Ready - Dark AI Mode")
        
    def update_confidence_label(self, value):
        """Actualiza la etiqueta de confianza cuando se mueve el slider."""
        confidence = value / 100
        self.confidence_input.setText(f"{confidence:.1f}")
        
    def update_max_genres_label(self, value):
        """Actualiza la etiqueta de máximo de géneros cuando cambia el spinner."""
        self.max_genres_input.setText(str(value))

    def browse_files(self):
        self.browse_files_triggered.emit()
        """Open file browser for MP3 selection."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select MP3 Files", "", "MP3 Files (*.mp3)"
        )
        if files:
            self.add_files(files)
            
    def browse_folder(self):
        self.browse_folder_triggered.emit()
        """Open folder browser."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.add_folder(folder)
            
    def add_files(self, files):
        """Add MP3 files to the list."""
        for file in files:
            if file.lower().endswith('.mp3'):
                self.mp3_files.append(file)
                self.file_list.addItem(Path(file).name)
        self.process_btn.setEnabled(bool(self.mp3_files))
                
    def add_folder(self, folder):
        """Add all MP3 files from a folder."""
        for file in Path(folder).rglob("*.mp3"):
            self.mp3_files.append(str(file))
            self.file_list.addItem(file.name)
        self.process_btn.setEnabled(bool(self.mp3_files))
            
    def select_backup_directory(self):
        new_backup_dir = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Backup")
        if new_backup_dir:
            self.backup_dir_path = new_backup_dir
            self.backup_dir_label.setText(f"Directorio de Backup: {self.backup_dir_path}")
            logger.info(f"Directorio de backup actualizado por el usuario a: {self.backup_dir_path}")
            # Actualizar también el file_handler en el modelo existente usando set_backup_dir
            if self.model and self.model.detector and self.model.detector.file_handler:
                if hasattr(self.model.detector.file_handler, 'set_backup_dir'):
                    self.model.detector.file_handler.set_backup_dir(self.backup_dir_path)
                    # El log ya lo hará set_backup_dir
                else:
                    logger.error("MainWindow: Mp3FileHandler en el modelo no tiene set_backup_dir.")
            else:
                logger.warning("MainWindow: No se pudo actualizar el backup_dir en el file_handler del modelo porque no existe.")

    def process_files(self):
        self.process_files_triggered.emit()
        self.results_list.clear()
        self.process_btn.setEnabled(False)
        analyze_only = self.analyze_only.isChecked()
        confidence = float(self.confidence_input.text())
        max_genres = int(self.max_genres_input.text())
        rename_files = self.rename_files.isChecked()

        # Pasar el backup_dir_path al ProcessingThread
        self.processing_thread = ProcessingThread(
            self.mp3_files,
            self.model,
            analyze_only=analyze_only,
            confidence=confidence,
            max_genres=max_genres,
            rename_files=rename_files,
            backup_dir=self.backup_dir_path # Pasar la ruta seleccionada
        )
        
        self.processing_thread.progress.connect(self.update_progress)
        self.processing_thread.finished.connect(self.processing_complete)
        self.processing_thread.file_processed.connect(self.on_file_processed)
        self.processing_thread.start()

    def update_progress(self, message):
        """Update progress display."""
        self.progress_label.setText(message)
        self.statusBar().showMessage(message)
        
    def processing_complete(self, results):
        total = results.get("total", 0)
        successful = results.get("success", 0)
        errors = results.get("errors", 0)
        renamed = results.get("renamed", 0)
        
        self.progress_label.clear()
        self.process_btn.setEnabled(True)
        self.analyze_only.setEnabled(True)
        self.rename_files.setEnabled(True)
        self.select_backup_dir_btn.setEnabled(True)

        if total == 0:
            self.statusBar().showMessage("No se seleccionaron archivos para procesar.", 7000)
        elif errors == 0:
            self.statusBar().showMessage(f"Procesamiento completado: {successful} archivo(s) exitoso(s). {renamed} renombrado(s).", 7000)
        else:
            self.statusBar().showMessage(f"Procesamiento finalizado: {successful} exitoso(s), {errors} error(es). {renamed} renombrado(s).", 10000)

        # Actualizar la lista de archivos con los resultados
        results_details = results.get("details", [])
        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            filepath = item.data(Qt.UserRole) # Asumiendo que guardaste el filepath original
            
            found_detail = False
            for detail in results_details:
                if detail["filepath"] == filepath:
                    status_message = "Éxito"
                    if detail.get("error"):
                        status_message = f"Error: {detail['error']}"
                    elif not detail.get("written_metadata_success", False) and not self.analyze_only.isChecked():
                         status_message = "Error: Escritura de metadatos falló"
                    
                    if detail.get("renamed_to"):
                        status_message += f" -> Renombrado a: {os.path.basename(detail['renamed_to'])}"
                        # Actualizar el texto del ítem y su data si fue renombrado
                        item.setText(f"{os.path.basename(detail['renamed_to'])} - {status_message}")
                        item.setData(Qt.UserRole, detail['renamed_to']) # Actualizar al nuevo path
                    else:
                        item.setText(f"{os.path.basename(filepath)} - {status_message}")
                    found_detail = True
                    break
            
            if not found_detail: # Si no está en los detalles, es porque no se procesó (ej. no era mp3)
                 # Podríamos querer obtener un estado más específico si es necesario
                 # item.setText(f"{os.path.basename(filepath)} - No procesado (ver logs)")
                 pass # Mantener el texto actual si no hay detalles, o decidir un mensaje
        
        # Limpiar la lista de mensajes de progreso individuales
        self.results_list.clear()
        # Mostrar resumen en la lista de progreso
        self.results_list.addItem(f"Total de archivos intentados: {total}")
        self.results_list.addItem(f"Operaciones de metadatos exitosas: {successful}")
        self.results_list.addItem(f"Errores durante el proceso: {errors}")
        self.results_list.addItem(f"Archivos renombrados: {renamed}")

        logger.info(f"Procesamiento GUI completado. Total: {total}, Exitosos: {successful}, Errores: {errors}, Renombrados: {renamed}")

    def on_file_processed(self, filepath, status):
        self.results_list.addItem(f"{os.path.basename(filepath)}: {status}")
        self.results_list.scrollToBottom()

    def setup_logging(self):
        # Implementa la lógica para configurar el registro de la aplicación
        pass

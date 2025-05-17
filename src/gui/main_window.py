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

from ..core.genre_detector import GenreDetector
from ..core.file_handler import Mp3FileHandler
from ..core.music_apis import MusicBrainzAPI
from src.gui.style import apply_dark_theme

# MODELO: Encapsula la lógica de negocio y datos
class GenreModel:
    def __init__(self):
        self.detector = GenreDetector([MusicBrainzAPI()], verbose=True)
        # Configurar un backup_dir para garantizar que se creen copias de seguridad
        # Usar la nueva ruta en disco externo
        backup_dir = "/Volumes/My Passport/Dj compilation 2025/Respados mp3"
        self.detector.file_handler = Mp3FileHandler(backup_dir=backup_dir)
        # Establecer un umbral de confianza más bajo para mejorar la detección
        self.min_confidence = 0.2
        # Establecer un límite de etiquetas para filtrar resultados ruidosos
        self.max_api_tags = 100
        # Opción para renombrar archivos después de actualizar géneros
        self.rename_after_update = True
        # Lista de términos a filtrar
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
                # Intentar hacer una copia de seguridad primero
                backup_success = self.detector.file_handler._create_backup(filepath)
                if not backup_success:
                    # Si la copia de seguridad falla, seguir pero notificar
                    print(f"Advertencia: No se pudo crear copia de seguridad para {filepath}")
                
                # Intentar escribir los géneros
                success = self.detector.file_handler.write_genre(filepath, selected_genres, backup=False)
                
                result = {"written": success}
                if success:
                    # Verificar que los cambios se hayan guardado realmente
                    time.sleep(0.2)  # Esperar un momento para que el sistema de archivos se actualice
                    info = self.detector.file_handler.get_file_info(filepath)
                    result["current_genre"] = info.get("current_genre", "")
                    result["selected_genres"] = selected_genres
                    result["threshold_used"] = adaptive_confidence
                    
                    # Renombrar el archivo si está habilitada la opción
                    if self.rename_after_update:
                        rename_result = self.detector.file_handler.rename_file_by_genre(filepath)
                        result["renamed"] = rename_result["success"]
                        if rename_result["success"]:
                            result["new_filepath"] = rename_result["new_path"]
                            result["rename_message"] = rename_result["message"]
                        else:
                            result["rename_error"] = rename_result.get("error", "Error desconocido al renombrar")
                else:
                    result["error"] = "Error al escribir géneros en el archivo"
                    
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
    def __init__(self, file_paths, analyze_only=True, confidence=0.3, max_genres=3, parent=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.analyze_only = analyze_only
        self.confidence = confidence
        self.max_genres = max_genres
        self.model = GenreModel()
    def run(self):
        results = {}
        for filepath in self.file_paths:
            self.progress.emit(f"Processing {Path(filepath).name}")
            try:
                if self.analyze_only:
                    result = self.model.analyze(filepath)
                else:
                    result = self.model.process(filepath, self.confidence, self.max_genres)
                results[filepath] = result
            except Exception as e:
                results[filepath] = {"error": str(e)}
        self.finished.emit(results)

# CONTROL: Interfaz y eventos
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mp3_files = []
        self.processing_thread = None
        self.setup_ui()
        apply_dark_theme(self)
    def setup_ui(self):
        self.setWindowTitle("Genre Detector - Dark AI")
        self.setMinimumSize(900, 650)
        font = QFont("Segoe UI", 11)
        self.setFont(font)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        # File list section
        file_list_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        add_file_btn = QPushButton("Add Files")
        add_file_btn.clicked.connect(self.browse_files)
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.browse_folder)
        button_layout.addWidget(add_file_btn)
        button_layout.addWidget(add_folder_btn)
        file_list_layout.addLayout(button_layout)
        self.file_list = QListWidget()
        self.file_list.setAcceptDrops(True)
        self.file_list.setMinimumHeight(200)
        file_list_layout.addWidget(self.file_list)
        layout.addLayout(file_list_layout)
        # Options
        options_layout = QVBoxLayout()
        
        # Modo de análisis
        analyze_row = QHBoxLayout()
        self.analyze_only = QCheckBox("Analysis Only")
        self.analyze_only.setChecked(True)
        analyze_row.addWidget(self.analyze_only)
        
        # Opción para renombrar archivos
        self.rename_files = QCheckBox("Rename Files After Update")
        self.rename_files.setChecked(True)
        self.rename_files.setToolTip("Renombra los archivos según el formato 'Artista - Título [Género]'")
        analyze_row.addWidget(self.rename_files)
        
        options_layout.addLayout(analyze_row)
        
        # Control de confianza
        confidence_row = QHBoxLayout()
        self.confidence_label = QLabel("Confidence Threshold:")
        confidence_row.addWidget(self.confidence_label)
        
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setMinimum(10)
        self.confidence_slider.setMaximum(90)
        self.confidence_slider.setValue(30)
        self.confidence_slider.setTickInterval(10)
        self.confidence_slider.setTickPosition(QSlider.TicksBelow)
        self.confidence_slider.valueChanged.connect(self.update_confidence_label)
        confidence_row.addWidget(self.confidence_slider)
        
        self.confidence_input = QLabel("0.3")
        confidence_row.addWidget(self.confidence_input)
        options_layout.addLayout(confidence_row)
        
        # Control de máx géneros
        max_genres_row = QHBoxLayout()
        self.max_genres_label = QLabel("Max Genres:")
        max_genres_row.addWidget(self.max_genres_label)
        
        self.max_genres_spinner = QSpinBox()
        self.max_genres_spinner.setMinimum(1)
        self.max_genres_spinner.setMaximum(10)
        self.max_genres_spinner.setValue(3)
        self.max_genres_spinner.valueChanged.connect(self.update_max_genres_label)
        max_genres_row.addWidget(self.max_genres_spinner)
        
        self.max_genres_input = QLabel("3")
        max_genres_row.addWidget(self.max_genres_input)
        options_layout.addLayout(max_genres_row)
        
        layout.addLayout(options_layout)
        # Process button
        self.process_btn = QPushButton("Process Files")
        self.process_btn.clicked.connect(self.process_files)
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)
        # Progress
        self.progress_label = QLabel()
        layout.addWidget(self.progress_label)
        # Results list
        self.results_list = QListWidget()
        layout.addWidget(self.results_list)
        # Status bar
        self.statusBar().showMessage("Ready - Dark AI Mode")
        
    def update_confidence_label(self, value):
        """Actualiza la etiqueta de confianza cuando se mueve el slider."""
        confidence = value / 100
        self.confidence_input.setText(f"{confidence:.1f}")
        
    def update_max_genres_label(self, value):
        """Actualiza la etiqueta de máximo de géneros cuando cambia el spinner."""
        self.max_genres_input.setText(str(value))

    def browse_files(self):
        """Open file browser for MP3 selection."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select MP3 Files", "", "MP3 Files (*.mp3)"
        )
        if files:
            self.add_files(files)
            
    def browse_folder(self):
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
            
    def process_files(self):
        """Process the selected MP3 files."""
        self.results_list.clear()
        self.process_btn.setEnabled(False)
        analyze_only = self.analyze_only.isChecked()
        confidence = float(self.confidence_input.text())
        max_genres = int(self.max_genres_input.text())
        
        # Configurar la opción de renombramiento
        rename_files = self.rename_files.isChecked()
        
        # Inicializar el hilo de procesamiento
        self.processing_thread = ProcessingThread(
            self.mp3_files,
            analyze_only=analyze_only,
            confidence=confidence,
            max_genres=max_genres
        )
        
        # Actualizar la configuración del modelo
        self.processing_thread.model.rename_after_update = rename_files
        self.processing_thread.progress.connect(self.update_progress)
        self.processing_thread.finished.connect(self.processing_complete)
        self.processing_thread.start()

    def update_progress(self, message):
        """Update progress display."""
        self.progress_label.setText(message)
        self.statusBar().showMessage(message)
        
    def processing_complete(self, results):
        """Handle completion of processing."""
        self.progress_label.clear()
        self.process_btn.setEnabled(True)
        
        # Estadísticas para mostrar en la barra de estado
        success_count = 0
        error_count = 0
        analyze_only = self.analyze_only.isChecked()
        
        for filepath, result in results.items():
            filename = Path(filepath).name
            
            if "error" in result:
                error_count += 1
                error_msg = result["error"]
                
                # Si hay géneros detectados pero ninguno con confianza suficiente, mostrarlos
                if "detected_genres" in result:
                    genres = result["detected_genres"]
                    if genres:
                        genre_str = ", ".join(f"{g} ({c:.2f})" for g, c in genres.items())
                        self.results_list.addItem(f"Error en {filename}: {error_msg}")
                        self.results_list.addItem(f"  Géneros detectados: {genre_str}")
                    else:
                        self.results_list.addItem(f"Error en {filename}: {error_msg}")
                else:
                    self.results_list.addItem(f"Error en {filename}: {error_msg}")
            
            elif "written" in result:
                if result["written"]:
                    success_count += 1
                    genre = result.get("current_genre", "?")
                    selected = ", ".join(result.get("selected_genres", []))
                    self.results_list.addItem(f"{filename}: Género escrito: {genre}")
                    if "selected_genres" in result:
                        self.results_list.addItem(f"  Géneros seleccionados: {selected}")
                    
                    # Mostrar información sobre el renombramiento si está disponible
                    if "renamed" in result:
                        if result["renamed"]:
                            new_name = Path(result["new_filepath"]).name
                            self.results_list.addItem(f"  Archivo renombrado: {new_name}")
                        else:
                            error_msg = result.get("rename_error", "Error desconocido")
                            self.results_list.addItem(f"  Error al renombrar: {error_msg}")
                else:
                    error_count += 1
                    self.results_list.addItem(f"{filename}: Error al escribir el género")
            
            else:
                # Análisis exitoso
                success_count += 1
                genres = result.get("detected_genres", {})
                if genres:
                    genre_str = ", ".join(f"{g} ({c:.2f})" for g, c in 
                                       sorted(genres.items(), key=lambda x: x[1], reverse=True))
                    self.results_list.addItem(f"{filename}: {genre_str}")
                else:
                    self.results_list.addItem(f"{filename}: No se detectaron géneros")
        
        # Actualizar la barra de estado con estadísticas
        mode = "análisis" if analyze_only else "actualización"
        status_msg = f"Procesamiento completado: {success_count} archivos procesados correctamente, {error_count} con errores - Modo: {mode}"
        self.statusBar().showMessage(status_msg)

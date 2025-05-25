import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QListWidget, QListWidgetItem, QPushButton, QMessageBox, QLabel, QSplitter, QFileDialog, QTabWidget, QSizePolicy)
from PyQt6.QtCore import Qt

# Imports para Matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt # Lo usaremos para algunos estilos y colores
import numpy as np

# Determinar la raíz del proyecto dinámicamente
_current_script_dir = os.path.dirname(os.path.abspath(__file__))
_ui_dir = _current_script_dir
_src_dir = os.path.dirname(_ui_dir)
_project_root = os.path.dirname(_src_dir)

# Añadir src al path para importar módulos
sys.path.insert(0, _src_dir)

# Imports de otros módulos del proyecto
from data import crud
from data.database_setup import setup_database, DB_FILE
from core import rule_engine
from core import exporter
from ui.playlist_edit_dialog import PlaylistEditDialog
from ui.camelot_wheel import CamelotWheelPanel
from ui.dj_tools_tab import DJToolsTab


# Clase para embeber Matplotlib en PyQt6
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Policy.Expanding,
                                   QSizePolicy.Policy.Expanding)
        FigureCanvas.updateGeometry(self)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nueva Biblioteca Musical - Sistema Avanzado de Playlists")
        self.setGeometry(100, 100, 1200, 800)
        self.db_conn = None # Inicializar db_conn
        self.ensure_db_connection()

        # Layout principal con tabs
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Sistema de tabs
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Tab 1: Playlists Inteligentes (funcionalidad original)
        self.playlists_tab = self.create_playlists_tab()
        self.tab_widget.addTab(self.playlists_tab, "🎵 Playlists Inteligentes")
        
        # Tab 2: Rueda Camelot
        self.camelot_tab = self.create_camelot_tab()
        self.tab_widget.addTab(self.camelot_tab, "🎛️ Rueda Camelot")
        
        # Tab 3: Análisis de Tracks (placeholder para futuras funcionalidades)
        self.analysis_tab = self.create_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "📊 Análisis de Tracks")
        
        # Tab 4: Herramientas de DJ
        self.dj_tab = self.create_dj_tab()
        self.tab_widget.addTab(self.dj_tab, "🎧 Herramientas DJ")

    def create_playlists_tab(self):
        """Crea el tab de playlists inteligentes (funcionalidad original)."""
        tab_widget = QWidget()
        main_layout = QHBoxLayout(tab_widget)

        # --- Panel Izquierdo (Playlists) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        left_layout.addWidget(QLabel("Playlists Inteligentes:"))
        self.playlist_list_widget = QListWidget()
        self.playlist_list_widget.itemSelectionChanged.connect(self.on_playlist_selected)
        left_layout.addWidget(self.playlist_list_widget)

        # Botones de acción para playlists
        playlist_buttons_layout = QHBoxLayout()
        self.new_playlist_button = QPushButton("Nueva")
        self.new_playlist_button.clicked.connect(self.create_new_playlist)
        playlist_buttons_layout.addWidget(self.new_playlist_button)

        self.edit_playlist_button = QPushButton("Editar")
        self.edit_playlist_button.clicked.connect(self.edit_selected_playlist)
        playlist_buttons_layout.addWidget(self.edit_playlist_button)

        self.delete_playlist_button = QPushButton("Eliminar")
        self.delete_playlist_button.clicked.connect(self.delete_selected_playlist)
        playlist_buttons_layout.addWidget(self.delete_playlist_button)
        left_layout.addLayout(playlist_buttons_layout)
        
        self.evaluate_rules_button = QPushButton("Evaluar Reglas de Playlist Seleccionada")
        self.evaluate_rules_button.clicked.connect(self.evaluate_rules_for_selected_playlist)
        left_layout.addWidget(self.evaluate_rules_button)
        
        # Botón de exportar M3U
        self.export_m3u_button = QPushButton("Exportar M3U")
        self.export_m3u_button.clicked.connect(self.export_selected_playlist_to_m3u)
        left_layout.addWidget(self.export_m3u_button)

        # --- Panel Derecho (Resultados de la Playlist) ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("Tracks en la Playlist:"))
        self.results_list_widget = QListWidget()
        right_layout.addWidget(self.results_list_widget)
        
        # --- Divisor entre paneles ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600]) # Tamaños iniciales
        main_layout.addWidget(splitter)

        self.load_playlists()
        return tab_widget

    def create_camelot_tab(self):
        """Crea el tab de la Rueda Camelot."""
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        
        # Panel de la Rueda Camelot
        self.camelot_panel = CamelotWheelPanel()
        main_layout.addWidget(self.camelot_panel)
        
        # Conectar señales de la rueda con funcionalidades de filtrado
        self.camelot_panel.filter_by_key.connect(self.filter_tracks_by_key)
        self.camelot_panel.filter_by_compatible.connect(self.filter_tracks_by_compatible_keys)
        
        # Panel de resultados de filtrado por tonalidad
        results_layout = QHBoxLayout()
        
        # Lista de tracks filtrados
        results_left = QWidget()
        results_left_layout = QVBoxLayout(results_left)
        results_left_layout.addWidget(QLabel("Tracks Filtrados por Tonalidad:"))
        self.camelot_results_list = QListWidget()
        results_left_layout.addWidget(self.camelot_results_list)
        
        # Información y estadísticas
        results_right = QWidget()
        results_right_layout = QVBoxLayout(results_right)
        results_right_layout.addWidget(QLabel("Estadísticas de Filtrado:"))
        self.camelot_stats_label = QLabel("Selecciona una tonalidad para ver estadísticas.")
        self.camelot_stats_label.setWordWrap(True)
        self.camelot_stats_label.setStyleSheet("padding: 10px; background-color: #f5f5f5; border: 1px solid #ddd;")
        results_right_layout.addWidget(self.camelot_stats_label)
        
        # Botones de acción
        camelot_actions_layout = QVBoxLayout()
        self.create_playlist_from_filter_btn = QPushButton("Crear Playlist desde Filtro")
        self.create_playlist_from_filter_btn.setEnabled(False)
        self.create_playlist_from_filter_btn.clicked.connect(self.create_playlist_from_camelot_filter)
        camelot_actions_layout.addWidget(self.create_playlist_from_filter_btn)
        
        self.export_filtered_m3u_btn = QPushButton("Exportar Filtro a M3U")
        self.export_filtered_m3u_btn.setEnabled(False)
        self.export_filtered_m3u_btn.clicked.connect(self.export_camelot_filter_to_m3u)
        camelot_actions_layout.addWidget(self.export_filtered_m3u_btn)
        
        results_right_layout.addLayout(camelot_actions_layout)
        results_right_layout.addStretch()
        
        # Splitter para resultados
        results_splitter = QSplitter(Qt.Orientation.Horizontal)
        results_splitter.addWidget(results_left)
        results_splitter.addWidget(results_right)
        results_splitter.setSizes([500, 300])
        
        results_layout.addWidget(results_splitter)
        main_layout.addLayout(results_layout)
        
        return tab_widget

    def create_analysis_tab(self):
        """Crea el tab de análisis de tracks con estadísticas y herramientas completas."""
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        
        title_label = QLabel("📊 Análisis Avanzado de Tracks")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px; color: #2c3e50;")
        main_layout.addWidget(title_label)
        
        refresh_layout = QHBoxLayout()
        self.refresh_analysis_btn = QPushButton("🔄 Actualizar Análisis")
        self.refresh_analysis_btn.clicked.connect(self.refresh_analysis_data_and_charts)
        self.refresh_analysis_btn.setStyleSheet("padding: 8px; font-weight: bold; background-color: #3498db; color: white; border-radius: 5px;")
        refresh_layout.addWidget(self.refresh_analysis_btn)
        refresh_layout.addStretch()
        main_layout.addLayout(refresh_layout)
        
        # Splitter principal: Estadísticas y Herramientas (Izquierda) vs Gráficos (Derecha)
        main_horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Contenedor para el lado izquierdo (Estadísticas y Herramientas)
        left_container_widget = QWidget()
        left_container_layout = QVBoxLayout(left_container_widget) # Usaremos QVBoxLayout para dos columnas

        # Columna 1: Estadísticas
        stats_column_widget = QWidget()
        stats_column_layout = QVBoxLayout(stats_column_widget)

        stats_group = QWidget()
        stats_group.setStyleSheet("background-color: #ecf0f1; border-radius: 10px; padding: 10px;")
        stats_layout_v = QVBoxLayout(stats_group)
        stats_title = QLabel("📈 Estadísticas Generales")
        stats_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #34495e;")
        stats_layout_v.addWidget(stats_title)
        self.general_stats_label = QLabel("Cargando estadísticas...")
        self.general_stats_label.setWordWrap(True)
        self.general_stats_label.setStyleSheet("padding: 10px; background-color: white; border-radius: 5px; min-height: 150px;")
        stats_layout_v.addWidget(self.general_stats_label)
        stats_column_layout.addWidget(stats_group)

        keys_group = QWidget()
        keys_group.setStyleSheet("background-color: #e8f5e8; border-radius: 10px; padding: 10px;")
        keys_layout_v = QVBoxLayout(keys_group)
        keys_title = QLabel("🎼 Análisis de Tonalidades")
        keys_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
        keys_layout_v.addWidget(keys_title)
        self.keys_stats_label = QLabel("Cargando análisis de tonalidades...")
        self.keys_stats_label.setWordWrap(True)
        self.keys_stats_label.setStyleSheet("padding: 10px; background-color: white; border-radius: 5px; min-height: 120px;")
        keys_layout_v.addWidget(self.keys_stats_label)
        stats_column_layout.addWidget(keys_group)
        
        bpm_group = QWidget()
        bpm_group.setStyleSheet("background-color: #fef9e7; border-radius: 10px; padding: 10px;")
        bpm_layout_v = QVBoxLayout(bpm_group)
        bpm_title = QLabel("🥁 Análisis de BPM")
        bpm_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #f39c12;")
        bpm_layout_v.addWidget(bpm_title)
        self.bpm_stats_label = QLabel("Cargando análisis de BPM...")
        self.bpm_stats_label.setWordWrap(True)
        self.bpm_stats_label.setStyleSheet("padding: 10px; background-color: white; border-radius: 5px; min-height: 120px;")
        bpm_layout_v.addWidget(self.bpm_stats_label)
        stats_column_layout.addWidget(bpm_group)
        stats_column_layout.addStretch()

        # Columna 2: Herramientas y Lista de Resultados
        tools_column_widget = QWidget()
        tools_column_layout = QVBoxLayout(tools_column_widget)

        tools_group = QWidget()
        tools_group.setStyleSheet("background-color: #fdf2e9; border-radius: 10px; padding: 10px;")
        tools_layout_v = QVBoxLayout(tools_group)
        tools_title = QLabel("🛠️ Herramientas de Análisis")
        tools_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #e67e22;")
        tools_layout_v.addWidget(tools_title)
        tools_buttons_layout = QHBoxLayout()
        self.find_duplicates_btn = QPushButton("🔍 Buscar Duplicados")
        self.find_duplicates_btn.clicked.connect(self.find_duplicate_tracks)
        tools_buttons_layout.addWidget(self.find_duplicates_btn)
        self.incomplete_metadata_btn = QPushButton("⚠️ Metadatos Incompletos")
        self.incomplete_metadata_btn.clicked.connect(self.find_incomplete_metadata)
        tools_buttons_layout.addWidget(self.incomplete_metadata_btn)
        self.export_stats_btn = QPushButton("📊 Exportar Estadísticas")
        self.export_stats_btn.clicked.connect(self.export_statistics_to_csv)
        tools_buttons_layout.addWidget(self.export_stats_btn)
        tools_layout_v.addLayout(tools_buttons_layout)
        tools_column_layout.addWidget(tools_group)

        results_title = QLabel("📋 Resultados de Análisis")
        results_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #8e44ad; margin-top: 10px;")
        tools_column_layout.addWidget(results_title)
        self.analysis_results_list = QListWidget()
        self.analysis_results_list.setStyleSheet("border: 1px solid #bdc3c7; border-radius: 5px;")
        tools_column_layout.addWidget(self.analysis_results_list)
        
        detail_title = QLabel("ℹ️ Información Detallada")
        detail_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2980b9; margin-top: 10px;")
        tools_column_layout.addWidget(detail_title)
        self.detail_info_label = QLabel("Selecciona un item para ver detalles.")
        self.detail_info_label.setWordWrap(True)
        self.detail_info_label.setStyleSheet("padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; min-height: 100px;")
        tools_column_layout.addWidget(self.detail_info_label)
        self.analysis_results_list.itemSelectionChanged.connect(self.on_analysis_item_selected)

        left_container_layout.addWidget(stats_column_widget, 1) # Columna de estadísticas con peso 1
        left_container_layout.addWidget(tools_column_widget, 1) # Columna de herramientas con peso 1
        
        # --- Panel Derecho: Gráficos ---
        charts_panel = QWidget()
        charts_layout = QVBoxLayout(charts_panel)
        charts_panel.setStyleSheet("background-color: #ffffff; border-radius: 10px; padding: 10px;")

        charts_title = QLabel("🖼️ Visualizaciones")
        charts_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #16a085; margin-bottom: 10px;")
        charts_layout.addWidget(charts_title)

        # Contenedores para los gráficos
        self.genre_chart_canvas = MplCanvas(self, width=5, height=3, dpi=100)
        charts_layout.addWidget(self.genre_chart_canvas)
        
        self.bpm_chart_canvas = MplCanvas(self, width=5, height=3, dpi=100)
        charts_layout.addWidget(self.bpm_chart_canvas)

        self.key_chart_canvas = MplCanvas(self, width=5, height=3, dpi=100) # Nuevo canvas para tonalidades
        charts_layout.addWidget(self.key_chart_canvas)

        charts_layout.addStretch()

        # Añadir paneles al splitter principal
        main_horizontal_splitter.addWidget(left_container_widget)
        main_horizontal_splitter.addWidget(charts_panel)
        main_horizontal_splitter.setStretchFactor(0, 2) # Dar más espacio inicial a estadísticas/herramientas
        main_horizontal_splitter.setStretchFactor(1, 1) # Menos espacio inicial a gráficos
        
        main_layout.addWidget(main_horizontal_splitter)
        
        self.refresh_analysis_data_and_charts() # Llamar a la nueva función de refresco
        
        return tab_widget

    def ensure_db_connection(self):
        if self.db_conn is None:
            setup_database(DB_FILE) # Asegura que la BD y el directorio existan
            self.db_conn = crud.create_connection(DB_FILE)
            if not self.db_conn:
                QMessageBox.critical(self, "Error de Base de Datos", f"No se pudo conectar a la base de datos: {DB_FILE}")
                sys.exit(1) # Salir si no hay BD

    def load_playlists(self):
        self.ensure_db_connection()
        self.playlist_list_widget.clear()
        try:
            playlists = crud.get_all_smart_playlists(self.db_conn)
            if playlists:
                for pl in playlists:
                    item = QListWidgetItem(f"{pl['name']} (ID: {pl['playlist_id']})")
                    item.setData(Qt.ItemDataRole.UserRole, pl['playlist_id']) # Guardar ID
                    self.playlist_list_widget.addItem(item)
            else:
                self.playlist_list_widget.addItem(QListWidgetItem("No hay playlists. ¡Crea una!"))
        except Exception as e:
            QMessageBox.warning(self, "Error Cargando Playlists", f"No se pudieron cargar las playlists: {e}")
            print(f"Error en load_playlists: {e}")
            
    def load_playlist_results(self, playlist_id):
        self.ensure_db_connection()
        self.results_list_widget.clear()
        if playlist_id is None:
            return
        try:
            tracks = crud.get_tracks_for_playlist(self.db_conn, playlist_id)
            if tracks:
                for track_info in tracks:
                    # Asumiendo que track_info tiene al menos 'title' y 'artist'
                    track_display = f"{track_info.get('title', 'N/A')} - {track_info.get('artist', 'N/A')}"
                    self.results_list_widget.addItem(QListWidgetItem(track_display))
            else:
                self.results_list_widget.addItem(QListWidgetItem("No hay tracks para esta regla o no ha sido evaluada."))
        except Exception as e:
            QMessageBox.warning(self, "Error Cargando Tracks", f"No se pudieron cargar los tracks de la playlist: {e}")
            print(f"Error en load_playlist_results: {e}")

    def on_playlist_selected(self):
        selected_items = self.playlist_list_widget.selectedItems()
        if selected_items:
            item = selected_items[0]
            playlist_id = item.data(Qt.ItemDataRole.UserRole)
            if playlist_id:
                self.load_playlist_results(playlist_id)
            else:
                self.results_list_widget.clear() # Limpiar si no hay ID (ej. item "No hay playlists")
        else:
            self.results_list_widget.clear()

    def create_new_playlist(self):
        self.ensure_db_connection()
        dialog = PlaylistEditDialog(parent=self, is_new=True)
        if dialog.exec():
            name, rule = dialog.get_data()
            if name and rule:
                # Crear la playlist primero
                playlist_id = crud.create_smart_playlist(self.db_conn, name)
                if playlist_id:
                    # Ahora añadir la regla
                    rule_id = crud.add_rule_to_playlist(self.db_conn, playlist_id, rule)
                    if rule_id:
                        QMessageBox.information(self, "Playlist Creada", f"Playlist '{name}' creada con ID: {playlist_id}")
                        self.load_playlists()
                    else:
                        QMessageBox.warning(self, "Error", "Playlist creada pero no se pudo añadir la regla.")
                        # Opcionalmente, eliminar la playlist que se creó sin regla
                        crud.delete_smart_playlist(self.db_conn, playlist_id)
                else:
                    QMessageBox.warning(self, "Error", "No se pudo crear la playlist.")
            else:
                QMessageBox.warning(self, "Datos incompletos", "El nombre y la regla no pueden estar vacíos.")

    def edit_selected_playlist(self):
        self.ensure_db_connection()
        selected_items = self.playlist_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, selecciona una playlist para editar.")
            return

        item = selected_items[0]
        playlist_id = item.data(Qt.ItemDataRole.UserRole)
        if not playlist_id:
             QMessageBox.warning(self, "Error", "Playlist no válida seleccionada.")
             return

        playlist_details = crud.get_smart_playlist_by_id(self.db_conn, playlist_id)
        rule_details = crud.get_rule_for_playlist(self.db_conn, playlist_id)

        if not playlist_details or not rule_details:
            QMessageBox.warning(self, "Error", f"No se pudieron obtener los detalles de la playlist ID: {playlist_id}")
            return

        dialog = PlaylistEditDialog(
            playlist_name=playlist_details['name'],
            rule_expression=rule_details['expression_text'],
            parent=self,
            is_new=False,
            playlist_id=playlist_id
        )

        if dialog.exec():
            name, rule = dialog.get_data()
            if name and rule:
                # Actualizar la playlist
                success_playlist = crud.update_smart_playlist(self.db_conn, playlist_id, name=name)
                # Actualizar la regla (add_rule_to_playlist reemplaza la regla existente)
                success_rule = crud.add_rule_to_playlist(self.db_conn, playlist_id, rule)
                
                if success_playlist and success_rule:
                    QMessageBox.information(self, "Playlist Actualizada", f"Playlist '{name}' (ID: {playlist_id}) actualizada.")
                    self.load_playlists()
                    self.evaluate_rules_for_selected_playlist() # Re-evaluar para refrescar resultados
                else:
                    QMessageBox.warning(self, "Error", "No se pudo actualizar completamente la playlist.")
            else:
                QMessageBox.warning(self, "Datos incompletos", "El nombre y la regla no pueden estar vacíos.")

    def delete_selected_playlist(self):
        self.ensure_db_connection()
        selected_items = self.playlist_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, selecciona una playlist para eliminar.")
            return

        item = selected_items[0]
        playlist_id = item.data(Qt.ItemDataRole.UserRole)
        if not playlist_id:
             QMessageBox.warning(self, "Error", "Playlist no válida seleccionada.")
             return
        
        playlist_name = item.text().split(" (")[0] # Obtener nombre del texto del item

        reply = QMessageBox.question(self, "Confirmar Eliminación", 
                                     f"¿Estás seguro de que quieres eliminar la playlist '{playlist_name}' (ID: {playlist_id})?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # También necesitamos eliminar la regla asociada y los resultados de playlist_tracks
            # crud.delete_rule_for_playlist(self.db_conn, playlist_id) # Suponiendo que existe esta función
            # crud.clear_playlist_tracks(self.db_conn, playlist_id) # Suponiendo que existe esta función
            success = crud.delete_smart_playlist(self.db_conn, playlist_id)
            if success:
                QMessageBox.information(self, "Playlist Eliminada", f"Playlist '{playlist_name}' eliminada.")
                self.load_playlists()
                self.results_list_widget.clear() # Limpiar resultados
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la playlist.")

    def evaluate_rules_for_selected_playlist(self):
        self.ensure_db_connection()
        selected_items = self.playlist_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, selecciona una playlist para evaluar sus reglas.")
            return

        item = selected_items[0]
        playlist_id = item.data(Qt.ItemDataRole.UserRole)
        if not playlist_id:
             QMessageBox.warning(self, "Error", "Playlist no válida seleccionada.")
             return

        try:
            print(f"UI: Solicitando evaluación para playlist ID: {playlist_id}")
            success = rule_engine.evaluate_playlist_rules(DB_FILE, playlist_id)
            if success:
                QMessageBox.information(self, "Reglas Evaluadas", f"Reglas para playlist ID {playlist_id} evaluadas exitosamente.")
                self.load_playlist_results(playlist_id) # Recargar los resultados en la UI
            else:
                QMessageBox.warning(self, "Error de Evaluación", f"Hubo un problema al evaluar las reglas para la playlist ID {playlist_id}. Revisa la consola para más detalles.")
        except Exception as e:
            QMessageBox.critical(self, "Error Crítico", f"Error evaluando reglas: {e}")
            print(f"Error crítico en evaluate_rules_for_selected_playlist: {e}")

    def export_selected_playlist_to_m3u(self):
        self.ensure_db_connection()
        selected_items = self.playlist_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, selecciona una playlist para exportar.")
            return

        item = selected_items[0]
        playlist_id = item.data(Qt.ItemDataRole.UserRole)
        playlist_name_from_item = item.text().split(" (")[0] # "Mi Playlist (ID: 1)" -> "Mi Playlist"

        if not playlist_id:
            QMessageBox.warning(self, "Error", "Playlist no válida seleccionada para exportar.")
            return
        
        # Obtener nombre de la playlist desde la DB para asegurar que es el actual
        playlist_details = crud.get_smart_playlist_by_id(self.db_conn, playlist_id)
        if not playlist_details:
            QMessageBox.warning(self, "Error", f"No se pudo encontrar la playlist ID {playlist_id} en la base de datos.")
            return
        playlist_name = playlist_details.get('name', playlist_name_from_item) # Usar nombre de DB o el del item como fallback

        # Sugerir un nombre de archivo
        suggested_filename = f"{playlist_name.replace(' ', '_').replace('[^a-zA-Z0-9_.-]', '')}.m3u"
        
        # Abrir diálogo para guardar archivo
        file_dialog = QFileDialog(self, "Exportar Playlist como M3U", "", "M3U Playlist Files (*.m3u)")
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.selectFile(suggested_filename)
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if not file_path.lower().endswith(".m3u"):
                file_path += ".m3u" # Asegurar extensión

            try:
                m3u_content = exporter.generate_m3u_content(DB_FILE, playlist_id)
                if m3u_content is not None:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(m3u_content)
                    QMessageBox.information(self, "Exportación Exitosa", f"Playlist exportada a:\n{file_path}")
                else:
                    # generate_m3u_content ya imprime errores, pero podemos dar un mensaje genérico
                    QMessageBox.warning(self, "Error de Exportación", "No se pudo generar el contenido M3U. Revisa la consola.")
            except Exception as e:
                QMessageBox.critical(self, "Error Crítico al Exportar", f"Ocurrió un error al guardar el archivo M3U: {e}")
                print(f"Error crítico en export_selected_playlist_to_m3u: {e}")

    # Métodos para la funcionalidad de la Rueda Camelot
    
    def filter_tracks_by_key(self, musical_key: str):
        """Filtra tracks por una tonalidad musical específica."""
        self.ensure_db_connection()
        try:
            # Buscar tracks por tonalidad musical
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT * FROM tracks WHERE key = ? OR camelot_key = ?", 
                         (musical_key, musical_key))
            tracks = cursor.fetchall()
            
            # Convertir a diccionarios
            column_names = [description[0] for description in cursor.description]
            tracks_list = [dict(zip(column_names, track)) for track in tracks]
            
            self.display_camelot_filtered_tracks(tracks_list, f"Tonalidad: {musical_key}")
            
        except Exception as e:
            QMessageBox.warning(self, "Error de Filtrado", f"Error al filtrar por tonalidad {musical_key}: {e}")
            print(f"Error en filter_tracks_by_key: {e}")

    def filter_tracks_by_compatible_keys(self, musical_keys: list):
        """Filtra tracks por múltiples tonalidades compatibles."""
        self.ensure_db_connection()
        try:
            if not musical_keys:
                self.camelot_results_list.clear()
                self.camelot_stats_label.setText("No hay tonalidades compatibles seleccionadas.")
                return
            
            # Crear placeholders para la consulta SQL
            placeholders = ','.join(['?' for _ in musical_keys])
            query = f"""
                SELECT * FROM tracks 
                WHERE key IN ({placeholders}) OR camelot_key IN ({placeholders})
            """
            
            cursor = self.db_conn.cursor()
            cursor.execute(query, musical_keys + musical_keys)  # Duplicar para ambas columnas
            tracks = cursor.fetchall()
            
            # Convertir a diccionarios
            column_names = [description[0] for description in cursor.description]
            tracks_list = [dict(zip(column_names, track)) for track in tracks]
            
            self.display_camelot_filtered_tracks(tracks_list, f"Compatibles: {', '.join(musical_keys)}")
            
        except Exception as e:
            QMessageBox.warning(self, "Error de Filtrado", f"Error al filtrar por tonalidades compatibles: {e}")
            print(f"Error en filter_tracks_by_compatible_keys: {e}")

    def display_camelot_filtered_tracks(self, tracks_list: list, filter_description: str):
        """Muestra los tracks filtrados en la interfaz de la Rueda Camelot."""
        self.camelot_results_list.clear()
        
        if not tracks_list:
            self.camelot_results_list.addItem(QListWidgetItem("No se encontraron tracks con esas tonalidades."))
            self.camelot_stats_label.setText(f"Filtro: {filter_description}\nResultados: 0 tracks")
            self.create_playlist_from_filter_btn.setEnabled(False)
            self.export_filtered_m3u_btn.setEnabled(False)
            return
        
        # Mostrar tracks en la lista
        for track in tracks_list:
            track_display = f"{track.get('title', 'N/A')} - {track.get('artist', 'N/A')}"
            if track.get('key'):
                track_display += f" [{track['key']}]"
            elif track.get('camelot_key'):
                track_display += f" [{track['camelot_key']}]"
            
            item = QListWidgetItem(track_display)
            item.setData(Qt.ItemDataRole.UserRole, track['track_id'])
            self.camelot_results_list.addItem(item)
        
        # Calcular estadísticas
        total_tracks = len(tracks_list)
        genres = [track.get('genre', 'N/A') for track in tracks_list if track.get('genre')]
        genre_counts = {}
        for genre in genres:
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # BPM promedio
        bpms = [track.get('bpm') for track in tracks_list if track.get('bpm')]
        avg_bpm = sum(bpms) / len(bpms) if bpms else 0
        
        # Duración total
        durations = [track.get('duration_seconds', 0) for track in tracks_list]
        total_duration = sum(durations)
        total_minutes = int(total_duration // 60)
        
        # Tonalidades encontradas
        keys_found = set()
        for track in tracks_list:
            if track.get('key'):
                keys_found.add(track['key'])
            if track.get('camelot_key'):
                keys_found.add(track['camelot_key'])
        
        # Mostrar estadísticas
        stats_text = f"""
<b>Filtro:</b> {filter_description}<br>
<b>Total de Tracks:</b> {total_tracks}<br>
<b>Duración Total:</b> {total_minutes} minutos<br>
<b>BPM Promedio:</b> {avg_bpm:.1f}<br>
<b>Tonalidades Encontradas:</b> {', '.join(sorted(keys_found))}<br>
<b>Géneros Principales:</b> {', '.join([f"{g}({c})" for g, c in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:3]])}
        """.strip()
        
        self.camelot_stats_label.setText(stats_text)
        
        # Habilitar botones de acción
        self.create_playlist_from_filter_btn.setEnabled(True)
        self.export_filtered_m3u_btn.setEnabled(True)
        
        # Guardar tracks filtrados para uso posterior
        self.current_filtered_tracks = tracks_list

    def create_playlist_from_camelot_filter(self):
        """Crea una nueva playlist inteligente basada en el filtro actual de la Rueda Camelot."""
        if not hasattr(self, 'current_filtered_tracks') or not self.current_filtered_tracks:
            QMessageBox.warning(self, "Sin Filtro", "No hay tracks filtrados para crear una playlist.")
            return
        
        # Obtener información del filtro actual
        filter_info = self.camelot_stats_label.text()
        
        # Extraer tonalidades del filtro para crear una regla
        # Esto es una aproximación - en un sistema más avanzado, podríamos ser más precisos
        keys_found = set()
        for track in self.current_filtered_tracks:
            if track.get('key'):
                keys_found.add(track['key'])
        
        if keys_found:
            # Crear regla basada en las tonalidades encontradas
            keys_list = list(keys_found)
            if len(keys_list) == 1:
                rule_expression = f"key = '{keys_list[0]}'"
            else:
                rule_conditions = [f"key = '{key}'" for key in keys_list]
                rule_expression = " OR ".join(rule_conditions)
        else:
            rule_expression = "rating >= 1"  # Regla por defecto
        
        # Abrir diálogo para crear playlist
        dialog = PlaylistEditDialog(
            playlist_name=f"Camelot Filter - {len(self.current_filtered_tracks)} tracks",
            rule_expression=rule_expression,
            parent=self,
            is_new=True
        )
        
        if dialog.exec():
            name, rule = dialog.get_data()
            if name and rule:
                self.ensure_db_connection()
                # Crear la playlist
                playlist_id = crud.create_smart_playlist(self.db_conn, name)
                if playlist_id:
                    # Añadir la regla
                    rule_id = crud.add_rule_to_playlist(self.db_conn, playlist_id, rule)
                    if rule_id:
                        QMessageBox.information(self, "Playlist Creada", 
                                              f"Playlist '{name}' creada desde filtro Camelot con ID: {playlist_id}")
                        self.load_playlists()
                        # Cambiar al tab de playlists para mostrar la nueva playlist
                        self.tab_widget.setCurrentIndex(0)
                    else:
                        QMessageBox.warning(self, "Error", "Playlist creada pero no se pudo añadir la regla.")
                        crud.delete_smart_playlist(self.db_conn, playlist_id)
                else:
                    QMessageBox.warning(self, "Error", "No se pudo crear la playlist.")

    def export_camelot_filter_to_m3u(self):
        """Exporta los tracks filtrados por la Rueda Camelot a un archivo M3U."""
        if not hasattr(self, 'current_filtered_tracks') or not self.current_filtered_tracks:
            QMessageBox.warning(self, "Sin Filtro", "No hay tracks filtrados para exportar.")
            return
        
        # Sugerir nombre de archivo basado en el filtro
        suggested_filename = f"camelot_filter_{len(self.current_filtered_tracks)}_tracks.m3u"
        
        # Abrir diálogo para guardar archivo
        file_dialog = QFileDialog(self, "Exportar Filtro Camelot como M3U", "", "M3U Playlist Files (*.m3u)")
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.selectFile(suggested_filename)
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if not file_path.lower().endswith(".m3u"):
                file_path += ".m3u"
            
            try:
                # Generar contenido M3U manualmente para los tracks filtrados
                m3u_lines = ["#EXTM3U"]
                
                for track in self.current_filtered_tracks:
                    title = track.get('title', 'Unknown Title')
                    artist = track.get('artist', 'Unknown Artist')
                    duration = int(track.get('duration_seconds', 0))
                    file_path_track = track.get('file_path', '')
                    
                    # Línea de información del track
                    m3u_lines.append(f"#EXTINF:{duration},{artist} - {title}")
                    # Línea de ruta del archivo
                    m3u_lines.append(file_path_track)
                
                # Escribir archivo
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(m3u_lines))
                
                QMessageBox.information(self, "Exportación Exitosa", 
                                      f"Filtro Camelot exportado a:\n{file_path}\n\n{len(self.current_filtered_tracks)} tracks incluidos.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error al Exportar", f"Error al guardar el archivo M3U: {e}")
                print(f"Error en export_camelot_filter_to_m3u: {e}")

    # Métodos para el Tab de Análisis de Tracks
    
    def refresh_analysis_data_and_charts(self):
        """Actualiza todos los datos de análisis y los gráficos."""
        self.ensure_db_connection()
        try:
            # Actualizar estadísticas textuales
            self.update_general_statistics()
            self.update_keys_analysis()
            self.update_bpm_analysis()
            
            # Actualizar gráficos
            self.plot_genre_distribution()
            self.plot_bpm_distribution()
            self.plot_key_distribution() # Nueva función para gráfico de tonalidades

            self.analysis_results_list.clear()
            self.detail_info_label.setText("Análisis actualizado. Usa las herramientas para obtener resultados específicos.")
        except Exception as e:
            QMessageBox.warning(self, "Error de Análisis", f"Error al actualizar análisis y gráficos: {e}")
            print(f"Error en refresh_analysis_data_and_charts: {e}")
    
    def update_general_statistics(self):
        """Actualiza las estadísticas generales de la biblioteca."""
        cursor = self.db_conn.cursor()
        
        # Estadísticas básicas
        cursor.execute("SELECT COUNT(*) FROM tracks")
        total_tracks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT artist) FROM tracks WHERE artist IS NOT NULL")
        total_artists = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT album) FROM tracks WHERE album IS NOT NULL")
        total_albums = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT genre) FROM tracks WHERE genre IS NOT NULL")
        total_genres = cursor.fetchone()[0]
        
        # Duración total
        cursor.execute("SELECT SUM(duration_seconds) FROM tracks WHERE duration_seconds IS NOT NULL")
        total_duration = cursor.fetchone()[0] or 0
        total_hours = int(total_duration // 3600)
        total_minutes = int((total_duration % 3600) // 60)
        
        # Distribución por géneros (top 5)
        cursor.execute("""
            SELECT genre, COUNT(*) as count 
            FROM tracks 
            WHERE genre IS NOT NULL 
            GROUP BY genre 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_genres = cursor.fetchall()
        
        # Distribución por años (rango)
        cursor.execute("SELECT MIN(year), MAX(year) FROM tracks WHERE year IS NOT NULL")
        year_range = cursor.fetchone()
        
        # Rating promedio
        cursor.execute("SELECT AVG(rating) FROM tracks WHERE rating IS NOT NULL")
        avg_rating = cursor.fetchone()[0] or 0
        
        # Formatear estadísticas
        stats_text = f"""
<b>📊 Resumen de la Biblioteca:</b><br>
• <b>Total de Tracks:</b> {total_tracks:,}<br>
• <b>Artistas Únicos:</b> {total_artists:,}<br>
• <b>Álbumes Únicos:</b> {total_albums:,}<br>
• <b>Géneros Únicos:</b> {total_genres:,}<br>
• <b>Duración Total:</b> {total_hours}h {total_minutes}m<br>
• <b>Rating Promedio:</b> {avg_rating:.1f}/5<br>

<b>🎵 Top Géneros:</b><br>
"""
        
        for genre, count in top_genres:
            percentage = (count / total_tracks) * 100 if total_tracks > 0 else 0
            stats_text += f"• {genre}: {count} tracks ({percentage:.1f}%)<br>"
        
        if year_range[0] and year_range[1]:
            stats_text += f"<br><b>📅 Rango de Años:</b> {year_range[0]} - {year_range[1]}"
        
        self.general_stats_label.setText(stats_text.strip())
    
    def update_keys_analysis(self):
        """Actualiza el análisis de tonalidades."""
        cursor = self.db_conn.cursor()
        
        # Tracks con tonalidad asignada
        cursor.execute("SELECT COUNT(*) FROM tracks WHERE key IS NOT NULL")
        tracks_with_keys = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tracks")
        total_tracks = cursor.fetchone()[0]
        
        # Distribución de tonalidades
        cursor.execute("""
            SELECT key, camelot_key, COUNT(*) as count 
            FROM tracks 
            WHERE key IS NOT NULL 
            GROUP BY key, camelot_key 
            ORDER BY count DESC 
            LIMIT 8
        """)
        top_keys = cursor.fetchall()
        
        # Tracks sin tonalidad
        tracks_without_keys = total_tracks - tracks_with_keys
        
        # Análisis de modos (mayor/menor)
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN key LIKE '%m' THEN 'Menor'
                    ELSE 'Mayor'
                END as mode,
                COUNT(*) as count
            FROM tracks 
            WHERE key IS NOT NULL 
            GROUP BY mode
        """)
        mode_distribution = cursor.fetchall()
        
        keys_text = f"""
<b>🎼 Análisis de Tonalidades:</b><br>
• <b>Tracks con Tonalidad:</b> {tracks_with_keys}/{total_tracks}<br>
• <b>Tracks sin Tonalidad:</b> {tracks_without_keys}<br>

<b>🎵 Tonalidades Más Comunes:</b><br>
"""
        
        for key, camelot_key, count in top_keys:
            percentage = (count / tracks_with_keys) * 100 if tracks_with_keys > 0 else 0
            camelot_display = f" ({camelot_key})" if camelot_key else ""
            keys_text += f"• {key}{camelot_display}: {count} tracks ({percentage:.1f}%)<br>"
        
        if mode_distribution:
            keys_text += f"<br><b>🎭 Distribución por Modo:</b><br>"
            for mode, count in mode_distribution:
                percentage = (count / tracks_with_keys) * 100 if tracks_with_keys > 0 else 0
                keys_text += f"• {mode}: {count} tracks ({percentage:.1f}%)<br>"
        
        self.keys_stats_label.setText(keys_text.strip())
    
    def update_bpm_analysis(self):
        """Actualiza el análisis de BPM."""
        cursor = self.db_conn.cursor()
        
        # Tracks con BPM asignado
        cursor.execute("SELECT COUNT(*) FROM tracks WHERE bpm IS NOT NULL")
        tracks_with_bpm = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tracks")
        total_tracks = cursor.fetchone()[0]
        
        # Estadísticas de BPM
        cursor.execute("SELECT MIN(bpm), MAX(bpm), AVG(bpm) FROM tracks WHERE bpm IS NOT NULL")
        bpm_stats = cursor.fetchone()
        min_bpm, max_bpm, avg_bpm = bpm_stats if bpm_stats[0] else (0, 0, 0)
        
        # Distribución por rangos de BPM
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN bpm < 90 THEN 'Lento (< 90)'
                    WHEN bpm BETWEEN 90 AND 120 THEN 'Medio (90-120)'
                    WHEN bpm BETWEEN 121 AND 140 THEN 'Rápido (121-140)'
                    WHEN bpm > 140 THEN 'Muy Rápido (> 140)'
                END as bpm_range,
                COUNT(*) as count
            FROM tracks 
            WHERE bpm IS NOT NULL 
            GROUP BY bpm_range
            ORDER BY MIN(bpm)
        """)
        bpm_ranges = cursor.fetchall()
        
        # BPM promedio por género
        cursor.execute("""
            SELECT genre, AVG(bpm) as avg_bpm, COUNT(*) as count
            FROM tracks 
            WHERE bpm IS NOT NULL AND genre IS NOT NULL
            GROUP BY genre 
            HAVING count >= 2
            ORDER BY avg_bpm DESC 
            LIMIT 5
        """)
        genre_bpm = cursor.fetchall()
        
        tracks_without_bpm = total_tracks - tracks_with_bpm
        
        bpm_text = f"""
<b>🥁 Análisis de BPM:</b><br>
• <b>Tracks con BPM:</b> {tracks_with_bpm}/{total_tracks}<br>
• <b>Tracks sin BPM:</b> {tracks_without_bpm}<br>
• <b>BPM Mínimo:</b> {min_bpm:.0f}<br>
• <b>BPM Máximo:</b> {max_bpm:.0f}<br>
• <b>BPM Promedio:</b> {avg_bpm:.1f}<br>

<b>📊 Distribución por Rangos:</b><br>
"""
        
        for bpm_range, count in bpm_ranges:
            percentage = (count / tracks_with_bpm) * 100 if tracks_with_bpm > 0 else 0
            bpm_text += f"• {bpm_range}: {count} tracks ({percentage:.1f}%)<br>"
        
        if genre_bpm:
            bpm_text += f"<br><b>🎵 BPM Promedio por Género:</b><br>"
            for genre, avg_bpm_genre, count in genre_bpm:
                bpm_text += f"• {genre}: {avg_bpm_genre:.1f} BPM ({count} tracks)<br>"
        
        self.bpm_stats_label.setText(bpm_text.strip())
    
    def find_duplicate_tracks(self):
        """Busca tracks duplicados por título y artista."""
        self.ensure_db_connection()
        self.analysis_results_list.clear()
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT title, artist, COUNT(*) as count, GROUP_CONCAT(track_id) as track_ids
                FROM tracks 
                WHERE title IS NOT NULL AND artist IS NOT NULL
                GROUP BY LOWER(title), LOWER(artist)
                HAVING count > 1
                ORDER BY count DESC, title
            """)
            
            duplicates = cursor.fetchall()
            
            if duplicates:
                for title, artist, count, track_ids in duplicates:
                    item_text = f"🔄 {title} - {artist} ({count} copias)"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'type': 'duplicate',
                        'title': title,
                        'artist': artist,
                        'count': count,
                        'track_ids': track_ids.split(',')
                    })
                    self.analysis_results_list.addItem(item)
                
                self.detail_info_label.setText(f"Se encontraron {len(duplicates)} grupos de tracks duplicados. Selecciona uno para ver detalles.")
            else:
                item = QListWidgetItem("✅ No se encontraron tracks duplicados")
                self.analysis_results_list.addItem(item)
                self.detail_info_label.setText("¡Excelente! Tu biblioteca no tiene duplicados detectados.")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al buscar duplicados: {e}")
            print(f"Error en find_duplicate_tracks: {e}")
    
    def find_incomplete_metadata(self):
        """Busca tracks con metadatos incompletos."""
        self.ensure_db_connection()
        self.analysis_results_list.clear()
        
        try:
            cursor = self.db_conn.cursor()
            
            # Buscar tracks con diferentes tipos de metadatos faltantes
            issues = [
                ("Sin Título", "title IS NULL OR title = ''"),
                ("Sin Artista", "artist IS NULL OR artist = ''"),
                ("Sin Álbum", "album IS NULL OR album = ''"),
                ("Sin Género", "genre IS NULL OR genre = ''"),
                ("Sin Año", "year IS NULL"),
                ("Sin BPM", "bpm IS NULL"),
                ("Sin Tonalidad", "key IS NULL OR key = ''"),
                ("Sin Rating", "rating IS NULL"),
                ("Sin Duración", "duration_seconds IS NULL")
            ]
            
            for issue_name, condition in issues:
                cursor.execute(f"""
                    SELECT track_id, title, artist, file_path 
                    FROM tracks 
                    WHERE {condition}
                    ORDER BY title, artist
                    LIMIT 50
                """)
                
                tracks_with_issue = cursor.fetchall()
                
                if tracks_with_issue:
                    item_text = f"⚠️ {issue_name} ({len(tracks_with_issue)} tracks)"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'type': 'incomplete_metadata',
                        'issue': issue_name,
                        'tracks': tracks_with_issue
                    })
                    self.analysis_results_list.addItem(item)
            
            if self.analysis_results_list.count() == 0:
                item = QListWidgetItem("✅ Todos los tracks tienen metadatos completos")
                self.analysis_results_list.addItem(item)
                self.detail_info_label.setText("¡Perfecto! Todos tus tracks tienen metadatos completos.")
            else:
                self.detail_info_label.setText(f"Se encontraron {self.analysis_results_list.count()} tipos de problemas de metadatos. Selecciona uno para ver detalles.")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al analizar metadatos: {e}")
            print(f"Error en find_incomplete_metadata: {e}")
    
    def export_statistics_to_csv(self):
        """Exporta las estadísticas de la biblioteca a un archivo CSV."""
        self.ensure_db_connection()
        
        try:
            from PyQt6.QtWidgets import QFileDialog
            import csv
            from datetime import datetime
            
            # Diálogo para guardar archivo
            file_dialog = QFileDialog(self, "Exportar Estadísticas", "", "CSV Files (*.csv)")
            file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            file_dialog.selectFile(f"biblioteca_estadisticas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            
            if file_dialog.exec():
                file_path = file_dialog.selectedFiles()[0]
                if not file_path.lower().endswith(".csv"):
                    file_path += ".csv"
                
                cursor = self.db_conn.cursor()
                
                # Obtener todos los tracks con sus metadatos
                cursor.execute("""
                    SELECT track_id, title, artist, album, genre, year, duration_seconds, 
                           bpm, rating, key, camelot_key, file_path
                    FROM tracks 
                    ORDER BY artist, album, title
                """)
                
                tracks = cursor.fetchall()
                
                # Escribir CSV
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Encabezados
                    writer.writerow([
                        'ID', 'Título', 'Artista', 'Álbum', 'Género', 'Año', 
                        'Duración (seg)', 'BPM', 'Rating', 'Tonalidad', 'Camelot', 'Archivo'
                    ])
                    
                    # Datos
                    for track in tracks:
                        writer.writerow(track)
                
                QMessageBox.information(self, "Exportación Exitosa", 
                                      f"Estadísticas exportadas exitosamente a:\n{file_path}\n\n{len(tracks)} tracks incluidos.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"Error al exportar estadísticas: {e}")
            print(f"Error en export_statistics_to_csv: {e}")
    
    def on_analysis_item_selected(self):
        """Maneja la selección de items en la lista de análisis."""
        selected_items = self.analysis_results_list.selectedItems()
        if not selected_items:
            self.detail_info_label.setText("Selecciona un item para ver detalles.")
            return
        
        item = selected_items[0]
        item_data = item.data(Qt.ItemDataRole.UserRole)
        
        if not item_data:
            self.detail_info_label.setText("No hay información detallada disponible para este item.")
            return
        
        try:
            if item_data['type'] == 'duplicate':
                self.show_duplicate_details(item_data)
            elif item_data['type'] == 'incomplete_metadata':
                self.show_incomplete_metadata_details(item_data)
            else:
                self.detail_info_label.setText("Tipo de análisis no reconocido.")
        except Exception as e:
            self.detail_info_label.setText(f"Error al mostrar detalles: {e}")
            print(f"Error en on_analysis_item_selected: {e}")
    
    def show_duplicate_details(self, data):
        """Muestra detalles de tracks duplicados."""
        cursor = self.db_conn.cursor()
        track_ids = data['track_ids']
        
        # Obtener detalles de cada track duplicado
        placeholders = ','.join(['?' for _ in track_ids])
        cursor.execute(f"""
            SELECT track_id, title, artist, album, year, file_path, duration_seconds
            FROM tracks 
            WHERE track_id IN ({placeholders})
            ORDER BY track_id
        """, track_ids)
        
        tracks = cursor.fetchall()
        
        detail_text = f"""
<b>🔄 Tracks Duplicados: {data['title']} - {data['artist']}</b><br>
<b>Total de copias:</b> {data['count']}<br><br>

<b>📋 Detalles de cada copia:</b><br>
"""
        
        for i, (track_id, title, artist, album, year, file_path, duration) in enumerate(tracks, 1):
            duration_min = int(duration // 60) if duration else 0
            duration_sec = int(duration % 60) if duration else 0
            detail_text += f"""
<b>Copia {i} (ID: {track_id}):</b><br>
• Álbum: {album or 'N/A'}<br>
• Año: {year or 'N/A'}<br>
• Duración: {duration_min}:{duration_sec:02d}<br>
• Archivo: {file_path}<br><br>
"""
        
        detail_text += """
<b>💡 Sugerencia:</b> Revisa las copias para determinar cuál conservar. 
Considera factores como calidad de audio, completitud de metadatos y ubicación del archivo.
"""
        
        self.detail_info_label.setText(detail_text.strip())
    
    def show_incomplete_metadata_details(self, data):
        """Muestra detalles de tracks con metadatos incompletos."""
        tracks = data['tracks']
        issue = data['issue']
        
        detail_text = f"""
<b>⚠️ {issue}</b><br>
<b>Tracks afectados:</b> {len(tracks)}<br><br>

<b>📋 Lista de tracks:</b><br>
"""
        
        for track_id, title, artist, file_path in tracks[:10]:  # Mostrar solo los primeros 10
            title_display = title or "Sin título"
            artist_display = artist or "Sin artista"
            detail_text += f"• {title_display} - {artist_display} (ID: {track_id})<br>"
        
        if len(tracks) > 10:
            detail_text += f"<br>... y {len(tracks) - 10} tracks más.<br>"
        
        detail_text += f"""
<br><b>💡 Sugerencia:</b> Considera actualizar los metadatos de estos tracks 
para mejorar la organización y funcionalidad de tu biblioteca musical.
"""
        
        self.detail_info_label.setText(detail_text.strip())

    def plot_genre_distribution(self):
        """Crea y muestra un gráfico de barras para la distribución de géneros."""
        self.ensure_db_connection()
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT genre, COUNT(*) as count 
            FROM tracks 
            WHERE genre IS NOT NULL AND genre != ''
            GROUP BY genre 
            ORDER BY count DESC 
            LIMIT 7  -- Mostrar los 7 géneros más comunes
        """)
        data = cursor.fetchall()

        self.genre_chart_canvas.axes.cla() # Limpiar el canvas anterior
        if data:
            genres = [row[0] for row in data]
            counts = [row[1] for row in data]
            
            colors = plt.colormaps.get_cmap('viridis')(np.linspace(0, 1, len(genres))) # Corregido get_cmap y usando numpy para espacio lineal
            bars = self.genre_chart_canvas.axes.bar(genres, counts, color=colors)
            
            self.genre_chart_canvas.axes.set_title('Distribución por Género (Top 7)', fontsize=10)
            self.genre_chart_canvas.axes.set_ylabel('Número de Tracks', fontsize=8)
            self.genre_chart_canvas.axes.set_xticks(range(len(genres))) # Añadido para definir explícitamente los ticks
            self.genre_chart_canvas.axes.set_xticklabels(genres, rotation=45, ha='right', fontsize=8) # Nueva forma de setear etiquetas X
            self.genre_chart_canvas.axes.tick_params(axis='y', labelsize=8) # Cambiado fontsize a labelsize
            self.genre_chart_canvas.axes.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Añadir etiquetas de valor en las barras
            for bar in bars:
                yval = bar.get_height()
                self.genre_chart_canvas.axes.text(bar.get_x() + bar.get_width()/2.0, yval + 0.05 * max(counts), \
                                                   round(yval,1), ha='center', va='bottom', fontsize=7)
        else:
            self.genre_chart_canvas.axes.text(0.5, 0.5, 'No hay datos de género suficientes', \
                                              horizontalalignment='center', verticalalignment='center')
        self.genre_chart_canvas.draw()

    def plot_bpm_distribution(self):
        """Crea y muestra un histograma para la distribución de BPM."""
        self.ensure_db_connection()
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT bpm FROM tracks WHERE bpm IS NOT NULL")
        data = [row[0] for row in cursor.fetchall()]

        self.bpm_chart_canvas.axes.cla()
        if data:
            # Crear rangos para el histograma
            bins = [60, 80, 100, 120, 140, 160, 180, 200] # Definir rangos de BPM
            
            n, bins, patches = self.bpm_chart_canvas.axes.hist(data, bins=bins, color='skyblue', edgecolor='black', alpha=0.7)
            
            self.bpm_chart_canvas.axes.set_title('Distribución de BPM', fontsize=10)
            self.bpm_chart_canvas.axes.set_xlabel('BPM', fontsize=8)
            self.bpm_chart_canvas.axes.set_ylabel('Número de Tracks', fontsize=8)
            self.bpm_chart_canvas.axes.tick_params(axis='both', labelsize=8)
            self.bpm_chart_canvas.axes.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Añadir etiquetas de valor en las barras del histograma
            for i in range(len(patches)):
                if n[i] > 0 : # Solo añadir texto si la barra tiene altura
                    x_pos = patches[i].get_x() + patches[i].get_width() / 2.0
                    y_pos = patches[i].get_height() + 0.01 * max(n) if n[i] > 0 else 0
                    self.bpm_chart_canvas.axes.text(x_pos, y_pos, str(int(n[i])), \
                                               ha='center', va='bottom', fontsize=7)

        else:
            self.bpm_chart_canvas.axes.text(0.5, 0.5, 'No hay datos de BPM suficientes', \
                                            horizontalalignment='center', verticalalignment='center')
        self.bpm_chart_canvas.draw()
        
    def plot_key_distribution(self):
        """Crea y muestra un gráfico de barras para la distribución de tonalidades."""
        self.ensure_db_connection()
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT COALESCE(key, 'N/A') as musical_key, COUNT(*) as count
            FROM tracks
            WHERE key IS NOT NULL AND key != ''
            GROUP BY musical_key
            ORDER BY count DESC
            LIMIT 7  -- Mostrar las 7 tonalidades más comunes
        """)
        data = cursor.fetchall()

        self.key_chart_canvas.axes.cla()
        if data:
            keys = [row[0] for row in data]
            counts = [row[1] for row in data]
            
            colors = plt.colormaps.get_cmap('coolwarm')(np.linspace(0, 1, len(keys))) # Corregido get_cmap y usando numpy
            bars = self.key_chart_canvas.axes.bar(keys, counts, color=colors)
            
            self.key_chart_canvas.axes.set_title('Distribución por Tonalidad (Top 7)', fontsize=10)
            self.key_chart_canvas.axes.set_ylabel('Número de Tracks', fontsize=8)
            self.key_chart_canvas.axes.set_xticks(range(len(keys))) # Añadido para definir explícitamente los ticks
            self.key_chart_canvas.axes.set_xticklabels(keys, rotation=30, ha='right', fontsize=8) # Nueva forma de setear etiquetas X
            self.key_chart_canvas.axes.tick_params(axis='y', labelsize=8) # Cambiado fontsize a labelsize
            self.key_chart_canvas.axes.grid(axis='y', linestyle='--', alpha=0.7)

            for bar in bars:
                yval = bar.get_height()
                self.key_chart_canvas.axes.text(bar.get_x() + bar.get_width()/2.0, yval + 0.05 * max(counts), \
                                                round(yval,1), ha='center', va='bottom', fontsize=7)
        else:
            self.key_chart_canvas.axes.text(0.5, 0.5, 'No hay datos de tonalidad suficientes', \
                                             horizontalalignment='center', verticalalignment='center')
        self.key_chart_canvas.draw()

    def create_dj_tab(self):
        """Crea el tab de herramientas de DJ."""
        return DJToolsTab(self.db_conn)

    def closeEvent(self, event):
        # Limpiar recursos de audio si existe el tab de DJ
        if hasattr(self, 'dj_tab') and hasattr(self.dj_tab, 'cleanup'):
            self.dj_tab.cleanup()
        
        if self.db_conn:
            self.db_conn.close()
            print(f"Conexión a la base de datos {DB_FILE} cerrada.")
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Crear ventana principal
    window = MainWindow() 
    if not window.db_conn: # Si la conexión falló críticamente en el init
        # Los mensajes de error ya se habrán mostrado.
        # Podemos decidir cerrar aquí si es un fallo irrecuperable.
        print("Error crítico con la base de datos. Cerrando aplicación.")
        sys.exit(1)
    
    window.show()
    sys.exit(app.exec()) 
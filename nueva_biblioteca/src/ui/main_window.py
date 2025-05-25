"""
Ventana principal de Nueva Biblioteca - UI Funcional Completa
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QStatusBar, QMenuBar, QMenu,
    QMessageBox, QFileDialog, QSplitter, QProgressBar
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QThread
from PySide6.QtGui import QScreen, QGuiApplication, QIcon, QAction

from .dialogs import ImportDialog, PreferencesDialog
from .components.search_bar import SearchBar
from .components.library_panel import LibraryPanel
from .views.library_view import LibraryView
from .components.filter_panel import FilterPanel
from .components.player_controls import PlayerControls

from ..services.music_service import MusicService
from ..services.rule_service import RuleService
from ..importers.import_manager import ImportManager, ImportProgress, ImportResult

class RefreshLibraryWorker(QThread):
    """Worker thread para actualizar la biblioteca en segundo plano."""
    finished = Signal(dict)
    
    def __init__(self, music_service: MusicService):
        super().__init__()
        self.music_service = music_service
    
    def run(self):
        """Ejecuta la actualización de biblioteca en segundo plano."""
        try:
            # Obtener estadísticas actualizadas
            stats = self.music_service.get_statistics()
            self.finished.emit(stats)
        except Exception as e:
            self.finished.emit({
                'total_tracks': 0,
                'total_artists': 0,
                'total_albums': 0,
                'error': str(e)
            })

class MainWindow(QMainWindow):
    """Ventana principal con UI funcional completa integrada con servicios backend."""
    
    def __init__(self):
        super().__init__()
        
        # Inicializar servicios
        self.music_service = MusicService()
        self.rule_service = RuleService(self.music_service)
        self.import_manager = ImportManager()
        
        # Datos de estado
        self._current_tracks = []
        self._filtered_tracks = []
        
        # Setup UI completa
        self.setup_ui()
        self.setup_connections()
        self.setup_styles()
        
        # Cargar datos iniciales
        self.load_initial_data()
        
    def setup_ui(self):
        """Configura la interfaz de usuario completa."""
        self.setWindowTitle("Nueva Biblioteca - Gestión Musical")
        self.resize(1400, 900)  # Tamaño apropiado para todos los componentes
        
        # Crear menús
        self.create_menus()
        
        # Widget central con splitter principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Barra de búsqueda en la parte superior
        self.search_bar = SearchBar()
        main_layout.addWidget(self.search_bar)
        
        # Splitter horizontal principal (panel lateral + contenido principal)
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter, 1)
        
        # Panel lateral izquierdo
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        
        # LibraryPanel con navegación y estadísticas
        self.library_panel = LibraryPanel()
        left_layout.addWidget(self.library_panel, 1)
        
        # FilterPanel para reglas y filtros avanzados
        self.filter_panel = FilterPanel()
        left_layout.addWidget(self.filter_panel)
        
        left_panel.setMaximumWidth(350)
        left_panel.setMinimumWidth(280)
        main_splitter.addWidget(left_panel)
        
        # Área principal de contenido
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        
        # Vista principal de biblioteca
        self.library_view = LibraryView()
        content_layout.addWidget(self.library_view, 1)
        
        # Controles de reproductor en la parte inferior
        self.player_controls = PlayerControls()
        content_layout.addWidget(self.player_controls)
        
        main_splitter.addWidget(content_widget)
        
        # Configurar proporciones del splitter (25% panel lateral, 75% contenido)
        main_splitter.setSizes([350, 1050])
        
        # Barra de estado con información
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Indicador de progreso para operaciones largas
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Label de estado
        self.status_label = self.status_bar.showMessage("Listo")
        
    def setup_connections(self):
        """Configura todas las conexiones entre componentes y servicios."""
        
        # === Conexiones SearchBar ===
        self.search_bar.search_changed.connect(self.on_search_changed)
        self.search_bar.rule_applied.connect(self.on_rule_applied)
        self.search_bar.quick_filter_applied.connect(self.on_quick_filter_applied)
        self.search_bar.search_cleared.connect(self.on_search_cleared)
        self.search_bar.rule_help_requested.connect(self.show_rule_help)
        
        # === Conexiones LibraryPanel ===
        self.library_panel.library_selected.connect(self.on_library_selected)
        self.library_panel.folder_selected.connect(self.on_folder_selected)
        self.library_panel.create_library_requested.connect(self.create_new_library)
        self.library_panel.import_music_requested.connect(self.import_music_from_folder)
        
        # === Conexiones LibraryView ===
        self.library_view.track_selected.connect(self.on_track_selected)
        self.library_view.track_double_clicked.connect(self.on_track_double_clicked)
        
        # === Conexiones FilterPanel ===
        self.filter_panel.filter_applied.connect(self.on_advanced_filter_applied)
        self.filter_panel.filter_cleared.connect(self.on_filter_cleared)
        self.filter_panel.rule_validated.connect(self.on_rule_validated)
        self.filter_panel.quick_rule_applied.connect(self.on_rule_applied)
        
        # === Conexiones PlayerControls ===
        self.player_controls.play_requested.connect(self.on_play_requested)
        self.player_controls.pause_requested.connect(self.on_pause_requested)
        self.player_controls.stop_requested.connect(self.on_stop_requested)
        self.player_controls.next_requested.connect(self.on_next_requested)
        self.player_controls.previous_requested.connect(self.on_previous_requested)
        
        # === Conexiones RuleService ===
        self.rule_service.tracks_filtered.connect(self.on_tracks_filtered)
        self.rule_service.rule_validated.connect(self.on_rule_validation_result)
        self.rule_service.playlist_created.connect(self.on_playlist_created)
        self.rule_service.playlist_updated.connect(self.on_playlist_updated)
        self.rule_service.playlist_deleted.connect(self.on_playlist_deleted)
        
    def setup_styles(self):
        """Configura los estilos globales de la aplicación."""
        self.setStyleSheet("""
            QMainWindow {
                background: #1C1B1F;
                color: #E6E1E5;
            }
            QSplitter::handle {
                background: rgba(103, 80, 164, 0.3);
                width: 2px;
                height: 2px;
            }
            QSplitter::handle:hover {
                background: rgba(103, 80, 164, 0.5);
            }
        """)
        
    def load_initial_data(self):
        """Carga los datos iniciales de la biblioteca."""
        try:
            # Cargar todos los tracks
            self._current_tracks = self.music_service.get_all_tracks()
            self._filtered_tracks = self._current_tracks.copy()
            
            # Actualizar vistas
            self.library_view.update_tracks(self._filtered_tracks)
            
            # Actualizar estadísticas
            self.update_library_statistics()
            
            # Actualizar sugerencias de búsqueda
            self.update_search_suggestions()
            
            # Actualizar datos en componentes
            self.update_filter_panel_data()
            
            # Mensaje en status bar
            track_count = len(self._current_tracks)
            self.status_bar.showMessage(f"Biblioteca cargada: {track_count} tracks")
            
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Error", 
                f"Error cargando datos iniciales: {str(e)}"
            )
            self.status_bar.showMessage("Error cargando biblioteca")
    
    def update_library_statistics(self):
        """Actualiza las estadísticas mostradas en LibraryPanel."""
        try:
            stats = self.music_service.get_statistics()
            self.library_panel.update_stats(
                stats.get('total_tracks', 0),
                stats.get('total_artists', 0), 
                stats.get('total_albums', 0)
            )
        except Exception as e:
            print(f"Error actualizando estadísticas: {e}")
    
    def update_search_suggestions(self):
        """Actualiza las sugerencias de autocompletado."""
        try:
            # Obtener artistas y géneros para sugerencias
            artists = self.music_service.get_artists()
            genres = self.music_service.get_genres()
            
            # Combinar sugerencias
            suggestions = artists + genres
            self.search_bar.set_suggestions(suggestions)
            
        except Exception as e:
            print(f"Error actualizando sugerencias: {e}")
    
    def update_filter_panel_data(self):
        """Actualiza los datos en FilterPanel."""
        try:
            # Actualizar listas de artistas y géneros
            artists = self.music_service.get_artists()
            genres = self.music_service.get_genres()
            
            self.filter_panel.update_artists(artists)
            self.filter_panel.update_genres(genres)
            
        except Exception as e:
            print(f"Error actualizando datos de FilterPanel: {e}")
    
    # === Handlers de SearchBar ===
    
    def on_search_changed(self, query: str):
        """Maneja cambios en la búsqueda de texto."""
        try:
            if query.strip():
                # Búsqueda de texto simple
                filtered_tracks = self.music_service.search_tracks(query)
                self._filtered_tracks = filtered_tracks
            else:
                # Sin búsqueda, mostrar todos
                self._filtered_tracks = self._current_tracks.copy()
            
            self.library_view.update_tracks(self._filtered_tracks)
            self.status_bar.showMessage(f"Búsqueda: {len(self._filtered_tracks)} resultados")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error en búsqueda: {str(e)}")
    
    def on_rule_applied(self, rule_expression: str):
        """Maneja aplicación de reglas desde SearchBar."""
        try:
            filtered_tracks = self.rule_service.apply_filter_rule(rule_expression)
            self._filtered_tracks = filtered_tracks
            self.library_view.update_tracks(self._filtered_tracks)
            
            count = len(self._filtered_tracks)
            self.status_bar.showMessage(f"Regla aplicada: {count} tracks")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error aplicando regla: {str(e)}")
    
    def on_quick_filter_applied(self, rule_expression: str):
        """Maneja aplicación de filtros rápidos."""
        self.on_rule_applied(rule_expression)
    
    def on_search_cleared(self):
        """Maneja limpieza de búsqueda."""
        self._filtered_tracks = self._current_tracks.copy()
        self.library_view.update_tracks(self._filtered_tracks)
        self.status_bar.showMessage("Búsqueda limpiada")
    
    def show_rule_help(self):
        """Muestra ayuda sobre reglas."""
        examples = self.rule_service.get_rule_examples()
        help_text = "Ejemplos de reglas:\n\n"
        
        for example in examples[:8]:  # Mostrar solo los primeros 8 ejemplos
            help_text += f"• {example['rule']}\n  {example['description']}\n\n"
        
        QMessageBox.information(self, "Ayuda de Reglas", help_text)
    
    # === Handlers de LibraryPanel ===
    
    def on_library_selected(self, library_path: str):
        """Maneja selección de biblioteca."""
        self.status_bar.showMessage(f"Biblioteca seleccionada: {library_path}")
    
    def on_folder_selected(self, folder_info: str):
        """Maneja selección de carpeta/categoría."""
        try:
            # Parsear información de carpeta (formato: "tipo:nombre")
            if ":" in folder_info:
                filter_type, filter_name = folder_info.split(":", 1)
                
                # Aplicar filtro según el tipo
                if filter_type == "genre":
                    rule = f"genre = '{filter_name}'"
                elif filter_type == "artist":
                    rule = f"artist = '{filter_name}'"
                elif filter_type == "album":
                    rule = f"album = '{filter_name}'"
                else:
                    return
                
                # Aplicar filtro
                filtered_tracks = self.rule_service.apply_filter_rule(rule)
                self._filtered_tracks = filtered_tracks
                self.library_view.update_tracks(self._filtered_tracks)
                
                count = len(self._filtered_tracks)
                self.status_bar.showMessage(f"Filtrado por {filter_type}: {count} tracks")
                
        except Exception as e:
            print(f"Error procesando selección de carpeta: {e}")
    
    def create_new_library(self):
        """Crea una nueva biblioteca."""
        # TODO: Implementar diálogo de nueva biblioteca
        QMessageBox.information(self, "Nueva Biblioteca", "Función en desarrollo")
    
    def import_music_from_folder(self, folder_path: str):
        """Importa música desde una carpeta."""
        self.open_import_dialog_with_path(folder_path)
    
    # === Handlers de LibraryView ===
    
    def on_track_selected(self, track_data: dict):
        """Maneja selección de track."""
        track_title = track_data.get('title', 'Desconocido')
        track_artist = track_data.get('artist', 'Desconocido')
        self.status_bar.showMessage(f"Seleccionado: {track_artist} - {track_title}")
    
    def on_track_double_clicked(self, track_data: dict):
        """Maneja doble clic en track (reproducir)."""
        # Establecer track en reproductor
        self.player_controls.set_current_track(track_data)
        
        track_title = track_data.get('title', 'Desconocido')
        self.status_bar.showMessage(f"Reproduciendo: {track_title}")
    
    # === Handlers de FilterPanel ===
    
    def on_advanced_filter_applied(self, filter_data: dict):
        """Maneja aplicación de filtros avanzados."""
        try:
            # Construir regla desde filter_data
            # TODO: Implementar construcción de regla compleja
            rule = filter_data.get('rule', '')
            if rule:
                self.on_rule_applied(rule)
        except Exception as e:
            print(f"Error aplicando filtro avanzado: {e}")
    
    def on_filter_cleared(self):
        """Maneja limpieza de filtros."""
        self.on_search_cleared()
    
    def on_rule_validated(self, is_valid: bool, message: str):
        """Maneja solicitud de validación de reglas desde FilterPanel."""
        try:
            # Validar regla usando RuleService
            is_valid, validation_message, used_fields = self.rule_service.validate_rule_expression(message)
            
            # Actualizar FilterPanel con resultado
            self.filter_panel.set_validation_result(is_valid, validation_message)
            
            # Actualizar status bar
            if is_valid:
                self.status_bar.showMessage(f"Regla válida: {validation_message}")
            else:
                self.status_bar.showMessage(f"Error en regla: {validation_message}")
                
        except Exception as e:
            error_msg = f"Error validando regla: {str(e)}"
            self.filter_panel.set_validation_result(False, error_msg)
            self.status_bar.showMessage(error_msg)
    
    # === Handlers de PlayerControls ===
    
    def on_play_requested(self):
        """Maneja solicitud de reproducción."""
        self.status_bar.showMessage("Reproduciendo...")
    
    def on_pause_requested(self):
        """Maneja solicitud de pausa."""
        self.status_bar.showMessage("Pausado")
    
    def on_stop_requested(self):
        """Maneja solicitud de detener."""
        self.status_bar.showMessage("Detenido")
    
    def on_next_requested(self):
        """Maneja solicitud de siguiente track."""
        self.status_bar.showMessage("Siguiente track")
    
    def on_previous_requested(self):
        """Maneja solicitud de track anterior."""
        self.status_bar.showMessage("Track anterior")
    
    # === Handlers de RuleService ===
    
    def on_tracks_filtered(self, filtered_tracks: list):
        """Maneja resultado de filtrado de tracks."""
        self._filtered_tracks = filtered_tracks
        self.library_view.update_tracks(self._filtered_tracks)
    
    def on_rule_validation_result(self, is_valid: bool, message: str):
        """Maneja resultado de validación de reglas."""
        self.on_rule_validated(is_valid, message)
    
    def on_playlist_created(self, playlist_id: str, playlist_name: str):
        """Maneja creación de playlist."""
        self.status_bar.showMessage(f"Playlist creada: {playlist_name}")
    
    def on_playlist_updated(self, playlist_id: str, playlist_name: str):
        """Maneja actualización de playlist."""
        self.status_bar.showMessage(f"Playlist actualizada: {playlist_name}")
    
    def on_playlist_deleted(self, playlist_id: str, playlist_name: str):
        """Maneja eliminación de playlist."""
        self.status_bar.showMessage(f"Playlist eliminada: {playlist_name}")
        
    # === Métodos de menús ===
    
    def create_menus(self):
        """Crea los menús de la aplicación."""
        # Menú Archivo
        file_menu = self.menuBar().addMenu("&Archivo")
        
        # Acción Importar
        import_action = QAction("&Importar Música...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.open_import_dialog)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # Acción Actualizar Biblioteca
        refresh_action = QAction("&Actualizar Biblioteca", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_library)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        # Acción Preferencias
        preferences_action = QAction("&Preferencias...", self)
        preferences_action.setShortcut("Ctrl+P")
        preferences_action.triggered.connect(self.open_preferences_dialog)
        file_menu.addAction(preferences_action)
        
        file_menu.addSeparator()
        
        # Acción Salir
        exit_action = QAction("&Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Vista
        view_menu = self.menuBar().addMenu("&Vista")
        
        # Alternar panel lateral
        toggle_sidebar_action = QAction("Mostrar/Ocultar Panel Lateral", self)
        toggle_sidebar_action.setShortcut("Ctrl+B")
        toggle_sidebar_action.triggered.connect(self.toggle_sidebar)
        view_menu.addAction(toggle_sidebar_action)
        
        # Enfocar búsqueda
        focus_search_action = QAction("Enfocar Búsqueda", self)
        focus_search_action.setShortcut("Ctrl+F")
        focus_search_action.triggered.connect(self.focus_search)
        view_menu.addAction(focus_search_action)
        
        # Menú Herramientas
        tools_menu = self.menuBar().addMenu("&Herramientas")
        
        # Crear playlist inteligente
        smart_playlist_action = QAction("Crear Playlist &Inteligente...", self)
        smart_playlist_action.setShortcut("Ctrl+Shift+N")
        smart_playlist_action.triggered.connect(self.create_smart_playlist)
        tools_menu.addAction(smart_playlist_action)
        
        # Validador de reglas
        rule_validator_action = QAction("&Validador de Reglas...", self)
        rule_validator_action.triggered.connect(self.show_rule_validator)
        tools_menu.addAction(rule_validator_action)
        
        # Menú Ayuda
        help_menu = self.menuBar().addMenu("A&yuda")
        
        # Ayuda de reglas
        rule_help_action = QAction("Ayuda de &Reglas", self)
        rule_help_action.setShortcut("F1")
        rule_help_action.triggered.connect(self.show_rule_help)
        help_menu.addAction(rule_help_action)
        
        help_menu.addSeparator()
        
        # Acción Acerca de
        about_action = QAction("&Acerca de", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    # === Acciones de menú ===
    
    def open_import_dialog(self):
        """Abre el diálogo de importación."""
        dialog = ImportDialog(self.music_service, self)
        if dialog.exec():
            # Recargar datos después de importar
            self.refresh_library()
    
    def open_import_dialog_with_path(self, folder_path: str):
        """Abre el diálogo de importación con ruta preseleccionada."""
        dialog = ImportDialog(self.music_service, self)
        dialog.set_import_path(folder_path)
        if dialog.exec():
            self.refresh_library()
    
    def refresh_library(self):
        """Actualiza la biblioteca completa."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminado
        self.status_bar.showMessage("Actualizando biblioteca...")
        
        # Crear un worker thread para la actualización
        worker = RefreshLibraryWorker(self.music_service)
        worker.finished.connect(self._finish_refresh)
        worker.start()
    
    def _finish_refresh(self, stats):
        """
        Finaliza la actualización de biblioteca.
        
        Args:
            stats: Estadísticas actualizadas de la biblioteca
        """
        # Cargar datos nuevos
        self.load_initial_data()
        
        # Actualizar UI
        self.progress_bar.setVisible(False)
        
        # Mostrar información detallada
        track_count = stats.get('total_tracks', 0)
        artist_count = stats.get('total_artists', 0)
        album_count = stats.get('total_albums', 0)
        
        self.status_bar.showMessage(
            f"Biblioteca actualizada: {track_count} tracks, {artist_count} artistas, {album_count} álbumes"
        )
    
    def open_preferences_dialog(self):
        """Abre el diálogo de preferencias."""
        dialog = PreferencesDialog(self)
        dialog.exec()
    
    def toggle_sidebar(self):
        """Alterna la visibilidad del panel lateral."""
        # TODO: Implementar ocultación del panel lateral
        pass
    
    def focus_search(self):
        """Enfoca el campo de búsqueda."""
        self.search_bar.focus_search()
    
    def create_smart_playlist(self):
        """Crea una nueva playlist inteligente."""
        # TODO: Implementar diálogo de playlist inteligente
        QMessageBox.information(self, "Playlist Inteligente", "Función en desarrollo")
    
    def show_rule_validator(self):
        """Muestra el validador de reglas."""
        # TODO: Implementar validador de reglas
        QMessageBox.information(self, "Validador de Reglas", "Función en desarrollo")
    
    def show_about_dialog(self):
        """Muestra el diálogo de acerca de."""
        QMessageBox.about(
            self,
            "Acerca de Nueva Biblioteca",
            """<h3>Nueva Biblioteca</h3>
            <p>Sistema de gestión musical con reglas inteligentes.</p>
            <p>Donde la música inteligente encuentra el diseño expresivo.</p>
            <p><strong>Características:</strong></p>
            <ul>
            <li>Búsqueda en tiempo real</li>
            <li>Motor de reglas avanzado</li>
            <li>Playlists inteligentes</li>
            <li>Interfaz Material 3 Expressive</li>
            </ul>
            <p><small>Versión 1.0.0</small></p>"""
        )
    
    def center_on_screen(self):
        """Centra la ventana en la pantalla."""
        screen = QGuiApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            frame = self.frameGeometry()
            frame.moveCenter(geometry.center())
            self.move(frame.topLeft())

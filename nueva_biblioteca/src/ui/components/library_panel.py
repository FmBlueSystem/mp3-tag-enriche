"""
Panel de navegación de biblioteca con Material 3 Expressive.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, 
    QTreeWidgetItem, QPushButton, QLabel, QFrame,
    QMenu, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont, QAction


class LibraryPanel(QWidget):
    """
    Panel de navegación de biblioteca con diseño Material 3 Expressive.
    
    Características:
    - Árbol de navegación expresivo
    - Acciones contextuales
    - Indicadores visuales de estado
    - Animaciones suaves
    """
    
    # Señales
    library_selected = Signal(str)
    folder_selected = Signal(str)
    create_library_requested = Signal()
    import_music_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_connections()
        self._populate_tree()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Encabezado con acciones
        header = self._create_header()
        layout.addWidget(header)
        
        # Árbol de navegación
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background: rgba(28, 27, 31, 0.4);
                border: 1px solid rgba(103, 80, 164, 0.2);
                border-radius: 12px;
                color: #E6E1E5;
                font-size: 13px;
                padding: 8px;
            }
            QTreeWidget::item {
                padding: 8px 12px;
                border-radius: 6px;
                margin: 1px 0px;
            }
            QTreeWidget::item:hover {
                background: rgba(103, 80, 164, 0.2);
            }
            QTreeWidget::item:selected {
                background: rgba(103, 80, 164, 0.3);
                color: #D0BCFF;
            }
            QTreeWidget::branch {
                background: transparent;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                image: url(:/icons/chevron_right.png);
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                image: url(:/icons/expand_more.png);
            }
        """)
        layout.addWidget(self.tree, 1)
        
        # Panel de estadísticas
        stats_panel = self._create_stats_panel()
        layout.addWidget(stats_panel)
        
    def _create_header(self) -> QWidget:
        """Crea el encabezado del panel."""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: rgba(103, 80, 164, 0.1);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Título
        title = QLabel("Biblioteca")
        title.setStyleSheet("""
            QLabel {
                color: #E6E1E5;
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Botón de nueva biblioteca
        new_btn = QPushButton("＋")
        new_btn.setFixedSize(28, 28)
        new_btn.setToolTip("Nueva biblioteca")
        new_btn.setStyleSheet("""
            QPushButton {
                background: rgba(103, 80, 164, 0.3);
                border: none;
                border-radius: 14px;
                color: #D0BCFF;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(103, 80, 164, 0.4);
                transform: scale(1.1);
            }
            QPushButton:pressed {
                background: rgba(103, 80, 164, 0.5);
            }
        """)
        new_btn.clicked.connect(self.create_library_requested.emit)
        layout.addWidget(new_btn)
        
        # Botón de menú
        menu_btn = QPushButton("⋮")
        menu_btn.setFixedSize(28, 28)
        menu_btn.setToolTip("Opciones")
        menu_btn.setStyleSheet("""
            QPushButton {
                background: rgba(103, 80, 164, 0.2);
                border: none;
                border-radius: 14px;
                color: #CAC4D0;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(103, 80, 164, 0.3);
            }
        """)
        menu_btn.clicked.connect(self._show_menu)
        layout.addWidget(menu_btn)
        
        return header
        
    def _create_stats_panel(self) -> QWidget:
        """Crea el panel de estadísticas."""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: rgba(144, 224, 239, 0.1);
                border: 1px solid rgba(144, 224, 239, 0.2);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # Título
        title = QLabel("Estadísticas")
        title.setStyleSheet("""
            QLabel {
                color: #90E0EF;
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            }
        """)
        layout.addWidget(title)
        
        # Estadísticas
        self.stats_tracks = QLabel("0 pistas")
        self.stats_artists = QLabel("0 artistas")
        self.stats_albums = QLabel("0 álbumes")
        
        for label in [self.stats_tracks, self.stats_artists, self.stats_albums]:
            label.setStyleSheet("""
                QLabel {
                    color: #CAF0F8;
                    font-size: 11px;
                    background: transparent;
                    padding: 2px 0px;
                }
            """)
            layout.addWidget(label)
            
        return panel
        
    def _setup_connections(self):
        """Configura las conexiones de señales."""
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        
    def _populate_tree(self):
        """Puebla el árbol con datos de ejemplo."""
        # Bibliotecas
        libraries_item = QTreeWidgetItem(self.tree, ["📚 Bibliotecas"])
        libraries_item.setExpanded(True)
        
        # Biblioteca principal
        main_lib = QTreeWidgetItem(libraries_item, ["🎵 Mi Biblioteca"])
        main_lib.setData(0, Qt.UserRole, {"type": "library", "path": "/path/to/library"})
        
        # Géneros
        genres_item = QTreeWidgetItem(main_lib, ["🎭 Géneros"])
        for genre in ["Rock", "Pop", "Jazz", "Electronic", "Classical"]:
            genre_item = QTreeWidgetItem(genres_item, [f"♪ {genre}"])
            genre_item.setData(0, Qt.UserRole, {"type": "genre", "name": genre})
            
        # Artistas
        artists_item = QTreeWidgetItem(main_lib, ["👤 Artistas"])
        for artist in ["The Beatles", "Pink Floyd", "Queen", "Led Zeppelin"]:
            artist_item = QTreeWidgetItem(artists_item, [f"🎤 {artist}"])
            artist_item.setData(0, Qt.UserRole, {"type": "artist", "name": artist})
            
        # Álbumes
        albums_item = QTreeWidgetItem(main_lib, ["💿 Álbumes"])
        for album in ["Abbey Road", "Dark Side of the Moon", "A Night at the Opera"]:
            album_item = QTreeWidgetItem(albums_item, [f"💽 {album}"])
            album_item.setData(0, Qt.UserRole, {"type": "album", "name": album})
            
        # Playlists
        playlists_item = QTreeWidgetItem(self.tree, ["📋 Playlists"])
        playlists_item.setExpanded(True)
        
        # Playlists de ejemplo
        for playlist in ["Favoritos", "Rock Clásico", "Chill Out", "Workout"]:
            playlist_item = QTreeWidgetItem(playlists_item, [f"🎶 {playlist}"])
            playlist_item.setData(0, Qt.UserRole, {"type": "playlist", "name": playlist})
            
        # Playlists inteligentes
        smart_item = QTreeWidgetItem(playlists_item, ["🧠 Inteligentes"])
        for smart in ["Recién Agregados", "Más Reproducidos", "Sin Reproducir"]:
            smart_playlist = QTreeWidgetItem(smart_item, [f"⚡ {smart}"])
            smart_playlist.setData(0, Qt.UserRole, {"type": "smart_playlist", "name": smart})
            
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Maneja clics en elementos del árbol."""
        data = item.data(0, Qt.UserRole)
        if data:
            item_type = data.get("type")
            if item_type == "library":
                self.library_selected.emit(data.get("path", ""))
            elif item_type in ["genre", "artist", "album", "playlist", "smart_playlist"]:
                self.folder_selected.emit(f"{item_type}:{data.get('name', '')}")
                
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Maneja doble clic en elementos del árbol."""
        data = item.data(0, Qt.UserRole)
        if data and data.get("type") == "library":
            # Abrir biblioteca
            pass
            
    def _show_menu(self):
        """Muestra el menú contextual."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #2B2930;
                border: 1px solid #6750A4;
                border-radius: 8px;
                color: #E6E1E5;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: rgba(103, 80, 164, 0.3);
            }
        """)
        
        # Acciones del menú
        new_library_action = QAction("Nueva Biblioteca", self)
        new_library_action.triggered.connect(self.create_library_requested.emit)
        menu.addAction(new_library_action)
        
        import_action = QAction("Importar Música", self)
        import_action.triggered.connect(self._import_music)
        menu.addAction(import_action)
        
        menu.addSeparator()
        
        refresh_action = QAction("Actualizar", self)
        refresh_action.triggered.connect(self._refresh_tree)
        menu.addAction(refresh_action)
        
        # Mostrar menú
        menu.exec(self.mapToGlobal(self.sender().pos()))
        
    def _import_music(self):
        """Importa música a la biblioteca."""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Seleccionar carpeta de música",
            ""
        )
        if folder:
            self.import_music_requested.emit(folder)
            
    def _refresh_tree(self):
        """Actualiza el árbol de navegación."""
        # TODO: Implementar actualización real
        self._populate_tree()
        
    def update_stats(self, tracks: int, artists: int, albums: int):
        """Actualiza las estadísticas mostradas."""
        self.stats_tracks.setText(f"{tracks:,} pistas")
        self.stats_artists.setText(f"{artists:,} artistas")
        self.stats_albums.setText(f"{albums:,} álbumes")
        
    def add_library(self, name: str, path: str):
        """Añade una nueva biblioteca al árbol."""
        # TODO: Implementar adición de biblioteca
        pass
        
    def remove_library(self, path: str):
        """Elimina una biblioteca del árbol."""
        # TODO: Implementar eliminación de biblioteca
        pass 
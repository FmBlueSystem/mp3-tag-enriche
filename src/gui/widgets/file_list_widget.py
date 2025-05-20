"""Widget for displaying and managing the file list."""
from PySide6.QtWidgets import QListView, QAbstractItemView, QWidget, QScroller
from PySide6.QtCore import Qt, Signal, QAbstractListModel, QModelIndex
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from pathlib import Path
import os
import logging
from typing import List, Optional, Dict, Set
from collections import OrderedDict

from ..i18n import tr

logger = logging.getLogger(__name__)

class FileListModel(QAbstractListModel):
    """Modelo optimizado para manejo de archivos."""
    def __init__(self):
        super().__init__()
        self.file_paths: List[str] = []
        self.displayed_paths: OrderedDict = OrderedDict()
        self.cache_size = 1000
        self.page_size = 100
        self.current_page = 0
    
    def rowCount(self, parent=QModelIndex()) -> int:
        """Retorna el número total de archivos."""
        return len(self.file_paths)
    
    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        """Obtiene datos para el índice dado."""
        if not index.isValid():
            return None
            
        row = index.row()
        if row < 0 or row >= len(self.file_paths):
            return None
            
        if role == Qt.DisplayRole:
            filepath = self.file_paths[row]
            return os.path.basename(filepath)
        elif role == Qt.UserRole:
            return self.file_paths[row]
            
        return None
    
    def add_files(self, files: List[str]) -> int:
        """Añade archivos al modelo."""
        new_files = [f for f in files if f.lower().endswith('.mp3') and f not in self.file_paths]
        if not new_files:
            return 0
            
        start_index = len(self.file_paths)
        self.beginInsertRows(QModelIndex(), start_index, start_index + len(new_files) - 1)
        self.file_paths.extend(new_files)
        self.endInsertRows()
        
        return len(new_files)
    
    def get_page(self, page: int) -> List[str]:
        """Obtiene una página de archivos."""
        start_idx = page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.file_paths))
        return self.file_paths[start_idx:end_idx]
    
    def update_cache(self, visible_range: tuple) -> None:
        """Actualiza la caché de items visibles."""
        start, end = visible_range
        new_displayed = OrderedDict()
        
        # Añadir items visibles y algunos extras como buffer
        buffer = self.page_size // 2
        cache_start = max(0, start - buffer)
        cache_end = min(len(self.file_paths), end + buffer)
        
        for idx in range(cache_start, cache_end):
            filepath = self.file_paths[idx]
            new_displayed[filepath] = idx
            
        # Mantener tamaño de caché
        while len(new_displayed) > self.cache_size:
            new_displayed.popitem(last=False)
            
        self.displayed_paths = new_displayed

class FileListWidget(QListView):
    """Custom widget for file listing with virtualización y carga lazy."""
    files_added = Signal(int)  # Señal emitida cuando se añaden archivos (cantidad)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model = FileListModel()
        self.setModel(self.model)
        
        # Configuración de la vista
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setUniformItemSizes(True)  # Optimización para virtualización
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setViewportMargins(0, 0, 0, 0)
        
        # Habilitar scroll suave
        QScroller.grabGesture(self.viewport(), QScroller.TouchGesture)
        
        # Configuración de accesibilidad y UI
        self.setAcceptDrops(True)
        self.setAccessibleName(tr("accessibility_file_list"))
        self.setAccessibleDescription(tr("accessibility_file_list_desc"))
        self.setToolTip(tr("tooltip_file_list"))
        self.setMinimumHeight(200)
        self.setAlternatingRowColors(True)
        
        # Conectar señales
        self.verticalScrollBar().valueChanged.connect(self._handle_scroll)
    
    def _handle_scroll(self, value: int) -> None:
        """Maneja eventos de scroll para actualizar caché."""
        viewport_height = self.viewport().height()
        item_height = self.sizeHintForRow(0)
        
        if item_height <= 0:
            return
            
        visible_items = viewport_height // item_height
        start_item = value // item_height
        end_item = start_item + visible_items + 1
        
        self.model.update_cache((start_item, end_item))
        
    def add_files(self, files: List[str]) -> int:
        """
        Añade archivos a la lista.
        
        Args:
            files: Lista de rutas de archivos a añadir
            
        Returns:
            int: Cantidad de archivos añadidos
        """
        try:
            added_count = self.model.add_files(files)
            
            if added_count > 0:
                self.files_added.emit(added_count)
                logger.info(f"Added {added_count} files to the list")
            
            return added_count
        except Exception as e:
            logger.error(f"Error adding files: {e}")
            return 0
    
    def add_folder(self, folder_path: str) -> int:
        """
        Añade todos los archivos MP3 de una carpeta.
        
        Args:
            folder_path: Ruta de la carpeta a procesar
            
        Returns:
            int: Cantidad de archivos añadidos
        """
        try:
            files = [str(f) for f in Path(folder_path).rglob("*.mp3")]
            return self.add_files(files)
        except Exception as e:
            logger.error(f"Error processing folder {folder_path}: {e}")
            return 0
    
    def get_selected_files(self) -> List[str]:
        """
        Get the full paths of selected files.
        
        Returns:
            List[str]: List of selected file paths
        """
        indexes = self.selectionModel().selectedIndexes()
        return [self.model.data(idx, Qt.UserRole) for idx in indexes]
    
    def get_all_files(self) -> List[str]:
        """
        Get the full paths of all files.
        
        Returns:
            List[str]: List of all file paths
        """
        return self.model.file_paths.copy()
    
    def clear_list(self) -> None:
        """Clear the file list."""
        self.model.beginResetModel()
        self.model.file_paths.clear()
        self.model.displayed_paths.clear()
        self.model.endResetModel()
        logger.debug("File list cleared")
        
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        Handle drag enter events for files.
        
        Args:
            event: Drag event
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent) -> None:
        """
        Handle drop events for files.
        
        Args:
            event: Drop event
        """
        files = []
        try:
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path) and path.lower().endswith('.mp3'):
                    files.append(path)
                elif os.path.isdir(path):
                    self.add_folder(path)
            
            if files:
                self.add_files(files)
        except Exception as e:
            logger.error(f"Error processing dropped files: {e}")

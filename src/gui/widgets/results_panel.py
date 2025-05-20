"""Results display panel widget."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListView, 
                             QAbstractItemView, QScrollBar)
from PySide6.QtCore import Qt, QTimer, QAbstractListModel, QModelIndex, Signal
from PySide6.QtGui import QColor
import logging
from typing import Dict, Optional, List, Deque
from collections import deque
import time

from ..i18n import tr

logger = logging.getLogger(__name__)

class ResultsModel(QAbstractListModel):
    """Modelo optimizado para resultados."""
    
    MAX_RESULTS = 10000  # Máximo número de resultados a mantener
    
    def __init__(self):
        super().__init__()
        self.results: Deque[tuple] = deque(maxlen=self.MAX_RESULTS)
        self.pending_updates: List[tuple] = []
        self.batch_size = 50
        self.last_update = 0
        self.update_interval = 100  # ms
    
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.results)
    
    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
            
        row = index.row()
        if row < 0 or row >= len(self.results):
            return None
            
        message, is_error = self.results[row]
        
        if role == Qt.DisplayRole:
            return message
        elif role == Qt.ForegroundRole and is_error:
            return QColor(Qt.red)
            
        return None
    
    def add_result(self, message: str, error: bool = False) -> None:
        """Agrega un resultado al buffer."""
        self.pending_updates.append((message, error))
        
        current_time = time.time() * 1000
        if (current_time - self.last_update >= self.update_interval and 
            len(self.pending_updates) >= self.batch_size):
            self.flush_updates()
    
    def flush_updates(self) -> None:
        """Aplica actualizaciones pendientes."""
        if not self.pending_updates:
            return
            
        start_index = len(self.results)
        self.beginInsertRows(QModelIndex(), start_index, 
                           start_index + len(self.pending_updates) - 1)
        
        self.results.extend(self.pending_updates)
        self.pending_updates.clear()
        self.last_update = time.time() * 1000
        
        self.endInsertRows()
    
    def clear(self) -> None:
        """Limpia todos los resultados."""
        self.beginResetModel()
        self.results.clear()
        self.pending_updates.clear()
        self.endResetModel()

class ResultsPanel(QWidget):
    """Panel for displaying processing results."""
    
    update_requested = Signal()  # Señal para solicitar actualización
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()
        
        # Configurar timer para actualizaciones
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._flush_updates)
        self.update_timer.start(100)  # 100ms intervalo
        
    def setup_ui(self) -> None:
        """Set up the results panel interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Etiqueta de progreso
        self.progress_label = QLabel()
        self.progress_label.setAccessibleName(tr("accessibility_progress"))
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)
        
        # Lista de resultados virtualizada
        self.results_view = QListView()
        self.results_model = ResultsModel()
        self.results_view.setModel(self.results_model)
        
        # Optimizaciones de la vista
        self.results_view.setUniformItemSizes(True)
        self.results_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.results_view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.results_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        # Configuración de accesibilidad
        self.results_view.setAccessibleName(tr("accessibility_results_list"))
        self.results_view.setAccessibleDescription(tr("accessibility_results_desc"))
        self.results_view.setToolTip(tr("tooltip_results"))
        self.results_view.setMinimumHeight(200)
        self.results_view.setAlternatingRowColors(True)
        
        layout.addWidget(self.results_view)
        
    def _flush_updates(self) -> None:
        """Fuerza actualización de resultados pendientes."""
        self.results_model.flush_updates()
        if self.results_view.verticalScrollBar().value() == (
            self.results_view.verticalScrollBar().maximum()):
            self.results_view.scrollToBottom()
        
    def update_progress(self, message: str) -> None:
        """Update the progress message."""
        self.progress_label.setText(message)
        logger.debug(f"Progress updated: {message}")
        
    def clear_progress(self) -> None:
        """Clear the progress message."""
        self.progress_label.clear()
        
    def add_result(self, message: str, error: bool = False) -> None:
        """
        Add a result to the list.
        
        Args:
            message: Message to display
            error: True if this is an error message
        """
        self.results_model.add_result(message, error)
        
    def clear_results(self) -> None:
        """Clear the results list."""
        self.results_model.clear()
        
    def show_summary(self, total: int, success: int, errors: int, renamed: int) -> None:
        """
        Show a summary of the results.
        
        Args:
            total: Total number of processed files
            success: Number of successful operations
            errors: Number of errors
            renamed: Number of renamed files
        """
        self.clear_results()
        
        # Agregar resultados en lote
        summary_items = [
            (tr("summary_total").format(total), False),
            (tr("summary_success").format(success), False),
            (tr("summary_errors").format(errors), errors > 0),
            (tr("summary_renamed").format(renamed), False)
        ]
        
        self.results_model.beginInsertRows(QModelIndex(), 0, len(summary_items)-1)
        self.results_model.results.extend(summary_items)
        self.results_model.endInsertRows()
        
        logger.info(
            f"Processing summary - "
            f"Total: {total}, Success: {success}, "
            f"Errors: {errors}, Renamed: {renamed}"
        )
    
    def closeEvent(self, event) -> None:
        """Limpia recursos al cerrar."""
        self.update_timer.stop()
        super().closeEvent(event)

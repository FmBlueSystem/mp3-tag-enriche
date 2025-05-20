"""Widgets package for Genre Detector GUI."""
# from .file_list_widget import FileListWidget # No longer used
from .control_panel import ControlPanel
from .backup_panel import BackupPanel
# from .results_panel import ResultsPanel # No longer used
from .file_results_table_widget import FileResultsTableWidget

__all__ = ['ControlPanel', 'BackupPanel', 'FileResultsTableWidget']

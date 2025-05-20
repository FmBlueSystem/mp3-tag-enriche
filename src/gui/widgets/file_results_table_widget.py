from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QWidget, QAbstractItemView
from PySide6.QtCore import Qt, Signal
from typing import List, Optional

class FileResultsTableWidget(QTableWidget):
    """Tabla para mostrar archivos, estado y resultados."""
    files_added = Signal(int)  # Señal emitida cuando se añaden archivos

    COL_FILE = 0
    COL_STATUS = 1
    COL_RESULT = 2

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Archivo", "Estado", "Resultado"])
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setMinimumHeight(200)
        self.file_paths_all: List[str] = []

    def add_files(self, files: List[str]) -> int:
        added_count = 0
        for file_path in files:
            if file_path.lower().endswith('.mp3') and file_path not in self.file_paths_all:
                row = self.rowCount()
                self.insertRow(row)
                self.setItem(row, self.COL_FILE, QTableWidgetItem(file_path))
                self.setItem(row, self.COL_STATUS, QTableWidgetItem("Pendiente"))
                self.setItem(row, self.COL_RESULT, QTableWidgetItem(""))
                self.file_paths_all.append(file_path)
                added_count += 1
        if added_count > 0:
            self.files_added.emit(added_count)
        return added_count

    def add_folder(self, folder_path: str) -> int:
        from pathlib import Path
        added_count = 0
        for file_path_obj in Path(folder_path).rglob("*.mp3"):
            file_path = str(file_path_obj)
            if file_path not in self.file_paths_all:
                row = self.rowCount()
                self.insertRow(row)
                self.setItem(row, self.COL_FILE, QTableWidgetItem(file_path))
                self.setItem(row, self.COL_STATUS, QTableWidgetItem("Pendiente"))
                self.setItem(row, self.COL_RESULT, QTableWidgetItem(""))
                self.file_paths_all.append(file_path)
                added_count += 1
        if added_count > 0:
            self.files_added.emit(added_count)
        return added_count

    def update_status(self, file_path: str, status: str):
        for row in range(self.rowCount()):
            if self.item(row, self.COL_FILE).text() == file_path:
                self.setItem(row, self.COL_STATUS, QTableWidgetItem(status))
                break

    def update_result(self, file_path: str, result: str, error: bool = False):
        for row in range(self.rowCount()):
            if self.item(row, self.COL_FILE).text() == file_path:
                item = QTableWidgetItem(result)
                if error:
                    item.setForeground(Qt.red)
                self.setItem(row, self.COL_RESULT, item)
                break

    def clear_table(self):
        self.setRowCount(0)
        self.file_paths_all.clear()

    def get_selected_files(self) -> List[str]:
        return [self.item(row, self.COL_FILE).text() for row in range(self.rowCount()) if self.isRowSelected(row)]

    def get_all_files(self) -> List[str]:
        return self.file_paths_all.copy() 
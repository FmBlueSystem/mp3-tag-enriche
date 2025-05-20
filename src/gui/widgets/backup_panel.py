"""Backup directory selection panel widget."""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QGroupBox, QVBoxLayout
from PySide6.QtCore import Signal
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BackupPanel(QWidget):
    """Panel para la selección del directorio de respaldo."""
    
    backup_dir_changed = Signal(str)  # Emite la nueva ruta cuando cambia
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.backup_dir: Optional[str] = None
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Configura la interfaz del panel de respaldo."""
        main_layout = QVBoxLayout(self) # Layout principal para el QGroupBox
        main_layout.setContentsMargins(0,0,0,0) # El QGroupBox ya tiene márgenes

        backup_group = QGroupBox("Configuración de Respaldo")
        layout = QHBoxLayout(backup_group) # Layout interno del QGroupBox
        layout.setSpacing(8)
        
        # Etiqueta que muestra el directorio actual
        self.backup_dir_label = QLabel("Dir de Respaldo: No establecido")
        self.backup_dir_label.setAccessibleName("Etiqueta Directorio de Respaldo")
        self.backup_dir_label.setToolTip("Directorio donde se guardarán las copias de respaldo")
        layout.addWidget(self.backup_dir_label, 1) # El 1 hace que la etiqueta se expanda
        
        # Botón para seleccionar el directorio
        self.select_backup_dir_btn = QPushButton("Seleccionar...") # Texto más corto
        self.select_backup_dir_btn.setAccessibleName("Botón Seleccionar Directorio de Respaldo")
        self.select_backup_dir_btn.setToolTip("Seleccionar una carpeta para almacenar las copias de respaldo")
        layout.addWidget(self.select_backup_dir_btn)
        
        main_layout.addWidget(backup_group)
        
    def set_backup_dir(self, dir_path: str) -> None:
        """
        Establece el directorio de respaldo.
        
        Args:
            dir_path: Ruta al directorio de respaldo
        """
        try:
            if dir_path and os.path.isdir(dir_path):
                # Only emit signal if directory actually changes
                dir_changed = self.backup_dir != dir_path
                
                self.backup_dir = dir_path
                dirname = os.path.basename(dir_path)
                self.backup_dir_label.setText(f"Dir de Respaldo: {dirname} (...)")
                self.backup_dir_label.setToolTip(dir_path)
                
                if dir_changed:
                    logger.debug(f"Emitiendo backup_dir_changed para: {dir_path}")
                    self.backup_dir_changed.emit(dir_path)
                
                logger.info(f"Directorio de respaldo establecido: {dir_path}")
            else:
                old_dir = self.backup_dir
                self.backup_dir = None
                self.backup_dir_label.setText("Dir de Respaldo: No establecido")
                self.backup_dir_label.setToolTip("Directorio donde se guardarán las copias de respaldo")
                
                if old_dir is not None:
                    logger.debug("Emitiendo backup_dir_changed con cadena vacía")
                    self.backup_dir_changed.emit("")
                
                logger.warning(f"Directorio de respaldo inválido: {dir_path}")
        except Exception as e:
            logger.error(f"Error al establecer directorio de respaldo {dir_path}: {e}")
            old_dir = self.backup_dir
            self.backup_dir = None
            self.backup_dir_label.setText("Dir de Respaldo: Error")
            
            if old_dir is not None:
                logger.debug("Emitiendo backup_dir_changed con cadena vacía debido a error")
                self.backup_dir_changed.emit("")
        
    def get_backup_dir(self) -> str:
        """
        Obtiene el directorio de respaldo actual.
        
        Returns:
            str: Ruta al directorio de respaldo o cadena vacía si no está establecido
        """
        return self.backup_dir if self.backup_dir else ""

    def is_backup_dir_set(self) -> bool:
        """
        Verifica si hay un directorio de respaldo válido establecido.
        
        Returns:
            bool: True si hay un directorio válido establecido
        """
        return bool(self.backup_dir and os.path.isdir(self.backup_dir))

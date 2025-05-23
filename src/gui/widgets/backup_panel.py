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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        backup_group = QGroupBox("Configuración de Respaldo")
        backup_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 2px solid #3E4451;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }
        """)
        layout = QVBoxLayout(backup_group)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 15, 12, 12)
        
        # Etiqueta que muestra el directorio actual
        self.backup_dir_label = QLabel("Dir de Respaldo: No establecido")
        self.backup_dir_label.setAccessibleName("Etiqueta Directorio de Respaldo")
        self.backup_dir_label.setToolTip("Directorio donde se guardarán las copias de respaldo")
        self.backup_dir_label.setWordWrap(True)
        self.backup_dir_label.setStyleSheet("""
            QLabel {
                background-color: #2C323C;
                border: 1px solid #3E4451;
                border-radius: 4px;
                padding: 8px;
                font-size: 9px;
                color: #ABB2BF;
            }
        """)
        layout.addWidget(self.backup_dir_label)
        
        # Botón para seleccionar el directorio
        self.select_backup_dir_btn = QPushButton("📁 Seleccionar Directorio")
        self.select_backup_dir_btn.setAccessibleName("Botón Seleccionar Directorio de Respaldo")
        self.select_backup_dir_btn.setToolTip("Seleccionar una carpeta para almacenar las copias de respaldo")
        self.select_backup_dir_btn.setMinimumHeight(35)
        self.select_backup_dir_btn.setStyleSheet("""
            QPushButton {
                background-color: #528BFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4A7FE7;
            }
            QPushButton:pressed {
                background-color: #3A6FD7;
            }
        """)
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
                
                # Mostrar el nombre del directorio padre y actual de forma compacta
                path_parts = dir_path.split(os.sep)
                if len(path_parts) > 2:
                    display_path = f".../{path_parts[-2]}/{path_parts[-1]}"
                else:
                    display_path = dir_path
                    
                self.backup_dir_label.setText(f"✅ {display_path}")
                self.backup_dir_label.setToolTip(f"Ruta completa: {dir_path}")
                
                if dir_changed:
                    logger.debug(f"Emitiendo backup_dir_changed para: {dir_path}")
                    self.backup_dir_changed.emit(dir_path)
                
                logger.info(f"Directorio de respaldo establecido: {dir_path}")
            else:
                old_dir = self.backup_dir
                self.backup_dir = None
                self.backup_dir_label.setText("❌ No establecido")
                self.backup_dir_label.setToolTip("Selecciona un directorio para guardar las copias de respaldo")
                
                if old_dir is not None:
                    logger.debug("Emitiendo backup_dir_changed con cadena vacía")
                    self.backup_dir_changed.emit("")
                
                logger.warning(f"Directorio de respaldo inválido: {dir_path}")
        except Exception as e:
            logger.error(f"Error al establecer directorio de respaldo {dir_path}: {e}")
            old_dir = self.backup_dir
            self.backup_dir = None
            self.backup_dir_label.setText("⚠️ Error en directorio")
            self.backup_dir_label.setToolTip(f"Error: {str(e)}")
            
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

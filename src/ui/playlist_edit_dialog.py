"""
Dialog para crear y editar playlists inteligentes.
"""

import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QTextEdit, QPushButton, QDialogButtonBox)
from PyQt6.QtCore import Qt


class PlaylistEditDialog(QDialog):
    """Dialog para crear y editar playlists inteligentes."""
    
    def __init__(self, playlist_name="", rule_expression="", parent=None, is_new=True, playlist_id=None):
        super().__init__(parent)
        self.is_new = is_new
        self.playlist_id = playlist_id
        
        self.setWindowTitle("Nueva Playlist Inteligente" if is_new else "Editar Playlist Inteligente")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Campo nombre
        layout.addWidget(QLabel("Nombre de la Playlist:"))
        self.name_input = QLineEdit(playlist_name)
        layout.addWidget(self.name_input)
        
        # Campo regla
        layout.addWidget(QLabel("Regla:"))
        self.rule_input = QTextEdit(rule_expression)
        self.rule_input.setMaximumHeight(100)
        layout.addWidget(self.rule_input)
        
        # Ayuda sobre sintaxis
        help_text = """
Sintaxis de reglas:
• Comparaciones: genre = 'rock', bpm > 120, year >= 2000
• Operadores: =, !=, >, <, >=, <=
• Campos disponibles: title, artist, album, genre, year, bpm, key, energy_level, rating, play_count
• Ejemplos: 
  - genre = 'rock'
  - bpm > 120 AND year >= 2000
  - artist = 'Queen' OR album = 'Bohemian Rhapsody'
        """
        help_label = QLabel(help_text)
        help_label.setStyleSheet("color: gray; font-size: 9pt; padding: 10px; background-color: #f5f5f5; border: 1px solid #ccc;")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_data(self):
        """Retorna los datos del dialog (nombre, regla)."""
        return self.name_input.text().strip(), self.rule_input.toPlainText().strip()


if __name__ == "__main__":
    # Test del dialog
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    dialog = PlaylistEditDialog()
    if dialog.exec():
        name, rule = dialog.get_data()
        print(f"Nombre: {name}")
        print(f"Regla: {rule}") 
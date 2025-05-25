from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferencias")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Preferencias"))
        layout.addWidget(QPushButton("Guardar"))
        self.setLayout(layout)

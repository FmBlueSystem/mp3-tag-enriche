"""Launch the GUI application."""
import sys
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.gui.style import apply_dark_theme

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

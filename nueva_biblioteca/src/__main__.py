from nueva_biblioteca.ui.main_window import MainWindow
from PySide6.QtWidgets import QApplication
import sys

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())

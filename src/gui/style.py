"""Style configurations for the GUI."""
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

def apply_dark_theme(app):
    """Apply dark theme to the application."""
    palette = QPalette()
    
    # Colors
    primary = QColor("#6200EE")
    surface = QColor("#121212")
    background = QColor("#1E1E1E")
    on_surface = QColor("#FFFFFF")
    on_background = QColor("#FFFFFF")
    
    # Set color roles
    palette.setColor(QPalette.Window, background)
    palette.setColor(QPalette.WindowText, on_background)
    palette.setColor(QPalette.Base, surface)
    palette.setColor(QPalette.AlternateBase, surface.lighter(15))
    palette.setColor(QPalette.Text, on_surface)
    palette.setColor(QPalette.Button, surface)
    palette.setColor(QPalette.ButtonText, on_surface)
    palette.setColor(QPalette.Link, primary)
    palette.setColor(QPalette.Highlight, primary)
    palette.setColor(QPalette.HighlightedText, on_surface)
    
    app.setPalette(palette)
    app.setStyleSheet("""
        QPushButton {
            background-color: #6200EE;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #7722FF;
        }
        QPushButton:disabled {
            background-color: #CCCCCC;
        }
        QListWidget {
            background-color: #1E1E1E;
            border: 1px solid #333333;
            border-radius: 4px;
        }
        QLabel {
            color: #FFFFFF;
        }
        QProgressBar {
            border: 1px solid #333333;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #6200EE;
        }
    """)

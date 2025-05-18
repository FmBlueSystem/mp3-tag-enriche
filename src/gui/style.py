"""Style configurations for the GUI following Material Design guidelines."""
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

def apply_dark_theme(app):
    """Apply Material Dark theme to the application.
    
    Following Material Design color system:
    https://material.io/design/color/dark-theme.html
    """
    palette = QPalette()
    
    # Material Design Colors
    primary = QColor("#BB86FC")  # Primary (purple)
    primary_variant = QColor("#3700B3")  # Primary variant (darker purple)
    secondary = QColor("#03DAC6")  # Secondary (teal)
    surface = QColor("#121212")  # Surface
    background = QColor("#121212")  # Background
    error = QColor("#CF6679")  # Error
    on_primary = QColor("#000000")  # On Primary
    on_secondary = QColor("#000000")  # On Secondary
    on_surface = QColor("#FFFFFF")  # On Surface (87% white)
    on_background = QColor("#FFFFFF")  # On Background (87% white)
    on_error = QColor("#000000")  # On Error
    
    # Material Design Elevation Overlays (white overlay with varying opacity)
    dp1 = QColor("#1F1F1F")  # Surface + 5% white
    dp2 = QColor("#232323")  # Surface + 7% white
    dp3 = QColor("#252525")  # Surface + 8% white
    dp4 = QColor("#272727")  # Surface + 9% white
    dp6 = QColor("#2C2C2C")  # Surface + 11% white
    dp8 = QColor("#2E2E2E")  # Surface + 12% white
    dp12 = QColor("#333333")  # Surface + 14% white
    dp16 = QColor("#363636")  # Surface + 15% white
    dp24 = QColor("#383838")  # Surface + 16% white
    
    # Set Material color roles
    palette.setColor(QPalette.Window, background)
    palette.setColor(QPalette.WindowText, on_background)
    palette.setColor(QPalette.Base, surface)
    palette.setColor(QPalette.AlternateBase, dp1)
    palette.setColor(QPalette.Text, on_surface)
    palette.setColor(QPalette.Button, surface)
    palette.setColor(QPalette.ButtonText, on_surface)
    palette.setColor(QPalette.Link, secondary)
    palette.setColor(QPalette.Highlight, primary)
    palette.setColor(QPalette.HighlightedText, on_primary)
    
    app.setPalette(palette)
    app.setStyleSheet("""
        /* Material Design Typography - usando fuentes que existen en todos los sistemas */
        * {
            font-family: "Helvetica Neue", Arial, "Roboto", sans-serif;
        }
        
        /* Buttons following Material Design */
        QPushButton {
            background-color: #BB86FC;
            color: black;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 500;
            min-width: 64px;
            margin: 4px;
        }
        QPushButton:hover {
            background-color: #CBB2FF;
            border: 1px solid rgba(0,0,0,0.2);
        }
        QPushButton:pressed {
            background-color: #9965F4;
            border: 1px solid rgba(0,0,0,0.2);
        }
        QPushButton:focus {
            outline: 2px solid #03DAC6;
            outline-offset: 2px;
        }
        QPushButton:disabled {
            background-color: rgba(255,255,255,0.12);
            color: rgba(255,255,255,0.38);
        }
        
        /* List Widgets with elevation */
        QListWidget {
            background-color: #1F1F1F;
            border: 1px solid #333333;
            border-radius: 4px;
            padding: 8px;
            selection-background-color: rgba(187,134,252,0.24);
            selection-color: #FFFFFF;
        }
        QListWidget::item {
            padding: 8px;
            border-radius: 4px;
        }
        QListWidget::item:hover {
            background-color: rgba(255,255,255,0.08);
        }
        QListWidget::item:selected {
            background-color: rgba(187,134,252,0.24);
        }
        
        /* Labels with proper contrast */
        QLabel {
            color: rgba(255,255,255,0.87);
            font-size: 14px;
        }
        
        /* Sliders following Material Design */
        QSlider::groove:horizontal {
            border: none;
            height: 4px;
            background: rgba(255,255,255,0.38);
            margin: 8px 0;
        }
        QSlider::handle:horizontal {
            background: #BB86FC;
            border: none;
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }
        QSlider::handle:horizontal:hover {
            background: #CBB2FF;
            border: 2px solid rgba(187,134,252,0.24);
        }
        
        /* Progress Bars with Material Design colors */
        QProgressBar {
            border: none;
            border-radius: 4px;
            background-color: rgba(255,255,255,0.12);
            height: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #BB86FC;
        }
        
        /* Checkboxes following Material Design */
        QCheckBox {
            color: rgba(255,255,255,0.87);
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255,255,255,0.6);
            border-radius: 2px;
        }
        QCheckBox::indicator:checked {
            background-color: #BB86FC;
            border-color: #BB86FC;
        }
        QCheckBox::indicator:hover {
            border-color: rgba(255,255,255,0.87);
        }
        
        /* Spinboxes following Material Design */
        QSpinBox {
            background-color: rgba(255,255,255,0.12);
            border: none;
            border-bottom: 2px solid rgba(255,255,255,0.38);
            color: rgba(255,255,255,0.87);
            padding: 4px;
        }
        QSpinBox:hover {
            border-bottom-color: rgba(255,255,255,0.6);
        }
        QSpinBox:focus {
            border-bottom-color: #BB86FC;
        }
    """)

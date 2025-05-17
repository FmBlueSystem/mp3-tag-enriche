"""GUI module for the MP3 Tag Enricher application."""

from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPalette, QColor

# Material Design color palette
COLORS = {
    'primary': '#6200EE',
    'primary_variant': '#3700B3',
    'secondary': '#03DAC6',
    'secondary_variant': '#018786',
    'background': '#FFFFFF',
    'surface': '#FFFFFF',
    'error': '#B00020',
    'on_primary': '#FFFFFF',
    'on_secondary': '#000000',
    'on_background': '#000000',
    'on_surface': '#000000',
    'on_error': '#FFFFFF',
}

# Material Design sizes
FONT_SIZES = {
    'h1': 96,
    'h2': 60,
    'h3': 48,
    'h4': 34,
    'h5': 24,
    'h6': 20,
    'subtitle1': 16,
    'subtitle2': 14,
    'body1': 16,
    'body2': 14,
    'button': 14,
    'caption': 12,
    'overline': 10,
}

# Material Design sizing constants
SIZES = {
    'input_height': 30,
    'button_height': 36,
    'spacing': 8,
    'padding': 16
}

def apply_material_style(widget):
    """Apply Material Design styling to a widget based on its type."""
    if isinstance(widget, QPushButton):
        widget.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['on_primary']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font: 14px;
                font-weight: 500;
                min-width: 64px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_variant']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['secondary']};
            }}
            QPushButton:disabled {{
                background-color: #CCCCCC;
                color: #666666;
            }}
        """)
    elif isinstance(widget, QMainWindow):
        widget.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['background']};
                color: {COLORS['on_background']};
            }}
        """)
    elif isinstance(widget, QLineEdit):
        widget.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['surface']};
                color: {COLORS['on_surface']};
                border: 1px solid {COLORS['primary']};
                border-radius: 4px;
                padding: 8px;
                font: 14px "Helvetica";
                height: {SIZES['input_height']}px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary_variant']};
            }}
            QLineEdit:disabled {{
                background-color: #F5F5F5;
                border: 1px solid #CCCCCC;
                color: #666666;
            }}
        """)
        widget.setFixedHeight(SIZES['input_height'])
    # Add more widget-specific styling as needed

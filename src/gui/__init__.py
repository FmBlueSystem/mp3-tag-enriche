"""GUI package initialization."""
def apply_material_style(widget):
    """Apply Material Design-inspired style to a widget."""
    widget.setStyleSheet("""
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
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            padding: 4px;
        }
        QLabel {
            font-size: 14px;
        }
        QCheckBox {
            font-size: 14px;
        }
    """)

# Color scheme
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

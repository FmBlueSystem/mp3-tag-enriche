"""Módulo de estilos para la GUI de Genre Detector."""
from enum import Enum
from dataclasses import dataclass
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPalette, QColor

@dataclass
class ColorScheme:
    """Esquema de colores para un tema."""
    primary: QColor
    secondary: QColor
    background: QColor
    surface: QColor
    error: QColor
    on_primary: QColor
    on_secondary: QColor
    on_background: QColor
    on_surface: QColor
    on_error: QColor
    border: QColor
    disabled_text: QColor = None
    disabled_background: QColor = None

    def __post_init__(self):
        """Inicializa colores con transparencia."""
        self.disabled_text = QColor(self.on_surface)
        self.disabled_text.setAlphaF(0.38)
        self.disabled_background = QColor(self.on_surface)
        self.disabled_background.setAlphaF(0.12)

class ThemeType(Enum):
    """Tipos de temas disponibles."""
    LIGHT = "light"
    DARK = "dark"

class ThemeManager:
    """Gestor centralizado de temas."""
    
    # Definición de esquemas de color
    LIGHT_SCHEME = ColorScheme(
        primary=QColor("#2196F3"),      # Blue 500
        secondary=QColor("#FFC107"),    # Amber 500
        background=QColor("#FFFFFF"),   # White
        surface=QColor("#F5F5F5"),      # Grey 100
        error=QColor("#B00020"),        # Material Error
        on_primary=QColor("#FFFFFF"),
        on_secondary=QColor("#000000"),
        on_background=QColor("#000000"),
        on_surface=QColor("#000000"),
        on_error=QColor("#FFFFFF"),
        border=QColor("#E0E0E0")        # Grey 300
    )

    DARK_SCHEME = ColorScheme(
        primary=QColor("#2196F3"),      # Blue 500
        secondary=QColor("#FFC107"),    # Amber 500
        background=QColor("#0D1B2A"),   # Night Blue Dark
        surface=QColor("#1B263B"),      # Night Blue Medium
        error=QColor("#CF6679"),        # Material Dark Error
        on_primary=QColor("#FFFFFF"),
        on_secondary=QColor("#000000"),
        on_background=QColor("#E0E0E0"),
        on_surface=QColor("#FFFFFF"),
        on_error=QColor("#000000"),
        border=QColor("#415A77")        # Night Blue Light
    )

    @classmethod
    def apply_theme(cls, widget: QWidget, theme_type: ThemeType) -> None:
        """Aplica un tema específico a un widget y sus descendientes."""
        scheme = cls.LIGHT_SCHEME if theme_type == ThemeType.LIGHT else cls.DARK_SCHEME
        cls._apply_palette(widget, scheme)
        cls._apply_stylesheets(widget, scheme)

    @classmethod
    def _apply_palette(cls, widget: QWidget, scheme: ColorScheme) -> None:
        """Aplica la paleta de colores al widget."""
        palette = QPalette()

        # Colores generales
        palette.setColor(QPalette.Window, scheme.background)
        palette.setColor(QPalette.WindowText, scheme.on_background)
        palette.setColor(QPalette.Base, scheme.surface)
        palette.setColor(QPalette.AlternateBase, scheme.surface.lighter(110))
        palette.setColor(QPalette.ToolTipBase, scheme.surface)
        palette.setColor(QPalette.ToolTipText, scheme.on_surface)
        palette.setColor(QPalette.Text, scheme.on_surface)
        palette.setColor(QPalette.Button, scheme.primary)
        palette.setColor(QPalette.ButtonText, scheme.on_primary)
        palette.setColor(QPalette.Link, scheme.primary)
        palette.setColor(QPalette.Highlight, scheme.primary)
        palette.setColor(QPalette.HighlightedText, scheme.on_primary)

        # Estados deshabilitados
        palette.setColor(QPalette.Disabled, QPalette.Text, scheme.disabled_text)
        palette.setColor(QPalette.Disabled, QPalette.WindowText, scheme.disabled_text)
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, scheme.disabled_text)
        palette.setColor(QPalette.Disabled, QPalette.Base, scheme.disabled_background)
        palette.setColor(QPalette.Disabled, QPalette.Button, scheme.disabled_background)
        palette.setColor(QPalette.Disabled, QPalette.Highlight, scheme.disabled_background)

        widget.setPalette(palette)

    @classmethod
    def _apply_stylesheets(cls, widget: QWidget, scheme: ColorScheme) -> None:
        """Aplica hojas de estilo específicas por componente."""
        widget.setStyleSheet(f"""
            /* Tooltips */
            QToolTip {{
                color: {scheme.on_surface.name()};
                background-color: {scheme.surface.name()};
                border: 1px solid {scheme.primary.name()};
                border-radius: 4px;
                padding: 5px;
            }}

            /* Listas */
            QListWidget {{
                background-color: {scheme.surface.name()};
                border: 1px solid {scheme.border.name()};
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 5px;
                color: {scheme.on_surface.name()};
            }}
            QListWidget::item:hover {{
                background-color: {scheme.surface.lighter(110).name()};
            }}
            QListWidget::item:selected {{
                background-color: {scheme.primary.name()};
                color: {scheme.on_primary.name()};
            }}

            /* Botones */
            QPushButton {{
                background-color: {scheme.primary.name()};
                color: {scheme.on_primary.name()};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {scheme.primary.darker(110).name()};
            }}
            QPushButton:pressed {{
                background-color: {scheme.primary.darker(130).name()};
            }}
            QPushButton:disabled {{
                background-color: {scheme.disabled_background.name()};
                color: {scheme.disabled_text.name()};
            }}

            /* Checkbox */
            QCheckBox {{
                spacing: 5px;
                color: {scheme.on_surface.name()};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 2px solid {scheme.secondary.name()};
                background-color: transparent;
            }}
            QCheckBox::indicator:checked {{
                background-color: {scheme.secondary.name()};
                border-color: {scheme.secondary.name()};
            }}

            /* Slider */
            QSlider::groove:horizontal {{
                border: 1px solid {scheme.border.name()};
                height: 4px;
                background: {scheme.surface.lighter(110).name()};
                margin: 2px 0;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {scheme.secondary.name()};
                border: 1px solid {scheme.secondary.name()};
                width: 18px;
                margin: -8px 0;
                border-radius: 9px;
            }}

            /* SpinBox */
            QSpinBox {{
                background-color: {scheme.surface.name()};
                border: 1px solid {scheme.border.name()};
                border-radius: 4px;
                padding: 5px;
                color: {scheme.on_surface.name()};
            }}

            /* Labels */
            QLabel {{
                color: {scheme.on_surface.name()};
            }}

            /* Status Bar */
            QStatusBar {{
                background-color: {scheme.surface.name()};
                color: {scheme.on_surface.name()};
                border-top: 1px solid {scheme.border.name()};
            }}
        """)

# Funciones de compatibilidad para código existente
def apply_light_theme(widget: QWidget) -> None:
    """Aplica el tema claro usando ThemeManager."""
    ThemeManager.apply_theme(widget, ThemeType.LIGHT)

def apply_dark_theme(widget: QWidget) -> None:
    """Aplica el tema oscuro usando ThemeManager."""
    ThemeManager.apply_theme(widget, ThemeType.DARK)

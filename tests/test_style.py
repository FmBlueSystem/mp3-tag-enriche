"""Pruebas unitarias para el sistema de theming."""
import pytest
from PySide6.QtWidgets import QWidget, QPushButton, QCheckBox, QLabel
from PySide6.QtGui import QPalette, QColor
from src.gui.style import ColorScheme, ThemeType, ThemeManager

@pytest.fixture
def test_widget():
    """Fixture que proporciona un widget de prueba."""
    return QWidget()

@pytest.fixture
def test_button():
    """Fixture que proporciona un botón de prueba."""
    return QPushButton("Test")

@pytest.fixture
def color_scheme():
    """Fixture que proporciona un esquema de color de prueba."""
    return ColorScheme(
        primary=QColor("#FF0000"),
        secondary=QColor("#00FF00"),
        background=QColor("#FFFFFF"),
        surface=QColor("#F5F5F5"),
        error=QColor("#FF0000"),
        on_primary=QColor("#FFFFFF"),
        on_secondary=QColor("#000000"),
        on_background=QColor("#000000"),
        on_surface=QColor("#000000"),
        on_error=QColor("#FFFFFF"),
        border=QColor("#CCCCCC")
    )

def test_color_scheme_initialization():
    """Prueba la inicialización del esquema de colores."""
    scheme = ColorScheme(
        primary=QColor("#FF0000"),
        secondary=QColor("#00FF00"),
        background=QColor("#FFFFFF"),
        surface=QColor("#F5F5F5"),
        error=QColor("#FF0000"),
        on_primary=QColor("#FFFFFF"),
        on_secondary=QColor("#000000"),
        on_background=QColor("#000000"),
        on_surface=QColor("#000000"),
        on_error=QColor("#FFFFFF"),
        border=QColor("#CCCCCC")
    )
    
    assert scheme.primary.name() == "#ff0000"
    assert scheme.secondary.name() == "#00ff00"
    assert scheme.background.name() == "#ffffff"
    
    # Verificar colores con transparencia
    assert scheme.disabled_text.alpha() < 255
    assert scheme.disabled_background.alpha() < 255

def test_theme_type_values():
    """Prueba los valores del enumerador ThemeType."""
    assert ThemeType.LIGHT.value == "light"
    assert ThemeType.DARK.value == "dark"
    assert len(ThemeType) == 2

def test_theme_manager_light_scheme():
    """Prueba el esquema de color claro predefinido."""
    scheme = ThemeManager.LIGHT_SCHEME
    assert scheme.background.name() == "#ffffff"
    assert scheme.surface.name() == "#f5f5f5"
    assert scheme.primary.name() == "#2196f3"

def test_theme_manager_dark_scheme():
    """Prueba el esquema de color oscuro predefinido."""
    scheme = ThemeManager.DARK_SCHEME
    assert scheme.background.name() == "#0d1b2a"
    assert scheme.surface.name() == "#1b263b"
    assert scheme.primary.name() == "#2196f3"

def test_apply_theme_to_widget(test_widget):
    """Prueba la aplicación de un tema a un widget."""
    ThemeManager.apply_theme(test_widget, ThemeType.LIGHT)
    palette = test_widget.palette()
    
    assert palette.color(QPalette.Window).name() == ThemeManager.LIGHT_SCHEME.background.name()
    assert palette.color(QPalette.WindowText).name() == ThemeManager.LIGHT_SCHEME.on_background.name()

def test_apply_theme_to_button(test_button):
    """Prueba la aplicación de un tema a un botón."""
    ThemeManager.apply_theme(test_button, ThemeType.DARK)
    stylesheet = test_button.styleSheet()
    
    # Verificar que el estilo del botón se aplicó
    assert "QPushButton" in stylesheet
    assert ThemeManager.DARK_SCHEME.primary.name() in stylesheet
    assert ThemeManager.DARK_SCHEME.on_primary.name() in stylesheet

def test_disabled_state_colors(test_button):
    """Prueba los colores en estado deshabilitado."""
    ThemeManager.apply_theme(test_button, ThemeType.LIGHT)
    palette = test_button.palette()
    
    # Verificar colores deshabilitados
    disabled_text = palette.color(QPalette.Disabled, QPalette.ButtonText)
    assert disabled_text.alpha() < 255

def test_theme_switching(test_widget):
    """Prueba el cambio entre temas."""
    # Aplicar tema claro
    ThemeManager.apply_theme(test_widget, ThemeType.LIGHT)
    light_background = test_widget.palette().color(QPalette.Window).name()
    
    # Cambiar a tema oscuro
    ThemeManager.apply_theme(test_widget, ThemeType.DARK)
    dark_background = test_widget.palette().color(QPalette.Window).name()
    
    assert light_background != dark_background
    assert dark_background == ThemeManager.DARK_SCHEME.background.name()

def test_widget_specific_styles():
    """Prueba estilos específicos por tipo de widget."""
    # Probar CheckBox
    checkbox = QCheckBox("Test")
    ThemeManager.apply_theme(checkbox, ThemeType.LIGHT)
    assert "QCheckBox" in checkbox.styleSheet()
    assert "indicator" in checkbox.styleSheet()
    
    # Probar Label
    label = QLabel("Test")
    ThemeManager.apply_theme(label, ThemeType.LIGHT)
    assert "QLabel" in label.styleSheet()

def test_color_transformations(color_scheme):
    """Prueba transformaciones de colores."""
    # Probar lighten
    lighter_surface = color_scheme.surface.lighter(110)
    assert lighter_surface.lightness() > color_scheme.surface.lightness()
    
    # Probar darken
    darker_primary = color_scheme.primary.darker(110)
    assert darker_primary.lightness() < color_scheme.primary.lightness()

def test_theme_inheritance(test_widget):
    """Prueba la herencia de temas en la jerarquía de widgets."""
    child_button = QPushButton("Child", test_widget)
    ThemeManager.apply_theme(test_widget, ThemeType.DARK)
    
    # El botón hijo debe heredar la paleta
    assert child_button.palette().color(QPalette.Window).name() == \
           test_widget.palette().color(QPalette.Window).name()

def test_stylesheet_components(test_widget):
    """Prueba componentes específicos del stylesheet."""
    ThemeManager.apply_theme(test_widget, ThemeType.LIGHT)
    stylesheet = test_widget.styleSheet()
    
    # Verificar secciones principales
    components = [
        "QToolTip",
        "QListWidget",
        "QPushButton",
        "QCheckBox",
        "QSlider",
        "QSpinBox",
        "QLabel",
        "QStatusBar"
    ]
    
    for component in components:
        assert component in stylesheet

def test_compatibility_functions(test_widget):
    """Prueba funciones de compatibilidad."""
    from src.gui.style import apply_light_theme, apply_dark_theme
    
    # Probar tema claro
    apply_light_theme(test_widget)
    light_background = test_widget.palette().color(QPalette.Window).name()
    assert light_background == ThemeManager.LIGHT_SCHEME.background.name()
    
    # Probar tema oscuro
    apply_dark_theme(test_widget)
    dark_background = test_widget.palette().color(QPalette.Window).name()
    assert dark_background == ThemeManager.DARK_SCHEME.background.name()
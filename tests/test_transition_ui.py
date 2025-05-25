"""Pruebas para la interfaz de usuario de efectos de transición."""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from nueva_biblioteca.src.ui.widgets.transition_effect_widget import (
    TransitionEffectWidget, MaterialSlider, MaterialComboBox)
from nueva_biblioteca.src.ui.dialogs.transition_effect_dialog import (
    TransitionEffectDialog)
from nueva_biblioteca.src.services.transition_effects import (
    TransitionEffectManager)

@pytest.fixture
def app():
    """Fixture que provee una instancia de QApplication."""
    return QApplication([])

@pytest.fixture
def effect_widget(app):
    """Fixture que provee un widget de efectos de transición."""
    return TransitionEffectWidget()

@pytest.fixture
def effect_dialog(app):
    """Fixture que provee un diálogo de efectos de transición."""
    manager = TransitionEffectManager()
    return TransitionEffectDialog(manager)

def test_material_slider_style(app):
    """Prueba el estilo Material Design del slider."""
    slider = MaterialSlider(Qt.Horizontal)
    style = slider.styleSheet()
    
    # Verificar elementos de estilo Material
    assert "#6200EE" in style  # Color primario
    assert "border-radius: 8px" in style
    assert "background: #E0E0E0" in style

def test_material_combobox_style(app):
    """Prueba el estilo Material Design del combobox."""
    combo = MaterialComboBox()
    style = combo.styleSheet()
    
    # Verificar elementos de estilo Material
    assert "border: 2px solid #E0E0E0" in style
    assert "border-radius: 4px" in style
    assert "padding: 8px" in style

def test_transition_widget_initial_state(effect_widget):
    """Prueba el estado inicial del widget de efectos."""
    # Verificar efectos disponibles
    assert effect_widget.effect_combo.count() == 2
    assert "CrossFade" in [
        effect_widget.effect_combo.itemText(i)
        for i in range(effect_widget.effect_combo.count())
    ]
    
    # Verificar rango del slider
    assert effect_widget.duration_slider.minimum() == 5
    assert effect_widget.duration_slider.maximum() == 100
    assert effect_widget.duration_slider.value() == 20  # 2s por defecto

def test_transition_widget_signals(effect_widget):
    """Prueba las señales del widget de efectos."""
    # Capturar señales
    effect_changes = []
    duration_changes = []
    preview_requests = []
    
    effect_widget.effect_changed.connect(lambda e: effect_changes.append(e))
    effect_widget.duration_changed.connect(lambda d: duration_changes.append(d))
    effect_widget.preview_requested.connect(
        lambda: preview_requests.append(True))
    
    # Cambiar efecto
    effect_widget.effect_combo.setCurrentText("EQ Transition")
    assert len(effect_changes) == 1
    assert effect_changes[0] == "eq_transition"
    
    # Cambiar duración
    effect_widget.duration_slider.setValue(30)  # 3s
    assert len(duration_changes) == 1
    assert duration_changes[0] == 3.0
    
    # Solicitar previsualización
    effect_widget.preview_button.click()
    assert len(preview_requests) == 1

def test_transition_dialog_initial_state(effect_dialog):
    """Prueba el estado inicial del diálogo de efectos."""
    # Verificar título
    assert effect_dialog.windowTitle() == "Configurar Efecto de Transición"
    
    # Verificar que el widget de efectos está presente
    assert hasattr(effect_dialog, "effect_widget")
    assert isinstance(effect_dialog.effect_widget, TransitionEffectWidget)

def test_transition_dialog_signals(effect_dialog):
    """Prueba las señales del diálogo de efectos."""
    # Capturar señales
    configurations = []
    effect_dialog.effect_configured.connect(
        lambda e, d: configurations.append((e, d)))
    
    # Configurar efecto
    effect_dialog.effect_widget.effect_combo.setCurrentText("EQ Transition")
    effect_dialog.effect_widget.duration_slider.setValue(30)  # 3s
    
    # Aceptar configuración
    effect_dialog.accept_button.click()
    
    # Verificar señal emitida
    assert len(configurations) == 1
    assert configurations[0] == ("eq_transition", 3.0)

def test_transition_widget_getters(effect_widget):
    """Prueba los getters del widget de efectos."""
    # Configurar widget
    effect_widget.effect_combo.setCurrentText("EQ Transition")
    effect_widget.duration_slider.setValue(30)  # 3s
    
    # Verificar valores
    assert effect_widget.get_current_effect() == "eq_transition"
    assert effect_widget.get_current_duration() == 3.0

def test_transition_dialog_preview(effect_dialog):
    """Prueba la función de previsualización del diálogo."""
    # Verificar que el método existe
    assert hasattr(effect_dialog, "_preview_effect")
    
    # Configurar y probar previsualización
    effect_dialog.effect_widget.effect_combo.setCurrentText("CrossFade")
    effect_dialog.effect_widget.duration_slider.setValue(20)
    effect_dialog._preview_effect()
    # Nota: La previsualización actual es un TODO, pero verificamos
    # que la función existe y se puede llamar

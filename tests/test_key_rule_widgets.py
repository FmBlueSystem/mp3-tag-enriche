import unittest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtTest import QTest

from src.ui.rule_editor.widgets.camelot_wheel import CamelotWheelWidget
from src.ui.rule_editor.widgets.key_rule_editor import KeyRuleEditor
from src.core.camelot import CompatibilityMode

# Necesitamos una instancia de QApplication para pruebas de widgets
app = QApplication([])

class TestCamelotWheelWidget(unittest.TestCase):
    """Pruebas para el widget de rueda Camelot."""
    
    def setUp(self):
        """Configura el ambiente de prueba."""
        self.wheel = CamelotWheelWidget()
        self.wheel.resize(400, 400)  # Tamaño mínimo
        
    def test_initial_state(self):
        """Prueba el estado inicial del widget."""
        self.assertIsNone(self.wheel.selected_key)
        self.assertEqual(len(self.wheel.compatible_keys), 0)
        self.assertEqual(self.wheel.compatibility_mode, CompatibilityMode.PERFECT)
        
    def test_key_selection(self):
        """Prueba la selección de una clave."""
        # Simular señales
        key_selected = Mock()
        compatibility_changed = Mock()
        self.wheel.keySelected.connect(key_selected)
        self.wheel.compatibilityChanged.connect(compatibility_changed)
        
        # Seleccionar clave
        self.wheel.select_key("8A")
        
        # Verificar señales
        key_selected.assert_called_with("8A")
        compatibility_changed.assert_called_once()
        
        # Verificar estado
        self.assertEqual(self.wheel.selected_key, "8A")
        self.assertTrue(len(self.wheel.compatible_keys) > 0)
        
    def test_compatibility_mode_change(self):
        """Prueba cambios en el modo de compatibilidad."""
        # Seleccionar clave y modo
        self.wheel.select_key("8A")
        old_compatible = self.wheel.compatible_keys.copy()
        
        # Cambiar modo
        self.wheel.set_compatibility_mode(CompatibilityMode.ENERGY_UP)
        
        # Verificar que las claves compatibles cambiaron
        self.assertNotEqual(self.wheel.compatible_keys, old_compatible)
        
    def test_wheel_rotation(self):
        """Prueba la rotación de la rueda."""
        initial_rotation = self.wheel.wheel_rotation
        
        # Rotar 30 grados
        self.wheel.rotate(30)
        
        self.assertEqual(self.wheel.wheel_rotation, 
                       (initial_rotation + 30) % 360)
        
    def test_mouse_interaction(self):
        """Prueba interacción con el mouse."""
        # Simular hover
        pos = QPoint(200, 200)  # Centro aproximado
        QTest.mouseMove(self.wheel, pos)
        
        # Verificar que se actualiza el hover
        self.assertIsNotNone(self.wheel.hover_key)
        
        # Simular click
        key_selected = Mock()
        self.wheel.keySelected.connect(key_selected)
        
        QTest.mouseClick(self.wheel, Qt.MouseButton.LeftButton, pos=pos)
        
        # Verificar que se emitió la señal
        key_selected.assert_called_once()

class TestKeyRuleEditor(unittest.TestCase):
    """Pruebas para el editor de reglas de clave."""
    
    def setUp(self):
        """Configura el ambiente de prueba."""
        self.editor = KeyRuleEditor()
        
    def test_initial_state(self):
        """Prueba el estado inicial del editor."""
        self.assertIsNotNone(self.editor.wheel)
        self.assertEqual(self.editor.get_rule(), "")
        
    def test_rule_generation(self):
        """Prueba la generación de reglas."""
        # Simular señal de regla cambiada
        rule_changed = Mock()
        self.editor.ruleChanged.connect(rule_changed)
        
        # Seleccionar clave en la rueda
        self.editor.wheel.select_key("8A")
        
        # Verificar regla generada
        rule = self.editor.get_rule()
        self.assertTrue(rule.startswith("key COMPATIBLE_WITH"))
        rule_changed.assert_called()
        
    def test_compatibility_mode_selection(self):
        """Prueba la selección de modo de compatibilidad."""
        # Seleccionar clave
        self.editor.wheel.select_key("8A")
        initial_rule = self.editor.get_rule()
        
        # Cambiar modo vía combo box
        self.editor.mode_combo.setCurrentIndex(1)  # Energy Up
        
        # Verificar que la regla se actualizó
        self.assertNotEqual(self.editor.get_rule(), initial_rule)
        
    def test_clear_selection(self):
        """Prueba limpiar la selección."""
        # Seleccionar clave
        self.editor.wheel.select_key("8A")
        self.assertNotEqual(self.editor.get_rule(), "")
        
        # Limpiar
        self.editor.clear_selection()
        
        # Verificar estado limpio
        self.assertEqual(self.editor.get_rule(), "")
        self.assertIsNone(self.editor.wheel.selected_key)
        self.assertEqual(len(self.editor.wheel.compatible_keys), 0)
        
    def test_description_updates(self):
        """Prueba actualización de descripción."""
        initial_text = self.editor.description.text()
        
        # Seleccionar clave
        self.editor.wheel.select_key("8A")
        
        # Verificar que la descripción cambió
        self.assertNotEqual(self.editor.description.text(), initial_text)
        self.assertIn("G maj", self.editor.description.text())

if __name__ == '__main__':
    unittest.main()

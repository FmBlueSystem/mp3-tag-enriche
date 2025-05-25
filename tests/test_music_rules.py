import unittest
from src.core.parser import Parser, NodeType, ParserError
from src.core.evaluator import Evaluator, EvaluatorError
from src.core.camelot import CamelotWheel, CompatibilityMode

class TestMusicRules(unittest.TestCase):
    """
    Pruebas para reglas relacionadas con música, especialmente
    compatibilidad de claves musicales.
    """
    
    def setUp(self):
        """Configura el ambiente de prueba."""
        self.parser = Parser()
        self.evaluator = Evaluator()
        self.wheel = CamelotWheel()
        
    def test_parse_compatibility_rule(self):
        """Prueba el parsing de reglas de compatibilidad."""
        # Regla válida
        rule = "key COMPATIBLE_WITH 'G maj'"
        node = self.parser.parse(rule)
        
        self.assertEqual(node.type, NodeType.COMPATIBILITY)
        self.assertEqual(node.value, "G maj")
        self.assertEqual(node.left.value, "key")
        
        # Regla sin comillas
        with self.assertRaises(ParserError):
            self.parser.parse("key COMPATIBLE_WITH G maj")
            
        # Regla incompleta
        with self.assertRaises(ParserError):
            self.parser.parse("key COMPATIBLE_WITH")
            
    def test_evaluate_perfect_match(self):
        """Prueba evaluación de compatibilidad perfecta."""
        rule = "key COMPATIBLE_WITH 'G maj'"
        node = self.parser.parse(rule)
        
        # Track con clave igual
        track = {"key": "G maj"}
        self.assertTrue(self.evaluator.evaluate(node, track))
        
        # Track con clave diferente
        track = {"key": "C maj"}
        self.assertFalse(self.evaluator.evaluate(node, track))
        
    def test_evaluate_energy_compatibility(self):
        """Prueba evaluación de compatibilidad energética."""
        rule = "key COMPATIBLE_WITH 'G maj'"  # 8A
        node = self.parser.parse(rule)
        
        # Track con clave +1 (energy up)
        track = {"key": "A maj"}  # 9A
        self.assertTrue(self.evaluator.evaluate(node, track))
        
        # Track con clave -1 (energy down)
        track = {"key": "C maj"}  # 7A
        self.assertTrue(self.evaluator.evaluate(node, track))
        
        # Track con clave no compatible
        track = {"key": "B♭ maj"}  # 5A
        self.assertFalse(self.evaluator.evaluate(node, track))
        
    def test_evaluate_harmonic_compatibility(self):
        """Prueba evaluación de compatibilidad armónica."""
        rule = "key COMPATIBLE_WITH 'G maj'"  # 8A
        node = self.parser.parse(rule)
        
        # Track con clave relativa
        track = {"key": "A♭ maj"}  # 3A
        self.assertTrue(self.evaluator.evaluate(node, track))
        
    def test_evaluate_minor_keys(self):
        """Prueba evaluación con claves menores."""
        rule = "key COMPATIBLE_WITH 'E min'"  # 8B
        node = self.parser.parse(rule)
        
        # Track con clave igual
        track = {"key": "E min"}
        self.assertTrue(self.evaluator.evaluate(node, track))
        
        # Track con clave compatible
        track = {"key": "B min"}  # 9B
        self.assertTrue(self.evaluator.evaluate(node, track))
        
        # Track con clave no compatible
        track = {"key": "G min"}  # 5B
        self.assertFalse(self.evaluator.evaluate(node, track))
        
    def test_evaluate_missing_key(self):
        """Prueba evaluación cuando falta la clave."""
        rule = "key COMPATIBLE_WITH 'G maj'"
        node = self.parser.parse(rule)
        
        # Track sin clave
        track = {"artist": "Test"}
        self.assertFalse(self.evaluator.evaluate(node, track))
        
        # Track con clave None
        track = {"key": None}
        self.assertFalse(self.evaluator.evaluate(node, track))
        
    def test_complex_rules(self):
        """Prueba reglas complejas que incluyen compatibilidad."""
        # Regla con AND
        rule = "(key COMPATIBLE_WITH 'G maj') AND (bpm > 120)"
        node = self.parser.parse(rule)
        
        # Track que cumple ambas condiciones
        track = {"key": "G maj", "bpm": 128}
        self.assertTrue(self.evaluator.evaluate(node, track))
        
        # Track que solo cumple compatibilidad
        track = {"key": "G maj", "bpm": 100}
        self.assertFalse(self.evaluator.evaluate(node, track))
        
        # Track que solo cumple bpm
        track = {"key": "F min", "bpm": 128}
        self.assertFalse(self.evaluator.evaluate(node, track))
        
    def test_alternative_notations(self):
        """Prueba notaciones alternativas de claves."""
        rule = "key COMPATIBLE_WITH 'Gmaj'"
        node = self.parser.parse(rule)
        
        # Diferentes notaciones para G major
        valid_notations = [
            "G maj", "Gmaj", "G major",
            "G M", "GM"
        ]
        
        for notation in valid_notations:
            with self.subTest(notation=notation):
                track = {"key": notation}
                self.assertTrue(
                    self.evaluator.evaluate(node, track),
                    f"Falló con notación: {notation}"
                )
                
    def test_camelot_wheel_integration(self):
        """Prueba integración directa con CamelotWheel."""
        # Verificar que el evaluador usa la rueda correctamente
        wheel = self.evaluator.wheel
        
        # Probar conversión
        self.assertEqual(
            wheel.get_camelot_key("G maj"),
            "8A"
        )
        
        # Probar compatibilidad
        compatible = wheel.get_compatible_keys(
            "G maj",
            CompatibilityMode.PERFECT
        )
        self.assertEqual(compatible, {"G maj"})
        
        # Probar que el evaluador usa estas conversiones
        rule = "key COMPATIBLE_WITH 'G maj'"
        node = self.parser.parse(rule)
        
        track = {"key": "8A"}  # Notación Camelot
        self.assertTrue(self.evaluator.evaluate(node, track))

if __name__ == '__main__':
    unittest.main()

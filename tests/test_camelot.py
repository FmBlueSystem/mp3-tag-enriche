import unittest
from src.core.camelot import CamelotWheel, CompatibilityMode

class TestCamelotWheel(unittest.TestCase):
    """Pruebas para la clase CamelotWheel."""
    
    def setUp(self):
        """Configura el ambiente de prueba."""
        self.wheel = CamelotWheel()
        
    def test_camelot_to_musical(self):
        """Prueba conversión de notación Camelot a musical."""
        test_cases = [
            ("8A", "G maj"),
            ("8B", "E min"),
            ("1A", "G♭ maj"),
            ("1B", "E♭ min")
        ]
        
        for camelot, musical in test_cases:
            with self.subTest(camelot=camelot):
                result = self.wheel.get_musical_key(camelot)
                self.assertEqual(result, musical)
                
    def test_musical_to_camelot(self):
        """Prueba conversión de notación musical a Camelot."""
        test_cases = [
            ("G maj", "8A"),
            ("Em", "8B"),
            ("Gb major", "1A"),
            ("Ebm", "1B")
        ]
        
        for musical, camelot in test_cases:
            with self.subTest(musical=musical):
                result = self.wheel.get_camelot_key(musical)
                self.assertEqual(result, camelot)
                
    def test_perfect_match_compatibility(self):
        """Prueba compatibilidad en modo perfect match."""
        key = "8A"  # G major
        compatible = self.wheel.get_compatible_keys(key, CompatibilityMode.PERFECT)
        self.assertEqual(compatible, {"8A"})
        
    def test_energy_up_compatibility(self):
        """Prueba compatibilidad en modo energy up."""
        key = "8A"  # G major
        compatible = self.wheel.get_compatible_keys(key, CompatibilityMode.ENERGY_UP)
        self.assertEqual(compatible, {"9A"})  # A major
        
    def test_energy_down_compatibility(self):
        """Prueba compatibilidad en modo energy down."""
        key = "8A"  # G major
        compatible = self.wheel.get_compatible_keys(key, CompatibilityMode.ENERGY_DOWN)
        self.assertEqual(compatible, {"7A"})  # C major
        
    def test_harmonic_compatibility(self):
        """Prueba compatibilidad en modo harmonic."""
        key = "8A"  # G major
        compatible = self.wheel.get_compatible_keys(key, CompatibilityMode.HARMONIC)
        self.assertEqual(compatible, {"3A"})
        
    def test_invalid_key_compatibility(self):
        """Prueba compatibilidad con clave inválida."""
        key = "invalid"
        compatible = self.wheel.get_compatible_keys(key)
        self.assertEqual(compatible, set())
        
    def test_custom_compatibility_rule(self):
        """Prueba regla de compatibilidad personalizada."""
        self.wheel.add_custom_rule([2, -2])  # 2 arriba, 2 abajo
        key = "8A"
        compatible = self.wheel.get_compatible_keys(key, CompatibilityMode.CUSTOM)
        self.assertEqual(compatible, {"10A", "6A"})
        
    def test_key_info(self):
        """Prueba obtención de información de clave."""
        info = self.wheel.get_key_info("8A")
        
        self.assertEqual(info["camelot_key"], "8A")
        self.assertEqual(info["musical_key"], "G maj")
        self.assertEqual(info["number"], 8)
        self.assertTrue(info["is_major"])
        self.assertEqual(info["mode"], "Major")
        self.assertIn("compatible_keys", info)
        
    def test_normalize_key_notation(self):
        """Prueba normalización de notación de claves."""
        test_cases = [
            ("Gmaj", "G maj"),
            ("Em", "E min"),
            ("C Major", "C maj"),
            ("D Minor", "D min"),
            ("F#M", "F# maj"),
            ("Bbm", "Bb min")
        ]
        
        for input_key, expected in test_cases:
            with self.subTest(input_key=input_key):
                result = self.wheel._normalize_key(input_key)
                self.assertEqual(result, expected)
                
    def test_cache_functionality(self):
        """Prueba funcionamiento del cache de compatibilidad."""
        # Primera llamada - debería calcular
        key = "8A"
        compatible1 = self.wheel.get_compatible_keys(key, CompatibilityMode.PERFECT)
        
        # Segunda llamada - debería usar cache
        compatible2 = self.wheel.get_compatible_keys(key, CompatibilityMode.PERFECT)
        
        self.assertEqual(compatible1, compatible2)
        
        # Modificar reglas debería invalidar cache
        self.wheel.add_custom_rule([1])
        cache_size = len(self.wheel._compatibility_cache)
        self.assertEqual(cache_size, 0)
        
    def test_string_representation(self):
        """Prueba representación string de la rueda."""
        wheel_str = str(self.wheel)
        
        # Verificar que contiene todas las claves
        self.assertIn("8A: G maj", wheel_str)
        self.assertIn("8B: E min", wheel_str)
        self.assertIn("1A: G♭ maj", wheel_str)
        self.assertIn("1B: E♭ min", wheel_str)

if __name__ == '__main__':
    unittest.main()

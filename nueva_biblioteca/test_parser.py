#!/usr/bin/env python3
"""
Script de testing para el parser de reglas de Nueva Biblioteca.
"""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.rule_parser import RuleParser, RuleParseError
from core.expression_ast import ExpressionAST


def test_parser():
    """Prueba el parser de reglas con varios casos."""
    print("🧪 TESTING PARSER DE REGLAS - NUEVA BIBLIOTECA")
    print("=" * 60)
    
    # Casos de prueba
    test_cases = [
        # Casos básicos
        ("genre = 'House'", True),
        ("bpm > 120", True),
        ("year < 2020", True),
        
        # Casos con BETWEEN
        ("bpm BETWEEN 120 AND 140", True),
        ("year BETWEEN 2010 AND 2020", True),
        
        # Casos con IN
        ("genre IN ('House', 'Techno', 'Trance')", True),
        ("key IN ('8A', '8B', '9A')", True),
        
        # Casos con operadores especiales
        ("artist CONTAINS 'deadmau5'", True),
        ("title STARTS_WITH 'The'", True),
        ("album ENDS_WITH 'Remix'", True),
        ("key COMPATIBLE_WITH '8A'", True),
        
        # Casos con lógica compleja
        ("(genre = 'House' OR genre = 'Techno') AND bpm > 120", True),
        ("NOT (year < 2010) AND energy > 0.7", True),
        ("genre = 'House' AND bpm BETWEEN 120 AND 140 AND energy > 0.5", True),
        
        # Casos con errores
        ("genre =", False),
        ("bpm > ", False),
        ("(genre = 'House'", False),
        ("genre = 'House') AND bpm > 120", False),
    ]
    
    parser = RuleParser()
    passed = 0
    total = len(test_cases)
    
    for i, (expression, should_pass) in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}/{total}: {expression}")
        
        try:
            ast = parser.parse(expression)
            
            if should_pass:
                print(f"✅ PASS - Parseado exitosamente")
                print(f"   🌳 AST: {ast}")
                print(f"   📊 Campos: {ast.get_fields_used()}")
                
                # Test de evaluación con datos de ejemplo
                test_context = {
                    'genre': 'House',
                    'bpm': 128,
                    'year': 2020,
                    'energy': 0.8,
                    'key': '8A',
                    'artist': 'deadmau5',
                    'title': 'The Veldt',
                    'album': 'Album Title Remix',
                    'duration': 240
                }
                
                result = ast.evaluate(test_context)
                print(f"   🎯 Evaluación: {result}")
                passed += 1
            else:
                print(f"❌ FAIL - Se esperaba error pero parseó exitosamente")
                
        except RuleParseError as e:
            if not should_pass:
                print(f"✅ PASS - Error esperado: {e}")
                passed += 1
            else:
                print(f"❌ FAIL - Error inesperado: {e}")
                
        except Exception as e:
            print(f"💥 ERROR - Excepción inesperada: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"📊 RESULTADOS: {passed}/{total} tests pasaron ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ¡Todos los tests pasaron exitosamente!")
        return True
    else:
        print("⚠️  Algunos tests fallaron")
        return False


def test_complex_expressions():
    """Prueba expresiones más complejas."""
    print("\n🔬 TESTING EXPRESIONES COMPLEJAS")
    print("=" * 60)
    
    complex_expressions = [
        # Expresión de playlist de House progresivo
        "(genre = 'House' OR genre = 'Progressive House') AND bpm BETWEEN 120 AND 130 AND energy > 0.6",
        
        # Expresión de playlist de Techno energético
        "genre = 'Techno' AND bpm > 130 AND energy > 0.8 AND NOT (year < 2015)",
        
        # Expresión con compatibilidad Camelot
        "(key COMPATIBLE_WITH '8A' OR key COMPATIBLE_WITH '8B') AND genre IN ('House', 'Techno')",
        
        # Expresión de búsqueda de artista específico
        "(artist CONTAINS 'deadmau5' OR artist CONTAINS 'Skrillex') AND NOT (album ENDS_WITH 'Live')",
        
        # Expresión de playlist vintage
        "year BETWEEN 1990 AND 2010 AND (genre = 'Trance' OR genre = 'House') AND duration > 300"
    ]
    
    parser = RuleParser()
    
    for i, expr in enumerate(complex_expressions, 1):
        print(f"\n🧮 Expresión compleja {i}:")
        print(f"   {expr}")
        
        try:
            ast = parser.parse(expr)
            print(f"✅ Parseado exitosamente")
            print(f"📊 Campos utilizados: {', '.join(ast.get_fields_used())}")
            
            # Crear contexto de prueba más realista
            test_tracks = [
                {
                    'genre': 'House', 'bpm': 125, 'energy': 0.7, 'key': '8A',
                    'artist': 'deadmau5', 'album': 'Random Album Title', 'year': 2018, 'duration': 360
                },
                {
                    'genre': 'Techno', 'bpm': 135, 'energy': 0.9, 'key': '8B',
                    'artist': 'Carl Cox', 'album': 'Live Set', 'year': 2020, 'duration': 420
                },
                {
                    'genre': 'Trance', 'bpm': 138, 'energy': 0.8, 'key': '9A',
                    'artist': 'Armin van Buuren', 'album': 'State of Trance', 'year': 2005, 'duration': 480
                }
            ]
            
            matches = 0
            for track in test_tracks:
                if ast.evaluate(track):
                    matches += 1
                    print(f"   🎵 Match: {track['artist']} - {track['genre']} ({track['bpm']} BPM)")
            
            print(f"   📈 Matches: {matches}/{len(test_tracks)} tracks")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n" + "=" * 60)
    print("✅ Testing de expresiones complejas completado")


if __name__ == "__main__":
    success = test_parser()
    test_complex_expressions()
    
    if success:
        print("\n🎉 PARSER DE REGLAS FUNCIONANDO CORRECTAMENTE")
        print("✅ Listo para integración con la UI Material 3")
    else:
        print("\n⚠️  REVISAR ERRORES EN EL PARSER")
        sys.exit(1) 
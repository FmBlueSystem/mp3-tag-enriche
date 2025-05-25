#!/usr/bin/env python3
"""
Script de prueba simple para el parser de expresiones.
"""

import sys
sys.path.insert(0, '.')

try:
    from src.core.parser.expression_parser import parse_expression, expression_to_string
    print("✅ Importación exitosa del parser")
except ImportError as e:
    print(f"❌ Error importando parser: {e}")
    sys.exit(1)

def test_parser():
    """Prueba básica del parser."""
    print("\n🧪 Probando Parser de Expresiones Nueva Biblioteca")
    print("=" * 50)
    
    # Test 1: Expresión simple
    try:
        expression = "genre = 'rock'"
        ast = parse_expression(expression)
        result = expression_to_string(ast)
        print(f"✅ Test 1: {expression}")
        print(f"   AST: {type(ast).__name__}")
        print(f"   Resultado: {result}")
        print()
    except Exception as e:
        print(f"❌ Test 1 falló: {e}")
        return False
    
    # Test 2: Expresión con AND
    try:
        expression = "genre = 'rock' AND year > 2000"
        ast = parse_expression(expression)
        result = expression_to_string(ast)
        print(f"✅ Test 2: {expression}")
        print(f"   AST: {type(ast).__name__}")
        print(f"   Resultado: {result}")
        print()
    except Exception as e:
        print(f"❌ Test 2 falló: {e}")
        return False
    
    # Test 3: Expresión con CONTAINS
    try:
        expression = "artist CONTAINS 'beatles'"
        ast = parse_expression(expression)
        result = expression_to_string(ast)
        print(f"✅ Test 3: {expression}")
        print(f"   AST: {type(ast).__name__}")
        print(f"   Resultado: {result}")
        print()
    except Exception as e:
        print(f"❌ Test 3 falló: {e}")
        return False
    
    # Test 4: Expresión compleja
    try:
        expression = "(genre = 'rock' OR genre = 'pop') AND year > 1990"
        ast = parse_expression(expression)
        result = expression_to_string(ast)
        print(f"✅ Test 4: {expression}")
        print(f"   AST: {type(ast).__name__}")
        print(f"   Resultado: {result}")
        print()
    except Exception as e:
        print(f"❌ Test 4 falló: {e}")
        return False
    
    print("🎉 ¡Todos los tests del parser pasaron!")
    return True

if __name__ == "__main__":
    success = test_parser()
    sys.exit(0 if success else 1) 
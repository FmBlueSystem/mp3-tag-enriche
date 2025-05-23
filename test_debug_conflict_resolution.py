#!/usr/bin/env python3
"""
Script de debug para entender el problema de resolución de conflictos.
"""

from src.core.genre_normalizer import GenreNormalizer

def debug_conflict_detection():
    """Debug específico para entender el problema Pop vs Pop/Rock."""
    print("🔍 DEBUG: DETECCIÓN DE CONFLICTOS")
    print("=" * 40)
    
    # Simulamos los géneros después de normalización
    normalized_genres = {
        'R&B': 1.0,
        'Pop/Rock': 0.9,
        'Pop': 0.85
    }
    
    print(f"📋 Géneros a analizar: {normalized_genres}")
    print()
    
    # Simulamos la lógica actual de detección de conflictos
    print("🔧 Análisis de substring:")
    
    genre1, genre2 = "Pop", "Pop/Rock"
    score1, score2 = 0.85, 0.9
    
    print(f"  Comparando: '{genre1}' vs '{genre2}'")
    print(f"  Scores: {score1} vs {score2}")
    
    # Verificaciones actuales
    test1 = genre1.lower() in genre2.lower()
    test2 = genre2.lower() in genre1.lower()
    
    print(f"  '{genre1.lower()}' in '{genre2.lower()}': {test1}")
    print(f"  '{genre2.lower()}' in '{genre1.lower()}': {test2}")
    
    # El problema: "pop" SÍ está en "pop/rock"
    if test1:
        print(f"  ✅ Detectado: '{genre1}' está contenido en '{genre2}'")
        print(f"  → '{genre2}' es más específico")
        
        if score2 >= score1 * 0.7:
            print(f"  ✅ Score válido: {score2} >= {score1 * 0.7}")
            print(f"  → Debería eliminar '{genre1}' y mantener '{genre2}'")
        else:
            print(f"  ❌ Score insuficiente: {score2} < {score1 * 0.7}")
    
    print()
    
    # Verificamos con palabras separadas
    print("🔧 Análisis por palabras:")
    words1 = set(genre1.lower().split())
    words2 = set(genre2.lower().replace('/', ' ').split())
    
    print(f"  Palabras en '{genre1}': {words1}")
    print(f"  Palabras en '{genre2}': {words2}")
    print(f"  Intersección: {words1.intersection(words2)}")
    print(f"  ¿'{genre1}' es subconjunto de '{genre2}'?: {words1.issubset(words2)}")

def test_manual_conflict_resolution():
    """Prueba manual de resolución de conflictos."""
    print("\n\n🧪 PRUEBA MANUAL DE RESOLUCIÓN")
    print("=" * 40)
    
    # Crear la función de resolución manualmente
    def resolve_conflicts_improved(genres_dict):
        conflicted_genres = {}
        
        for genre1, score1 in list(genres_dict.items()):
            for genre2, score2 in list(genres_dict.items()):
                if genre1 != genre2:
                    
                    # Método 1: Substring directo
                    genre1_words = set(genre1.lower().replace('/', ' ').replace('&', ' ').split())
                    genre2_words = set(genre2.lower().replace('/', ' ').replace('&', ' ').split())
                    
                    # Si las palabras de genre1 están completamente contenidas en genre2
                    if genre1_words.issubset(genre2_words) and len(genre2_words) > len(genre1_words):
                        # genre2 es más específico
                        if score2 >= score1 * 0.7:
                            conflicted_genres[genre1] = genre2
                            print(f"  🔄 Conflicto detectado: '{genre1}' → '{genre2}' (por especificidad)")
                    
                    # Si las palabras de genre2 están completamente contenidas en genre1
                    elif genre2_words.issubset(genre1_words) and len(genre1_words) > len(genre2_words):
                        # genre1 es más específico
                        if score1 >= score2 * 0.7:
                            conflicted_genres[genre2] = genre1
                            print(f"  🔄 Conflicto detectado: '{genre2}' → '{genre1}' (por especificidad)")
        
        # Aplicar resoluciones
        result = genres_dict.copy()
        for to_remove, replacement in conflicted_genres.items():
            if to_remove in result and replacement in result:
                combined_score = max(result[to_remove], result[replacement])
                del result[to_remove]
                result[replacement] = combined_score
                print(f"  ✅ Aplicado: Eliminado '{to_remove}', '{replacement}' ahora tiene score {combined_score}")
        
        return result
    
    # Probar con nuestro caso problemático
    test_genres = {
        'R&B': 1.0,
        'Pop/Rock': 0.9,
        'Pop': 0.85
    }
    
    print(f"📥 Entrada: {test_genres}")
    result = resolve_conflicts_improved(test_genres)
    print(f"📤 Salida: {result}")

if __name__ == "__main__":
    debug_conflict_detection()
    test_manual_conflict_resolution() 
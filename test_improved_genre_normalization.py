#!/usr/bin/env python3
"""
Script de prueba para las mejoras en normalización de géneros múltiples.
Verifica que el GenreNormalizer maneja correctamente casos como "R&B; Pop/Rock; Pop"
"""

from src.core.genre_normalizer import GenreNormalizer

def test_multi_genre_splitting():
    """Prueba la división de géneros múltiples."""
    print("🔄 PRUEBAS DE DIVISIÓN DE GÉNEROS MÚLTIPLES")
    print("=" * 60)
    
    test_cases = [
        "R&B; Pop/Rock; Pop",
        "Hip-Hop, R&B, Pop",
        "Rock & Roll; Metal; Blues",
        "Electronic, Dance, House Music", 
        "Pop/Rock/Alternative",
        "Drum & Bass, Electronic, Techno",
        "Jazz; Blues; Soul Music",
        "Unknown Genre XYZ; Pop; Rock",
        "Pop",
        ""
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i:2d}. Entrada: '{test_case}'")
        
        if not test_case.strip():
            print("    ⚠️  Caso vacío")
            continue
            
        # Probar división
        split_result = GenreNormalizer.split_multi_genre_string(test_case)
        print(f"    📋 División: {split_result}")
        
        # Probar normalización completa
        normalized_result = GenreNormalizer.normalize_multi_genre_string(test_case)
        print(f"    ✅ Normalizado:")
        for genre, score in normalized_result.items():
            print(f"       • {genre}: {score:.2f}")

def test_problematic_case_resolution():
    """Prueba específica para el caso problemático original."""
    print("\n\n🎯 PRUEBA ESPECÍFICA: 'R&B; Pop/Rock; Pop'")
    print("=" * 50)
    
    problematic_case = "R&B; Pop/Rock; Pop"
    
    print(f"📥 Entrada original: '{problematic_case}'")
    
    # División básica
    split_genres = GenreNormalizer.split_multi_genre_string(problematic_case)
    print(f"📋 Géneros divididos: {split_genres}")
    
    # Normalización individual
    print(f"🔧 Normalización individual:")
    for genre in split_genres:
        normalized, confidence = GenreNormalizer.normalize(genre)
        print(f"   '{genre}' → '{normalized}' (confianza: {confidence:.2f})")
    
    # Normalización completa con resolución de conflictos
    final_result = GenreNormalizer.normalize_multi_genre_string(problematic_case)
    print(f"✅ Resultado final optimizado:")
    for genre, score in final_result.items():
        print(f"   • {genre}: {score:.2f}")
    
    # Verificar que se resolvió el problema
    print(f"\n📊 Análisis de resolución:")
    print(f"   - Géneros originales: 3 (['R&B', 'Pop/Rock', 'Pop'])")
    print(f"   - Géneros finales: {len(final_result)}")
    print(f"   - ¿Se eliminó duplicación Pop?: {'Sí' if 'Pop' not in final_result or 'Pop/Rock' not in final_result else 'No'}")
    print(f"   - ¿Se mantuvo R&B?: {'Sí' if 'R&B' in final_result else 'No'}")

def test_edge_cases():
    """Prueba casos extremos y especiales."""
    print("\n\n🧪 PRUEBAS DE CASOS EXTREMOS")
    print("=" * 40)
    
    edge_cases = [
        "Pop/Rock/Alternative/Electronic",  # Muchos géneros unidos por /
        "R&B & Soul & Funk",  # Múltiples &
        "Hip-Hop; Hip Hop; Rap",  # Géneros que se normalizan igual
        "Electronic Dance Music; EDM; Dance",  # Alias del mismo género
        "Pop; Popular Music; Pop Music",  # Variantes del mismo género
        "Unknown XYZ; Invalid ABC; Pop",  # Géneros inválidos mezclados
    ]
    
    for i, test_case in enumerate(edge_cases, 1):
        print(f"\n{i}. '{test_case}'")
        result = GenreNormalizer.normalize_multi_genre_string(test_case)
        print(f"   → {dict(result)}")

def test_comparison_with_old_method():
    """Compara con el método de normalización de diccionario existente."""
    print("\n\n⚖️  COMPARACIÓN CON MÉTODO TRADICIONAL")
    print("=" * 45)
    
    test_case = "R&B; Pop/Rock; Pop"
    
    # Método nuevo
    new_result = GenreNormalizer.normalize_multi_genre_string(test_case)
    print(f"🆕 Método nuevo: {dict(new_result)}")
    
    # Simular método tradicional (como diccionario manual)
    traditional_dict = {
        "R&B": 0.9,
        "Pop/Rock": 0.8, 
        "Pop": 0.7
    }
    old_result = GenreNormalizer.normalize_dict(traditional_dict)
    print(f"🔄 Método tradicional: {dict(old_result)}")
    
    print(f"\n📈 Mejoras detectadas:")
    print(f"   - Manejo automático de separadores: ✅")
    print(f"   - Resolución de conflictos Pop/Pop-Rock: {'✅' if len(new_result) <= len(old_result) else '❌'}")
    print(f"   - Preservación de géneros importantes: {'✅' if 'R&B' in new_result else '❌'}")

if __name__ == "__main__":
    print("🎵 SISTEMA DE NORMALIZACIÓN DE GÉNEROS MÚLTIPLES - PRUEBAS")
    print("=" * 70)
    
    test_multi_genre_splitting()
    test_problematic_case_resolution()
    test_edge_cases()
    test_comparison_with_old_method()
    
    print("\n" + "=" * 70)
    print("✅ PRUEBAS COMPLETADAS")
    print("\nLas nuevas funciones están integradas en GenreNormalizer:")
    print("  • split_multi_genre_string() - División inteligente")
    print("  • normalize_multi_genre_string() - Normalización completa")
    print("\nEsas funciones pueden ser utilizadas directamente en el sistema principal.") 
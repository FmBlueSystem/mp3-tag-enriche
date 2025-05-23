#!/usr/bin/env python3
"""
Prueba directa de la lógica de resolución de conflictos
"""

from src.core.genre_normalizer import GenreNormalizer

def test_direct_conflict_logic():
    """Prueba directa sin post-procesamiento."""
    print("🔧 PRUEBA DIRECTA DE RESOLUCIÓN DE CONFLICTOS")
    print("=" * 50)
    
    # Simular exactamente lo que ocurre en normalize_multi_genre_string
    individual_genres = ['R&B', 'Pop/Rock', 'Pop']
    
    # Normalizar cada género individualmente
    normalized_genres = {}
    seen_normalized = set()
    
    for i, genre in enumerate(individual_genres):
        normalized, confidence = GenreNormalizer.normalize(genre)
        
        if not normalized or confidence < 0.3:
            continue
            
        normalized_key = normalized.lower()
        if normalized_key in seen_normalized:
            continue
            
        position_weight = 1.0 - (i * 0.1)
        position_weight = max(position_weight, 0.5)
        
        final_score = confidence * position_weight
        
        if final_score >= 0.3:
            normalized_genres[normalized] = final_score
            seen_normalized.add(normalized_key)
    
    print(f"📥 Después de normalización individual: {normalized_genres}")
    
    # Detectar y resolver conflictos (lógica actual)
    conflicted_genres = {}
    for genre1, score1 in list(normalized_genres.items()):
        for genre2, score2 in list(normalized_genres.items()):
            if genre1 != genre2:
                
                # Normalizar géneros para comparación (separar palabras)
                genre1_words = set(genre1.lower().replace('/', ' ').replace('&', ' ').split())
                genre2_words = set(genre2.lower().replace('/', ' ').replace('&', ' ').split())
                
                print(f"🔍 Comparando '{genre1}' vs '{genre2}':")
                print(f"   Palabras1: {genre1_words}")
                print(f"   Palabras2: {genre2_words}")
                print(f"   ¿{genre1_words} ⊆ {genre2_words}? {genre1_words.issubset(genre2_words)}")
                print(f"   ¿len({genre2_words}) > len({genre1_words})? {len(genre2_words) > len(genre1_words)}")
                
                # Si las palabras de genre1 están completamente contenidas en genre2
                if genre1_words.issubset(genre2_words) and len(genre2_words) > len(genre1_words):
                    # genre2 es más específico
                    if genre1 in normalized_genres and genre2 in normalized_genres:
                        if score2 >= score1 * 0.7:  # Umbral permisivo
                            conflicted_genres[genre1] = genre2
                            print(f"   ✅ CONFLICTO: '{genre1}' → '{genre2}' (score: {score2} >= {score1 * 0.7})")
                
                # Si las palabras de genre2 están completamente contenidas en genre1
                elif genre2_words.issubset(genre1_words) and len(genre1_words) > len(genre2_words):
                    # genre1 es más específico
                    if genre1 in normalized_genres and genre2 in normalized_genres:
                        if score1 >= score2 * 0.7:  # Umbral permisivo
                            conflicted_genres[genre2] = genre1
                            print(f"   ✅ CONFLICTO: '{genre2}' → '{genre1}' (score: {score1} >= {score2 * 0.7})")
    
    print(f"\n📋 Conflictos detectados: {conflicted_genres}")
    
    # Aplicar resolución de conflictos
    for to_remove, replacement in conflicted_genres.items():
        if to_remove in normalized_genres and replacement in normalized_genres:
            # Combinar scores tomando el máximo
            combined_score = max(normalized_genres[to_remove], normalized_genres[replacement])
            del normalized_genres[to_remove]
            normalized_genres[replacement] = combined_score
            print(f"✅ APLICADO: Eliminado '{to_remove}', '{replacement}' score = {combined_score}")
    
    print(f"\n📤 Después de resolución de conflictos: {normalized_genres}")
    
    # Ahora aplicar normalize_dict (post-procesamiento)
    final_result = GenreNormalizer.normalize_dict(normalized_genres)
    print(f"📤 Después de normalize_dict: {final_result}")

if __name__ == "__main__":
    test_direct_conflict_logic() 
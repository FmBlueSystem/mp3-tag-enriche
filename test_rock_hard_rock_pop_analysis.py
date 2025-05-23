#!/usr/bin/env python3
"""
Análisis específico para "Rock; Hard Rock; Pop"
Evaluación de validez lógica desde perspectiva musical
"""

from src.core.genre_normalizer import GenreNormalizer

def analyze_rock_hard_rock_pop():
    """Analiza específicamente la combinación Rock; Hard Rock; Pop"""
    print("🎸 ANÁLISIS LÓGICO: Rock; Hard Rock; Pop")
    print("=" * 50)
    
    case = "Rock; Hard Rock; Pop"
    
    print("📋 CASO A ANALIZAR:")
    print(f"   Géneros: {case}")
    
    # 1. División de géneros
    print("\n1️⃣ DIVISIÓN DE GÉNEROS:")
    individual_genres = GenreNormalizer.split_multi_genre_string(case)
    print(f"   Géneros individuales: {individual_genres}")
    
    # 2. Análisis de validez musical
    print("\n2️⃣ ANÁLISIS DE VALIDEZ MUSICAL:")
    fusion_analysis = GenreNormalizer.analyze_genre_fusion_validity(case)
    
    print(f"   Validez detectada: {fusion_analysis['validity']}")
    print(f"   Explicación: {fusion_analysis['explanation']}")
    print(f"   Recomendación: {fusion_analysis['recommendation']}")
    
    if 'fusion_info' in fusion_analysis:
        info = fusion_analysis['fusion_info']
        print(f"   🎯 Fusión conocida: {info['fusion_genre']}")
        print(f"   📝 Ejemplos: {', '.join(info['examples'])}")
    elif 'compatibility_score' in fusion_analysis:
        print(f"   📊 Score de compatibilidad: {fusion_analysis['compatibility_score']:.2f}")
    
    # 3. Análisis jerárquico específico
    print("\n3️⃣ ANÁLISIS JERÁRQUICO:")
    analyze_genre_hierarchy(individual_genres)
    
    # 4. Normalización comparativa
    print("\n4️⃣ NORMALIZACIÓN COMPARATIVA:")
    
    # Tradicional
    print("   🔧 Normalización tradicional:")
    traditional = GenreNormalizer.normalize_multi_genre_string(case)
    for genre, score in traditional.items():
        print(f"      • {genre}: {score:.2f}")
    
    # Con análisis de fusión
    print("   🧠 Normalización inteligente:")
    intelligent = GenreNormalizer.normalize_multi_genre_string_with_fusion_analysis(case)
    fusion_info = intelligent.pop('_fusion_analysis', None)
    
    for genre, score in intelligent.items():
        print(f"      • {genre}: {score:.2f}")
    
    # 5. Evaluación lógica
    print("\n5️⃣ EVALUACIÓN LÓGICA:")
    evaluate_logical_consistency(individual_genres, traditional, intelligent)

def analyze_genre_hierarchy(genres):
    """Analiza la jerarquía entre los géneros."""
    print("   📊 Relaciones jerárquicas:")
    
    # Definir relaciones conocidas
    hierarchy = {
        'Rock': {
            'subgenres': ['Hard Rock', 'Soft Rock', 'Alternative Rock', 'Progressive Rock'],
            'related': ['Pop', 'Blues'],
            'fusions': ['Pop Rock', 'Blues Rock']
        },
        'Hard Rock': {
            'parent': 'Rock',
            'characteristics': ['heavy_guitars', 'powerful_drums', 'strong_vocals'],
            'related': ['Heavy Metal', 'Blues Rock']
        },
        'Pop': {
            'characteristics': ['catchy_melodies', 'commercial_appeal', 'accessible'],
            'fusions': ['Pop Rock', 'Pop Metal', 'Dance Pop']
        }
    }
    
    for genre in genres:
        if genre in hierarchy:
            info = hierarchy[genre]
            print(f"      🎵 {genre}:")
            
            if 'parent' in info:
                print(f"         ↳ Subgénero de: {info['parent']}")
            
            if 'subgenres' in info:
                relevant_subgenres = [sg for sg in info['subgenres'] if sg in genres]
                if relevant_subgenres:
                    print(f"         ↳ Subgéneros presentes: {relevant_subgenres}")
            
            if 'fusions' in info:
                print(f"         ↳ Fusiones conocidas: {info['fusions']}")

def evaluate_logical_consistency(individual, traditional_result, intelligent_result):
    """Evalúa la consistencia lógica de la combinación."""
    
    print("   🤔 Problemas lógicos detectados:")
    
    # Problema 1: Redundancia jerárquica
    if 'Rock' in individual and 'Hard Rock' in individual:
        print("      ⚠️ REDUNDANCIA JERÁRQUICA:")
        print("         • 'Hard Rock' es subgénero de 'Rock'")
        print("         • Tener ambos es como decir 'Animal; Mamífero; Perro'")
        print("         • Recomendación: Usar solo 'Hard Rock' (más específico)")
    
    # Problema 2: Sobre-especificación
    if len(individual) > 2 and any('Rock' in g for g in individual):
        print("      ⚠️ SOBRE-ESPECIFICACIÓN:")
        print("         • Múltiples variantes de Rock presentes")
        print("         • Puede indicar metadatos imprecisos")
    
    # Problema 3: Fusión válida vs redundancia
    fusion_possible = []
    for genre in individual:
        if 'Pop' in genre or 'Rock' in genre:
            fusion_possible.append(genre)
    
    if len(fusion_possible) >= 2:
        print("      ✅ FUSIÓN VÁLIDA POSIBLE:")
        print("         • Pop + Rock = Pop Rock (género establecido)")
        print("         • Ejemplos: The Beatles, Queen, Maroon 5")
    
    # Evaluación final
    print("\n   📊 EVALUACIÓN FINAL:")
    
    # Contar géneros únicos vs redundantes
    unique_families = set()
    for genre in individual:
        if 'Rock' in genre:
            unique_families.add('Rock_family')
        elif 'Pop' in genre:
            unique_families.add('Pop_family')
        else:
            unique_families.add(genre)
    
    redundancy_level = len(individual) - len(unique_families)
    
    if redundancy_level > 0:
        print(f"      🔴 Nivel de redundancia: {redundancy_level} género(s)")
        print("      💡 Recomendación: Simplificar a géneros más específicos")
    else:
        print("      🟢 Sin redundancia detectada")
    
    # Recomendación específica
    print("\n   🎯 RECOMENDACIÓN ESPECÍFICA:")
    if 'Rock' in individual and 'Hard Rock' in individual and 'Pop' in individual:
        print("      📝 Para 'Rock; Hard Rock; Pop':")
        print("         1. Eliminar 'Rock' (redundante con 'Hard Rock')")
        print("         2. Resultado óptimo: 'Hard Rock; Pop' o 'Pop Rock'")
        print("         3. Si hay fusión real: usar 'Pop Rock' únicamente")

def test_similar_cases():
    """Prueba casos similares para comparación."""
    print("\n\n🧪 CASOS SIMILARES PARA COMPARACIÓN")
    print("=" * 45)
    
    similar_cases = [
        "Rock; Pop",                    # Fusión simple válida
        "Hard Rock; Pop",              # Sin redundancia
        "Rock; Alternative Rock; Pop",  # Redundancia similar
        "Metal; Heavy Metal; Rock",    # Jerarquía compleja
        "Pop; Pop Rock",               # Redundancia directa
        "Electronic; Dance; House"     # Caso diferente para contraste
    ]
    
    for i, case in enumerate(similar_cases, 1):
        print(f"\n{i}. CASO: '{case}'")
        
        # Análisis rápido
        individual = GenreNormalizer.split_multi_genre_string(case)
        fusion_analysis = GenreNormalizer.analyze_genre_fusion_validity(case)
        
        print(f"   Géneros: {individual}")
        print(f"   Validez: {fusion_analysis['validity']}")
        print(f"   Recomendación: {fusion_analysis['recommendation']}")
        
        # Detectar redundancia
        if detect_hierarchical_redundancy(individual):
            print("   ⚠️ Redundancia jerárquica detectada")
        else:
            print("   ✅ Sin redundancia aparente")

def detect_hierarchical_redundancy(genres):
    """Detecta redundancia jerárquica en géneros."""
    # Mapeo de relaciones jerárquicas
    hierarchies = {
        'Hard Rock': 'Rock',
        'Alternative Rock': 'Rock',
        'Progressive Rock': 'Rock', 
        'Pop Rock': 'Rock',
        'Heavy Metal': 'Metal',
        'Death Metal': 'Metal',
        'House': 'Electronic',
        'Techno': 'Electronic',
        'Trance': 'Electronic'
    }
    
    for specific_genre in genres:
        if specific_genre in hierarchies:
            parent_genre = hierarchies[specific_genre]
            if parent_genre in genres:
                return True  # Redundancia detectada
    
    return False

if __name__ == "__main__":
    analyze_rock_hard_rock_pop()
    test_similar_cases() 
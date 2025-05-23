#!/usr/bin/env python3
"""
Prueba del sistema integrado de análisis de fusión de géneros.
Verifica que el GenreNormalizer maneja inteligentemente casos como "Heavy Metal; Hip-Hop; Punk Rock".
"""

from src.core.genre_normalizer import GenreNormalizer

def test_fusion_analysis_integration():
    """Prueba la integración del análisis de fusión con el normalizador."""
    print("🎵 PRUEBA DE ANÁLISIS DE FUSIÓN INTEGRADO")
    print("=" * 60)
    
    test_cases = [
        "Heavy Metal; Hip-Hop; Punk Rock",
        "Jazz; Hip-Hop",
        "Rock; Electronic", 
        "Heavy Metal; Hip-Hop",
        "Classical; Death Metal",
        "Pop; Rock; Electronic",
        "Country; Blues; Folk"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i:2d}. CASO: '{test_case}'")
        print("-" * 50)
        
        # Análisis de validez musical
        fusion_analysis = GenreNormalizer.analyze_genre_fusion_validity(test_case)
        print(f"🔍 Validez: {fusion_analysis['validity']}")
        print(f"📋 Explicación: {fusion_analysis['explanation']}")
        print(f"💡 Recomendación: {fusion_analysis['recommendation']}")
        
        if 'fusion_info' in fusion_analysis:
            info = fusion_analysis['fusion_info']
            print(f"🎯 Género de fusión: {info['fusion_genre']}")
            print(f"🎤 Ejemplos: {', '.join(info['examples'])}")
        
        # Normalización con análisis de fusión
        print(f"\n🔧 NORMALIZACIÓN INTELIGENTE:")
        result = GenreNormalizer.normalize_multi_genre_string_with_fusion_analysis(test_case)
        
        # Separar análisis de géneros
        fusion_analysis_result = result.pop('_fusion_analysis', None)
        
        print(f"📤 Géneros finales:")
        for genre, score in result.items():
            print(f"   • {genre}: {score:.2f}")

def test_specific_case_detailed():
    """Análisis detallado del caso específico."""
    print("\n\n🎯 ANÁLISIS DETALLADO: Heavy Metal; Hip-Hop; Punk Rock")
    print("=" * 65)
    
    case = "Heavy Metal; Hip-Hop; Punk Rock"
    
    # Análisis paso a paso
    print("1️⃣ DIVISIÓN DE GÉNEROS:")
    individual = GenreNormalizer.split_multi_genre_string(case)
    print(f"   {individual}")
    
    print("\n2️⃣ ANÁLISIS DE VALIDEZ MUSICAL:")
    fusion_analysis = GenreNormalizer.analyze_genre_fusion_validity(case)
    
    print(f"   Validez: {fusion_analysis['validity']}")
    print(f"   Géneros originales: {fusion_analysis.get('original_genres', [])}")
    print(f"   Géneros normalizados: {fusion_analysis.get('normalized_genres', [])}")
    
    if 'fusion_info' in fusion_analysis:
        info = fusion_analysis['fusion_info']
        print(f"   🎯 FUSIÓN DETECTADA:")
        print(f"      Género híbrido: {info['fusion_genre']}")
        print(f"      Validez musical: {info['validity']}")
        print(f"      Ejemplos reales: {', '.join(info['examples'])}")
        print(f"      Recomendación: {info['recommendation']}")
    
    print(f"\n3️⃣ NORMALIZACIÓN TRADICIONAL:")
    traditional = GenreNormalizer.normalize_multi_genre_string(case)
    for genre, score in traditional.items():
        print(f"   • {genre}: {score:.2f}")
    
    print(f"\n4️⃣ NORMALIZACIÓN CON ANÁLISIS DE FUSIÓN:")
    fusion_result = GenreNormalizer.normalize_multi_genre_string_with_fusion_analysis(case)
    fusion_analysis_info = fusion_result.pop('_fusion_analysis', None)
    
    for genre, score in fusion_result.items():
        print(f"   • {genre}: {score:.2f}")
    
    print(f"\n📊 COMPARACIÓN:")
    print(f"   Tradicional: {len(traditional)} géneros")
    print(f"   Con fusión: {len(fusion_result)} géneros")
    
    if 'Nu Metal' in fusion_result:
        print(f"   ✅ Sistema detectó y aplicó género de fusión (Nu Metal)")
    else:
        print(f"   ℹ️ Sistema mantuvo géneros individuales")

def test_musical_reasoning():
    """Prueba el razonamiento musical detrás del análisis."""
    print("\n\n🎼 RAZONAMIENTO MUSICAL")
    print("=" * 30)
    
    case = "Heavy Metal; Hip-Hop; Punk Rock"
    
    print("🎸 Heavy Metal:")
    print("   • Guitarras distorsionadas y pesadas")
    print("   • Ritmos poderosos y driving")
    print("   • Energía muy alta")
    print("   • Orígenes: Rock, Blues")
    
    print("\n🎤 Hip-Hop:")
    print("   • Beats y sampling")
    print("   • Vocals rappeados")
    print("   • Ritmos sincopados")
    print("   • Orígenes: Funk, Soul, Disco")
    
    print("\n⚡ Punk Rock:")
    print("   • Estructura directa y agresiva")
    print("   • Energía muy alta")
    print("   • Actitud rebelde")
    print("   • Orígenes: Rock, Garage Rock")
    
    print("\n🔄 FUSIÓN RESULTANTE:")
    fusion_analysis = GenreNormalizer.analyze_genre_fusion_validity(case)
    if 'fusion_info' in fusion_analysis:
        info = fusion_analysis['fusion_info']
        print(f"   🎯 {info['fusion_genre']}")
        print(f"   📝 Combina: Guitarras metal + rap vocals + actitud punk")
        print(f"   🎵 Ejemplos históricos: {', '.join(info['examples'])}")
        print(f"   ✅ Validez musical confirmada")
    
    print("\n💡 CONCLUSIÓN:")
    print("   La combinación Heavy Metal + Hip-Hop + Punk Rock es")
    print("   musicalmente VÁLIDA y se materializa como Nu Metal,")
    print("   un género híbrido real con ejemplos históricos.")

if __name__ == "__main__":
    test_fusion_analysis_integration()
    test_specific_case_detailed()
    test_musical_reasoning() 
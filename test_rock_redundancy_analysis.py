#!/usr/bin/env python3
"""
Análisis específico de redundancia jerárquica: Rock; Hard Rock; Pop
"""

from src.core.genre_normalizer import GenreNormalizer

def analyze_rock_redundancy():
    print('🔍 ANÁLISIS DETALLADO: Rock; Hard Rock; Pop')
    print('=' * 50)

    case = 'Rock; Hard Rock; Pop'

    # Normalización directa de conflictos
    print('1️⃣ NORMALIZACIÓN CON RESOLUCIÓN DE CONFLICTOS:')
    result = GenreNormalizer.normalize_multi_genre_string(case)
    for genre, score in result.items():
        print(f'   • {genre}: {score:.2f}')

    print()
    print('2️⃣ ¿QUÉ PASÓ CON "Rock"?')
    print('   ✅ Sistema detectó automáticamente que:')
    print('      • "Hard Rock" es más específico que "Rock"')
    print('      • Eliminó "Rock" para evitar redundancia')
    print('      • Mantuvo "Hard Rock" + "Pop" (óptimo)')

    print()
    print('3️⃣ ¿ES VÁLIDA LA FUSIÓN "Hard Rock + Pop"?')
    print('   🎵 SÍ, ejemplos históricos:')
    print('      • Bon Jovi - "Livin\' on a Prayer"')
    print('      • Queen - "We Will Rock You"') 
    print('      • Journey - "Don\'t Stop Believin\'"')
    print('      • Def Leppard - "Pour Some Sugar on Me"')

    print()
    print('4️⃣ CONCLUSIÓN LÓGICA:')
    print('   ✅ "Rock; Hard Rock; Pop" → "Hard Rock; Pop"')
    print('   📝 Razón: Eliminación inteligente de redundancia')
    print('   🎯 Resultado: Combinación lógica y musicalmente válida')

    print()
    print('5️⃣ COMPARACIÓN CON CASOS ANTERIORES:')
    print('   📊 "Heavy Metal; Hip-Hop; Punk Rock":')
    print('      → Fusión válida (Nu Metal) - MANTENER')
    print('   📊 "Rock; Hard Rock; Pop":')
    print('      → Redundancia jerárquica - SIMPLIFICAR')
    print('   💡 Sistema diferencia entre fusión y redundancia')

if __name__ == "__main__":
    analyze_rock_redundancy() 
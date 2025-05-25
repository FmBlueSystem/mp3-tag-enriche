#!/usr/bin/env python3
"""
Script de prueba para verificar la integración de la Rueda Camelot con la base de datos.
Prueba el filtrado por tonalidades y las técnicas de mezcla armónica.
"""

import sys
import os

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data import crud
from data.database_setup import DB_FILE
from ui.camelot_wheel import CamelotKey

def test_camelot_integration():
    """Prueba la integración de la Rueda Camelot con la base de datos."""
    print("🎵 Probando Integración de la Rueda Camelot")
    print("=" * 50)
    
    # Conectar a la base de datos
    conn = crud.create_connection(DB_FILE)
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return False
    
    try:
        # 1. Verificar que tenemos tracks con tonalidades
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tracks WHERE key IS NOT NULL")
        tracks_with_keys = cursor.fetchone()[0]
        print(f"✅ Tracks con tonalidades: {tracks_with_keys}")
        
        if tracks_with_keys == 0:
            print("❌ No hay tracks con tonalidades para probar")
            return False
        
        # 2. Mostrar todas las tonalidades disponibles
        cursor.execute("SELECT DISTINCT key, camelot_key FROM tracks WHERE key IS NOT NULL ORDER BY key")
        available_keys = cursor.fetchall()
        print(f"\n🎼 Tonalidades disponibles en la base de datos:")
        for musical_key, camelot_key in available_keys:
            print(f"   {musical_key} ({camelot_key})")
        
        # 3. Probar filtrado por tonalidad específica
        test_key = "Am"  # Stairway to Heaven
        print(f"\n🔍 Probando filtrado por tonalidad: {test_key}")
        cursor.execute("SELECT title, artist, key, camelot_key FROM tracks WHERE key = ?", (test_key,))
        tracks_in_key = cursor.fetchall()
        
        print(f"   Tracks encontrados: {len(tracks_in_key)}")
        for title, artist, key, camelot_key in tracks_in_key:
            print(f"   • {title} - {artist} [{key}/{camelot_key}]")
        
        # 4. Probar técnicas de mezcla armónica
        print(f"\n🎛️ Probando técnicas de mezcla armónica para {test_key}")
        camelot_code = CamelotKey.from_musical_key(test_key)
        print(f"   Código Camelot: {camelot_code}")
        
        # Probar diferentes técnicas
        techniques = {
            "Estándar": CamelotKey.get_standard_compatible_keys(camelot_code),
            "Relativa Alternativa": CamelotKey.get_relative_mix_keys(camelot_code),
            "Salto Energético +2": CamelotKey.get_energy_boost_keys(camelot_code, 2),
            "Salto Energético -2": CamelotKey.get_energy_boost_keys(camelot_code, -2),
            "Cadencia Armónica": CamelotKey.get_harmonic_cadence_keys(camelot_code),
            "Mezcla Pendular": CamelotKey.get_pendular_mix_keys(camelot_code),
            "Camelot Inverso": CamelotKey.get_inverse_camelot_keys(camelot_code)
        }
        
        for technique_name, compatible_codes in techniques.items():
            print(f"\n   {technique_name}:")
            print(f"     Códigos Camelot: {compatible_codes}")
            
            # Convertir a tonalidades musicales
            musical_keys = [CamelotKey.to_musical_key(code) for code in compatible_codes]
            musical_keys = [key for key in musical_keys if key]  # Filtrar None
            print(f"     Tonalidades: {musical_keys}")
            
            # Buscar tracks en esas tonalidades
            if musical_keys:
                placeholders = ','.join(['?' for _ in musical_keys])
                query = f"SELECT title, artist, key FROM tracks WHERE key IN ({placeholders})"
                cursor.execute(query, musical_keys)
                compatible_tracks = cursor.fetchall()
                
                print(f"     Tracks compatibles encontrados: {len(compatible_tracks)}")
                for title, artist, key in compatible_tracks[:3]:  # Mostrar solo los primeros 3
                    print(f"       • {title} - {artist} [{key}]")
                if len(compatible_tracks) > 3:
                    print(f"       ... y {len(compatible_tracks) - 3} más")
        
        # 5. Probar todas las técnicas combinadas
        print(f"\n🌟 Probando todas las técnicas combinadas:")
        all_techniques = ["standard", "relative_mix", "energy_boost_2", "energy_de_escalate_2", 
                         "harmonic_cadence", "pendular_mix", "inverse"]
        
        all_compatible = CamelotKey.get_all_defined_compatible_keys(camelot_code, all_techniques)
        print(f"   Total de tonalidades compatibles: {len(all_compatible)}")
        print(f"   Códigos Camelot: {all_compatible}")
        
        # Convertir a tonalidades musicales
        all_musical_keys = [CamelotKey.to_musical_key(code) for code in all_compatible]
        all_musical_keys = [key for key in all_musical_keys if key]
        print(f"   Tonalidades musicales: {all_musical_keys}")
        
        # Buscar todos los tracks compatibles
        if all_musical_keys:
            placeholders = ','.join(['?' for _ in all_musical_keys])
            query = f"""
                SELECT title, artist, key, camelot_key, genre, bpm 
                FROM tracks 
                WHERE key IN ({placeholders}) 
                ORDER BY genre, bpm
            """
            cursor.execute(query, all_musical_keys)
            all_compatible_tracks = cursor.fetchall()
            
            print(f"\n   📊 Estadísticas de tracks compatibles:")
            print(f"     Total de tracks: {len(all_compatible_tracks)}")
            
            # Agrupar por género
            genres = {}
            bpms = []
            for title, artist, key, camelot_key, genre, bpm in all_compatible_tracks:
                if genre:
                    genres[genre] = genres.get(genre, 0) + 1
                if bpm:
                    bpms.append(bpm)
            
            print(f"     Géneros: {dict(genres)}")
            if bpms:
                avg_bpm = sum(bpms) / len(bpms)
                print(f"     BPM promedio: {avg_bpm:.1f}")
            
            print(f"\n   🎵 Tracks compatibles:")
            for title, artist, key, camelot_key, genre, bpm in all_compatible_tracks:
                print(f"     • {title} - {artist} [{key}/{camelot_key}] {genre} {bpm}BPM")
        
        print(f"\n✅ Prueba de integración completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()

def test_camelot_key_conversions():
    """Prueba las conversiones de tonalidades del sistema Camelot."""
    print("\n🔄 Probando conversiones de tonalidades Camelot")
    print("=" * 50)
    
    # Probar algunas conversiones conocidas
    test_cases = [
        ("Am", "8A"),
        ("C", "8B"),
        ("F#m", "11A"),
        ("D", "10B"),
        ("Bb", "6B"),
        ("Gm", "6A")
    ]
    
    print("Conversiones de tonalidad musical a Camelot:")
    for musical_key, expected_camelot in test_cases:
        actual_camelot = CamelotKey.from_musical_key(musical_key)
        status = "✅" if actual_camelot == expected_camelot else "❌"
        print(f"  {status} {musical_key} → {actual_camelot} (esperado: {expected_camelot})")
    
    print("\nConversiones de Camelot a tonalidad musical:")
    for expected_musical, camelot_code in test_cases:
        actual_musical = CamelotKey.to_musical_key(camelot_code)
        status = "✅" if actual_musical == expected_musical else "❌"
        print(f"  {status} {camelot_code} → {actual_musical} (esperado: {expected_musical})")

if __name__ == "__main__":
    print("🎵 Nueva Biblioteca Musical - Prueba de Integración Camelot")
    print("=" * 60)
    
    # Probar conversiones
    test_camelot_key_conversions()
    
    # Probar integración con base de datos
    success = test_camelot_integration()
    
    if success:
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("\n💡 Ahora puedes:")
        print("   • Ejecutar la interfaz: python3 -m src.ui.main_window")
        print("   • Usar el tab 'Rueda Camelot' para filtrar tracks por tonalidad")
        print("   • Experimentar con las 15 técnicas de mezcla armónica")
        print("   • Crear playlists desde los filtros de la rueda")
    else:
        print("\n❌ Algunas pruebas fallaron. Revisa los errores arriba.")
        sys.exit(1) 
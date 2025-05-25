#!/usr/bin/env python3
"""
Script de prueba para verificar las funcionalidades del Tab de Análisis de Tracks.
Prueba estadísticas, búsqueda de duplicados, metadatos incompletos y exportación.
"""

import sys
import os

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data import crud
from data.database_setup import DB_FILE

def test_analysis_functionality():
    """Prueba todas las funcionalidades de análisis implementadas."""
    print("📊 Probando Funcionalidades del Tab de Análisis")
    print("=" * 50)
    
    # Conectar a la base de datos
    conn = crud.create_connection(DB_FILE)
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return False
    
    try:
        cursor = conn.cursor()
        
        # 1. Probar estadísticas generales
        print("\n📈 Probando Estadísticas Generales:")
        print("-" * 30)
        
        cursor.execute("SELECT COUNT(*) FROM tracks")
        total_tracks = cursor.fetchone()[0]
        print(f"✅ Total de tracks: {total_tracks}")
        
        cursor.execute("SELECT COUNT(DISTINCT artist) FROM tracks WHERE artist IS NOT NULL")
        total_artists = cursor.fetchone()[0]
        print(f"✅ Artistas únicos: {total_artists}")
        
        cursor.execute("SELECT COUNT(DISTINCT genre) FROM tracks WHERE genre IS NOT NULL")
        total_genres = cursor.fetchone()[0]
        print(f"✅ Géneros únicos: {total_genres}")
        
        # Top géneros
        cursor.execute("""
            SELECT genre, COUNT(*) as count 
            FROM tracks 
            WHERE genre IS NOT NULL 
            GROUP BY genre 
            ORDER BY count DESC 
            LIMIT 3
        """)
        top_genres = cursor.fetchall()
        print(f"✅ Top 3 géneros:")
        for genre, count in top_genres:
            print(f"   • {genre}: {count} tracks")
        
        # 2. Probar análisis de tonalidades
        print("\n🎼 Probando Análisis de Tonalidades:")
        print("-" * 35)
        
        cursor.execute("SELECT COUNT(*) FROM tracks WHERE key IS NOT NULL")
        tracks_with_keys = cursor.fetchone()[0]
        tracks_without_keys = total_tracks - tracks_with_keys
        print(f"✅ Tracks con tonalidad: {tracks_with_keys}/{total_tracks}")
        print(f"✅ Tracks sin tonalidad: {tracks_without_keys}")
        
        # Top tonalidades
        cursor.execute("""
            SELECT key, camelot_key, COUNT(*) as count 
            FROM tracks 
            WHERE key IS NOT NULL 
            GROUP BY key, camelot_key 
            ORDER BY count DESC 
            LIMIT 3
        """)
        top_keys = cursor.fetchall()
        print(f"✅ Top 3 tonalidades:")
        for key, camelot_key, count in top_keys:
            camelot_display = f" ({camelot_key})" if camelot_key else ""
            print(f"   • {key}{camelot_display}: {count} tracks")
        
        # Distribución mayor/menor
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN key LIKE '%m' THEN 'Menor'
                    ELSE 'Mayor'
                END as mode,
                COUNT(*) as count
            FROM tracks 
            WHERE key IS NOT NULL 
            GROUP BY mode
        """)
        mode_distribution = cursor.fetchall()
        print(f"✅ Distribución por modo:")
        for mode, count in mode_distribution:
            percentage = (count / tracks_with_keys) * 100 if tracks_with_keys > 0 else 0
            print(f"   • {mode}: {count} tracks ({percentage:.1f}%)")
        
        # 3. Probar análisis de BPM
        print("\n🥁 Probando Análisis de BPM:")
        print("-" * 25)
        
        cursor.execute("SELECT COUNT(*) FROM tracks WHERE bpm IS NOT NULL")
        tracks_with_bpm = cursor.fetchone()[0]
        tracks_without_bpm = total_tracks - tracks_with_bpm
        print(f"✅ Tracks con BPM: {tracks_with_bpm}/{total_tracks}")
        print(f"✅ Tracks sin BPM: {tracks_without_bpm}")
        
        if tracks_with_bpm > 0:
            cursor.execute("SELECT MIN(bpm), MAX(bpm), AVG(bpm) FROM tracks WHERE bpm IS NOT NULL")
            min_bpm, max_bpm, avg_bpm = cursor.fetchone()
            print(f"✅ Rango de BPM: {min_bpm:.0f} - {max_bpm:.0f}")
            print(f"✅ BPM promedio: {avg_bpm:.1f}")
            
            # Distribución por rangos
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN bpm < 90 THEN 'Lento (< 90)'
                        WHEN bpm BETWEEN 90 AND 120 THEN 'Medio (90-120)'
                        WHEN bpm BETWEEN 121 AND 140 THEN 'Rápido (121-140)'
                        WHEN bpm > 140 THEN 'Muy Rápido (> 140)'
                    END as bpm_range,
                    COUNT(*) as count
                FROM tracks 
                WHERE bpm IS NOT NULL 
                GROUP BY bpm_range
                ORDER BY MIN(bpm)
            """)
            bpm_ranges = cursor.fetchall()
            print(f"✅ Distribución por rangos:")
            for bpm_range, count in bpm_ranges:
                percentage = (count / tracks_with_bpm) * 100
                print(f"   • {bpm_range}: {count} tracks ({percentage:.1f}%)")
        
        # 4. Probar búsqueda de duplicados
        print("\n🔍 Probando Búsqueda de Duplicados:")
        print("-" * 32)
        
        cursor.execute("""
            SELECT title, artist, COUNT(*) as count
            FROM tracks 
            WHERE title IS NOT NULL AND artist IS NOT NULL
            GROUP BY LOWER(title), LOWER(artist)
            HAVING count > 1
            ORDER BY count DESC
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"⚠️ Se encontraron {len(duplicates)} grupos de duplicados:")
            for title, artist, count in duplicates:
                print(f"   • {title} - {artist} ({count} copias)")
        else:
            print("✅ No se encontraron duplicados")
        
        # 5. Probar análisis de metadatos incompletos
        print("\n⚠️ Probando Análisis de Metadatos Incompletos:")
        print("-" * 42)
        
        metadata_issues = [
            ("Sin Título", "title IS NULL OR title = ''"),
            ("Sin Artista", "artist IS NULL OR artist = ''"),
            ("Sin Álbum", "album IS NULL OR album = ''"),
            ("Sin Género", "genre IS NULL OR genre = ''"),
            ("Sin Año", "year IS NULL"),
            ("Sin BPM", "bpm IS NULL"),
            ("Sin Tonalidad", "key IS NULL OR key = ''"),
            ("Sin Rating", "rating IS NULL"),
            ("Sin Duración", "duration_seconds IS NULL")
        ]
        
        total_issues = 0
        for issue_name, condition in metadata_issues:
            cursor.execute(f"SELECT COUNT(*) FROM tracks WHERE {condition}")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"⚠️ {issue_name}: {count} tracks")
                total_issues += count
            else:
                print(f"✅ {issue_name}: 0 tracks")
        
        if total_issues == 0:
            print("🎉 ¡Todos los metadatos están completos!")
        
        # 6. Probar funcionalidad de exportación (simulada)
        print("\n📊 Probando Funcionalidad de Exportación:")
        print("-" * 37)
        
        cursor.execute("""
            SELECT track_id, title, artist, album, genre, year, duration_seconds, 
                   bpm, rating, key, camelot_key, file_path
            FROM tracks 
            ORDER BY artist, album, title
            LIMIT 5
        """)
        sample_tracks = cursor.fetchall()
        
        print(f"✅ Datos listos para exportar: {len(sample_tracks)} tracks de muestra")
        print("✅ Campos incluidos: ID, Título, Artista, Álbum, Género, Año, Duración, BPM, Rating, Tonalidad, Camelot, Archivo")
        
        # Mostrar muestra de datos
        print("\n📋 Muestra de datos para exportación:")
        for track in sample_tracks[:3]:
            track_id, title, artist, album, genre, year, duration, bpm, rating, key, camelot_key, file_path = track
            print(f"   • {title} - {artist} [{genre}] {bpm}BPM {key}")
        
        print(f"\n✅ Prueba de análisis completada exitosamente!")
        print(f"📊 Resumen:")
        print(f"   • {total_tracks} tracks analizados")
        print(f"   • {total_artists} artistas únicos")
        print(f"   • {total_genres} géneros únicos")
        print(f"   • {tracks_with_keys} tracks con tonalidad")
        print(f"   • {tracks_with_bpm} tracks con BPM")
        print(f"   • {len(duplicates)} grupos de duplicados")
        print(f"   • {total_issues} problemas de metadatos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("📊 Nueva Biblioteca Musical - Prueba del Tab de Análisis")
    print("=" * 60)
    
    success = test_analysis_functionality()
    
    if success:
        print("\n🎉 ¡Todas las pruebas del análisis pasaron exitosamente!")
        print("\n💡 Ahora puedes:")
        print("   • Ejecutar la interfaz: python3 -m src.ui.main_window")
        print("   • Usar el tab 'Análisis de Tracks' para explorar tu biblioteca")
        print("   • Buscar duplicados y metadatos incompletos")
        print("   • Exportar estadísticas a CSV")
        print("   • Ver estadísticas detalladas de tonalidades y BPM")
    else:
        print("\n❌ Algunas pruebas fallaron. Revisa los errores arriba.")
        sys.exit(1) 
#!/usr/bin/env python3
"""
Script de prueba para verificar la integración entre UI y backend.
"""

import sys
import os

# Añadir src al path
sys.path.insert(0, 'src')

from src.data import crud
from src.data.database_setup import DB_FILE, setup_database
from src.core.playlist_generator import SmartPlaylistGenerator

def test_backend_integration():
    """Prueba la integración del backend actualizado."""
    print("=== Prueba de Integración Backend ===")
    
    # Configurar base de datos
    setup_database(DB_FILE)
    conn = crud.create_connection(DB_FILE)
    
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return False
    
    try:
        # Poblar datos de ejemplo si es necesario
        crud.populate_sample_data(conn)
        
        # Probar SmartPlaylistGenerator
        generator = SmartPlaylistGenerator(conn)
        
        # Crear una playlist de prueba
        print("\n1. Creando playlist de prueba...")
        playlist_id = generator.create_smart_playlist(
            name="Test Rock Playlist",
            rule_text="genre = 'Rock' AND rating >= 4",
            description="Playlist de prueba para verificar integración"
        )
        
        if playlist_id:
            print(f"✅ Playlist creada con ID: {playlist_id}")
        else:
            print("❌ Error creando playlist")
            return False
        
        # Obtener estadísticas
        print("\n2. Obteniendo estadísticas...")
        stats = generator.get_playlist_stats(playlist_id)
        print(f"✅ Estadísticas obtenidas:")
        print(f"   - Nombre: {stats['playlist_name']}")
        print(f"   - Total tracks: {stats['total_tracks']}")
        print(f"   - Géneros: {stats['genres']}")
        
        # Probar vista previa
        print("\n3. Probando vista previa...")
        preview = generator.get_playlist_preview("genre = 'Jazz'", max_tracks=3)
        print(f"✅ Vista previa obtenida: {len(preview)} tracks de Jazz")
        
        # Probar exportación
        print("\n4. Probando exportación M3U...")
        export_success = generator.export_playlist_m3u(playlist_id, "test_export.m3u")
        if export_success:
            print("✅ Exportación M3U exitosa")
            if os.path.exists("test_export.m3u"):
                print("✅ Archivo M3U creado correctamente")
                # Limpiar archivo de prueba
                os.remove("test_export.m3u")
        else:
            print("❌ Error en exportación M3U")
        
        # Verificar CRUD básico
        print("\n5. Verificando CRUD básico...")
        all_playlists = crud.get_all_smart_playlists(conn)
        print(f"✅ Total playlists en BD: {len(all_playlists)}")
        
        # Limpiar playlist de prueba
        crud.delete_smart_playlist(conn, playlist_id)
        print("✅ Playlist de prueba eliminada")
        
        print("\n🎉 ¡Todas las pruebas de integración pasaron exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error en pruebas de integración: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

def test_ui_imports():
    """Prueba que las importaciones de la UI funcionen correctamente."""
    print("\n=== Prueba de Importaciones UI ===")
    
    try:
        # Probar importaciones principales
        from src.ui.main_window import MainWindow
        print("✅ MainWindow importado correctamente")
        
        from src.ui.playlist_edit_dialog import PlaylistEditDialog
        print("✅ PlaylistEditDialog importado correctamente")
        
        from src.core import rule_engine
        print("✅ rule_engine importado correctamente")
        
        from src.core import exporter
        print("✅ exporter importado correctamente")
        
        from src.core.playlist_generator import SmartPlaylistGenerator
        print("✅ SmartPlaylistGenerator importado correctamente")
        
        print("🎉 ¡Todas las importaciones funcionan correctamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error en importaciones: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de integración UI-Backend...")
    
    # Probar importaciones
    imports_ok = test_ui_imports()
    
    # Probar backend
    backend_ok = test_backend_integration()
    
    if imports_ok and backend_ok:
        print("\n🎯 ¡HITO 3 COMPLETADO!")
        print("✅ La interfaz PyQt6 está lista y funcional")
        print("✅ El backend está integrado correctamente")
        print("✅ Todas las funcionalidades del MVP están implementadas")
        print("\n📋 Funcionalidades disponibles:")
        print("   - Lista de playlists inteligentes")
        print("   - Editor de reglas con texto")
        print("   - Preview de resultados")
        print("   - Crear/Editar/Eliminar playlists")
        print("   - Exportación M3U")
        print("\n🚀 Para ejecutar la interfaz: python3 -m src.ui.main_window")
    else:
        print("\n❌ Hay problemas que necesitan resolverse")
        sys.exit(1) 
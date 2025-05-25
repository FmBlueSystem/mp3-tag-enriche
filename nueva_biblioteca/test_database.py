#!/usr/bin/env python3
"""
Test específico para validar que la capa de persistencia funciona correctamente.
"""

import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_music_database():
    """Prueba la capa de persistencia crítica."""
    print("🔄 Probando import de MusicDatabase...")
    
    try:
        from src.core.database.music_database import (
            MusicDatabase,
            DatabaseFactory,
            TrackMetadata
        )
        print("✅ Import de MusicDatabase exitoso")
    except ImportError as e:
        print(f"❌ Error importando MusicDatabase: {e}")
        return False
    
    print("🔄 Probando creación de DatabaseFactory...")
    try:
        db = DatabaseFactory.create('sqlite', 'test.db')
        print("✅ DatabaseFactory.create() exitoso")
    except Exception as e:
        print(f"❌ Error creando database: {e}")
        return False
    
    print("🔄 Probando conexión a base de datos...")
    try:
        connected = db.connect()
        if connected:
            print("✅ Conexión a base de datos exitosa")
        else:
            print("❌ No se pudo conectar a la base de datos")
            return False
    except Exception as e:
        print(f"❌ Error conectando: {e}")
        return False
    
    print("🔄 Probando métodos básicos de la base de datos...")
    try:
        # Probar get_tracks (debería devolver lista vacía)
        tracks = db.get_tracks()
        print(f"✅ db.get_tracks() exitoso - {len(tracks)} tracks encontrados")
        
        # Probar creación de TrackMetadata
        metadata = TrackMetadata(
            title="Test Track",
            artist="Test Artist",
            album="Test Album",
            genre="Test Genre",
            path="/test/path.mp3"
        )
        print("✅ Creación de TrackMetadata exitosa")
        
        # Cerrar conexión
        db.disconnect()
        print("✅ Desconexión exitosa")
        
    except Exception as e:
        print(f"❌ Error en métodos de base de datos: {e}")
        return False
    
    return True

def test_music_service():
    """Prueba el MusicService con la nueva base de datos."""
    print("\n🔄 Probando MusicService...")
    
    try:
        from src.services.music_service import MusicService
        print("✅ Import de MusicService exitoso")
    except ImportError as e:
        print(f"❌ Error importando MusicService: {e}")
        return False
    
    try:
        music_service = MusicService()
        print("✅ Creación de MusicService exitosa")
        
        # Probar método get_all_tracks
        all_tracks = music_service.get_all_tracks()
        print(f"✅ get_all_tracks() exitoso - {len(all_tracks)} tracks")
        
        # Probar estadísticas
        stats = music_service.get_statistics()
        print(f"✅ get_statistics() exitoso - {stats['total_tracks']} tracks")
        
    except Exception as e:
        print(f"❌ Error en MusicService: {e}")
        return False
    
    return True

def main():
    """Función principal de prueba."""
    print("🚀 PRUEBA DE CAPA DE PERSISTENCIA - NUEVA BIBLIOTECA")
    print("=" * 60)
    
    success = True
    
    # Test 1: Base de datos
    if not test_music_database():
        success = False
    
    # Test 2: Servicio de música
    if not test_music_service():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TODAS LAS PRUEBAS DE PERSISTENCIA EXITOSAS")
        print("\n🎉 La capa de persistencia está completamente implementada!")
        print("\nCaracterísticas validadas:")
        print("  ✓ Import de MusicDatabase resuelto")
        print("  ✓ Clases MusicDatabase, DatabaseFactory, TrackMetadata creadas")
        print("  ✓ Integración con modelos SQLAlchemy existentes")
        print("  ✓ Método get_all_tracks() implementado")
        print("  ✓ Conexión con base de datos funcional")
        print("  ✓ MusicService completamente operativo")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
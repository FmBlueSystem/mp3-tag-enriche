#!/usr/bin/env python3
"""
🧪 PRUEBA DEL IMPORTADOR - NUEVA BIBLIOTECA v2.0
===============================================
Script para probar el sistema de importación de archivos musicales
"""

import sys
import os
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.importers import ImportManager, MusicFileScanner, MetadataExtractor

def test_scanner():
    """Probar el escáner de archivos."""
    print("🔍 PROBANDO ESCÁNER DE ARCHIVOS")
    print("=" * 40)
    
    scanner = MusicFileScanner()
    
    # Mostrar formatos soportados
    formats = scanner.get_supported_formats()
    print(f"📁 Formatos soportados: {formats['total_formats']}")
    print(f"   Extensiones: {', '.join(formats['extensions'][:5])}...")
    
    # Probar con directorio de música común en macOS
    test_directories = [
        os.path.expanduser("~/Music"),
        os.path.expanduser("~/Downloads"),
        "/System/Library/Sounds",  # Sonidos del sistema
        "."  # Directorio actual
    ]
    
    for directory in test_directories:
        if os.path.exists(directory):
            print(f"\n📂 Escaneando: {directory}")
            try:
                results = scanner.quick_scan(directory, max_files=5)
                print(f"   ✓ Archivos encontrados: {len(results)}")
                
                for result in results[:3]:  # Mostrar primeros 3
                    size_mb = result.file_size / (1024 * 1024)
                    print(f"   • {result.file_extension}: {Path(result.file_path).name} ({size_mb:.1f}MB)")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
            break
    else:
        print("⚠️ No se encontraron directorios de prueba")

def test_metadata_extractor():
    """Probar el extractor de metadatos."""
    print("\n🏷️ PROBANDO EXTRACTOR DE METADATOS")
    print("=" * 40)
    
    try:
        extractor = MetadataExtractor()
        print("✓ MetadataExtractor inicializado correctamente")
        
        # Buscar archivos de audio para probar
        scanner = MusicFileScanner()
        test_dirs = [
            os.path.expanduser("~/Music"),
            "/System/Library/Sounds"
        ]
        
        test_files = []
        for directory in test_dirs:
            if os.path.exists(directory):
                results = scanner.quick_scan(directory, max_files=3)
                test_files.extend([r.file_path for r in results])
                if test_files:
                    break
                    
        if test_files:
            print(f"\n📁 Probando con {len(test_files)} archivos:")
            
            for file_path in test_files[:2]:  # Probar primeros 2
                print(f"\n🎵 Archivo: {Path(file_path).name}")
                
                metadata = extractor.extract_metadata(file_path)
                if metadata:
                    print(f"   ✓ Título: {metadata.title or 'N/A'}")
                    print(f"   ✓ Artista: {metadata.artist or 'N/A'}")
                    print(f"   ✓ Duración: {metadata.duration or 'N/A'}s")
                    print(f"   ✓ Formato: {metadata.file_extension}")
                    print(f"   ✓ Tamaño: {metadata.file_size / (1024*1024):.1f}MB")
                    
                    # Validar metadatos
                    issues = extractor.validate_metadata(metadata)
                    completeness = extractor.get_metadata_completeness(metadata)
                    print(f"   📊 Completitud: {completeness['overall']:.1f}%")
                    
                else:
                    print("   ❌ No se pudieron extraer metadatos")
                    
        else:
            print("⚠️ No se encontraron archivos de audio para probar")
            
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("💡 Instala mutagen: pip install mutagen")

def test_import_manager():
    """Probar el gestor de importación."""
    print("\n📥 PROBANDO GESTOR DE IMPORTACIÓN")
    print("=" * 40)
    
    try:
        manager = ImportManager(max_workers=2)
        print("✓ ImportManager inicializado correctamente")
        
        # Callback de progreso
        def progress_callback(progress):
            print(f"   📊 {progress.phase}: {progress.files_processed}/{progress.total_files} - {progress.current_operation}")
            
        manager.set_progress_callback(progress_callback)
        
        # Probar validación de directorio
        test_dirs = [
            os.path.expanduser("~/Music"),
            "/System/Library/Sounds",
            "/tmp"  # Directorio que probablemente existe pero sin música
        ]
        
        for directory in test_dirs:
            if os.path.exists(directory):
                print(f"\n📂 Validando directorio: {directory}")
                validation = manager.validate_directory(directory)
                
                print(f"   ✓ Existe: {validation['exists']}")
                print(f"   ✓ Legible: {validation['readable']}")
                print(f"   ✓ Tiene audio: {validation['has_audio_files']}")
                print(f"   📊 Archivos estimados: {validation['estimated_files']}")
                
                if validation['errors']:
                    for error in validation['errors']:
                        print(f"   ❌ {error}")
                        
                # Si tiene archivos de audio, hacer preview
                if validation['has_audio_files']:
                    print(f"\n🔍 Vista previa de {directory}:")
                    preview = manager.quick_preview(directory, max_files=3)
                    
                    for track in preview:
                        print(f"   🎵 {track.file_name}")
                        print(f"      Artista: {track.artist or 'Desconocido'}")
                        print(f"      Título: {track.title or 'Sin título'}")
                        
                break
                
        print("\n📈 Estadísticas del importador:")
        stats = manager.get_import_statistics()
        print(f"   📁 Formatos soportados: {stats['supported_formats']['total_formats']}")
        print(f"   🔧 Workers configurados: {manager.max_workers}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal de prueba."""
    print("🧪 PRUEBA DEL SISTEMA DE IMPORTACIÓN - NUEVA BIBLIOTECA v2.0")
    print("=" * 60)
    
    try:
        # Probar componentes individuales
        test_scanner()
        test_metadata_extractor()
        test_import_manager()
        
        print("\n" + "=" * 60)
        print("🎉 PRUEBAS COMPLETADAS")
        print("\n✅ COMPONENTES PROBADOS:")
        print("   • MusicFileScanner - Escaneo de archivos")
        print("   • MetadataExtractor - Extracción de metadatos")
        print("   • ImportManager - Gestión de importación")
        
        print("\n🚀 PRÓXIMOS PASOS:")
        print("   1. Integrar con la UI existente")
        print("   2. Crear diálogo de importación")
        print("   3. Conectar con base de datos")
        print("   4. Implementar reproductor de audio")
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
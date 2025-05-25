"""
Demostración de integración de todos los componentes implementados.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List

# Configurar path para imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.data.models import create_tables, drop_tables
from src.importers import ImportManager, ImportProgress, ImportResult
from src.metadata.extractor import MetadataExtractor
from src.audio.player import AudioPlayer, Track
from src.data.repositories import TrackRepository
from src.data.models import get_db

def setup_logging():
    """Configura el logging para la demostración."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('integration_demo.log')
        ]
    )

def create_sample_database():
    """Crea una base de datos de ejemplo."""
    print("🗄️  Creando base de datos...")
    
    # Recrear tablas
    drop_tables()
    create_tables()
    
    print("✅ Base de datos creada correctamente")

def demo_metadata_extraction():
    """Demuestra la extracción de metadatos."""
    print("\n🔍 Demostración de Extracción de Metadatos")
    print("=" * 50)
    
    extractor = MetadataExtractor()
    
    # Buscar archivos de ejemplo en el directorio de tests
    test_files_dir = Path(__file__).parent.parent.parent / "tests" / "resources"
    
    if test_files_dir.exists():
        music_files = list(test_files_dir.glob("*.mp3"))
        
        if music_files:
            for music_file in music_files[:3]:  # Solo los primeros 3
                print(f"\n📁 Analizando: {music_file.name}")
                
                metadata = extractor.extract_metadata(music_file)
                
                if metadata.extraction_success:
                    print(f"  🎵 Título: {metadata.title}")
                    print(f"  👤 Artista: {metadata.artist}")
                    print(f"  💿 Álbum: {metadata.album}")
                    print(f"  ⏱️  Duración: {metadata.duration_formatted if metadata.duration else 'N/A'}")
                    print(f"  🎼 Género: {metadata.genre or 'N/A'}")
                    print(f"  📅 Año: {metadata.year or 'N/A'}")
                    print(f"  🎚️  Bitrate: {metadata.bitrate or 'N/A'} kbps")
                else:
                    print(f"  ❌ Error extrayendo metadatos: {metadata.extraction_errors}")
        else:
            print("  ⚠️  No se encontraron archivos MP3 en el directorio de tests")
    else:
        print("  ⚠️  Directorio de tests no encontrado")
        
        # Crear un ejemplo sintético
        print("  📝 Creando ejemplo sintético...")
        from src.metadata.extractor import TrackMetadata
        from datetime import datetime
        
        sample_metadata = TrackMetadata(
            file_path="/ejemplo/cancion.mp3",
            file_size=5242880,
            file_format="mp3",
            last_modified=datetime.now(),
            title="Canción de Ejemplo",
            artist="Artista de Ejemplo",
            album="Álbum de Ejemplo",
            duration=210.5,
            bitrate=320,
            genre="Rock",
            year=2024
        )
        
        print(f"  🎵 Título: {sample_metadata.title}")
        print(f"  👤 Artista: {sample_metadata.artist}")
        print(f"  💿 Álbum: {sample_metadata.album}")
        print(f"  ⏱️  Duración: {sample_metadata.duration_formatted}")

def demo_import_system():
    """Demuestra el sistema de importación."""
    print("\n📥 Demostración del Sistema de Importación")
    print("=" * 50)
    
    import_manager = ImportManager(max_workers=2)
    
    # Callbacks de ejemplo
    def on_progress(progress: ImportProgress):
        if progress.total_files > 0:
            percentage = (progress.processed_files / progress.total_files) * 100
            print(f"  📊 Progreso: {progress.processed_files}/{progress.total_files} ({percentage:.1f}%)")
            if progress.current_file:
                print(f"  📄 Archivo actual: {Path(progress.current_file).name}")
    
    def on_completion(result: ImportResult):
        print(f"\n✅ Importación completada:")
        print(f"  📊 Total procesado: {result.total_processed}")
        print(f"  ✅ Exitosos: {result.successful_imports}")
        print(f"  ❌ Fallidos: {result.failed_imports}")
        print(f"  🔄 Duplicados: {result.duplicate_files}")
        print(f"  ⏱️  Duración: {result.duration_seconds:.2f}s")
        
        if result.errors:
            print(f"  ⚠️  Errores: {len(result.errors)}")
    
    def on_error(error: str):
        print(f"  ❌ Error: {error}")
    
    # Registrar callbacks
    import_manager.add_progress_callback(on_progress)
    import_manager.add_completion_callback(on_completion)
    import_manager.add_error_callback(on_error)
    
    # Buscar directorio de música del usuario
    music_dirs = [
        Path.home() / "Music",
        Path.home() / "Música",
        Path(__file__).parent.parent.parent / "tests" / "resources"
    ]
    
    target_dir = None
    for music_dir in music_dirs:
        if music_dir.exists():
            music_files = list(music_dir.glob("*.mp3"))
            if music_files:
                target_dir = music_dir
                break
    
    if target_dir:
        print(f"  📁 Importando desde: {target_dir}")
        
        try:
            result = import_manager.import_directory(
                str(target_dir),
                recursive=False,  # Solo nivel superior para demo
                check_duplicates=True,
                extract_metadata=True
            )
        except Exception as e:
            print(f"  ❌ Error durante importación: {e}")
    else:
        print("  ⚠️  No se encontró directorio con archivos musicales")
        print("  💡 Tip: Coloque algunos archivos MP3 en ~/Music para probar la importación")

def demo_database_queries():
    """Demuestra las consultas a la base de datos."""
    print("\n🔍 Demostración de Consultas a Base de Datos")
    print("=" * 50)
    
    try:
        with next(get_db()) as db:
            track_repo = TrackRepository(db)
            
            # Estadísticas generales
            stats = track_repo.get_statistics()
            print(f"  📊 Estadísticas de la biblioteca:")
            print(f"    🎵 Total de tracks: {stats['total_tracks']}")
            print(f"    ⏱️  Duración total: {stats['total_duration_formatted']}")
            print(f"    🔄 Total reproducciones: {stats['total_plays']}")
            print(f"    ⭐ Favoritos: {stats['favorites_count']}")
            
            if stats['most_common_format']:
                print(f"    📁 Formato más común: {stats['most_common_format']}")
            
            # Tracks recientes
            recent_tracks = track_repo.get_recent_tracks(days=30, limit=5)
            if recent_tracks:
                print(f"\n  📅 Tracks agregados recientemente:")
                for track in recent_tracks:
                    artist_name = track.primary_artist.name if track.primary_artist else "Artista desconocido"
                    print(f"    🎵 {track.title} - {artist_name}")
            
            # Búsqueda de ejemplo
            if stats['total_tracks'] > 0:
                print(f"\n  🔍 Búsqueda de ejemplo (primeros 3 resultados):")
                all_tracks = track_repo.get_all(limit=3)
                for track in all_tracks:
                    artist_name = track.primary_artist.name if track.primary_artist else "Artista desconocido"
                    duration = track.duration_formatted if track.duration else "0:00"
                    print(f"    🎵 {track.title} - {artist_name} ({duration})")
            
    except Exception as e:
        print(f"  ❌ Error accediendo a la base de datos: {e}")

def demo_audio_player():
    """Demuestra el reproductor de audio."""
    print("\n🎮 Demostración del Reproductor de Audio")
    print("=" * 50)
    
    try:
        # Crear reproductor
        player = AudioPlayer()
        
        # Verificar si pygame está disponible
        if hasattr(player, '_status'):
            print("  ✅ Reproductor inicializado correctamente")
            
            # Buscar archivos para reproducir
            test_files_dir = Path(__file__).parent.parent.parent / "tests" / "resources"
            music_files = []
            
            if test_files_dir.exists():
                music_files = list(test_files_dir.glob("*.mp3"))
            
            if not music_files:
                # Buscar en directorio de música del usuario
                music_dirs = [Path.home() / "Music", Path.home() / "Música"]
                for music_dir in music_dirs:
                    if music_dir.exists():
                        music_files = list(music_dir.glob("*.mp3"))[:3]  # Solo 3 archivos
                        if music_files:
                            break
            
            if music_files:
                print(f"  📁 Encontrados {len(music_files)} archivos para demo")
                
                # Crear tracks para el reproductor
                demo_tracks = []
                for i, file_path in enumerate(music_files):
                    track = Track(
                        id=i + 1,
                        file_path=str(file_path),
                        title=file_path.stem,
                        artist="Artista Demo",
                        duration=180.0  # 3 minutos por defecto
                    )
                    demo_tracks.append(track)
                
                # Configurar playlist
                player.set_playlist(demo_tracks)
                print(f"  📝 Playlist configurada con {len(demo_tracks)} tracks")
                
                # Demostrar funcionalidades básicas
                print(f"  🎵 Track actual: {player.current_track.title if player.current_track else 'Ninguno'}")
                print(f"  📊 Estado: {player.status.state.value}")
                print(f"  🔊 Volumen: {player.status.volume:.1f}")
                
                # Nota sobre reproducción
                print(f"\n  💡 Para reproducir realmente:")
                print(f"    player.play()          # Reproducir")
                print(f"    player.pause()         # Pausar")
                print(f"    player.stop()          # Detener")
                print(f"    player.next_track()    # Siguiente")
                print(f"    player.previous_track() # Anterior")
                
            else:
                print("  ⚠️  No se encontraron archivos MP3 para la demostración")
                print("  💡 Coloque archivos MP3 en tests/resources/ o ~/Music/")
            
            # Limpiar recursos
            player.cleanup()
            print("  🧹 Recursos del reproductor limpiados")
            
        else:
            print("  ❌ Error inicializando el reproductor")
            
    except Exception as e:
        print(f"  ❌ Error con el reproductor: {e}")

def demo_integration_workflow():
    """Demuestra un flujo de trabajo completo de integración."""
    print("\n🔄 Flujo de Trabajo Completo")
    print("=" * 50)
    
    print("  Este flujo demuestra cómo todos los componentes trabajan juntos:")
    print("  1. 🗄️  Configurar base de datos")
    print("  2. 📥 Importar archivos musicales")
    print("  3. 🔍 Extraer y almacenar metadatos")
    print("  4. 🎮 Configurar reproductor")
    print("  5. 📊 Consultar biblioteca")
    
    print("\n  💡 Para una demostración completa en una aplicación real:")
    print("    - Use el ImportWizard para importación con UI")
    print("    - Integre el AudioPlayer en la interfaz principal")
    print("    - Use TrackRepository para todas las consultas")
    print("    - Implemente callbacks para actualizar la UI en tiempo real")

def main():
    """Función principal de la demostración."""
    print("🚀 Nueva Biblioteca - Demostración de Integración")
    print("=" * 60)
    print("Esta demostración muestra los componentes implementados:")
    print("• Sistema de base de datos con modelos SQLAlchemy")
    print("• Importador de archivos musicales con progreso")
    print("• Extractor de metadatos con soporte multi-formato")
    print("• Reproductor de audio básico")
    print("• Repositorios para consultas optimizadas")
    print("=" * 60)
    
    # Configurar logging
    setup_logging()
    
    try:
        # 1. Configurar base de datos
        create_sample_database()
        
        # 2. Demostrar extracción de metadatos
        demo_metadata_extraction()
        
        # 3. Demostrar sistema de importación
        demo_import_system()
        
        # 4. Demostrar consultas a base de datos
        demo_database_queries()
        
        # 5. Demostrar reproductor de audio
        demo_audio_player()
        
        # 6. Mostrar flujo de trabajo completo
        demo_integration_workflow()
        
        print("\n" + "=" * 60)
        print("✅ Demostración completada exitosamente")
        print("📝 Los logs detallados están en 'integration_demo.log'")
        print("🎯 ¡El sistema está listo para trabajar con bibliotecas musicales reales!")
        
    except Exception as e:
        print(f"\n❌ Error durante la demostración: {e}")
        logging.exception("Error en demostración")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
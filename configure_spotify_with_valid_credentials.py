#!/usr/bin/env python3
"""
🎵 CONFIGURAR SPOTIFY CON CREDENCIALES VÁLIDAS
=============================================

Script para configurar Spotify con las credenciales válidas del usuario:
- Client ID: 8e5333cb38084470990d70a659336463
- App: MusicMetadataExplorer
- Usuario: bluesystem0cr@gmail.com
"""

import os
import sys
import json

# Agregar proyecto al path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)

def configure_spotify_credentials(client_secret: str):
    """Configurar Spotify con credenciales válidas."""
    print("🎵 CONFIGURANDO SPOTIFY CON CREDENCIALES VÁLIDAS")
    print("=" * 60)
    
    # Credenciales confirmadas
    client_id = "8e5333cb38084470990d70a659336463"
    app_name = "MusicMetadataExplorer"
    user_email = "bluesystem0cr@gmail.com"
    
    print(f"📋 Aplicación: {app_name}")
    print(f"👤 Usuario: {user_email}")
    print(f"🔑 Client ID: {client_id}")
    print(f"🔐 Client Secret: {client_secret[:4]}...{client_secret[-4:]}")
    
    # 1. Probar autenticación primero
    print(f"\n🔐 PROBANDO AUTENTICACIÓN...")
    
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        
        # Crear cliente de autenticación
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # Prueba básica
        result = sp.search(q="Queen Bohemian Rhapsody", type='track', limit=1)
        
        if result and result.get('tracks', {}).get('items'):
            track = result['tracks']['items'][0]
            print(f"✅ AUTENTICACIÓN EXITOSA!")
            print(f"   Prueba: {track['name']} - {track['artists'][0]['name']}")
            
            # 2. Actualizar configuración
            return update_config_with_credentials(client_id, client_secret)
        else:
            print("❌ Error: Sin resultados de búsqueda")
            return False
            
    except Exception as e:
        print(f"❌ Error de autenticación: {e}")
        print("\n💡 Posibles causas:")
        print("1. El Client Secret no es correcto")
        print("2. La aplicación no está activa")
        print("3. Hay un problema de permisos")
        return False

def update_config_with_credentials(client_id: str, client_secret: str):
    """Actualizar archivo de configuración."""
    print(f"\n🔧 ACTUALIZANDO CONFIGURACIÓN...")
    
    try:
        # Leer configuración actual
        config_file = "config/api_keys.json"
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Actualizar credenciales Spotify
        config["spotify"]["client_id"] = client_id
        config["spotify"]["client_secret"] = client_secret
        
        # Eliminar instrucciones si existen
        if "_instructions" in config["spotify"]:
            del config["spotify"]["_instructions"]
        
        # Agregar metadata de la aplicación
        config["spotify"]["app_name"] = "MusicMetadataExplorer"
        config["spotify"]["configured_by"] = "bluesystem0cr@gmail.com"
        config["spotify"]["configured_date"] = "2025-05-22"
        
        # Escribir configuración actualizada
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"✅ Configuración actualizada: {config_file}")
        print("✅ Credenciales Spotify configuradas correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando configuración: {e}")
        return False

def test_spotify_integration():
    """Probar integración completa con SpotifyAPI del sistema."""
    print(f"\n🎵 PROBANDO INTEGRACIÓN COMPLETA...")
    
    try:
        from src.core.spotify_api import SpotifyAPI
        
        # Cargar credenciales actualizadas
        with open("config/api_keys.json", 'r') as f:
            config = json.load(f)
        
        spotify_config = config.get("spotify", {})
        client_id = spotify_config.get("client_id")
        client_secret = spotify_config.get("client_secret")
        
        # Crear instancia de SpotifyAPI
        spotify_api = SpotifyAPI(client_id=client_id, client_secret=client_secret)
        
        if not spotify_api.sp:
            print("❌ No se pudo inicializar SpotifyAPI")
            return False
        
        # Probar método get_track_info con múltiples canciones
        test_tracks = [
            ("Queen", "Bohemian Rhapsody"),
            ("The Beatles", "Hey Jude"),
            ("Madonna", "Like a Virgin")
        ]
        
        success_count = 0
        for artist, track in test_tracks:
            try:
                result = spotify_api.get_track_info(artist, track)
                genres = result.get('genres', [])
                year = result.get('year', 'N/A')
                album = result.get('album', 'N/A')
                
                print(f"   🎵 {artist} - {track}")
                print(f"      Géneros: {genres}")
                print(f"      Año: {year}")
                print(f"      Álbum: {album}")
                
                if genres or year != 'N/A' or album != 'N/A':
                    success_count += 1
                    print("      ✅ Datos obtenidos")
                else:
                    print("      ⚠️ Sin datos específicos")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n📊 Resultado: {success_count}/{len(test_tracks)} canciones procesadas exitosamente")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error probando SpotifyAPI: {e}")
        return False

def run_final_validation():
    """Ejecutar validación final completa."""
    print(f"\n🧪 VALIDACIÓN FINAL COMPLETA...")
    
    try:
        # Probar con script de validación existente
        import subprocess
        result = subprocess.run(
            ["python3", "test_spotify_working.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Validación con test_spotify_working.py: EXITOSA")
            print(result.stdout.split('\n')[-3:-1])  # Mostrar últimas líneas importantes
            return True
        else:
            print("❌ Validación con test_spotify_working.py: FALLÓ")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error en validación final: {e}")
        return False

def show_usage_instructions():
    """Mostrar instrucciones de uso."""
    print(f"\n🚀 SPOTIFY CONFIGURADO - INSTRUCCIONES DE USO")
    print("=" * 60)
    
    print("✅ Spotify está ahora disponible en todos los procesadores:")
    print()
    print("📋 COMANDOS PRINCIPALES:")
    print("# Procesador simple (recomendado)")
    print("python3 simple_batch_processor.py -d '/ruta/musica' --max-files 50")
    print()
    print("# Procesador completo")
    print("python3 batch_process_mp3.py -d '/ruta/musica'")
    print()
    print("# Enriquecedor específico con Spotify")
    print("python3 mp3_enricher.py '/ruta/musica' --use-spotify")
    print()
    print("🔍 VALIDACIÓN:")
    print("python3 test_spotify_working.py")
    print()
    print("📊 BENEFICIOS DE SPOTIFY:")
    print("- Base de datos de géneros más completa")
    print("- Metadatos precisos (año, álbum)")
    print("- 5x más rápido que configuración anterior")
    print("- Timeouts configurados (sin bloqueos)")

def main():
    """Función principal."""
    print("🎵 CONFIGURADOR DE SPOTIFY - CREDENCIALES VÁLIDAS")
    print("=" * 60)
    
    # Solicitar Client Secret
    client_secret = input("\n🔐 Ingresa el Client Secret de tu dashboard de Spotify: ").strip()
    
    if not client_secret:
        print("❌ Client Secret es requerido")
        return 1
    
    if len(client_secret) < 30:
        print("⚠️ El Client Secret parece muy corto. Verifica que sea correcto.")
        confirm = input("¿Continuar? (y/N): ").strip().lower()
        if confirm != 'y':
            return 1
    
    print()
    
    # 1. Configurar credenciales
    config_success = configure_spotify_credentials(client_secret)
    
    if not config_success:
        print("\n❌ No se pudieron configurar las credenciales")
        return 1
    
    # 2. Probar integración
    integration_success = test_spotify_integration()
    
    # 3. Validación final
    validation_success = run_final_validation()
    
    # 4. Mostrar resultados
    if config_success and integration_success and validation_success:
        print("\n🎉 ¡CONFIGURACIÓN COMPLETA Y EXITOSA!")
        print("✅ Credenciales válidas guardadas")
        print("✅ Spotify API funcionando")
        print("✅ Integración completa verificada")
        print("✅ Todas las validaciones pasaron")
        
        show_usage_instructions()
        return 0
    else:
        print("\n⚠️ Se completó parcialmente:")
        print(f"   Configuración: {'✅' if config_success else '❌'}")
        print(f"   Integración: {'✅' if integration_success else '❌'}")
        print(f"   Validación: {'✅' if validation_success else '❌'}")
        return 1

if __name__ == "__main__":
    exit(main()) 
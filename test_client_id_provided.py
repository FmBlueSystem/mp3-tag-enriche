#!/usr/bin/env python3
"""
🧪 PROBAR CLIENT ID PROPORCIONADO POR USUARIO
=============================================

Script para probar el Client ID: 8e5333cb38084470990d70a659336463
con el Client Secret correspondiente.
"""

import os
import sys
import json

# Agregar proyecto al path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)

def test_provided_credentials():
    """Probar las credenciales proporcionadas por el usuario."""
    print("🧪 PROBANDO CLIENT ID PROPORCIONADO")
    print("=" * 50)
    
    # Client ID proporcionado por el usuario
    provided_client_id = "8e5333cb38084470990d70a659336463"
    
    # Intentar obtener el Client Secret de diferentes fuentes
    client_secret = None
    
    # 1. Desde backup de configuración
    try:
        with open("config/api_keys.json.backup", 'r') as f:
            config = json.load(f)
            backup_secret = config.get("spotify", {}).get("client_secret")
            if backup_secret and backup_secret != "TU_CLIENT_SECRET_AQUI":
                client_secret = backup_secret
                print(f"✅ Client Secret encontrado en backup: {client_secret[:4]}...{client_secret[-4:]}")
    except Exception:
        pass
    
    # 2. Si no hay backup válido, necesitamos que el usuario proporcione el secret
    if not client_secret:
        print("❌ No se encontró Client Secret válido")
        print(f"📋 Client ID proporcionado: {provided_client_id}")
        print("⚠️ Para completar la prueba, necesito también el Client Secret")
        print()
        print("💡 Opciones:")
        print("1. Proporciona el Client Secret correspondiente a este Client ID")
        print("2. Ve a https://developer.spotify.com/dashboard/ para obtenerlo")
        print("3. Si ya tienes el secret, edita config/api_keys.json")
        return False
    
    # 3. Probar autenticación con credenciales completas
    print(f"\n🔐 PROBANDO CREDENCIALES:")
    print(f"   Client ID: {provided_client_id}")
    print(f"   Client Secret: {client_secret[:4]}...{client_secret[-4:]}")
    
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        
        # Crear cliente de autenticación
        auth_manager = SpotifyClientCredentials(
            client_id=provided_client_id,
            client_secret=client_secret
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # Prueba básica de búsqueda
        result = sp.search(q="Queen Bohemian Rhapsody", type='track', limit=1)
        
        if result and result.get('tracks', {}).get('items'):
            track = result['tracks']['items'][0]
            print(f"✅ AUTENTICACIÓN EXITOSA!")
            print(f"   Prueba: {track['name']} - {track['artists'][0]['name']}")
            
            # Actualizar configuración con credenciales válidas
            update_config_with_valid_credentials(provided_client_id, client_secret)
            
            return True
        else:
            print("⚠️ Autenticación OK pero sin resultados")
            return False
            
    except Exception as e:
        print(f"❌ Error de autenticación: {e}")
        return False

def update_config_with_valid_credentials(client_id: str, client_secret: str):
    """Actualizar configuración con credenciales válidas."""
    print(f"\n🔧 ACTUALIZANDO CONFIGURACIÓN...")
    
    try:
        # Leer configuración actual
        with open("config/api_keys.json", 'r') as f:
            config = json.load(f)
        
        # Actualizar credenciales Spotify
        config["spotify"]["client_id"] = client_id
        config["spotify"]["client_secret"] = client_secret
        
        # Eliminar instrucciones si existen
        if "_instructions" in config["spotify"]:
            del config["spotify"]["_instructions"]
        
        # Escribir configuración actualizada
        with open("config/api_keys.json", 'w') as f:
            json.dump(config, f, indent=4)
        
        print("✅ Configuración actualizada con credenciales válidas")
        print("✅ Spotify API ahora debería funcionar correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando configuración: {e}")
        return False

def test_spotify_integration_with_new_credentials():
    """Probar integración completa con nuevas credenciales."""
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
        
        # Probar método get_track_info
        result = spotify_api.get_track_info("Queen", "Bohemian Rhapsody")
        
        print("✅ SpotifyAPI funcionando correctamente:")
        print(f"   Géneros: {result.get('genres', [])}")
        print(f"   Año: {result.get('year', 'N/A')}")
        print(f"   Álbum: {result.get('album', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando SpotifyAPI: {e}")
        return False

def main():
    """Función principal."""
    print("🧪 VALIDACIÓN DE CLIENT ID PROPORCIONADO POR USUARIO")
    print("=" * 60)
    print()
    
    # 1. Probar credenciales proporcionadas
    auth_success = test_provided_credentials()
    
    if not auth_success:
        print("\n⚠️ No se pudieron validar las credenciales")
        print("📋 Para continuar, proporciona el Client Secret correspondiente")
        return 1
    
    # 2. Probar integración completa
    integration_success = test_spotify_integration_with_new_credentials()
    
    if auth_success and integration_success:
        print("\n🎉 ¡ÉXITO COMPLETO!")
        print("✅ Credenciales válidas configuradas")
        print("✅ Spotify API funcionando")
        print("✅ Integración completa verificada")
        print("\n🚀 Spotify está ahora 100% funcional en el sistema!")
        return 0
    else:
        print("\n⚠️ Se encontraron algunos problemas")
        return 1

if __name__ == "__main__":
    exit(main()) 
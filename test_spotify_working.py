#!/usr/bin/env python3
"""
🎵 VALIDADOR DE SPOTIFY - PRUEBA RÁPIDA
======================================

Script simple para validar que Spotify funciona correctamente.
"""

import os
import sys
import json

# Agregar proyecto al path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)

def test_spotify():
    """Probar Spotify con credenciales actuales."""
    print("🎵 PROBANDO SPOTIFY API")
    print("=" * 30)
    
    try:
        # Cargar credenciales
        with open("config/api_keys.json", 'r') as f:
            config = json.load(f)
        
        spotify_config = config.get("spotify", {})
        client_id = spotify_config.get("client_id")
        client_secret = spotify_config.get("client_secret")
        
        if client_id == "TU_CLIENT_ID_AQUI" or client_secret == "TU_CLIENT_SECRET_AQUI":
            print("❌ Credenciales no configuradas")
            print("📋 Edita config/api_keys.json con credenciales válidas")
            return False
        
        # Probar autenticación directa
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # Prueba simple
        result = sp.search(q="Queen", type='track', limit=1)
        
        if result and result.get('tracks', {}).get('items'):
            track = result['tracks']['items'][0]
            print(f"✅ Spotify funcionando: {track['name']} - {track['artists'][0]['name']}")
            
            # Probar con SpotifyAPI del sistema
            try:
                from src.core.spotify_api import SpotifyAPI
                spotify_api = SpotifyAPI(client_id=client_id, client_secret=client_secret)
                
                info = spotify_api.get_track_info("Queen", "Bohemian Rhapsody")
                print(f"✅ SpotifyAPI funcionando: {len(info.get('genres', []))} géneros obtenidos")
                
                return True
            except Exception as e:
                print(f"⚠️ SpotifyAPI error: {e}")
                return False
        else:
            print("❌ Sin resultados de búsqueda")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if test_spotify():
        print("\n🎉 ¡Spotify configurado correctamente!")
        exit(0)
    else:
        print("\n⚠️ Spotify requiere configuración")
        exit(1)

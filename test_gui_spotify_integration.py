#!/usr/bin/env python3
"""
Test script to verify Spotify integration in the GUI system.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gui.models.genre_model import GenreModel
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_spotify_in_gui():
    """Test if Spotify is working in the GUI model."""
    print("🧪 Probando integración de Spotify en la GUI...")
    
    # Create a temporary backup directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize GenreModel (this is what the GUI uses)
        model = GenreModel(backup_dir=temp_dir)
        
        # Check which APIs are loaded
        apis = model.detector.apis
        api_names = [api.__class__.__name__ for api in apis]
        
        print(f"✅ APIs cargadas en GUI: {api_names}")
        
        # Check if Spotify is included
        spotify_found = any('Spotify' in name for name in api_names)
        
        if spotify_found:
            print("🎵 ¡Spotify está integrado en la GUI!")
            
            # Test a quick search
            try:
                print("🔍 Probando búsqueda rápida con Spotify...")
                
                # Find Spotify API instance
                spotify_api = None
                for api in apis:
                    if 'Spotify' in api.__class__.__name__:
                        spotify_api = api
                        break
                
                if spotify_api:
                    # Test search
                    result = spotify_api.get_track_info("Queen", "Bohemian Rhapsody")
                    if result and result.get('genres'):
                        print(f"🎯 Géneros encontrados: {result['genres']}")
                        print("✅ ¡Spotify funciona perfectamente en la GUI!")
                        return True
                    else:
                        print("⚠️ Spotify está integrado pero no devolvió géneros")
                        return False
                else:
                    print("❌ No se pudo encontrar instancia de Spotify API")
                    return False
                    
            except Exception as e:
                print(f"❌ Error probando Spotify: {e}")
                return False
        else:
            print("❌ Spotify NO está integrado en la GUI")
            return False

if __name__ == "__main__":
    success = test_spotify_in_gui()
    print(f"\n{'='*50}")
    if success:
        print("🎉 RESULTADO: Spotify está completamente integrado y funcionando en la GUI")
    else:
        print("😞 RESULTADO: Hay problemas con la integración de Spotify en la GUI")
    print(f"{'='*50}") 
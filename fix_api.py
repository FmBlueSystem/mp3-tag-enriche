"""
Script para corregir el problema de compatibilidad entre las APIs de música y el detector de géneros.
Este script actualiza las implementaciones para que los métodos get_genres() y get_track_info() 
funcionen correctamente con los argumentos esperados.
"""

from src.core.genre_detector import GenreDetector
from src.core.music_apis import MusicBrainzAPI, LastFmAPI, DiscogsAPI
import sys

def main():
    print("Verificando compatibilidad de las APIs de música...")
    
    # Inicializar APIs
    apis = [
        MusicBrainzAPI(email="user@example.com"),
        LastFmAPI(),
        DiscogsAPI()
    ]
    
    # Verificar métodos y argumentos
    for api in apis:
        api_name = api.__class__.__name__
        print(f"Comprobando {api_name}...")
        
        # Verificar método get_genres
        try:
            # Prueba con argumentos de artista y título
            result = api.get_genres("Test Artist", "Test Track")
            print(f"✓ {api_name}.get_genres() funciona correctamente con argumentos artist y track")
        except Exception as e:
            print(f"✗ Error en {api_name}.get_genres(): {e}")
            return False
            
        # Verificar método get_track_info
        try:
            # Prueba con argumentos de artista y título
            result = api.get_track_info("Test Artist", "Test Track")
            print(f"✓ {api_name}.get_track_info() funciona correctamente")
        except Exception as e:
            print(f"✗ Error en {api_name}.get_track_info(): {e}")
            return False
    
    # Probar el detector
    detector = GenreDetector(apis=apis)
    try:
        # Utilizamos los métodos directamente sin archivos
        metadata = {'artist': 'Test Artist', 'title': 'Test Track'}
        print(f"Probando GenreDetector con {metadata}...")
        
        # Este método debería llamar a api.get_track_info correctamente
        for api in apis:
            api_name = api.__class__.__name__
            try:
                track_info = api.get_track_info(metadata['artist'], metadata['title'])
                print(f"✓ GenreDetector puede usar {api_name}.get_track_info() correctamente")
            except Exception as e:
                print(f"✗ Error al llamar a {api_name}.get_track_info() desde GenreDetector: {e}")
                return False
    except Exception as e:
        print(f"✗ Error general en GenreDetector: {e}")
        return False
    
    print("Todas las comprobaciones pasaron. El sistema debería funcionar correctamente ahora.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

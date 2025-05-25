"""
Módulo para exportar playlists a diferentes formatos, como M3U.
"""
import os
from typing import List, Dict, Optional
import sys # Añadir sys para modificar el path

# Añadir la ruta src al path para importar módulos
_current_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.dirname(_current_dir) # src/
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from data import crud

def generate_m3u_content(db_path: str, playlist_id: int) -> Optional[str]:
    """
    Genera el contenido de un archivo M3U para una playlist dada.

    Args:
        db_path (str): Ruta al archivo de la base de datos SQLite.
        playlist_id (int): El ID de la smart playlist a exportar.

    Returns:
        Optional[str]: Una cadena con el contenido del archivo M3U, 
                       o None si la playlist no existe o no tiene tracks.
    """
    conn = crud.create_connection(db_path)
    if not conn:
        print(f"[Exporter] Error: No se pudo conectar a la base de datos {db_path}")
        return None

    try:
        playlist_details = crud.get_smart_playlist_by_id(conn, playlist_id)
        if not playlist_details:
            print(f"[Exporter] Error: Playlist ID {playlist_id} no encontrada.")
            return None

        # Obtener los tracks de la playlist (resultados de la última evaluación)
        # Asumimos que crud.get_tracks_for_playlist devuelve tracks con 'file_path', 'duration_seconds', 'artist', 'title'
        tracks = crud.get_tracks_for_playlist(conn, playlist_id)
        if not tracks:
            print(f"[Exporter] Info: Playlist ID {playlist_id} ('{playlist_details.get('name', 'N/A')}') no tiene tracks o no ha sido evaluada.")
            return """#EXTM3U\n""" # Retornar un M3U vacío

        m3u_lines = ["#EXTM3U"]

        for track in tracks:
            duration = int(track.get('duration_seconds', -1)) # -1 si no hay duración
            artist = track.get('artist', 'Unknown Artist')
            title = track.get('title', 'Unknown Title')
            file_path = track.get('file_path')

            if not file_path:
                print(f"[Exporter] Warning: Track ID {track.get('track_id')} no tiene file_path, omitiendo.")
                continue

            # Asegurar que la ruta del archivo sea absoluta o relativa según necesidad.
            # Para M3U, usualmente se usan rutas relativas al archivo M3U o absolutas.
            # Por ahora, usaremos la ruta tal como está en la base de datos.
            
            m3u_lines.append(f"#EXTINF:{duration},{artist} - {title}")
            m3u_lines.append(file_path)
        
        return "\n".join(m3u_lines)

    except Exception as e:
        print(f"[Exporter] Error generando M3U para playlist ID {playlist_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Ejemplo de uso (requiere que la base de datos exista y tenga datos)
    # Asumiendo que database_setup.DB_FILE apunta a la base de datos correcta
    
    # Necesitamos DB_FILE para este ejemplo. Asumimos que está en el path.
    # Este bloque de prueba es más complejo de ejecutar directamente sin contexto.
    print("Para probar, ejecuta la UI y usa la funcionalidad de exportación.")
    
    # Ejemplo de cómo se podría llamar:
    # from database_setup import DB_FILE # Ajustar import si es necesario
    # test_playlist_id = 1 # Cambiar por un ID de playlist existente
    # content = generate_m3u_content(DB_FILE, test_playlist_id)
    # if content:
    #     print("\n--- Contenido M3U Generado ---")
    #     print(content)
    #     # Guardar a un archivo
    #     # with open(f"playlist_{test_playlist_id}.m3u", "w", encoding="utf-8") as f:
    #     #     f.write(content)
    #     # print(f"Playlist guardada como playlist_{test_playlist_id}.m3u")
    # else:
    #     print(f"No se pudo generar M3U para playlist ID {test_playlist_id}") 
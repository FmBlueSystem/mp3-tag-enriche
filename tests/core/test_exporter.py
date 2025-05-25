import unittest
import os
import sqlite3
import sys
from unittest.mock import patch, MagicMock

# Asegurar que src/ está en el PYTHONPATH para encontrar los módulos del proyecto
# Esto es crucial si ejecutas los tests desde el directorio raíz del proyecto
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_src_dir = os.path.join(_project_root, 'src')
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from core import exporter
from data import crud # Para poblar la BD de prueba
from data.database_setup import setup_database # Para crear tablas

# Constante para la BD en memoria para tests
TEST_DB_MEMORY = ":memory:"

class TestExporter(unittest.TestCase):

    def setUp(self):
        """Configura una base de datos en memoria para cada test."""
        self.conn = sqlite3.connect(TEST_DB_MEMORY)
        # No usamos setup_database directamente aquí porque crea la BD en disco.
        # En su lugar, creamos las tablas manualmente.
        # O, si setup_database puede tomar una conexión, la usamos.
        # Por ahora, asumiremos que necesitamos crear tablas manualmente para :memory:
        
        cursor = self.conn.cursor()
        # Replicar la estructura de tablas necesaria de database_setup.py
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                track_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT,
                album TEXT,
                genre TEXT,
                year INTEGER,
                duration INTEGER, -- en segundos
                path TEXT UNIQUE NOT NULL,
                bitrate INTEGER,
                sample_rate INTEGER,
                channels INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                play_count INTEGER DEFAULT 0,
                rating INTEGER, -- 0-5 estrellas
                bpm REAL,
                key TEXT, -- e.g., '12A' or 'C#m'
                energy INTEGER, -- 1-10
                danceability REAL, -- 0.0-1.0
                moods TEXT -- JSON array de strings
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS smart_playlists (
                playlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                is_enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_generated_at TIMESTAMP, -- Cuándo se actualizaron los tracks por última vez
                sort_field TEXT, -- Campo por el cual ordenar (e.g., 'title', 'artist', 'bpm')
                sort_order TEXT -- 'ASC' o 'DESC'
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS smart_playlist_rules (
                rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER NOT NULL,
                rule_text TEXT NOT NULL, -- La expresión de la regla, e.g., "genre = 'Rock' AND year > 2000"
                FOREIGN KEY (playlist_id) REFERENCES smart_playlists (playlist_id) ON DELETE CASCADE
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS smart_playlist_tracks (
                playlist_id INTEGER NOT NULL,
                track_id INTEGER NOT NULL,
                rank INTEGER, -- Orden del track en la playlist generada
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (playlist_id, track_id),
                FOREIGN KEY (playlist_id) REFERENCES smart_playlists (playlist_id) ON DELETE CASCADE,
                FOREIGN KEY (track_id) REFERENCES tracks (track_id) ON DELETE CASCADE
            );
        ''')
        self.conn.commit()

        # Poblar con algunos datos
        self.track1_id = crud.add_track(self.conn, title="Test Track 1", artist="Artist A", path="/music/track1.mp3", genre="Rock", duration=180)
        self.track2_id = crud.add_track(self.conn, title="Test Track 2", artist="Artist B", path="/music/track2.wav", genre="Pop", duration=240)
        self.track3_id = crud.add_track(self.conn, title="Test Track 3", artist="Artist C", path="/music/track3.flac", genre="Rock", duration=200)

        self.playlist1_id = crud.create_smart_playlist(self.conn, name="Test Rock Playlist")
        # Asumimos que los tracks ya han sido evaluados y añadidos a smart_playlist_tracks
        # Para el exporter, lo importante es que existan en smart_playlist_tracks
        crud.add_track_to_playlist_results(self.conn, self.playlist1_id, self.track1_id, rank=0)
        crud.add_track_to_playlist_results(self.conn, self.playlist1_id, self.track3_id, rank=1)


    def tearDown(self):
        """Cierra la conexión a la base de datos después de cada test."""
        self.conn.close()

    def test_generate_m3u_content_success(self):
        """Prueba la generación exitosa de contenido M3U."""
        # Usamos TEST_DB_MEMORY pero la función exporter espera una ruta de archivo.
        # Necesitamos 'engañar' a crud.create_connection para que use nuestra conexión en memoria.
        
        with patch('src.data.crud.create_connection') as mock_create_conn:
            mock_create_conn.return_value = self.conn # Devolver nuestra conexión en memoria
            
            m3u_content = exporter.generate_m3u_content(db_path="dummy_path.db", playlist_id=self.playlist1_id)
            
            self.assertIsNotNone(m3u_content)
            self.assertIn("#EXTM3U", m3u_content)
            
            # Verificar Track 1
            self.assertIn("#EXTINF:180,Artist A - Test Track 1", m3u_content)
            self.assertIn("/music/track1.mp3", m3u_content)
            
            # Verificar Track 3 (Track 2 no debería estar)
            self.assertIn("#EXTINF:200,Artist C - Test Track 3", m3u_content)
            self.assertIn("/music/track3.flac", m3u_content)
            
            self.assertNotIn("Test Track 2", m3u_content)
            self.assertNotIn("/music/track2.wav", m3u_content)

            # Asegurar que la conexión mock fue llamada
            mock_create_conn.assert_called_once_with("dummy_path.db")

    def test_generate_m3u_content_playlist_not_found(self):
        """Prueba la generación de M3U cuando la playlist_id no existe."""
        with patch('src.data.crud.create_connection') as mock_create_conn:
            mock_create_conn.return_value = self.conn
            
            non_existent_playlist_id = 999
            m3u_content = exporter.generate_m3u_content(db_path="dummy_path.db", playlist_id=non_existent_playlist_id)
            
            # Esperamos None o una cadena M3U vacía (solo #EXTM3U)
            # La implementación actual de exporter.py devuelve None en este caso.
            self.assertIsNone(m3u_content, 
                              msg=f"Se esperaba None para playlist ID no existente, pero se obtuvo: {m3u_content}")
            mock_create_conn.assert_called_once_with("dummy_path.db")

    def test_generate_m3u_content_playlist_empty(self):
        """Prueba la generación de M3U para una playlist existente pero vacía."""
        # Crear una playlist vacía adicional
        empty_playlist_id = crud.create_smart_playlist(self.conn, name="Empty Test Playlist")
        self.assertIsNotNone(empty_playlist_id) # Asegurar que se creó

        with patch('src.data.crud.create_connection') as mock_create_conn:
            mock_create_conn.return_value = self.conn
            
            m3u_content = exporter.generate_m3u_content(db_path="dummy_path.db", playlist_id=empty_playlist_id)
            
            self.assertIsNotNone(m3u_content, "El contenido M3U no debería ser None para una playlist vacía.")
            # Debería contener solo la cabecera o estar vacío después de la cabecera
            # La especificación M3U dice que un archivo vacío es válido, o uno solo con #EXTM3U
            # La implementación actual en exporter.py, si no hay tracks, devuelve:
            # "#EXTM3U\n"
            expected_empty_content = "#EXTM3U\n"
            self.assertEqual(m3u_content, expected_empty_content,
                             msg=f"Contenido M3U para playlist vacía no es el esperado. Se obtuvo: '{m3u_content}'")
            mock_create_conn.assert_called_once_with("dummy_path.db")

    def test_generate_m3u_content_db_error(self):
        """Prueba el manejo de un error al conectar a la base de datos."""
        # Simular que crud.create_connection devuelve None o lanza una excepción
        with patch('src.data.crud.create_connection') as mock_create_conn:
            mock_create_conn.return_value = None # Simula fallo al crear conexión
            
            m3u_content = exporter.generate_m3u_content(db_path="error_path.db", playlist_id=self.playlist1_id)
            
            self.assertIsNone(m3u_content,
                              msg=f"Se esperaba None cuando la conexión a BD falla, pero se obtuvo: {m3u_content}")
            mock_create_conn.assert_called_once_with("error_path.db")

        # También podríamos probar si lanza una excepción específica si esa fuera la lógica
        # Por ejemplo, si create_connection puede lanzar sqlite3.Error
        with patch('src.data.crud.create_connection') as mock_create_conn_exception:
            mock_create_conn_exception.side_effect = sqlite3.OperationalError("simulated DB error")
            
            m3u_content_on_exception = exporter.generate_m3u_content(db_path="exception_path.db", playlist_id=self.playlist1_id)
            self.assertIsNone(m3u_content_on_exception,
                              msg=f"Se esperaba None cuando create_connection lanza excepción, pero se obtuvo: {m3u_content_on_exception}")
            mock_create_conn_exception.assert_called_once_with("exception_path.db")

if __name__ == '__main__':
    unittest.main() 
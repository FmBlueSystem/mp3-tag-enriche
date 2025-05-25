import unittest
import os
import sqlite3
import sys
from datetime import datetime

# Asegurar que src/ está en el PYTHONPATH
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_src_dir = os.path.join(_project_root, 'src')
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from data import crud
from data.database_setup import DB_FILE # Aunque no usaremos el archivo, sí las querys de creación de tabla

# Usaremos una BD en memoria para los tests
TEST_DB_MEMORY = ":memory:"

class TestCrudOperations(unittest.TestCase):

    def setUp(self):
        """Configura una base de datos en memoria y crea las tablas para cada test."""
        self.conn = crud.create_connection(TEST_DB_MEMORY) # crud.create_connection debería funcionar con :memory:
        self.assertIsNotNone(self.conn, "La conexión a la BD en memoria no debería ser None.")
        
        # Habilitar foreign keys en SQLite (necesario para ON DELETE CASCADE)
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Crear tablas usando las mismas definiciones de database_setup.py
        # Idealmente, database_setup.py tendría una función para crear tablas en una conexión dada.
        # Por ahora, replicamos la lógica o extraemos las CREATE TABLE statements.
        # Nota: La importación de DB_FILE arriba no es para usar el archivo, sino para potencialmente
        # acceder a las sentencias CREATE TABLE si estuvieran definidas como constantes allí.
        # Asumimos que crud.create_connection() con :memory: es suficiente y las tablas deben crearse.
        
        # Para simplificar, vamos a obtener las sentencias CREATE TABLE del archivo database_setup.py
        # Esto es un poco frágil si el archivo cambia mucho, pero evita duplicar SQL aquí.
        # Una mejor solución a largo plazo sería tener setup_database(conn) en database_setup.py
        
        # Manera robusta (si database_setup.setup_database puede tomar una conexión):
        # setup_database(self.conn) # Si setup_database aceptara un objeto de conexión

        # Manera manual (copiando las CREATE de TestExporter o database_setup.py):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                track_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, artist TEXT,
                album TEXT, genre TEXT, year INTEGER, duration INTEGER, path TEXT UNIQUE NOT NULL,
                bitrate INTEGER, sample_rate INTEGER, channels INTEGER, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, play_count INTEGER DEFAULT 0,
                rating INTEGER, bpm REAL, key TEXT, energy INTEGER, danceability REAL, moods TEXT,
                track_number INTEGER
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS smart_playlists (
                playlist_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, description TEXT,
                is_enabled BOOLEAN DEFAULT TRUE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_generated_at TIMESTAMP,
                sort_field TEXT, sort_order TEXT
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS smart_playlist_rules (
                rule_id INTEGER PRIMARY KEY AUTOINCREMENT, playlist_id INTEGER NOT NULL, rule_text TEXT NOT NULL,
                FOREIGN KEY (playlist_id) REFERENCES smart_playlists (playlist_id) ON DELETE CASCADE
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS smart_playlist_tracks (
                playlist_id INTEGER NOT NULL, track_id INTEGER NOT NULL, rank INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (playlist_id, track_id),
                FOREIGN KEY (playlist_id) REFERENCES smart_playlists (playlist_id) ON DELETE CASCADE,
                FOREIGN KEY (track_id) REFERENCES tracks (track_id) ON DELETE CASCADE
            );
        ''')
        self.conn.commit()

    def tearDown(self):
        """Cierra la conexión a la base de datos después de cada test."""
        if self.conn:
            self.conn.close()

    def test_add_track_success(self):
        """Prueba añadir un track exitosamente."""
        track_data = {
            "title": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "genre": "Test Genre",
            "year": 2023,
            "duration": 180, # segundos
            "path": "/music/test_song.mp3",
            "bitrate": 320,
            "sample_rate": 44100,
            "channels": 2,
            "bpm": 120.0,
            "key": "6A",
            "energy": 7,
            "danceability": 0.8,
            "moods": '["happy", "energetic"]',
            "track_number": 1
        }
        
        track_id = crud.add_track(self.conn, track_data)
        self.assertIsNotNone(track_id, "add_track debería devolver un ID.")
        
        # Verificar que el track se guardó correctamente
        retrieved_track = crud.get_track_by_id(self.conn, track_id)
        self.assertIsNotNone(retrieved_track, "El track guardado no pudo ser recuperado.")
        
        self.assertEqual(retrieved_track["title"], track_data["title"])
        self.assertEqual(retrieved_track["artist"], track_data["artist"])
        self.assertEqual(retrieved_track["path"], track_data["path"])
        self.assertEqual(retrieved_track["year"], track_data["year"])
        self.assertEqual(retrieved_track["duration"], track_data["duration"])
        self.assertEqual(retrieved_track["bpm"], track_data["bpm"])
        self.assertEqual(retrieved_track["key"], track_data["key"])
        self.assertEqual(retrieved_track["energy"], track_data["energy"])
        self.assertEqual(retrieved_track["track_number"], track_data["track_number"])
        # Podríamos seguir verificando todos los campos

    def test_add_track_duplicate_path(self):
        """Prueba que añadir un track con un path duplicado falle."""
        track_data1 = {"title": "Song A", "path": "/music/unique_song.mp3"}
        track_id1 = crud.add_track(self.conn, track_data1)
        self.assertIsNotNone(track_id1)

        track_data2 = {"title": "Song B", "path": "/music/unique_song.mp3"}
        result_id2 = crud.add_track(self.conn, track_data2)
        self.assertIsNone(result_id2, "Añadir track con path duplicado debería devolver None.")

    def test_get_track_by_id(self):
        """Prueba obtener un track por su ID."""
        track_data = {"title": "Gettable Track", "path": "/music/gettable.mp3", "artist": "Artist G"}
        track_id = crud.add_track(self.conn, track_data)
        self.assertIsNotNone(track_id)

        retrieved_track = crud.get_track_by_id(self.conn, track_id)
        self.assertIsNotNone(retrieved_track)
        self.assertEqual(retrieved_track["track_id"], track_id)
        self.assertEqual(retrieved_track["title"], "Gettable Track")
        self.assertEqual(retrieved_track["artist"], "Artist G")

    def test_get_track_by_id_not_found(self):
        """Prueba obtener un track con un ID que no existe."""
        non_existent_id = 9999
        retrieved_track = crud.get_track_by_id(self.conn, non_existent_id)
        self.assertIsNone(retrieved_track)

    def test_get_all_tracks(self):
        """Prueba obtener todos los tracks."""
        # Primero, asegurar que la tabla está vacía o contar cuántos hay si setUp los crea
        initial_tracks = crud.get_all_tracks(self.conn)
        initial_count = len(initial_tracks) if initial_tracks else 0

        crud.add_track(self.conn, {"title":"Track Alpha", "path":"/music/alpha.mp3"})
        crud.add_track(self.conn, {"title":"Track Beta", "path":"/music/beta.mp3"})
        crud.add_track(self.conn, {"title":"Track Gamma", "path":"/music/gamma.mp3"})

        all_tracks = crud.get_all_tracks(self.conn)
        self.assertIsNotNone(all_tracks)
        self.assertEqual(len(all_tracks), initial_count + 3)

        # Verificar que los títulos están presentes (orden no garantizado por get_all_tracks)
        titles_retrieved = {track['title'] for track in all_tracks}
        self.assertIn("Track Alpha", titles_retrieved)
        self.assertIn("Track Beta", titles_retrieved)
        self.assertIn("Track Gamma", titles_retrieved)

    def test_update_track(self):
        """Prueba actualizar los campos de un track existente."""
        track_id = crud.add_track(self.conn, {"title":"Old Title", "artist":"Old Artist", "path":"/music/updatable.mp3", "year":2000})
        self.assertIsNotNone(track_id)

        update_data = {
            "title": "New Title",
            "artist": "New Artist",
            "year": 2024,
            "genre": "Updated Genre"
        }
        success = crud.update_track(self.conn, track_id, **update_data)
        self.assertTrue(success, "update_track debería devolver True si la actualización fue exitosa.")

        updated_track = crud.get_track_by_id(self.conn, track_id)
        self.assertIsNotNone(updated_track)
        self.assertEqual(updated_track["title"], "New Title")
        self.assertEqual(updated_track["artist"], "New Artist")
        self.assertEqual(updated_track["year"], 2024)
        self.assertEqual(updated_track["genre"], "Updated Genre")
        # El path no debería cambiar si no se especifica en update_data
        self.assertEqual(updated_track["path"], "/music/updatable.mp3")

    def test_update_track_non_existent(self):
        """Prueba actualizar un track que no existe."""
        success = crud.update_track(self.conn, 9999, title="No Such Track")
        self.assertFalse(success, "update_track debería devolver False para un ID de track no existente.")

    def test_delete_track(self):
        """Prueba eliminar un track existente."""
        track_id = crud.add_track(self.conn, {"title":"To Be Deleted", "path":"/music/deletable.mp3"})
        self.assertIsNotNone(track_id)

        # Verificar que existe antes de borrar
        self.assertIsNotNone(crud.get_track_by_id(self.conn, track_id))

        success = crud.delete_track(self.conn, track_id)
        self.assertTrue(success, "delete_track debería devolver True si la eliminación fue exitosa.")

        # Verificar que ya no existe
        self.assertIsNone(crud.get_track_by_id(self.conn, track_id))

    def test_delete_track_non_existent(self):
        """Prueba eliminar un track que no existe."""
        success = crud.delete_track(self.conn, 9999)
        self.assertFalse(success, "delete_track debería devolver False para un ID de track no existente.")

    # --- Tests para Smart Playlists ---
    def test_create_smart_playlist_success(self):
        """Prueba crear una smart playlist exitosamente."""
        playlist_name = "My Awesome Playlist"
        playlist_description = "A playlist for awesome music."
        
        playlist_id = crud.create_smart_playlist(self.conn, playlist_name, playlist_description)
        self.assertIsNotNone(playlist_id, "create_smart_playlist debería devolver un ID.")
        
        retrieved_playlist = crud.get_smart_playlist_by_id(self.conn, playlist_id)
        self.assertIsNotNone(retrieved_playlist)
        self.assertEqual(retrieved_playlist["name"], playlist_name)
        self.assertEqual(retrieved_playlist["description"], playlist_description)
        self.assertTrue(retrieved_playlist["is_enabled"]) # Debería ser True por defecto

    def test_create_smart_playlist_duplicate_name(self):
        """Prueba que crear una playlist con nombre duplicado falle."""
        playlist_name = "Unique Playlist Name"
        crud.create_smart_playlist(self.conn, playlist_name) # Primera creación exitosa
        
        # Segunda creación con el mismo nombre debería fallar
        with self.assertRaises(sqlite3.IntegrityError):
            crud.create_smart_playlist(self.conn, playlist_name)

    def test_get_smart_playlist_by_id_and_name(self):
        """Prueba obtener una smart playlist por ID y por nombre."""
        pid1 = crud.create_smart_playlist(self.conn, "Playlist Alpha", "Desc Alpha")
        pid2 = crud.create_smart_playlist(self.conn, "Playlist Beta", "Desc Beta")

        # Por ID
        p_alpha_by_id = crud.get_smart_playlist_by_id(self.conn, pid1)
        self.assertIsNotNone(p_alpha_by_id)
        self.assertEqual(p_alpha_by_id["name"], "Playlist Alpha")

        p_beta_by_id = crud.get_smart_playlist_by_id(self.conn, pid2)
        self.assertIsNotNone(p_beta_by_id)
        self.assertEqual(p_beta_by_id["description"], "Desc Beta")

        self.assertIsNone(crud.get_smart_playlist_by_id(self.conn, 9999), "No debería encontrar playlist con ID inexistente.")

        # Por Nombre
        p_alpha_by_name = crud.get_smart_playlist_by_name(self.conn, "Playlist Alpha")
        self.assertIsNotNone(p_alpha_by_name)
        self.assertEqual(p_alpha_by_name["playlist_id"], pid1)

        p_beta_by_name = crud.get_smart_playlist_by_name(self.conn, "Playlist Beta")
        self.assertIsNotNone(p_beta_by_name)
        self.assertEqual(p_beta_by_name["playlist_id"], pid2)

        self.assertIsNone(crud.get_smart_playlist_by_name(self.conn, "Non Existent Playlist Name"))

    def test_get_all_smart_playlists(self):
        """Prueba obtener todas las smart playlists."""
        initial_playlists = crud.get_all_smart_playlists(self.conn)
        initial_count = len(initial_playlists) if initial_playlists else 0

        crud.create_smart_playlist(self.conn, "Playlist One")
        crud.create_smart_playlist(self.conn, "Playlist Two")

        all_playlists = crud.get_all_smart_playlists(self.conn)
        self.assertIsNotNone(all_playlists)
        self.assertEqual(len(all_playlists), initial_count + 2)
        
        names_retrieved = {p['name'] for p in all_playlists}
        self.assertIn("Playlist One", names_retrieved)
        self.assertIn("Playlist Two", names_retrieved)

    def test_update_smart_playlist(self):
        """Prueba actualizar una smart playlist."""
        playlist_id = crud.create_smart_playlist(self.conn, "Old Name", "Old Desc")
        self.assertIsNotNone(playlist_id)

        # Actualizar nombre, descripción y estado
        update_data = {
            "name": "New Name For Playlist",
            "description": "New Description Updated",
            "is_enabled": False,
            "sort_field": "artist",
            "sort_order": "DESC"
        }
        success = crud.update_smart_playlist(self.conn, playlist_id, **update_data)
        self.assertTrue(success, "update_smart_playlist debería devolver True en éxito.")

        updated_p = crud.get_smart_playlist_by_id(self.conn, playlist_id)
        self.assertIsNotNone(updated_p)
        self.assertEqual(updated_p["name"], "New Name For Playlist")
        self.assertEqual(updated_p["description"], "New Description Updated")
        self.assertFalse(updated_p["is_enabled"])
        self.assertEqual(updated_p["sort_field"], "artist")
        self.assertEqual(updated_p["sort_order"], "DESC")
        
        # Probar actualizar solo un campo
        success_partial = crud.update_smart_playlist(self.conn, playlist_id, name="Partially New Name")
        self.assertTrue(success_partial)
        partially_updated_p = crud.get_smart_playlist_by_id(self.conn, playlist_id)
        self.assertEqual(partially_updated_p["name"], "Partially New Name")
        self.assertEqual(partially_updated_p["description"], "New Description Updated") # No debería cambiar

    def test_update_smart_playlist_non_existent(self):
        """Prueba actualizar una playlist que no existe."""
        success = crud.update_smart_playlist(self.conn, 9999, name="No Such Playlist")
        self.assertFalse(success, "update_smart_playlist debería devolver False para un ID no existente.")

    def test_delete_smart_playlist(self):
        """Prueba eliminar una smart playlist y sus dependencias (reglas, tracks asociados)."""
        # Crear una playlist con una regla y un track asociado
        pid = crud.create_smart_playlist(self.conn, "Playlist To Delete")
        self.assertIsNotNone(pid)
        rule_id = crud.add_rule_to_playlist(self.conn, pid, "genre = 'Test'")
        self.assertIsNotNone(rule_id)
        track_id = crud.add_track(self.conn, {"title":"Track For Deletable Playlist", "path":"/music/track_for_delete.mp3"})
        self.assertIsNotNone(track_id)
        crud.add_track_to_playlist_results(self.conn, pid, track_id, rank=0)

        # Verificar que todo existe antes de borrar
        self.assertIsNotNone(crud.get_smart_playlist_by_id(self.conn, pid))
        self.assertTrue(len(crud.get_rules_for_playlist(self.conn, pid)) > 0)
        self.assertTrue(len(crud.get_tracks_for_playlist_results(self.conn, pid)) > 0)

        success_delete = crud.delete_smart_playlist(self.conn, pid)
        self.assertTrue(success_delete, "delete_smart_playlist debería devolver True en éxito.")

        # Verificar que la playlist y sus dependencias (reglas, tracks) ya no existen
        self.assertIsNone(crud.get_smart_playlist_by_id(self.conn, pid))
        self.assertEqual(len(crud.get_rules_for_playlist(self.conn, pid)), 0, "Las reglas deberían eliminarse con la playlist (ON DELETE CASCADE).")
        self.assertEqual(len(crud.get_tracks_for_playlist_results(self.conn, pid)), 0, "Los tracks asociados deberían eliminarse (ON DELETE CASCADE).")

    def test_delete_smart_playlist_non_existent(self):
        """Prueba eliminar una playlist que no existe."""
        success = crud.delete_smart_playlist(self.conn, 9999)
        self.assertFalse(success, "delete_smart_playlist debería devolver False para un ID no existente.")

    # --- Tests para Reglas de Smart Playlists (smart_playlist_rules) ---
    def test_add_and_get_rules_for_playlist(self):
        """Prueba añadir y obtener la regla para una playlist."""
        pid = crud.create_smart_playlist(self.conn, "Playlist With Rules")
        self.assertIsNotNone(pid)

        # Inicialmente no debería haber regla
        self.assertIsNone(crud.get_rule_for_playlist(self.conn, pid), "Inicialmente no debería existir regla.")

        rule_text1 = "genre = 'Rock'"
        rule_id1 = crud.add_rule_to_playlist(self.conn, pid, rule_text1)
        self.assertIsNotNone(rule_id1, "add_rule_to_playlist debería devolver un ID de regla.")

        rule = crud.get_rule_for_playlist(self.conn, pid)
        self.assertIsNotNone(rule, "Debería haber una regla después de añadirla.")
        self.assertEqual(rule["rule_text"], rule_text1)
        self.assertEqual(rule["rule_id"], rule_id1)

        # Probar que add_rule_to_playlist reemplaza la regla existente
        rule_text2 = "year > 2000"
        rule_id2 = crud.add_rule_to_playlist(self.conn, pid, rule_text2)
        self.assertIsNotNone(rule_id2)
        self.assertNotEqual(rule_id1, rule_id2, "Al reemplazar, se debería generar un nuevo rule_id.")

        updated_rule = crud.get_rule_for_playlist(self.conn, pid)
        self.assertIsNotNone(updated_rule)
        self.assertEqual(updated_rule["rule_text"], rule_text2)
        self.assertEqual(updated_rule["rule_id"], rule_id2, "El ID de la regla debería ser el más reciente.")

    def test_get_rules_for_non_existent_playlist(self):
        """Prueba obtener la regla para una playlist que no existe."""
        rule = crud.get_rule_for_playlist(self.conn, 9999)
        self.assertIsNone(rule, "No debería haber regla para playlist no existente.")

    def test_remove_rules_from_playlist(self):
        """Prueba eliminar todas las reglas de una playlist."""
        pid = crud.create_smart_playlist(self.conn, "Playlist For Rule Removal")
        crud.add_rule_to_playlist(self.conn, pid, "genre = 'Pop'") # Añadir una regla
        
        # Verificar que la regla existe
        self.assertIsNotNone(crud.get_rule_for_playlist(self.conn, pid))
        
        success = crud.remove_rules_from_playlist(self.conn, pid)
        self.assertTrue(success, "remove_rules_from_playlist debería devolver True en éxito.")
        
        # Verificar que ya no hay reglas
        self.assertIsNone(crud.get_rule_for_playlist(self.conn, pid))

        # Probar eliminar reglas de una playlist que no tiene (no debería fallar)
        pid_no_rules = crud.create_smart_playlist(self.conn, "Playlist With No Rules Initially")
        success_no_rules = crud.remove_rules_from_playlist(self.conn, pid_no_rules)
        self.assertTrue(success_no_rules, "remove_rules_from_playlist debería devolver True incluso si no hay reglas que borrar.")
        self.assertEqual(len(crud.get_rules_for_playlist(self.conn, pid_no_rules)), 0)

        # Probar eliminar reglas de una playlist que no existe (debería devolver False o no fallar, según implementación)
        # La implementación actual de remove_rules_from_playlist no verifica si la playlist existe, solo intenta borrar.
        # Si la playlist_id no existe, el DELETE no afectará filas y no lanzará error.
        # Devolverá True porque el execute no falló.
        success_non_existent_playlist = crud.remove_rules_from_playlist(self.conn, 9999)
        self.assertTrue(success_non_existent_playlist, "remove_rules_from_playlist para playlist no existente no debería fallar y devolver True.")

    # --- Tests para Tracks en Playlists (smart_playlist_tracks) ---
    def test_add_and_get_tracks_for_playlist_results(self):
        """Prueba añadir y obtener tracks para los resultados de una playlist."""
        pid = crud.create_smart_playlist(self.conn, "Playlist For Results")
        track1_id = crud.add_track(self.conn, {"title":"Track Res 1", "path":"/music/res1.mp3"})
        track2_id = crud.add_track(self.conn, {"title":"Track Res 2", "path":"/music/res2.mp3"})
        track3_id = crud.add_track(self.conn, {"title":"Track Res 3", "path":"/music/res3.mp3"})

        # Inicialmente no hay tracks en los resultados
        self.assertEqual(len(crud.get_tracks_for_playlist_results(self.conn, pid)), 0)

        # Añadir tracks con ranks
        crud.add_track_to_playlist_results(self.conn, pid, track1_id, rank=0)
        crud.add_track_to_playlist_results(self.conn, pid, track2_id, rank=1)
        # Añadir un track duplicado (mismo pid, track_id) debería fallar por PRIMARY KEY constraint
        with self.assertRaises(sqlite3.IntegrityError):
            crud.add_track_to_playlist_results(self.conn, pid, track1_id, rank=2) # Mismo track_id

        results = crud.get_tracks_for_playlist_results(self.conn, pid)
        self.assertEqual(len(results), 2)
        
        # get_tracks_for_playlist_results debería devolverlos ordenados por rank
        # Asumiendo que devuelve una lista de diccionarios/objetos con las columnas de 'tracks' y 'rank'
        # (esto requiere un JOIN en la función crud)
        # Si solo devuelve track_ids, el test sería diferente.
        # Voy a asumir que la función crud.get_tracks_for_playlist_results hace JOIN y ordena por rank.
        self.assertEqual(results[0]["track_id"], track1_id)
        self.assertEqual(results[0]["title"], "Track Res 1") # Asumiendo que se recupera el título
        self.assertEqual(results[0]["rank"], 0)
        
        self.assertEqual(results[1]["track_id"], track2_id)
        self.assertEqual(results[1]["title"], "Track Res 2")
        self.assertEqual(results[1]["rank"], 1)

    def test_get_tracks_for_playlist_results_non_existent_playlist(self):
        """Prueba obtener tracks para una playlist que no existe."""
        results = crud.get_tracks_for_playlist(self.conn, 9999)
        self.assertEqual(len(results), 0)

    def test_clear_playlist_tracks(self):
        """Prueba limpiar todos los tracks de los resultados de una playlist."""
        pid = crud.create_smart_playlist(self.conn, "Playlist To Clear")
        track1_id = crud.add_track(self.conn, {"title":"Track Clr 1", "path":"/music/clr1.mp3"})
        track2_id = crud.add_track(self.conn, {"title":"Track Clr 2", "path":"/music/clr2.mp3"})

        crud.add_track_to_playlist_results(self.conn, pid, track1_id, rank=0)
        crud.add_track_to_playlist_results(self.conn, pid, track2_id, rank=1)

        # Verificar que hay tracks antes de limpiar
        self.assertEqual(len(crud.get_tracks_for_playlist(self.conn, pid)), 2)

        success = crud.clear_playlist_tracks(self.conn, pid)
        self.assertTrue(success, "clear_playlist_tracks debería devolver True en éxito.")

        # Verificar que ya no hay tracks en los resultados
        self.assertEqual(len(crud.get_tracks_for_playlist(self.conn, pid)), 0)

        # Probar limpiar una playlist que ya está vacía
        pid_already_empty = crud.create_smart_playlist(self.conn, "Playlist Already Empty")
        success_already_empty = crud.clear_playlist_tracks(self.conn, pid_already_empty)
        self.assertTrue(success_already_empty, "clear_playlist_tracks para una playlist ya vacía debería devolver True.")
        self.assertEqual(len(crud.get_tracks_for_playlist(self.conn, pid_already_empty)), 0)
        
        # Probar limpiar una playlist que no existe
        # Debería devolver True ya que el DELETE no fallará
        success_non_existent = crud.clear_playlist_tracks(self.conn, 9999)
        self.assertTrue(success_non_existent, "clear_playlist_tracks para una playlist no existente debería devolver True.")

    # --- Test para Poblado de Datos ---
    def test_populate_sample_data(self):
        """Prueba que se añadan datos de ejemplo si la tabla de tracks está vacía."""
        # Asegurar que la tabla de tracks está realmente vacía antes de poblar
        # (setUp crea las tablas pero no las puebla por defecto con estos datos de sample)
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tracks;") # Limpiar por si acaso
        self.conn.commit()
        self.assertEqual(len(crud.get_all_tracks(self.conn)), 0, "La tabla de tracks debería estar vacía antes de poblar.")

        crud.populate_sample_data(self.conn)
        
        tracks_after_population = crud.get_all_tracks(self.conn)
        # La función populate_sample_data actual añade 5 tracks de ejemplo
        self.assertEqual(len(tracks_after_population), 5, "Deberían haberse añadido 5 tracks de ejemplo.")

        # Opcional: verificar alguno de los datos si son constantes
        titles = {t['title'] for t in tracks_after_population}
        self.assertIn("Midnight City", titles) # Asumiendo que este es uno de los tracks de ejemplo

    def test_populate_sample_data_not_empty(self):
        """Prueba que no se añadan datos de ejemplo si la tabla de tracks NO está vacía."""
        # Añadir un track para que la tabla no esté vacía
        initial_track_id = crud.add_track(self.conn, {"title":"Initial Track", "path":"/music/initial.mp3"})
        self.assertIsNotNone(initial_track_id)
        self.assertEqual(len(crud.get_all_tracks(self.conn)), 1, "Debería haber 1 track inicial.")

        crud.populate_sample_data(self.conn) # Intentar poblar de nuevo
        
        # El número de tracks no debería haber cambiado
        tracks_after_attempted_population = crud.get_all_tracks(self.conn)
        self.assertEqual(len(tracks_after_attempted_population), 1, 
                         "No deberían añadirse tracks de ejemplo si la tabla ya tiene datos.")
        self.assertEqual(tracks_after_attempted_population[0]["title"], "Initial Track")

if __name__ == '__main__':
    unittest.main() 
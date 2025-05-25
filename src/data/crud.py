import sqlite3
from datetime import datetime
import json

# --- Funciones de Utilidad para la Base de Datos ---
def create_connection(db_file):
    """Crea una conexión a la base de datos SQLite."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(f"Error conectando a la base de datos: {e}")
    return conn

# --- Operaciones CRUD para Smart Playlists ---

def create_smart_playlist(conn, name, description=""):
    """Crea una nueva playlist inteligente."""
    sql = ''' INSERT INTO smart_playlists(name, description, created_at, updated_at)
              VALUES(?,?,?,?)
    '''
    cur = conn.cursor()
    try:
        now = datetime.now()
        cur.execute(sql, (name, description, now, now))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        # Dejar que IntegrityError se propague para que los tests puedan capturarla
        raise
    except sqlite3.Error as e:
        print(f"Error al crear playlist: {e}")
        return None

def get_smart_playlist_by_id(conn, playlist_id):
    """Obtiene una playlist inteligente por su ID."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM smart_playlists WHERE playlist_id=?", (playlist_id,))
    row = cur.fetchone()
    # Convertir la tupla a un diccionario para facilitar el acceso
    if row:
        keys = [description[0] for description in cur.description]
        return dict(zip(keys, row))
    return None

def get_all_smart_playlists(conn):
    """Obtiene todas las playlists inteligentes."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM smart_playlists ORDER BY name")
    rows = cur.fetchall()
    # Convertir las tuplas a diccionarios
    playlists = []
    if rows:
        keys = [description[0] for description in cur.description]
        for row in rows:
            playlists.append(dict(zip(keys, row)))
    return playlists

def update_smart_playlist(conn, playlist_id, name=None, description=None, is_enabled=None, sort_field=None, sort_order=None, last_generated_at=None):
    """Actualiza una playlist inteligente existente."""
    fields_to_update = []
    params = []

    if name is not None:
        fields_to_update.append("name = ?")
        params.append(name)
    if description is not None:
        fields_to_update.append("description = ?")
        params.append(description)
    if is_enabled is not None:
        fields_to_update.append("is_enabled = ?")
        params.append(is_enabled)
    if sort_field is not None: # Podría ser útil incluso para MVP si se quiere orden fijo
        fields_to_update.append("sort_field = ?")
        params.append(sort_field)
    if sort_order is not None:
        fields_to_update.append("sort_order = ?")
        params.append(sort_order)
    if last_generated_at is not None:
        fields_to_update.append("last_generated_at = ?")
        params.append(last_generated_at)

    if not fields_to_update:
        print("No hay campos para actualizar en la playlist.")
        return True # O False, dependiendo de cómo se quiera manejar

    fields_to_update.append("updated_at = ?")
    params.append(datetime.now())

    sql = f"UPDATE smart_playlists SET {', '.join(fields_to_update)} WHERE playlist_id = ?"
    params.append(playlist_id)

    cur = conn.cursor()
    try:
        cur.execute(sql, tuple(params))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error al actualizar playlist {playlist_id}: {e}")
        return False

def delete_smart_playlist(conn, playlist_id):
    """Elimina una playlist inteligente. Las reglas y tracks asociados se eliminan por CASCADE."""
    sql = 'DELETE FROM smart_playlists WHERE playlist_id=?'
    cur = conn.cursor()
    try:
        cur.execute(sql, (playlist_id,))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error al eliminar playlist {playlist_id}: {e}")
        return False

# --- Operaciones CRUD para Rules ---

def add_rule_to_playlist(conn, playlist_id, rule_text):
    """Añade o actualiza la regla para una playlist inteligente.
       Para el MVP, asumimos una única regla activa por playlist.
       Si ya existe una regla, se desactiva la anterior y se crea una nueva activa,
       o se actualiza la existente si se prefiere un solo registro de regla por playlist.
       Aquí optamos por actualizar la existente si la hay, o crearla si no.
    """
    # Primero, intentar actualizar si ya existe una regla para la playlist
    # Para simplificar en MVP, asumiremos que solo hay una regla por playlist en la tabla `rules`,
    # o que gestionamos la activación fuera o borramos/insertamos.
    # Una forma sencilla es borrar la regla anterior y añadir la nueva.

    cur = conn.cursor()
    # Opción 1: Borrar reglas existentes para esta playlist_id y crear la nueva.
    # Esto asegura que solo hay una regla según el diseño MVP de una expresión textual por playlist.
    try:
        cur.execute("DELETE FROM rules WHERE playlist_id=?", (playlist_id,))
        sql_insert = ''' INSERT INTO rules(playlist_id, expression_text)
                      VALUES(?,?)
        '''
        cur.execute(sql_insert, (playlist_id, rule_text))
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error as e:
        print(f"Error al añadir/actualizar regla para playlist {playlist_id}: {e}")
        return None

def get_rules_for_playlist(conn, playlist_id):
    """Obtiene las reglas para una playlist inteligente."""
    cur = conn.cursor()
    # En el MVP, esperamos una sola regla activa o la más reciente.
    cur.execute("SELECT * FROM rules WHERE playlist_id=?", (playlist_id,))
    rows = cur.fetchall()
    rules = []
    if rows:
        keys = [description[0] for description in cur.description]
        for row in rows:
            rules.append(dict(zip(keys, row)))
    return rules

def get_rule_for_playlist(conn, playlist_id):
    """Obtiene la regla activa para una playlist inteligente."""
    rules = get_rules_for_playlist(conn, playlist_id)
    return rules[0] if rules else None

def remove_rules_from_playlist(conn, playlist_id):
    """Elimina todas las reglas de una playlist."""
    sql = 'DELETE FROM rules WHERE playlist_id=?'
    cur = conn.cursor()
    try:
        cur.execute(sql, (playlist_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error al eliminar reglas de playlist {playlist_id}: {e}")
        return False

# --- Funciones adicionales para Smart Playlists ---

def get_smart_playlist_by_name(conn, name):
    """Obtiene una playlist inteligente por su nombre."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM smart_playlists WHERE name=?", (name,))
    row = cur.fetchone()
    # Convertir la tupla a un diccionario para facilitar el acceso
    if row:
        keys = [description[0] for description in cur.description]
        return dict(zip(keys, row))
    return None

# --- Operaciones CRUD para Tracks (Ejemplos iniciales) ---

def add_track(conn, track_data: dict):
    """Añade una nueva pista a la base de datos."""
    # track_data es un diccionario con claves que coinciden con las columnas de 'tracks'
    # Es importante manejar la conversion de tipos y valores por defecto aquí si es necesario.
    # Ejemplo: file_path es obligatorio.
    if not track_data.get('file_path'):
        print("Error: file_path es obligatorio para añadir una pista.")
        return None

    # Serializar campos JSON si existen
    data_to_insert = track_data.copy()
    if 'enriched_genres' in data_to_insert and data_to_insert['enriched_genres'] is not None:
        data_to_insert['enriched_genres'] = json.dumps(data_to_insert['enriched_genres'])
    if 'enrichment_sources' in data_to_insert and data_to_insert['enrichment_sources'] is not None:
        data_to_insert['enrichment_sources'] = json.dumps(data_to_insert['enrichment_sources'])

    placeholders = ', '.join(['?'] * len(data_to_insert))
    columns = ', '.join(data_to_insert.keys())
    sql = f"INSERT INTO tracks({columns}) VALUES({placeholders})"
    cur = conn.cursor()
    try:
        cur.execute(sql, list(data_to_insert.values()))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        # Podría ser por path UNIQUE constraint
        print(f"Error de integridad al añadir pista (¿duplicada?): {e}")
        return None
    except sqlite3.Error as e:
        print(f"Error al añadir pista: {e}")
        return None

def get_all_tracks(conn, limit=100, offset=0):
    """Obtiene todas las pistas, con paginación opcional."""
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM tracks ORDER BY artist, album, track_number LIMIT {limit} OFFSET {offset}")
    rows = cur.fetchall()
    tracks = []
    if rows:
        keys = [description[0] for description in cur.description]
        for row in rows:
            tracks.append(dict(zip(keys, row)))
    return tracks

def get_track_by_id(conn, track_id):
    """Obtiene una pista por su ID."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM tracks WHERE track_id=?", (track_id,))
    row = cur.fetchone()
    if row:
        keys = [description[0] for description in cur.description]
        return dict(zip(keys, row))
    return None

def update_track(conn, track_id, **track_data):
    """Actualiza una pista existente. track_data es un diccionario de campos a actualizar."""
    if not track_data:
        # print("No hay datos para actualizar el track.")
        return True # Considerar True si no hay nada que hacer, o False.

    fields_to_update = []
    params = []
    for key, value in track_data.items():
        fields_to_update.append(f"{key} = ?")
        # Serializar campos JSON si se están actualizando
        if key == 'enriched_genres' and value is not None:
            params.append(json.dumps(value))
        elif key == 'enrichment_sources' and value is not None:
            params.append(json.dumps(value))
        else:
            params.append(value)
    
    if not fields_to_update:
        return True # No debería ocurrir si track_data no está vacío, pero por si acaso.

    sql = f"UPDATE tracks SET {', '.join(fields_to_update)} WHERE track_id = ?"
    params.append(track_id)

    cur = conn.cursor()
    try:
        cur.execute(sql, tuple(params))
        conn.commit()
        return cur.rowcount > 0 # True si se actualizó al menos una fila
    except sqlite3.Error as e:
        print(f"Error al actualizar track {track_id}: {e}")
        return False

def delete_track(conn, track_id):
    """Elimina una pista de la base de datos."""
    sql = 'DELETE FROM tracks WHERE track_id=?'
    cur = conn.cursor()
    try:
        cur.execute(sql, (track_id,))
        conn.commit()
        return cur.rowcount > 0 # True si se eliminó al menos una fila
    except sqlite3.Error as e:
        print(f"Error al eliminar track {track_id}: {e}")
        return False

# --- Operaciones CRUD para Playlist Tracks (Resultados de Evaluación) ---

def clear_playlist_tracks(conn, playlist_id):
    """Elimina todas las entradas de pistas para una playlist_id específica en playlist_tracks."""
    sql = 'DELETE FROM playlist_tracks WHERE playlist_id=?'
    cur = conn.cursor()
    try:
        cur.execute(sql, (playlist_id,))
        conn.commit()
        return cur.rowcount >= 0 # Devuelve True si se ejecutó sin error (0 o más filas afectadas)
    except sqlite3.Error as e:
        print(f"Error al limpiar tracks de playlist {playlist_id}: {e}")
        return False # Indicar error

def add_track_to_playlist_results(conn, playlist_id, track_id, rank=None):
    """Añade una pista a los resultados de una playlist inteligente."""
    sql = ''' INSERT INTO playlist_tracks(playlist_id, track_id, rank_in_playlist, added_at)
              VALUES(?,?,?,?)
    '''
    cur = conn.cursor()
    try:
        cur.execute(sql, (playlist_id, track_id, rank, datetime.now()))
        conn.commit() # Añadido commit para uso standalone
        return cur.lastrowid
    except sqlite3.IntegrityError:
        # Dejar que IntegrityError se propague para que los tests puedan capturarla
        raise
    except sqlite3.Error as e:
        print(f"Error al añadir track {track_id} a playlist {playlist_id}: {e}")
        return None

def get_tracks_for_playlist_results(conn, playlist_id, limit=None, offset=None):
    """Obtiene las pistas asociadas a una playlist inteligente desde playlist_tracks, uniéndose a tracks."""
    cur = conn.cursor()
    sql = """
    SELECT t.*, pt.rank_in_playlist 
    FROM tracks t
    JOIN playlist_tracks pt ON t.track_id = pt.track_id
    WHERE pt.playlist_id = ?
    ORDER BY pt.rank_in_playlist ASC, t.title ASC
    """
    params = [playlist_id]
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    if offset is not None:
        sql += " OFFSET ?"
        params.append(offset)
    
    cur.execute(sql, params)
    rows = cur.fetchall()
    tracks = []
    if rows:
        keys = [description[0] for description in cur.description]
        for row in rows:
            tracks.append(dict(zip(keys, row)))
    return tracks

def get_tracks_for_playlist(conn, playlist_id, limit=None, offset=None):
    """Obtiene las pistas asociadas a una playlist inteligente desde playlist_tracks, uniéndose a tracks."""
    cur = conn.cursor()
    sql = """
    SELECT t.* 
    FROM tracks t
    JOIN playlist_tracks pt ON t.track_id = pt.track_id
    WHERE pt.playlist_id = ?
    ORDER BY pt.rank_in_playlist ASC, t.title ASC
    """
    params = [playlist_id]
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    if offset is not None:
        sql += " OFFSET ?"
        params.append(offset)
    
    cur.execute(sql, params)
    rows = cur.fetchall()
    tracks = []
    if rows:
        keys = [description[0] for description in cur.description]
        for row in rows:
            tracks.append(dict(zip(keys, row)))
    return tracks

# --- Funciones para Carga de Datos de Prueba ---

def populate_sample_data(conn):
    """
    Puebla la base de datos con datos de ejemplo si está vacía.
    Incluye pistas, una playlist inteligente y reglas.
    """
    sample_tracks_data = [
        {
            'file_path': '/audio/track1.mp3', 'file_hash': 'hash1', 'title': 'Bohemian Rhapsody', 
            'artist': 'Queen', 'album': 'A Night at the Opera', 'genre': 'Rock', 
            'year': 1975, 'duration_seconds': 354, 'bpm': 71, 'rating': 5,
            'key': 'Bb', 'camelot_key': '6B'
        },
        {
            'file_path': '/audio/track2.mp3', 'file_hash': 'hash2', 'title': 'Stairway to Heaven', 
            'artist': 'Led Zeppelin', 'album': 'Led Zeppelin IV', 'genre': 'Rock', 
            'year': 1971, 'duration_seconds': 482, 'bpm': 63, 'rating': 5,
            'key': 'Am', 'camelot_key': '8A'
        },
        {
            'file_path': '/audio/track3.flac', 'file_hash': 'hash3', 'title': 'So What', 
            'artist': 'Miles Davis', 'album': 'Kind of Blue', 'genre': 'Jazz', 
            'year': 1959, 'duration_seconds': 562, 'bpm': 136, 'rating': 5,
            'key': 'Dm', 'camelot_key': '7A'
        },
        {
            'file_path': '/audio/track4.aac', 'file_hash': 'hash4', 'title': 'One More Time', 
            'artist': 'Daft Punk', 'album': 'Discovery', 'genre': 'Electronic', 
            'year': 2000, 'duration_seconds': 320, 'bpm': 123, 'rating': 4,
            'key': 'E', 'camelot_key': '12B'
        },
        {
            'file_path': '/audio/track5.ogg', 'file_hash': 'hash5', 'title': 'The Real Slim Shady', 
            'artist': 'Eminem', 'album': 'The Marshall Mathers LP', 'genre': 'Hip Hop', 
            'year': 2000, 'duration_seconds': 284, 'bpm': 104, 'rating': 4,
            'key': 'Gm', 'camelot_key': '6A'
        },
        {
            'file_path': '/audio/track6.mp3', 'file_hash': 'hash6', 'title': 'Uptown Funk',
            'artist': 'Mark Ronson ft. Bruno Mars', 'album': 'Uptown Special', 'genre': 'Funk',
            'year': 2014, 'duration_seconds': 270, 'bpm': 115, 'rating': 5,
            'key': 'Dm', 'camelot_key': '7A'
        },
        {
            'file_path': '/audio/track7.mp3', 'file_hash': 'hash7', 'title': 'Wonderwall',
            'artist': 'Oasis', 'album': '(What\'s the Story) Morning Glory?', 'genre': 'Britpop',
            'year': 1995, 'duration_seconds': 258, 'bpm': 174, 'rating': 4,
            'key': 'F#m', 'camelot_key': '11A'
        },
        {
            'file_path': '/audio/track8.flac', 'file_hash': 'hash8', 'title': 'Take Five',
            'artist': 'Dave Brubeck Quartet', 'album': 'Time Out', 'genre': 'Jazz',
            'year': 1959, 'duration_seconds': 324, 'bpm': 172, 'rating': 5,
            'key': 'Ebm', 'camelot_key': '2A'
        },
        {
            'file_path': '/audio/track9.mp3', 'file_hash': 'hash9', 'title': 'Billie Jean',
            'artist': 'Michael Jackson', 'album': 'Thriller', 'genre': 'Pop',
            'year': 1982, 'duration_seconds': 294, 'bpm': 117, 'rating': 5,
            'key': 'F#m', 'camelot_key': '11A'
        },
        {
            'file_path': '/audio/track10.mp3', 'file_hash': 'hash10', 'title': 'Smells Like Teen Spirit',
            'artist': 'Nirvana', 'album': 'Nevermind', 'genre': 'Grunge',
            'year': 1991, 'duration_seconds': 301, 'bpm': 117, 'rating': 5,
            'key': 'F', 'camelot_key': '7B'
        },
        # Añadir más tracks para tener mejor variedad de tonalidades
        {
            'file_path': '/audio/track11.mp3', 'file_hash': 'hash11', 'title': 'Hotel California',
            'artist': 'Eagles', 'album': 'Hotel California', 'genre': 'Rock',
            'year': 1976, 'duration_seconds': 391, 'bpm': 75, 'rating': 5,
            'key': 'Bm', 'camelot_key': '10A'
        },
        {
            'file_path': '/audio/track12.mp3', 'file_hash': 'hash12', 'title': 'Sweet Child O\' Mine',
            'artist': 'Guns N\' Roses', 'album': 'Appetite for Destruction', 'genre': 'Rock',
            'year': 1987, 'duration_seconds': 356, 'bpm': 125, 'rating': 5,
            'key': 'D', 'camelot_key': '10B'
        },
        {
            'file_path': '/audio/track13.mp3', 'file_hash': 'hash13', 'title': 'Thriller',
            'artist': 'Michael Jackson', 'album': 'Thriller', 'genre': 'Pop',
            'year': 1982, 'duration_seconds': 357, 'bpm': 118, 'rating': 5,
            'key': 'C#m', 'camelot_key': '12A'
        },
        {
            'file_path': '/audio/track14.mp3', 'file_hash': 'hash14', 'title': 'Superstition',
            'artist': 'Stevie Wonder', 'album': 'Talking Book', 'genre': 'Funk',
            'year': 1972, 'duration_seconds': 245, 'bpm': 100, 'rating': 5,
            'key': 'Ebm', 'camelot_key': '2A'
        },
        {
            'file_path': '/audio/track15.mp3', 'file_hash': 'hash15', 'title': 'Blue Train',
            'artist': 'John Coltrane', 'album': 'Blue Train', 'genre': 'Jazz',
            'year': 1957, 'duration_seconds': 623, 'bpm': 140, 'rating': 5,
            'key': 'Bb', 'camelot_key': '6B'
        }
    ]
    
    print("Poblando tabla 'tracks' con datos de ejemplo...")
    cur = conn.cursor()
    for track_data in sample_tracks_data:
        try:
            # Verificar si la pista ya existe por su file_path
            cur.execute("SELECT track_id FROM tracks WHERE file_path = ?", (track_data['file_path'],))
            existing_track = cur.fetchone()
            if not existing_track:
                add_track(conn, track_data)
        except sqlite3.Error as e:
            print(f"Error al insertar pista de ejemplo {track_data.get('title')}: {e}")
    print("Datos de ejemplo para 'tracks' poblados.")

    # Crear una playlist inteligente de ejemplo
    playlist_name = "Awesome Rock"
    playlist_description = "Las mejores canciones de rock de todos los tiempos"
    
    # Verificar si la playlist ya existe
    existing_playlist = get_smart_playlist_by_name(conn, playlist_name)
    playlist_id = None

    if not existing_playlist:
        playlist_id = create_smart_playlist(conn, playlist_name, playlist_description)
        if playlist_id:
            print(f"Playlist inteligente '{playlist_name}' creada con ID: {playlist_id}")
            # Añadir una regla de ejemplo
            rule_text = "genre = 'Rock' AND rating >= 4"
            rule_id = add_rule_to_playlist(conn, playlist_id, rule_text)
            if rule_id:
                print(f"Regla '{rule_text}' añadida a la playlist {playlist_id}")
            else:
                print(f"Error al añadir regla a la playlist {playlist_id}")
        else:
            print(f"Error al crear playlist inteligente '{playlist_name}'")
    else:
        playlist_id = existing_playlist['playlist_id']
        print(f"Playlist inteligente '{playlist_name}' ya existe con ID: {playlist_id}. No se creará de nuevo.")

    # Podrías añadir más datos de ejemplo para otras tablas aquí si es necesario.
    print("Datos de ejemplo poblados (o verificados).")


def populate_sample_tracks(conn):
    """Alias para populate_sample_data para compatibilidad."""
    return populate_sample_data(conn)

# --- Ejemplo de uso (para probar las funciones) ---
if __name__ == '__main__':
    db_file = "nueva_biblioteca.db" # Asegúrate que este archivo exista o se cree por database_setup.py

    # Es recomendable ejecutar database_setup.py primero si la db no existe.
    # from database_setup import setup_database
    # setup_database(db_file) # Descomentar si necesitas crear la DB y tablas

    conn = create_connection(db_file)

    if conn:
        print("\n--- Poblando con datos de ejemplo (si es necesario) ---")
        populate_sample_data(conn)

        print("\n--- Probando CRUD de Smart Playlists ---")
        # Crear playlist
        playlist_name = "Mi Playlist de Prueba"
        playlist_id = create_smart_playlist(conn, playlist_name, "Una descripción de prueba")
        if playlist_id:
            print(f"Playlist '{playlist_name}' creada con ID: {playlist_id}")

            # Obtener playlist por ID
            pl = get_smart_playlist_by_id(conn, playlist_id)
            print(f"Playlist obtenida: {pl}")

            # Actualizar playlist
            update_success = update_smart_playlist(conn, playlist_id, name="Nombre Actualizado de Playlist", description="Nueva descripción.")
            if update_success:
                print(f"Playlist {playlist_id} actualizada.")
                pl_updated = get_smart_playlist_by_id(conn, playlist_id)
                print(f"Playlist actualizada: {pl_updated}")
            else:
                print(f"Fallo al actualizar playlist {playlist_id}")

        # Listar todas las playlists
        all_playlists = get_all_smart_playlists(conn)
        print(f"Todas las playlists ({len(all_playlists)}):")
        for p in all_playlists:
            print(f"  ID: {p['playlist_id']}, Nombre: {p['name']}, Descripción: {p['description']}")

        print("\n--- Probando CRUD de Rules ---")
        if playlist_id: # Solo si la playlist se creó
            rule_expr = "genre = 'Rock' AND bpm > 100"
            rule_id = add_rule_to_playlist(conn, playlist_id, rule_expr)
            if rule_id:
                print(f"Regla añadida/actualizada para playlist {playlist_id} con ID de regla: {rule_id}")
                rule_obj = get_rule_for_playlist(conn, playlist_id)
                print(f"Regla obtenida: {rule_obj}")
            else:
                print(f"Fallo al añadir/actualizar regla para playlist {playlist_id}")

        print("\n--- Probando CRUD de Tracks (Básico) ---")
        # Añadir un track de ejemplo
        # En una aplicación real, file_hash se calcularía y más campos se llenarían.
        sample_track_data_1 = {
            'file_path': '/music/sample1.mp3',
            'title': 'Canción de Prueba 1',
            'artist': 'Artista de Prueba',
            'album': 'Álbum de Prueba',
            'genre': 'Rock',
            'year': 2023,
            'bpm': 120
        }
        track_id_1 = add_track(conn, sample_track_data_1)
        if track_id_1:
            print(f"Track '{sample_track_data_1['title']}' añadido con ID: {track_id_1}")
            retrieved_track = get_track_by_id(conn, track_id_1)
            print(f"Track obtenido por ID: {retrieved_track}")

        sample_track_data_2 = {
            'file_path': '/music/sample2.flac',
            'title': 'Otro Tema',
            'artist': 'Otro Artista',
            'album': 'Otro Álbum',
            'genre': 'Pop',
            'year': 2022,
            'bpm': 98
        }
        track_id_2 = add_track(conn, sample_track_data_2)
        if track_id_2:
            print(f"Track '{sample_track_data_2['title']}' añadido con ID: {track_id_2}")

        all_tracks_sample = get_all_tracks(conn, limit=5)
        print(f"Algunas pistas ({len(all_tracks_sample)}):")
        for t in all_tracks_sample:
            print(f"  ID: {t['track_id']}, Título: {t['title']}, Artista: {t['artist']}")


        # Ejemplo de limpieza (opcional, para mantener la DB limpia entre pruebas)
        # print("\n--- Limpiando datos de prueba ---")
        # if playlist_id:
        #     delete_success = delete_smart_playlist(conn, playlist_id) # Esto debería eliminar reglas y playlist_tracks por CASCADE
        #     print(f"Playlist {playlist_id} eliminada: {delete_success}")
        # if track_id_1:
        #     # Necesitaríamos una función delete_track(conn, track_id)
        #     pass 

        conn.close()
        print("\nConexión cerrada.")
    else:
        print("No se pudo conectar a la base de datos para probar CRUD.") 
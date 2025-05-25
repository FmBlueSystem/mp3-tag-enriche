import sqlite3
import os
# Importar la función de poblado desde crud.py
# Esto asume que crud.py está en el mismo directorio o accesible vía PYTHONPATH
from . import crud # Usar import relativo si están en el mismo paquete 'data'

# Definir la ruta de la base de datos como constante exportable
# Determinar la raíz del proyecto asumiendo que este script está en src/data/
_current_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_script_dir, "..", ".."))
DB_FILE = os.path.join(_project_root, "data", "music_library.db")

def create_connection(db_file):
    """Crea una conexión a la base de datos SQLite especificada por db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"SQLite version: {sqlite3.sqlite_version}")
        print(f"Conectado a {db_file}")
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    """Crea una tabla a partir de la declaración create_table_sql."""
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)

def setup_database(db_file):
    """Crea todas las tablas necesarias en la base de datos."""

    # Asegurarse que el directorio de la base de datos exista
    db_dir = os.path.dirname(db_file)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir)
            print(f"Directorio {db_dir} creado.")
        except OSError as e:
            print(f"Error al crear directorio {db_dir}: {e}")
            return # No continuar si no se puede crear el directorio

    sql_create_tracks_table = '''
    CREATE TABLE IF NOT EXISTS tracks (
        track_id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE NOT NULL,
        file_hash TEXT NOT NULL,
        title TEXT,
        artist TEXT,
        album_artist TEXT,
        album TEXT,
        genre TEXT,
        year INTEGER,
        track_number INTEGER,
        total_tracks_in_album INTEGER,
        disc_number INTEGER,
        total_discs_in_album INTEGER,
        duration_seconds REAL,
        bpm REAL,
        key TEXT,
        camelot_key TEXT,
        energy INTEGER,
        rating INTEGER,
        play_count INTEGER DEFAULT 0,
        last_played_at TIMESTAMP,
        date_added_to_library TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_metadata_update_at TIMESTAMP,
        last_modified_file_timestamp TIMESTAMP,
        bitrate_kbps INTEGER,
        sample_rate_hz INTEGER,
        channels INTEGER,
        comment TEXT,
        lyrics TEXT
    );'''

    sql_create_smart_playlists_table = '''
    CREATE TABLE IF NOT EXISTS smart_playlists (
        playlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP,
        last_generated_at TIMESTAMP,
        is_enabled BOOLEAN DEFAULT TRUE,
        target_track_count INTEGER,
        sort_field TEXT,
        sort_order TEXT DEFAULT "ASC"
    );'''

    sql_create_rules_table = '''
    CREATE TABLE IF NOT EXISTS rules (
        rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
        playlist_id INTEGER NOT NULL,
        expression_text TEXT NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (playlist_id) REFERENCES smart_playlists (playlist_id) ON DELETE CASCADE
    );'''

    sql_create_playlist_tracks_table = '''
    CREATE TABLE IF NOT EXISTS playlist_tracks (
        playlist_track_id INTEGER PRIMARY KEY AUTOINCREMENT,
        playlist_id INTEGER NOT NULL,
        track_id INTEGER NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        rank_in_playlist INTEGER,
        FOREIGN KEY (playlist_id) REFERENCES smart_playlists (playlist_id) ON DELETE CASCADE,
        FOREIGN KEY (track_id) REFERENCES tracks (track_id) ON DELETE CASCADE,
        UNIQUE (playlist_id, track_id)
    );'''

    sql_create_templates_table = '''
    CREATE TABLE IF NOT EXISTS templates (
        template_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        rule_expression_text TEXT NOT NULL,
        category TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_system_template BOOLEAN DEFAULT FALSE
    );'''

    sql_create_triggers_table = '''
    CREATE TABLE IF NOT EXISTS triggers (
        trigger_id INTEGER PRIMARY KEY AUTOINCREMENT,
        playlist_id INTEGER,
        name TEXT NOT NULL,
        trigger_type TEXT NOT NULL,
        config_json TEXT NOT NULL,
        is_enabled BOOLEAN DEFAULT TRUE,
        last_fired_at TIMESTAMP,
        last_successful_run_at TIMESTAMP,
        last_error_at TIMESTAMP,
        last_error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (playlist_id) REFERENCES smart_playlists (playlist_id) ON DELETE CASCADE
    );'''

    sql_create_app_config_table = '''
    CREATE TABLE IF NOT EXISTS app_config (
        config_key TEXT PRIMARY KEY NOT NULL,
        config_value TEXT,
        description TEXT,
        data_type TEXT DEFAULT "TEXT",
        is_user_configurable BOOLEAN DEFAULT TRUE,
        updated_at TIMESTAMP
    );'''

    # Crear conexión a la base de datos
    conn = create_connection(db_file)

    # Crear tablas
    if conn is not None:
        create_table(conn, sql_create_tracks_table)
        create_table(conn, sql_create_smart_playlists_table)
        create_table(conn, sql_create_rules_table)
        create_table(conn, sql_create_playlist_tracks_table)
        create_table(conn, sql_create_templates_table)
        create_table(conn, sql_create_triggers_table)
        create_table(conn, sql_create_app_config_table)
        print(f"Tablas creadas exitosamente en {db_file}")

        # Poblar tracks de ejemplo si la tabla está vacía
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tracks")
            count = cursor.fetchone()[0]
            if count == 0:
                print("La tabla 'tracks' está vacía. Poblando con datos de ejemplo...")
                crud.populate_sample_tracks(conn) # Llamar a la función importada
                print("Datos de ejemplo para 'tracks' poblados.")
            else:
                print(f"La tabla 'tracks' ya contiene {count} registros.")
        except sqlite3.Error as e:
            print(f"Error al verificar o poblar la tabla 'tracks': {e}")
        
        conn.close()
    else:
        print("Error! No se pudo crear la conexión a la base de datos.")

if __name__ == '__main__':
    # Ejemplo de uso: crea una base de datos llamada 'music_library.db'
    # en un directorio 'data' relativo a la raíz del proyecto.
    
    print(f"Intentando configurar la base de datos en: {DB_FILE}")
    setup_database(DB_FILE) 
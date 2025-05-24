import sqlite3
import logging
from pathlib import Path

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DBManager:
    """
    Gestiona la conexión y las operaciones de la base de datos SQLite para la aplicación.

    Atributos:
        db_path (Path): Ruta al archivo de la base de datos SQLite.
        conn (sqlite3.Connection): Objeto de conexión a la base de datos.
    """

    def __init__(self, db_name: str = "music_organization.db"):
        """
        Inicializa el gestor de la base de datos.

        Args:
            db_name (str): Nombre del archivo de la base de datos.
        """
        self.db_path = Path("data") / db_name
        self.conn = None
        self._ensure_data_directory_exists()
        self.connect()
        self.create_tables()

    def _ensure_data_directory_exists(self):
        """Asegura que el directorio 'data' exista."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logging.info(f"Directorio de datos '{self.db_path.parent}' asegurado.")

    def connect(self):
        """
        Establece la conexión con la base de datos SQLite.
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row # Permite acceder a las columnas por nombre
            logging.info(f"Conexión a la base de datos '{self.db_path}' establecida exitosamente.")
        except sqlite3.Error as e:
            logging.error(f"Error al conectar a la base de datos: {e}")
            self.conn = None

    def close(self):
        """
        Cierra la conexión con la base de datos.
        """
        if self.conn:
            self.conn.close()
            logging.info(f"Conexión a la base de datos '{self.db_path}' cerrada.")

    def execute_query(self, query: str, params: tuple = ()) -> bool:
        """
        Ejecuta una consulta SQL (INSERT, UPDATE, DELETE).

        Args:
            query (str): La consulta SQL a ejecutar.
            params (tuple): Parámetros para la consulta.

        Returns:
            bool: True si la consulta se ejecutó con éxito, False en caso contrario.
        """
        if not self.conn:
            logging.error("No hay conexión a la base de datos para ejecutar la consulta.")
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            logging.info(f"Consulta ejecutada exitosamente: {query[:100]}...")
            return True
        except sqlite3.Error as e:
            logging.error(f"Error al ejecutar la consulta '{query[:100]}...': {e}")
            return False

    def fetch_query(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """
        Ejecuta una consulta SQL (SELECT) y devuelve los resultados.

        Args:
            query (str): La consulta SQL a ejecutar.
            params (tuple): Parámetros para la consulta.

        Returns:
            list[sqlite3.Row]: Lista de filas resultantes de la consulta.
        """
        if not self.conn:
            logging.error("No hay conexión a la base de datos para obtener resultados.")
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error al obtener resultados de la consulta '{query[:100]}...': {e}")
            return []

    def create_tables(self):
        """
        Crea las tablas necesarias en la base de datos si no existen.
        """
        if not self.conn:
            logging.error("No hay conexión a la base de datos para crear tablas.")
            return

        # Tabla para almacenar información de los tracks musicales
        tracks_table_query = """
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT NOT NULL UNIQUE,
            title TEXT,
            artist TEXT,
            album TEXT,
            genre TEXT,
            year INTEGER,
            bpm REAL,
            key TEXT,
            energy_level INTEGER,
            rating INTEGER,
            play_count INTEGER,
            last_played TEXT,
            date_added TEXT,
            checksum TEXT UNIQUE
        );
        """

        # Tabla para almacenar las playlists inteligentes
        smart_playlists_table_query = """
        CREATE TABLE IF NOT EXISTS smart_playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            rules TEXT NOT NULL, -- JSON o formato de texto para las reglas
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """

        # Tabla para almacenar el historial de sincronización/cambios
        sync_history_table_query = """
        CREATE TABLE IF NOT EXISTS sync_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL, -- ej. 'scan', 'metadata_update', 'file_move'
            details TEXT -- JSON o texto con detalles del evento
        );
        """

        # Tabla para almacenar la configuración de la aplicación
        config_table_query = """
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """

        tables = [
            tracks_table_query,
            smart_playlists_table_query,
            sync_history_table_query,
            config_table_query
        ]

        for query in tables:
            if not self.execute_query(query):
                logging.error(f"Fallo al crear tabla con consulta: {query[:50]}...")
                return

        logging.info("Tablas de la base de datos verificadas/creadas exitosamente.")

if __name__ == "__main__":
    # Ejemplo de uso
    db_manager = DBManager("test_music_db.db")

    # Insertar un track
    if db_manager.execute_query(
        "INSERT INTO tracks (filepath, title, artist, genre, year) VALUES (?, ?, ?, ?, ?)",
        ("/path/to/song.mp3", "Song Title", "Artist Name", "Pop", 2023)
    ):
        logging.info("Track insertado.")

    # Consultar tracks
    tracks = db_manager.fetch_query("SELECT * FROM tracks")
    for track in tracks:
        logging.info(f"Track: {track['title']} by {track['artist']}")

    # Insertar una playlist inteligente
    rules_json = '{"genre": "Electronic", "bpm_min": 120, "bpm_max": 130}'
    if db_manager.execute_query(
        "INSERT INTO smart_playlists (name, rules) VALUES (?, ?)",
        ("My Electronic Playlist", rules_json)
    ):
        logging.info("Playlist inteligente insertada.")

    # Consultar playlists
    playlists = db_manager.fetch_query("SELECT * FROM smart_playlists")
    for playlist in playlists:
        logging.info(f"Playlist: {playlist['name']} with rules: {playlist['rules']}")

    db_manager.close()

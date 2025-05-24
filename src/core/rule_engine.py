import json
import re
import logging
from typing import List, Dict, Any, Callable, Union

from src.core.database.db_manager import DBManager
from src.core.database.models import Track

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RuleEngine:
    """
    Motor de reglas lógicas para filtrar tracks musicales.
    Permite construir y evaluar reglas complejas sobre los metadatos de los tracks.
    """

    def __init__(self, db_manager: DBManager):
        """
        Inicializa el motor de reglas con una instancia de DBManager.

        Args:
            db_manager (DBManager): Gestor de la base de datos para acceder a los tracks.
        """
        self.db_manager = db_manager
        self.operators = {
            '=': lambda a, b: str(a).lower() == str(b).lower(),
            '!=': lambda a, b: str(a).lower() != str(b).lower(),
            '>': lambda a, b: float(a) > float(b),
            '<': lambda a, b: float(a) < float(b),
            '>=': lambda a, b: float(a) >= float(b),
            '<=': lambda a, b: float(a) <= float(b),
            'IN': lambda a, b: str(a).lower() in [x.lower() for x in b],
            'NOT IN': lambda a, b: str(a).lower() not in [x.lower() for x in b],
            'CONTAINS': lambda a, b: str(b).lower() in str(a).lower(),
            'NOT CONTAINS': lambda a, b: str(b).lower() not in str(a).lower(),
            'BETWEEN': lambda a, b: float(b[0]) <= float(a) <= float(b[1])
        }
        self.logical_operators = {
            'AND': lambda *args: all(args),
            'OR': lambda *args: any(args),
            'NOT': lambda arg: not arg
        }
        self.supported_fields = [
            'title', 'artist', 'album', 'genre', 'year', 'bpm', 'key',
            'energy_level', 'rating', 'play_count'
        ]

    def _evaluate_condition(self, track: Track, field: str, operator: str, value: Any) -> bool:
        """
        Evalúa una condición simple para un track dado.

        Args:
            track (Track): El objeto Track a evaluar.
            field (str): El campo del track a comparar.
            operator (str): El operador de comparación (ej. '=', '>', 'IN').
            value (Any): El valor con el que comparar.

        Returns:
            bool: True si la condición se cumple, False en caso contrario.
        """
        if field not in self.supported_fields:
            logger.warning(f"Campo '{field}' no soportado para evaluación de reglas.")
            return False

        track_value = getattr(track, field, None)

        if operator == 'BETWEEN':
            if not isinstance(value, list) or len(value) != 2:
                logger.error(f"Valor para 'BETWEEN' debe ser una lista de 2 elementos: {value}")
                return False
            try:
                return self.operators[operator](track_value, [float(v) for v in value])
            except (ValueError, TypeError):
                return False # No se puede convertir a float
        
        op_func = self.operators.get(operator)
        if not op_func:
            logger.error(f"Operador '{operator}' no reconocido.")
            return False
        
        # Manejo de tipos para comparación
        if isinstance(track_value, (int, float)) and isinstance(value, (int, float, str)):
            try:
                return op_func(track_value, float(value))
            except ValueError:
                return False # No se puede convertir a float
        elif isinstance(track_value, str) and isinstance(value, (str, list)):
            return op_func(track_value, value)
        elif track_value is None:
            # Si el valor del track es None, solo se cumple si el operador es != y el valor es None, o si el operador es = y el valor no es None
            if operator == '=':
                return value is None
            elif operator == '!=':
                return value is not None
            return False
        
        return False # Tipos no compatibles o caso no manejado

    def _parse_rule_expression(self, expression: str) -> Dict[str, Any]:
        """
        Parsea una expresión de regla en formato de cadena a una estructura de diccionario.
        Soporta operadores lógicos y paréntesis.
        Ej: "genre = 'Rock' AND (bpm > 120 OR year = 2020)"
        """
        # Simplificación: Asumimos que la expresión ya viene en un formato estructurado (JSON)
        # o que es una expresión simple que se puede convertir.
        # Para un parser completo de expresiones complejas, se necesitaría una librería como pyparsing o una implementación de shunting-yard.
        # Por ahora, se espera un formato JSON para reglas complejas o una cadena simple para reglas básicas.
        try:
            parsed_rule = json.loads(expression)
            return parsed_rule
        except json.JSONDecodeError:
            # Si no es JSON, intentar parsear como una regla simple
            match = re.match(r"(\w+)\s*([<>=!]+|IN|NOT IN|CONTAINS|NOT CONTAINS|BETWEEN)\s*(.*)", expression, re.IGNORECASE)
            if match:
                field, op, val_str = match.groups()
                op = op.upper()
                value = val_str.strip().strip("'\"")
                if op in ['IN', 'NOT IN', 'BETWEEN']:
                    value = [x.strip().strip("'\"") for x in value.split(',')]
                return {"field": field, "operator": op, "value": value}
            else:
                raise ValueError(f"Formato de regla no soportado: {expression}")

    def evaluate_rules(self, track: Track, rules: Union[str, Dict[str, Any]]) -> bool:
        """
        Evalúa un conjunto de reglas para un track dado.
        Las reglas pueden ser una cadena JSON o un diccionario estructurado.

        Args:
            track (Track): El objeto Track a evaluar.
            rules (Union[str, Dict[str, Any]]): Las reglas a aplicar.
                                                Puede ser una cadena JSON de reglas complejas
                                                o un diccionario de reglas.

        Returns:
            bool: True si el track cumple todas las reglas, False en caso contrario.
        """
        if isinstance(rules, str):
            try:
                rules_dict = json.loads(rules)
            except json.JSONDecodeError:
                logger.error(f"Reglas no válidas (no es JSON): {rules}")
                return False
        else:
            rules_dict = rules

        if "operator" in rules_dict and "field" in rules_dict: # Regla simple
            return self._evaluate_condition(
                track,
                rules_dict["field"],
                rules_dict["operator"],
                rules_dict["value"]
            )
        elif "logical_operator" in rules_dict and "conditions" in rules_dict: # Regla compuesta
            op = rules_dict["logical_operator"].upper()
            conditions = rules_dict["conditions"]
            
            if op == 'NOT':
                if not conditions or not isinstance(conditions, dict):
                    logger.error("La condición 'NOT' debe tener una única sub-condición en formato de diccionario.")
                    return False
                return self.logical_operators['NOT'](self.evaluate_rules(track, conditions))
            
            results = [self.evaluate_rules(track, cond) for cond in conditions]
            logical_op_func = self.logical_operators.get(op)
            if not logical_op_func:
                logger.error(f"Operador lógico '{op}' no reconocido.")
                return False
            return logical_op_func(*results)
        else:
            logger.error(f"Formato de reglas no válido: {rules_dict}")
            return False

    def get_matching_tracks(self, rules: Union[str, Dict[str, Any]]) -> List[Track]:
        """
        Obtiene una lista de tracks que cumplen con un conjunto de reglas.

        Args:
            rules (Union[str, Dict[str, Any]]): Las reglas a aplicar.

        Returns:
            List[Track]: Lista de objetos Track que cumplen las reglas.
        """
        all_tracks_data = self.db_manager.fetch_query("SELECT * FROM tracks")
        matching_tracks = []
        for row in all_tracks_data:
            track = Track.from_row(row)
            if self.evaluate_rules(track, rules):
                matching_tracks.append(track)
        return matching_tracks

    def save_smart_playlist(self, name: str, rules: Dict[str, Any], description: Optional[str] = None) -> bool:
        """
        Guarda una nueva playlist inteligente en la base de datos.

        Args:
            name (str): Nombre de la playlist.
            rules (Dict[str, Any]): Diccionario de reglas de la playlist.
            description (Optional[str]): Descripción de la playlist.

        Returns:
            bool: True si se guardó con éxito, False en caso contrario.
        """
        rules_json = json.dumps(rules)
        query = "INSERT INTO smart_playlists (name, rules, description) VALUES (?, ?, ?)"
        return self.db_manager.execute_query(query, (name, rules_json, description))

    def update_smart_playlist(self, playlist_id: int, name: Optional[str] = None,
                               rules: Optional[Dict[str, Any]] = None,
                               description: Optional[str] = None) -> bool:
        """
        Actualiza una playlist inteligente existente.

        Args:
            playlist_id (int): ID de la playlist a actualizar.
            name (Optional[str]): Nuevo nombre.
            rules (Optional[Dict[str, Any]]): Nuevas reglas.
            description (Optional[str]): Nueva descripción.

        Returns:
            bool: True si se actualizó con éxito, False en caso contrario.
        """
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if rules is not None:
            updates.append("rules = ?")
            params.append(json.dumps(rules))
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if not updates:
            return False # No hay nada que actualizar

        query = f"UPDATE smart_playlists SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        params.append(playlist_id)
        return self.db_manager.execute_query(query, tuple(params))

    def delete_smart_playlist(self, playlist_id: int) -> bool:
        """
        Elimina una playlist inteligente de la base de datos.

        Args:
            playlist_id (int): ID de la playlist a eliminar.

        Returns:
            bool: True si se eliminó con éxito, False en caso contrario.
        """
        query = "DELETE FROM smart_playlists WHERE id = ?"
        return self.db_manager.execute_query(query, (playlist_id,))

    def get_smart_playlist(self, playlist_id: int) -> Optional[SmartPlaylist]:
        """
        Obtiene una playlist inteligente por su ID.

        Args:
            playlist_id (int): ID de la playlist.

        Returns:
            Optional[SmartPlaylist]: Objeto SmartPlaylist si se encuentra, None en caso contrario.
        """
        query = "SELECT * FROM smart_playlists WHERE id = ?"
        row = self.db_manager.fetch_query(query, (playlist_id,))
        if row:
            return SmartPlaylist.from_row(row[0])
        return None

    def get_all_smart_playlists(self) -> List[SmartPlaylist]:
        """
        Obtiene todas las playlists inteligentes.

        Returns:
            List[SmartPlaylist]: Lista de objetos SmartPlaylist.
        """
        query = "SELECT * FROM smart_playlists"
        rows = self.db_manager.fetch_query(query)
        return [SmartPlaylist.from_row(row) for row in rows]

if __name__ == "__main__":
    # Ejemplo de uso del RuleEngine
    db_manager = DBManager("test_music_db.db")
    rule_engine = RuleEngine(db_manager)

    # Asegurarse de que haya algunos tracks en la DB para probar
    db_manager.execute_query("DELETE FROM tracks") # Limpiar para pruebas
    db_manager.execute_query(
        "INSERT INTO tracks (filepath, title, artist, genre, year, bpm, energy_level) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("/music/song1.mp3", "Bohemian Rhapsody", "Queen", "Rock", 1975, 144.0, 8)
    )
    db_manager.execute_query(
        "INSERT INTO tracks (filepath, title, artist, genre, year, bpm, energy_level) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("/music/song2.mp3", "Billie Jean", "Michael Jackson", "Pop", 1982, 117.0, 7)
    )
    db_manager.execute_query(
        "INSERT INTO tracks (filepath, title, artist, genre, year, bpm, energy_level) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("/music/song3.mp3", "Smells Like Teen Spirit", "Nirvana", "Grunge", 1991, 116.0, 9)
    )
    db_manager.execute_query(
        "INSERT INTO tracks (filepath, title, artist, genre, year, bpm, energy_level) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("/music/song4.mp3", "Shape of You", "Ed Sheeran", "Pop", 2017, 96.0, 6)
    )
    db_manager.execute_query(
        "INSERT INTO tracks (filepath, title, artist, genre, year, bpm, energy_level) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("/music/song5.mp3", "Hotel California", "Eagles", "Rock", 1976, 147.0, 7)
    )

    logger.info("\n--- Probando reglas simples ---")
    # Regla simple: género es Rock
    rock_rule = {"field": "genre", "operator": "=", "value": "Rock"}
    rock_tracks = rule_engine.get_matching_tracks(rock_rule)
    logger.info(f"Tracks de Rock ({len(rock_tracks)}): {[t.title for t in rock_tracks]}")

    # Regla simple: BPM mayor a 120
    fast_bpm_rule = {"field": "bpm", "operator": ">", "value": 120}
    fast_tracks = rule_engine.get_matching_tracks(fast_bpm_rule)
    logger.info(f"Tracks con BPM > 120 ({len(fast_tracks)}): {[t.title for t in fast_tracks]}")

    logger.info("\n--- Probando reglas compuestas (AND) ---")
    # Regla compuesta: género es Pop AND año es 2017
    pop_2017_rule = {
        "logical_operator": "AND",
        "conditions": [
            {"field": "genre", "operator": "=", "value": "Pop"},
            {"field": "year", "operator": "=", "value": 2017}
        ]
    }
    pop_2017_tracks = rule_engine.get_matching_tracks(pop_2017_rule)
    logger.info(f"Tracks Pop 2017 ({len(pop_2017_tracks)}): {[t.title for t in pop_2017_tracks]}")

    logger.info("\n--- Probando reglas compuestas (OR) ---")
    # Regla compuesta: género es Rock OR género es Grunge
    rock_grunge_rule = {
        "logical_operator": "OR",
        "conditions": [
            {"field": "genre", "operator": "=", "value": "Rock"},
            {"field": "genre", "operator": "=", "value": "Grunge"}
        ]
    }
    rock_grunge_tracks = rule_engine.get_matching_tracks(rock_grunge_rule)
    logger.info(f"Tracks Rock/Grunge ({len(rock_grunge_tracks)}): {[t.title for t in rock_grunge_tracks]}")

    logger.info("\n--- Probando reglas compuestas (NOT) ---")
    # Regla compuesta: NOT (género es Pop)
    not_pop_rule = {
        "logical_operator": "NOT",
        "conditions": {"field": "genre", "operator": "=", "value": "Pop"}
    }
    not_pop_tracks = rule_engine.get_matching_tracks(not_pop_rule)
    logger.info(f"Tracks NO Pop ({len(not_pop_tracks)}): {[t.title for t in not_pop_tracks]}")

    logger.info("\n--- Probando operador IN ---")
    # Regla: género IN (Pop, Rock)
    genres_in_rule = {"field": "genre", "operator": "IN", "value": ["Pop", "Rock"]}
    in_tracks = rule_engine.get_matching_tracks(genres_in_rule)
    logger.info(f"Tracks Pop o Rock (IN) ({len(in_tracks)}): {[t.title for t in in_tracks]}")

    logger.info("\n--- Probando operador BETWEEN ---")
    # Regla: año BETWEEN 1970 y 1980
    year_between_rule = {"field": "year", "operator": "BETWEEN", "value": [1970, 1980]}
    between_tracks = rule_engine.get_matching_tracks(year_between_rule)
    logger.info(f"Tracks entre 1970-1980 ({len(between_tracks)}): {[t.title for t in between_tracks]}")

    logger.info("\n--- Probando guardar y recuperar Smart Playlists ---")
    # Guardar una playlist inteligente
    playlist_rules = {
        "logical_operator": "AND",
        "conditions": [
            {"field": "genre", "operator": "IN", "value": ["Rock", "Grunge"]},
            {"field": "energy_level", "operator": ">=", "value": 8}
        ]
    }
    if rule_engine.save_smart_playlist("High Energy Rock/Grunge", playlist_rules, "Playlists de rock y grunge con alta energía"):
        logger.info("Playlist 'High Energy Rock/Grunge' guardada.")

    # Obtener todas las playlists
    all_playlists = rule_engine.get_all_smart_playlists()
    logger.info(f"Total Smart Playlists: {len(all_playlists)}")
    for pl in all_playlists:
        logger.info(f"  ID: {pl.id}, Nombre: {pl.name}, Reglas: {pl.rules}")
        # Evaluar la playlist guardada
        matching_saved_tracks = rule_engine.get_matching_tracks(pl.rules)
        logger.info(f"    Tracks que coinciden: {[t.title for t in matching_saved_tracks]}")

    # Actualizar una playlist
    if all_playlists:
        first_playlist_id = all_playlists[0].id
        new_rules = {
            "logical_operator": "AND",
            "conditions": [
                {"field": "genre", "operator": "=", "value": "Pop"},
                {"field": "bpm", "operator": "<", "value": 100}
            ]
        }
        if rule_engine.update_smart_playlist(first_playlist_id, name="Slow Pop Hits", rules=new_rules):
            logger.info(f"Playlist ID {first_playlist_id} actualizada.")
            updated_playlist = rule_engine.get_smart_playlist(first_playlist_id)
            if updated_playlist:
                logger.info(f"  Actualizada: {updated_playlist.name}, Reglas: {updated_playlist.rules}")

    # Eliminar una playlist
    if all_playlists and len(all_playlists) > 1: # Asegurarse de que haya al menos dos para eliminar una
        playlist_to_delete_id = all_playlists[1].id
        if rule_engine.delete_smart_playlist(playlist_to_delete_id):
            logger.info(f"Playlist ID {playlist_to_delete_id} eliminada.")

    db_manager.close()

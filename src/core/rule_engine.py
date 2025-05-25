import json
import re
import logging
from typing import List, Dict, Any, Callable, Union, Optional, Tuple
import sqlite3
from datetime import datetime
import sys
import os

# Añadir la ruta src al path para importar módulos
_current_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.dirname(_current_dir)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from core.database.db_manager import DBManager
from core.database.models import Track, SmartPlaylist
from data import crud

# --- IMPORTACIONES REALES del Parser y Evaluador ---
# Estas funciones vienen de los módulos que ya estaban 'Done'
# según el setup inicial del proyecto.
from src.core.parser import LogicalExpression, Condition, OperatorType # MODIFICADO
# from core.parser_engine import Parser  # MODIFICADO: Importar desde parser_engine.py <-- ELIMINADO
# from core.evaluator_logic import Evaluator # MODIFICADO: Importar la clase Evaluator <-- ELIMINADO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SQLQueryBuilder:
    """Construye consultas SQL a partir de expresiones lógicas parseadas."""
    
    def __init__(self):
        self.params = []  # Parámetros para la consulta preparada
        self.param_counter = 0
    
    def build_query(self, expression: LogicalExpression, 
                   base_query: str = "SELECT * FROM tracks WHERE",
                   order_by: str = None,
                   limit: int = None) -> Tuple[str, List[Any]]:
        """
        Construye una consulta SQL completa a partir de una expresión lógica.
        
        Args:
            expression: Expresión lógica parseada
            base_query: Consulta base (por defecto selecciona todos los tracks)
            order_by: Cláusula ORDER BY opcional
            limit: Límite de resultados opcional
            
        Returns:
            Tupla con (consulta_sql, parámetros)
        """
        self.params = []
        self.param_counter = 0
        
        where_clause = self._build_where_clause(expression)
        
        query = f"{base_query} {where_clause}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return query, self.params
    
    def _build_where_clause(self, expression: LogicalExpression) -> str:
        """Construye la cláusula WHERE a partir de una expresión lógica."""
        if not expression.conditions:
            return "1=1"  # Condición siempre verdadera si no hay condiciones
        
        clauses = []
        
        for i, condition in enumerate(expression.conditions):
            if isinstance(condition, Condition):
                clause = self._build_condition_clause(condition)
            elif isinstance(condition, LogicalExpression):
                # Expresión anidada (entre paréntesis)
                clause = f"({self._build_where_clause(condition)})"
            else:
                raise ValueError(f"Tipo de condición no soportado: {type(condition)}")
            
            clauses.append(clause)
        
        # Unir las cláusulas con los operadores lógicos
        if len(clauses) == 1:
            return clauses[0]
        
        result = clauses[0]
        for i, operator in enumerate(expression.operators):
            if i + 1 < len(clauses):
                result += f" {operator.value} {clauses[i + 1]}"
        
        return result
    
    def _build_condition_clause(self, condition: Condition) -> str:
        """Construye una cláusula SQL para una condición individual."""
        field = condition.field
        operator = condition.operator
        value = condition.value
        
        # Validar que el campo existe en la tabla
        if field not in {'title', 'artist', 'album', 'genre', 'year', 'duration', 
                        'bpm', 'key', 'energy', 'rating', 'play_count', 'track_number',
                        'danceability', 'moods'}:
            raise ValueError(f"Campo no válido: {field}")
        
        if operator == OperatorType.EQUALS:
            return self._add_param_condition(field, "=", value)
        
        elif operator == OperatorType.NOT_EQUALS:
            return self._add_param_condition(field, "!=", value)
        
        elif operator == OperatorType.GREATER_THAN:
            return self._add_param_condition(field, ">", value)
        
        elif operator == OperatorType.LESS_THAN:
            return self._add_param_condition(field, "<", value)
        
        elif operator == OperatorType.GREATER_EQUAL:
            return self._add_param_condition(field, ">=", value)
        
        elif operator == OperatorType.LESS_EQUAL:
            return self._add_param_condition(field, "<=", value)
        
        elif operator == OperatorType.CONTAINS:
            # Para campos de texto, usar LIKE
            if isinstance(value, str):
                return self._add_param_condition(field, "LIKE", f"%{value}%")
            else:
                raise ValueError("CONTAINS solo se puede usar con valores de texto")
        
        elif operator == OperatorType.NOT_CONTAINS:
            if isinstance(value, str):
                return self._add_param_condition(field, "NOT LIKE", f"%{value}%")
            else:
                raise ValueError("NOT_CONTAINS solo se puede usar con valores de texto")
        
        elif operator == OperatorType.STARTS_WITH:
            if isinstance(value, str):
                return self._add_param_condition(field, "LIKE", f"{value}%")
            else:
                raise ValueError("STARTS_WITH solo se puede usar con valores de texto")
        
        elif operator == OperatorType.ENDS_WITH:
            if isinstance(value, str):
                return self._add_param_condition(field, "LIKE", f"%{value}")
            else:
                raise ValueError("ENDS_WITH solo se puede usar con valores de texto")
        
        elif operator == OperatorType.BETWEEN:
            if isinstance(value, list) and len(value) == 2:
                self.params.extend(value)  # Añadir ambos valores a los parámetros
                return f"{field} BETWEEN ? AND ?"
            else:
                raise ValueError("BETWEEN requiere exactamente dos valores")
        
        elif operator == OperatorType.IN:
            if isinstance(value, list):
                placeholders = ",".join("?" for _ in value)
                self.params.extend(value)
                return f"{field} IN ({placeholders})"
            else:
                raise ValueError("IN requiere una lista de valores")
        
        elif operator == OperatorType.NOT_IN:
            if isinstance(value, list):
                placeholders = ",".join("?" for _ in value)
                self.params.extend(value)
                return f"{field} NOT IN ({placeholders})"
            else:
                raise ValueError("NOT_IN requiere una lista de valores")
        
        else:
            raise ValueError(f"Operador no soportado: {operator}")
    
    def _add_param_condition(self, field: str, sql_operator: str, value: Any) -> str:
        """Añade una condición con parámetro a la consulta."""
        self.params.append(value)
        return f"{field} {sql_operator} ?"

class RuleEngine:
    """Motor de reglas que ejecuta consultas basadas en expresiones lógicas."""
    
    def __init__(self, db_connection):
        """
        Inicializa el motor de reglas.
        
        Args:
            db_connection: Conexión a la base de datos SQLite
        """
        self.conn = db_connection
        self.query_builder = SQLQueryBuilder()
    
    def evaluate_rule(self, expression: LogicalExpression, 
                     order_by: str = None, 
                     limit: int = None) -> List[Dict]:
        """
        Evalúa una regla y devuelve los tracks que la cumplen.
        
        Args:
            expression: Expresión lógica parseada
            order_by: Campo por el que ordenar (ej: "bpm DESC", "artist ASC")
            limit: Número máximo de resultados
            
        Returns:
            Lista de diccionarios con los datos de los tracks
        """
        query, params = self.query_builder.build_query(
            expression, 
            order_by=order_by, 
            limit=limit
        )
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        # Convertir resultados a diccionarios
        columns = [description[0] for description in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            track_dict = dict(zip(columns, row))
            results.append(track_dict)
        
        return results
    
    def count_matching_tracks(self, expression: LogicalExpression) -> int:
        """
        Cuenta cuántos tracks cumplen una regla sin recuperar todos los datos.
        
        Args:
            expression: Expresión lógica parseada
            
        Returns:
            Número de tracks que cumplen la regla
        """
        query, params = self.query_builder.build_query(
            expression, 
            base_query="SELECT COUNT(*) FROM tracks WHERE"
        )
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        return cursor.fetchone()[0]
    
    def get_track_ids_for_rule(self, expression: LogicalExpression,
                              order_by: str = None,
                              limit: int = None) -> List[int]:
        """
        Obtiene solo los IDs de los tracks que cumplen una regla.
        
        Args:
            expression: Expresión lógica parseada
            order_by: Campo por el que ordenar
            limit: Número máximo de resultados
            
        Returns:
            Lista de track_ids
        """
        query, params = self.query_builder.build_query(
            expression,
            base_query="SELECT track_id FROM tracks WHERE",
            order_by=order_by,
            limit=limit
        )
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        return [row[0] for row in cursor.fetchall()]

def test_rule_engine():
    """Función de prueba para el motor de reglas."""
    # Esta función requiere una base de datos con datos de prueba
    pass

# Funciones de utilidad
def validate_order_by(order_by: str) -> bool:
    """
    Valida que una cláusula ORDER BY sea segura.
    
    Args:
        order_by: Cláusula ORDER BY a validar
        
    Returns:
        True si es válida, False en caso contrario
    """
    if not order_by:
        return True
    
    # Campos válidos para ordenar
    valid_fields = {
        'title', 'artist', 'album', 'genre', 'year', 'duration', 
        'bpm', 'key', 'energy', 'rating', 'play_count', 'track_number',
        'danceability', 'moods', 'added_at', 'last_modified_at'
    }
    
    # Dividir por comas para múltiples campos
    parts = [part.strip() for part in order_by.split(',')]
    
    for part in parts:
        # Dividir campo y dirección (ASC/DESC)
        tokens = part.split()
        if len(tokens) == 0 or len(tokens) > 2:
            return False
        
        field = tokens[0].lower()
        if field not in valid_fields:
            return False
        
        if len(tokens) == 2:
            direction = tokens[1].upper()
            if direction not in ['ASC', 'DESC']:
                return False
    
    return True

# Ejemplo de uso
if __name__ == "__main__":
    from .parser import parse_rule
    import sqlite3
    
    # Crear una base de datos de prueba en memoria
    conn = sqlite3.connect(":memory:")
    
    # Crear tabla de prueba (simplificada)
    conn.execute("""
        CREATE TABLE tracks (
            track_id INTEGER PRIMARY KEY,
            title TEXT,
            artist TEXT,
            genre TEXT,
            year INTEGER,
            bpm REAL,
            energy INTEGER
        )
    """)
    
    # Insertar datos de prueba
    test_data = [
        (1, "Song A", "Artist 1", "Rock", 2020, 120.0, 7),
        (2, "Song B", "Artist 2", "Electronic", 2021, 128.0, 8),
        (3, "Song C", "Artist 1", "Rock", 2019, 110.0, 6),
    ]
    
    conn.executemany(
        "INSERT INTO tracks (track_id, title, artist, genre, year, bpm, energy) VALUES (?, ?, ?, ?, ?, ?, ?)",
        test_data
    )
    conn.commit()
    
    # Probar el motor de reglas
    engine = RuleEngine(conn)
    
    # Ejemplo 1: Buscar rock
    rule1 = "genre = 'Rock'"
    expr1 = parse_rule(rule1)
    results1 = engine.evaluate_rule(expr1)
    print(f"Regla: {rule1}")
    print(f"Resultados: {len(results1)} tracks")
    for track in results1:
        print(f"  - {track['title']} by {track['artist']}")
    
    # Ejemplo 2: Buscar con múltiples condiciones
    rule2 = "year >= 2020 AND bpm > 125"
    expr2 = parse_rule(rule2)
    results2 = engine.evaluate_rule(expr2)
    print(f"\nRegla: {rule2}")
    print(f"Resultados: {len(results2)} tracks")
    for track in results2:
        print(f"  - {track['title']} ({track['year']}, {track['bpm']} BPM)")
    
    conn.close()

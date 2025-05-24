"""
Motor de reglas para el filtrado inteligente de tracks.
"""
import logging
import json
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime

from .base_rule import BaseRule
from .rule_factory import RuleFactory
from ...core.database.music_database import MusicDatabase, Track, Rule

logger = logging.getLogger(__name__)

@dataclass
class RuleResult:
    """Resultado de la aplicación de una regla."""
    rule_name: str
    success: bool
    details: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

# Operadores disponibles para las condiciones
OPERATORS = {
    "equals": lambda a, b: a == b,
    "not_equals": lambda a, b: a != b,
    "contains": lambda a, b: b in a if a else False,
    "not_contains": lambda a, b: b not in a if a else True,
    "greater_than": lambda a, b: a > b if a is not None and b is not None else False,
    "less_than": lambda a, b: a < b if a is not None and b is not None else False,
    "starts_with": lambda a, b: a.startswith(b) if a else False,
    "ends_with": lambda a, b: a.endswith(b) if a else False,
    "matches_regex": lambda a, b: bool(re.search(b, a)) if a and b else False,
    "in_range": lambda a, b: b[0] <= a <= b[1] if a is not None and len(b) == 2 else False,
    "in_list": lambda a, b: a in b if a and b else False
}

@dataclass
class RuleCondition:
    """Condición para una regla."""
    field: str
    operator: str
    value: Any
    
    def evaluate(self, track_data: Dict[str, Any]) -> bool:
        """Evalúa la condición contra los datos de un track."""
        if self.field not in track_data:
            return False
            
        track_value = track_data[self.field]
        op_func = OPERATORS.get(self.operator)
        
        if not op_func:
            logger.warning(f"Operador desconocido: {self.operator}")
            return False
            
        try:
            return op_func(track_value, self.value)
        except Exception as e:
            logger.error(f"Error evaluando condición: {e}")
            return False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RuleCondition':
        """Crea una condición desde un diccionario."""
        return cls(
            field=data.get("field", ""),
            operator=data.get("operator", "equals"),
            value=data.get("value")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la condición a un diccionario."""
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value
        }

@dataclass
class RuleAction:
    """Acción a ejecutar cuando se cumple una regla."""
    action_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RuleAction':
        """Crea una acción desde un diccionario."""
        return cls(
            action_type=data.get("action_type", ""),
            parameters=data.get("parameters", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la acción a un diccionario."""
        return {
            "action_type": self.action_type,
            "parameters": self.parameters
        }
        
    def execute(self, track_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Ejecuta la acción."""
        action_handler = ACTION_HANDLERS.get(self.action_type)
        if not action_handler:
            logger.warning(f"Tipo de acción desconocido: {self.action_type}")
            return False
            
        try:
            return action_handler(track_data, self.parameters, context)
        except Exception as e:
            logger.error(f"Error ejecutando acción: {e}")
            return False

@dataclass
class Rule:
    """Regla completa con condiciones y acciones."""
    name: str
    description: str = ""
    conditions: List[RuleCondition] = field(default_factory=list)
    actions: List[RuleAction] = field(default_factory=list)
    logical_operator: str = "AND"  # AND, OR
    is_active: bool = True
    
    def evaluate(self, track_data: Dict[str, Any]) -> bool:
        """Evalúa todas las condiciones de la regla."""
        if not self.is_active or not self.conditions:
            return False
            
        results = [condition.evaluate(track_data) for condition in self.conditions]
        
        if self.logical_operator == "AND":
            return all(results)
        elif self.logical_operator == "OR":
            return any(results)
        else:
            logger.warning(f"Operador lógico desconocido: {self.logical_operator}")
            return False
    
    def execute_actions(self, track_data: Dict[str, Any], context: Dict[str, Any]) -> List[bool]:
        """Ejecuta todas las acciones de la regla."""
        return [action.execute(track_data, context) for action in self.actions]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """Crea una regla desde un diccionario."""
        conditions = [RuleCondition.from_dict(c) for c in data.get("conditions", [])]
        actions = [RuleAction.from_dict(a) for a in data.get("actions", [])]
        
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            conditions=conditions,
            actions=actions,
            logical_operator=data.get("logical_operator", "AND"),
            is_active=data.get("is_active", True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la regla a un diccionario."""
        return {
            "name": self.name,
            "description": self.description,
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "logical_operator": self.logical_operator,
            "is_active": self.is_active
        }
    
    def to_json(self) -> str:
        """Convierte la regla a JSON."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Rule':
        """Crea una regla desde JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)

class RuleEngine:
    """Motor de reglas para aplicar filtros inteligentes."""
    
    def __init__(self, db_manager=None):
        """
        Inicializa el motor de reglas.
        
        Args:
            db_manager: Gestor de base de datos opcional
        """
        self.rules: List[Rule] = []
        self.db_manager = db_manager
        self._load_rules_from_db()
        
    def _load_rules_from_db(self):
        """Carga todas las reglas desde la base de datos."""
        if not self.db_manager:
            logger.warning("No hay gestor de base de datos, no se cargarán reglas")
            return
            
        try:
            rows = self.db_manager.fetch_query("SELECT * FROM rules WHERE is_active = 1")
            for row in rows:
                try:
                    conditions = json.loads(row['conditions_json'])
                    actions = json.loads(row['actions_json'])
                    
                    rule = Rule.from_dict({
                        "name": row['name'],
                        "description": row['description'],
                        "conditions": conditions,
                        "actions": actions,
                        "is_active": bool(row['is_active'])
                    })
                    
                    self.rules.append(rule)
                except Exception as e:
                    logger.error(f"Error cargando regla {row['name']}: {e}")
            
            logger.info(f"Cargadas {len(self.rules)} reglas desde la base de datos")
        except Exception as e:
            logger.error(f"Error cargando reglas desde la base de datos: {e}")
    
    def add_rule(self, rule: Rule) -> bool:
        """
        Añade una regla al motor y opcionalmente a la base de datos.
        
        Args:
            rule: Regla a añadir
            
        Returns:
            True si se añadió correctamente
        """
        try:
            # Añadir a la lista en memoria
            self.rules.append(rule)
            
            # Persistir en la base de datos si está disponible
            if self.db_manager:
                conditions_json = json.dumps([c.to_dict() for c in rule.conditions])
                actions_json = json.dumps([a.to_dict() for a in rule.actions])
                
                self.db_manager.execute_query(
                    """
                    INSERT INTO rules (name, description, conditions_json, actions_json, is_active)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (rule.name, rule.description, conditions_json, actions_json, rule.is_active)
                )
                
            logger.info(f"Regla '{rule.name}' añadida correctamente")
            return True
        except Exception as e:
            logger.error(f"Error añadiendo regla: {e}")
            return False
    
    def update_rule(self, rule: Rule) -> bool:
        """
        Actualiza una regla existente.
        
        Args:
            rule: Regla con datos actualizados
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            # Actualizar en memoria
            for i, r in enumerate(self.rules):
                if r.name == rule.name:
                    self.rules[i] = rule
                    break
            
            # Actualizar en la base de datos
            if self.db_manager:
                conditions_json = json.dumps([c.to_dict() for c in rule.conditions])
                actions_json = json.dumps([a.to_dict() for a in rule.actions])
                
                self.db_manager.execute_query(
                    """
                    UPDATE rules
                    SET description = ?, conditions_json = ?, actions_json = ?, is_active = ?
                    WHERE name = ?
                    """,
                    (rule.description, conditions_json, actions_json, rule.is_active, rule.name)
                )
            
            logger.info(f"Regla '{rule.name}' actualizada correctamente")
            return True
        except Exception as e:
            logger.error(f"Error actualizando regla: {e}")
            return False
    
    def get_rule(self, name: str) -> Optional[Rule]:
        """
        Obtiene una regla por su nombre.
        
        Args:
            name: Nombre de la regla
            
        Returns:
            La regla si existe, None en caso contrario
        """
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None
    
    def delete_rule(self, name: str) -> bool:
        """
        Elimina una regla.
        
        Args:
            name: Nombre de la regla a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            # Eliminar de la memoria
            self.rules = [r for r in self.rules if r.name != name]
            
            # Eliminar de la base de datos
            if self.db_manager:
                self.db_manager.execute_query("DELETE FROM rules WHERE name = ?", (name,))
            
            logger.info(f"Regla '{name}' eliminada correctamente")
            return True
        except Exception as e:
            logger.error(f"Error eliminando regla: {e}")
            return False
    
    def apply_rules(self, track_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, List[str]]:
        """
        Aplica todas las reglas activas a un track.
        
        Args:
            track_data: Datos del track a evaluar
            context: Contexto adicional para la ejecución de acciones
            
        Returns:
            Diccionario con los resultados de las acciones
        """
        if context is None:
            context = {}
            
        results = {"applied_rules": [], "actions_executed": []}
        
        for rule in self.rules:
            if not rule.is_active:
                continue
                
            if rule.evaluate(track_data):
                results["applied_rules"].append(rule.name)
                
                # Ejecutar acciones
                for i, action in enumerate(rule.actions):
                    success = action.execute(track_data, context)
                    if success:
                        results["actions_executed"].append(f"{rule.name}:{action.action_type}")
        
        return results

# Definición de manejadores de acciones
def add_to_playlist_handler(track_data: Dict[str, Any], params: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Añade un track a una playlist."""
    db_manager = context.get("db_manager")
    if not db_manager:
        return False
        
    playlist_name = params.get("playlist_name")
    if not playlist_name:
        return False
        
    track_id = track_data.get("id")
    if not track_id:
        return False
    
    # Buscar la playlist por nombre
    rows = db_manager.fetch_query("SELECT id FROM playlists WHERE name = ?", (playlist_name,))
    if not rows:
        # Crear la playlist si no existe
        from ..database.models import Playlist
        playlist = Playlist(name=playlist_name)
        playlist_id = db_manager.create_playlist(playlist)
    else:
        playlist_id = rows[0]["id"]
    
    # Añadir el track a la playlist
    return db_manager.add_track_to_playlist(playlist_id, track_id)

def set_tag_handler(track_data: Dict[str, Any], params: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Establece un valor de metadatos en un track."""
    db_manager = context.get("db_manager")
    file_handler = context.get("file_handler")
    if not db_manager or not file_handler:
        return False
        
    field = params.get("field")
    value = params.get("value")
    write_to_file = params.get("write_to_file", True)
    
    if not field:
        return False
        
    track_id = track_data.get("id")
    filepath = track_data.get("filepath")
    
    if not track_id or not filepath:
        return False
    
    # Actualizar en la base de datos
    update_query = f"UPDATE tracks SET {field} = ? WHERE id = ?"
    db_manager.execute_query(update_query, (value, track_id))
    
    # Actualizar el archivo si se solicita
    if write_to_file and file_handler:
        # Los campos específicos requieren tratamiento especial
        if field == "genre":
            file_handler.write_genre(filepath, [value])
        elif field == "year":
            file_handler.set_tag_value(filepath, "year", value)
        elif field == "bpm":
            file_handler.set_tag_value(filepath, "bpm", value)
        else:
            # Campos generales
            file_handler.set_tag_value(filepath, field, value)
    
    return True

def generate_recommendations_handler(track_data: Dict[str, Any], params: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Genera recomendaciones basadas en compatibilidad armónica y energética."""
    db_manager = context.get("db_manager")
    if not db_manager:
        return False
        
    track_id = track_data.get("id")
    if not track_id:
        return False
        
    max_results = params.get("max_results", 10)
    energy_direction = params.get("energy_direction", "up")  # up, down, similar
    
    # Obtener tracks compatibles
    compatible_tracks = db_manager.get_compatible_tracks(track_id, max_results * 2)
    
    # Filtrar por dirección de energía
    current_energy = track_data.get("energy", 0.5)
    filtered_tracks = []
    
    for track, score in compatible_tracks:
        if energy_direction == "up" and track.energy > current_energy:
            filtered_tracks.append((track, score))
        elif energy_direction == "down" and track.energy < current_energy:
            filtered_tracks.append((track, score))
        elif energy_direction == "similar" and 0.8 * current_energy <= track.energy <= 1.2 * current_energy:
            filtered_tracks.append((track, score))
    
    # Ordenar por compatibilidad y limitar resultados
    filtered_tracks = sorted(filtered_tracks, key=lambda x: x[1], reverse=True)[:max_results]
    
    # Crear una playlist de recomendaciones
    if filtered_tracks:
        playlist_name = params.get("playlist_name", f"Recomendaciones para {track_data.get('title', 'track')}")
        
        # Buscar si ya existe la playlist
        rows = db_manager.fetch_query("SELECT id FROM playlists WHERE name = ?", (playlist_name,))
        if rows:
            playlist_id = rows[0]["id"]
            # Limpiar la playlist existente
            db_manager.execute_query("DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
        else:
            # Crear nueva playlist
            from ..database.models import Playlist
            playlist = Playlist(name=playlist_name, description=f"Recomendaciones para {track_data.get('title', 'track')}")
            playlist_id = db_manager.create_playlist(playlist)
        
        # Añadir tracks a la playlist
        for i, (track, _) in enumerate(filtered_tracks):
            db_manager.add_track_to_playlist(playlist_id, track.id, i)
        
        context["recommendation_playlist_id"] = playlist_id
        return True
    
    return False

# Registrar manejadores de acciones
ACTION_HANDLERS = {
    "add_to_playlist": add_to_playlist_handler,
    "set_tag": set_tag_handler,
    "generate_recommendations": generate_recommendations_handler
}

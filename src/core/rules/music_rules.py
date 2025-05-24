"""
Reglas específicas para el filtrado de música.
Incluye reglas para filtrar por metadatos, propiedades y compatibilidad.
"""
import logging
import re
from typing import Dict, Any, List, Tuple, Optional, Union, Set
from .base_rule import BaseRule

logger = logging.getLogger(__name__)

class MetadataRule(BaseRule):
    """Regla para filtrar por metadatos de un track."""
    
    def __init__(self, name: str, field: str, operator: str, value: Any, description: str = ""):
        """
        Inicializa una regla de metadatos.
        
        Args:
            name: Nombre de la regla
            field: Campo de metadatos a evaluar (title, artist, album, genre, etc.)
            operator: Operador de comparación (==, !=, >, <, >=, <=, contains, startswith, endswith, regex)
            value: Valor a comparar
            description: Descripción de la regla
        """
        super().__init__(name=name, description=description)
        self.field = field
        self.operator = operator
        self.value = value
        
        # Validar operador
        valid_operators = ["==", "!=", ">", "<", ">=", "<=", "contains", "startswith", "endswith", "regex", "in"]
        if self.operator not in valid_operators:
            logger.warning(f"Operador inválido '{operator}', usando '==' por defecto.")
            self.operator = "=="
        
        # Compilar regex si es necesario
        self._regex = None
        if self.operator == "regex" and isinstance(self.value, str):
            try:
                self._regex = re.compile(self.value, re.IGNORECASE)
            except re.error as e:
                logger.error(f"Error compilando regex '{self.value}': {e}")
                self._regex = None
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evalúa si el track cumple con la regla de metadatos.
        
        Args:
            context: Diccionario con información del track a evaluar
            
        Returns:
            True si el track cumple la regla, False en caso contrario
        """
        # Obtener el valor del campo del track
        track = context.get("track", {})
        if not track:
            return False
        
        # Soporte para campos anidados (metadata_json.something)
        if "." in self.field:
            parts = self.field.split(".")
            track_value = track
            for part in parts:
                if isinstance(track_value, dict) and part in track_value:
                    track_value = track_value[part]
                else:
                    track_value = None
                    break
        else:
            track_value = track.get(self.field)
        
        # Si el valor es None, la regla no aplica
        if track_value is None:
            return False
        
        # Evaluar según el operador
        if self.operator == "==":
            return track_value == self.value
        
        elif self.operator == "!=":
            return track_value != self.value
        
        elif self.operator == ">":
            try:
                return float(track_value) > float(self.value)
            except (ValueError, TypeError):
                return False
        
        elif self.operator == "<":
            try:
                return float(track_value) < float(self.value)
            except (ValueError, TypeError):
                return False
        
        elif self.operator == ">=":
            try:
                return float(track_value) >= float(self.value)
            except (ValueError, TypeError):
                return False
        
        elif self.operator == "<=":
            try:
                return float(track_value) <= float(self.value)
            except (ValueError, TypeError):
                return False
        
        elif self.operator == "contains":
            if isinstance(track_value, str) and isinstance(self.value, str):
                return self.value.lower() in track_value.lower()
            return False
        
        elif self.operator == "startswith":
            if isinstance(track_value, str) and isinstance(self.value, str):
                return track_value.lower().startswith(self.value.lower())
            return False
        
        elif self.operator == "endswith":
            if isinstance(track_value, str) and isinstance(self.value, str):
                return track_value.lower().endswith(self.value.lower())
            return False
        
        elif self.operator == "regex":
            if self._regex and isinstance(track_value, str):
                return bool(self._regex.search(track_value))
            return False
        
        elif self.operator == "in":
            if isinstance(self.value, (list, tuple, set)):
                if isinstance(track_value, str):
                    return track_value.lower() in [str(v).lower() for v in self.value]
                return track_value in self.value
            return False
        
        # Si llegamos aquí, algo salió mal
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la regla a un diccionario para serialización."""
        result = super().to_dict()
        result.update({
            "field": self.field,
            "operator": self.operator,
            "value": self.value
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetadataRule':
        """
        Crea una instancia de regla de metadatos a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos de la regla
            
        Returns:
            Instancia de la regla de metadatos
        """
        rule = cls(
            name=data.get("name", ""),
            field=data.get("field", ""),
            operator=data.get("operator", "=="),
            value=data.get("value"),
            description=data.get("description", "")
        )
        rule.is_active = data.get("is_active", True)
        return rule


class CamelotRule(BaseRule):
    """Regla para filtrar por compatibilidad armónica Camelot."""
    
    def __init__(self, name: str, reference_key: str, compatibility_type: str = "all", 
                 min_score: float = 0.7, description: str = ""):
        """
        Inicializa una regla de compatibilidad Camelot.
        
        Args:
            name: Nombre de la regla
            reference_key: Clave Camelot de referencia (ej: "8A")
            compatibility_type: Tipo de compatibilidad ("perfect", "compatible", "energy", "all")
            min_score: Puntuación mínima de compatibilidad (0.0 - 1.0)
            description: Descripción de la regla
        """
        super().__init__(name=name, description=description)
        self.reference_key = reference_key
        self.compatibility_type = compatibility_type
        self.min_score = max(0.0, min(1.0, min_score))  # Asegurar que esté entre 0 y 1
        
        # Validar tipo de compatibilidad
        valid_types = ["perfect", "compatible", "energy", "all"]
        if self.compatibility_type not in valid_types:
            logger.warning(f"Tipo de compatibilidad inválido '{compatibility_type}', usando 'all' por defecto.")
            self.compatibility_type = "all"
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evalúa si el track cumple con la regla de compatibilidad Camelot.
        
        Args:
            context: Diccionario con información del track y la base de datos
            
        Returns:
            True si el track cumple la regla, False en caso contrario
        """
        track = context.get("track", {})
        if not track:
            return False
        
        # Si el track no tiene clave Camelot, no puede ser compatible
        track_key = track.get("camelot_key")
        if not track_key:
            return False
        
        # Obtener la base de datos para consultar compatibilidad
        db = context.get("database")
        if not db:
            logger.warning("No se proporcionó base de datos para evaluar compatibilidad Camelot")
            return False
        
        # Consultar compatibilidad
        try:
            cursor = db.connection.execute('''
                SELECT compatibility_score, transition_type
                FROM camelot_transitions
                WHERE from_key = ? AND to_key = ?
            ''', (self.reference_key, track_key))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            compatibility_score = result[0]
            transition_type = result[1]
            
            # Evaluar según el tipo y puntuación
            if self.compatibility_type == "all":
                return compatibility_score >= self.min_score
            
            return (transition_type == self.compatibility_type and 
                    compatibility_score >= self.min_score)
            
        except Exception as e:
            logger.error(f"Error evaluando compatibilidad Camelot: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la regla a un diccionario para serialización."""
        result = super().to_dict()
        result.update({
            "reference_key": self.reference_key,
            "compatibility_type": self.compatibility_type,
            "min_score": self.min_score
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CamelotRule':
        """
        Crea una instancia de regla Camelot a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos de la regla
            
        Returns:
            Instancia de la regla Camelot
        """
        rule = cls(
            name=data.get("name", ""),
            reference_key=data.get("reference_key", ""),
            compatibility_type=data.get("compatibility_type", "all"),
            min_score=data.get("min_score", 0.7),
            description=data.get("description", "")
        )
        rule.is_active = data.get("is_active", True)
        return rule


class EnergyProgressionRule(BaseRule):
    """Regla para filtrar por progresión de energía."""
    
    def __init__(self, name: str, reference_energy: float, direction: str = "up", 
                 delta_range: Tuple[float, float] = (0.05, 0.2), description: str = ""):
        """
        Inicializa una regla de progresión de energía.
        
        Args:
            name: Nombre de la regla
            reference_energy: Valor de energía de referencia (0.0 - 1.0)
            direction: Dirección de la progresión ("up", "down", "similar")
            delta_range: Rango de delta aceptable (min, max)
            description: Descripción de la regla
        """
        super().__init__(name=name, description=description)
        self.reference_energy = max(0.0, min(1.0, reference_energy))
        self.direction = direction
        self.delta_range = delta_range
        
        # Validar dirección
        valid_directions = ["up", "down", "similar"]
        if self.direction not in valid_directions:
            logger.warning(f"Dirección inválida '{direction}', usando 'similar' por defecto.")
            self.direction = "similar"
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evalúa si el track cumple con la progresión de energía deseada.
        
        Args:
            context: Diccionario con información del track a evaluar
            
        Returns:
            True si el track cumple la regla, False en caso contrario
        """
        track = context.get("track", {})
        if not track:
            return False
        
        # Si el track no tiene valor de energía, no puede evaluarse
        track_energy = track.get("energy")
        if track_energy is None:
            return False
        
        # Asegurarse de que es un número
        try:
            track_energy = float(track_energy)
        except (ValueError, TypeError):
            return False
        
        # Calcular la diferencia de energía
        energy_delta = track_energy - self.reference_energy
        
        # Evaluar según la dirección
        if self.direction == "up":
            return (energy_delta > 0 and 
                    self.delta_range[0] <= energy_delta <= self.delta_range[1])
        
        elif self.direction == "down":
            return (energy_delta < 0 and 
                    self.delta_range[0] <= abs(energy_delta) <= self.delta_range[1])
        
        else:  # similar
            return abs(energy_delta) <= self.delta_range[1]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la regla a un diccionario para serialización."""
        result = super().to_dict()
        result.update({
            "reference_energy": self.reference_energy,
            "direction": self.direction,
            "delta_range": self.delta_range
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnergyProgressionRule':
        """
        Crea una instancia de regla de progresión de energía a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos de la regla
            
        Returns:
            Instancia de la regla de progresión de energía
        """
        rule = cls(
            name=data.get("name", ""),
            reference_energy=data.get("reference_energy", 0.5),
            direction=data.get("direction", "similar"),
            delta_range=data.get("delta_range", (0.05, 0.2)),
            description=data.get("description", "")
        )
        rule.is_active = data.get("is_active", True)
        return rule


class BpmRule(BaseRule):
    """Regla para filtrar por rango de BPM."""
    
    def __init__(self, name: str, reference_bpm: float, tolerance_pct: float = 5.0, 
                 allow_double_half: bool = True, description: str = ""):
        """
        Inicializa una regla de BPM.
        
        Args:
            name: Nombre de la regla
            reference_bpm: BPM de referencia
            tolerance_pct: Porcentaje de tolerancia (%)
            allow_double_half: Permitir BPM al doble o a la mitad
            description: Descripción de la regla
        """
        super().__init__(name=name, description=description)
        self.reference_bpm = max(0.0, reference_bpm)
        self.tolerance_pct = max(0.0, tolerance_pct)
        self.allow_double_half = allow_double_half
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evalúa si el track cumple con el rango de BPM.
        
        Args:
            context: Diccionario con información del track a evaluar
            
        Returns:
            True si el track cumple la regla, False en caso contrario
        """
        track = context.get("track", {})
        if not track:
            return False
        
        # Si el track no tiene BPM, no puede evaluarse
        track_bpm = track.get("bpm")
        if track_bpm is None:
            return False
        
        # Asegurarse de que es un número
        try:
            track_bpm = float(track_bpm)
        except (ValueError, TypeError):
            return False
        
        # Calcular el rango de BPM aceptable
        tolerance = self.reference_bpm * (self.tolerance_pct / 100.0)
        min_bpm = self.reference_bpm - tolerance
        max_bpm = self.reference_bpm + tolerance
        
        # Comprobar si está en el rango principal
        if min_bpm <= track_bpm <= max_bpm:
            return True
        
        # Comprobar rangos alternativos si está permitido
        if self.allow_double_half:
            # BPM al doble
            double_min = (self.reference_bpm * 2) - (tolerance * 2)
            double_max = (self.reference_bpm * 2) + (tolerance * 2)
            if double_min <= track_bpm <= double_max:
                return True
            
            # BPM a la mitad
            half_min = (self.reference_bpm / 2) - (tolerance / 2)
            half_max = (self.reference_bpm / 2) + (tolerance / 2)
            if half_min <= track_bpm <= half_max:
                return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la regla a un diccionario para serialización."""
        result = super().to_dict()
        result.update({
            "reference_bpm": self.reference_bpm,
            "tolerance_pct": self.tolerance_pct,
            "allow_double_half": self.allow_double_half
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BpmRule':
        """
        Crea una instancia de regla de BPM a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos de la regla
            
        Returns:
            Instancia de la regla de BPM
        """
        rule = cls(
            name=data.get("name", ""),
            reference_bpm=data.get("reference_bpm", 120.0),
            tolerance_pct=data.get("tolerance_pct", 5.0),
            allow_double_half=data.get("allow_double_half", True),
            description=data.get("description", "")
        )
        rule.is_active = data.get("is_active", True)
        return rule

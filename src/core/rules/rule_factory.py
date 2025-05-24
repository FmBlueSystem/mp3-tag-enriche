"""
Fábrica para la creación de reglas a partir de configuraciones.
"""
import logging
import json
from typing import Dict, Any, Optional, Type, List

from .base_rule import BaseRule, CompositeRule
from .music_rules import MetadataRule, CamelotRule, EnergyProgressionRule, BpmRule

logger = logging.getLogger(__name__)

class RuleFactory:
    """Fábrica para la creación de reglas."""
    
    # Mapeo de tipos de reglas
    _rule_classes = {
        "MetadataRule": MetadataRule,
        "CamelotRule": CamelotRule,
        "EnergyProgressionRule": EnergyProgressionRule,
        "BpmRule": BpmRule,
        "CompositeRule": CompositeRule
    }
    
    @classmethod
    def register_rule_class(cls, rule_type: str, rule_class: Type[BaseRule]) -> None:
        """
        Registra una clase de regla en la fábrica.
        
        Args:
            rule_type: Nombre del tipo de regla
            rule_class: Clase de regla a registrar
        """
        cls._rule_classes[rule_type] = rule_class
    
    @classmethod
    def create_rule(cls, rule_data: Dict[str, Any]) -> Optional[BaseRule]:
        """
        Crea una instancia de regla a partir de datos JSON.
        
        Args:
            rule_data: Datos de la regla en formato diccionario
            
        Returns:
            Instancia de regla o None si no se pudo crear
        """
        try:
            if not isinstance(rule_data, dict):
                logger.error(f"Datos de regla inválidos: {rule_data}")
                return None
            
            rule_type = rule_data.get("type")
            if not rule_type:
                logger.error("Tipo de regla no especificado")
                return None
            
            rule_class = cls._rule_classes.get(rule_type)
            if not rule_class:
                logger.error(f"Tipo de regla desconocido: {rule_type}")
                return None
            
            # Crear la regla usando el método from_dict de la clase
            return rule_class.from_dict(rule_data)
            
        except Exception as e:
            logger.error(f"Error creando regla: {e}")
            return None
    
    @classmethod
    def create_from_json(cls, json_str: str) -> Optional[BaseRule]:
        """
        Crea una instancia de regla a partir de una cadena JSON.
        
        Args:
            json_str: Cadena JSON con la definición de la regla
            
        Returns:
            Instancia de regla o None si no se pudo crear
        """
        try:
            rule_data = json.loads(json_str)
            return cls.create_rule(rule_data)
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado creando regla desde JSON: {e}")
            return None
            
    @classmethod
    def create_rules_batch(cls, rules_data: List[Dict[str, Any]]) -> List[BaseRule]:
        """
        Crea múltiples instancias de reglas a partir de una lista de datos.
        
        Args:
            rules_data: Lista de diccionarios con datos de reglas
            
        Returns:
            Lista de instancias de reglas (ignora las que no se pudieron crear)
        """
        rules = []
        for rule_data in rules_data:
            rule = cls.create_rule(rule_data)
            if rule:
                rules.append(rule)
        return rules

"""
Base para el sistema de reglas de filtrado inteligente.
Proporciona la estructura básica para la definición y evaluación de reglas.
"""
import logging
from typing import Dict, Any, List, Callable, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseRule(ABC):
    """Clase base para todas las reglas del sistema."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.is_active = True
    
    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evalúa la regla según el contexto proporcionado.
        
        Args:
            context: Diccionario con información contextual para la evaluación
            
        Returns:
            True si la regla se cumple, False en caso contrario
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la regla a un diccionario para serialización."""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__,
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseRule':
        """
        Crea una instancia de regla a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos de la regla
            
        Returns:
            Instancia de la regla
        """
        rule = cls(name=data.get("name", ""), description=data.get("description", ""))
        rule.is_active = data.get("is_active", True)
        return rule


class CompositeRule(BaseRule):
    """
    Regla compuesta que combina múltiples reglas con operadores lógicos.
    Implementa el patrón Composite para reglas.
    """
    
    def __init__(self, name: str, operator: str = "AND", description: str = ""):
        """
        Inicializa una regla compuesta.
        
        Args:
            name: Nombre de la regla
            operator: Operador lógico ("AND", "OR", "NOT")
            description: Descripción de la regla
        """
        super().__init__(name=name, description=description)
        self.operator = operator.upper()
        self.rules: List[BaseRule] = []
        
        if self.operator not in ["AND", "OR", "NOT"]:
            logger.warning(f"Operador inválido '{operator}', usando 'AND' por defecto.")
            self.operator = "AND"
    
    def add_rule(self, rule: BaseRule) -> None:
        """Añade una regla al conjunto."""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str) -> bool:
        """Elimina una regla del conjunto por su nombre."""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                return True
        return False
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evalúa la regla compuesta según el contexto proporcionado.
        
        Args:
            context: Diccionario con información contextual para la evaluación
            
        Returns:
            True si la regla compuesta se cumple, False en caso contrario
        """
        if not self.rules:
            return True
        
        if self.operator == "AND":
            return all(rule.evaluate(context) for rule in self.rules if rule.is_active)
        
        elif self.operator == "OR":
            return any(rule.evaluate(context) for rule in self.rules if rule.is_active)
        
        elif self.operator == "NOT":
            # Para NOT, solo se considera la primera regla
            if not self.rules:
                return True
            return not self.rules[0].evaluate(context)
        
        # Por defecto, usar AND
        return all(rule.evaluate(context) for rule in self.rules if rule.is_active)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la regla compuesta a un diccionario para serialización."""
        result = super().to_dict()
        result.update({
            "operator": self.operator,
            "rules": [rule.to_dict() for rule in self.rules]
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompositeRule':
        """
        Crea una instancia de regla compuesta a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos de la regla
            
        Returns:
            Instancia de la regla compuesta
        """
        from .rule_factory import RuleFactory
        
        rule = cls(
            name=data.get("name", ""),
            operator=data.get("operator", "AND"),
            description=data.get("description", "")
        )
        rule.is_active = data.get("is_active", True)
        
        # Añadir reglas hijas
        for rule_data in data.get("rules", []):
            child_rule = RuleFactory.create_rule(rule_data)
            if child_rule:
                rule.add_rule(child_rule)
        
        return rule

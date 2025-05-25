"""
Evaluador de reglas de playlist que procesa el AST y aplica
las condiciones a los tracks.
"""

from typing import Dict, Any
from .parser_engine import NodeType, ASTNode # MODIFICADO: Cambiar de .parser a .parser_engine
from .camelot import CamelotWheel, CompatibilityMode

class EvaluatorError(Exception):
    """Error durante la evaluación de una regla."""
    pass

class Evaluator:
    """Evaluador de reglas de playlist."""
    
    def __init__(self):
        self.wheel = CamelotWheel()  # Para evaluar compatibilidad de claves
        
    def evaluate(self, node: ASTNode, track: Dict[str, Any]) -> bool:
        """
        Evalúa un nodo del AST contra un track.
        
        Args:
            node: Nodo del AST a evaluar
            track: Track a evaluar
            
        Returns:
            bool: True si el track cumple la condición
            
        Raises:
            EvaluatorError: Si hay errores durante la evaluación
        """
        try:
            if node.type == NodeType.AND:
                return self.evaluate(node.left, track) and self.evaluate(node.right, track)
                
            if node.type == NodeType.OR:
                return self.evaluate(node.left, track) or self.evaluate(node.right, track)
                
            if node.type == NodeType.COMPARISON:
                return self._evaluate_comparison(node, track)
                
            if node.type == NodeType.COMPATIBILITY:
                return self._evaluate_compatibility(node, track)
                
            if node.type == NodeType.BETWEEN:
                return self._evaluate_between(node, track)
                
            if node.type == NodeType.IN:
                return self._evaluate_in(node, track)
                
            if node.type == NodeType.MATCHES:
                return self._evaluate_matches(node, track)
                
            if node.type == NodeType.FUNCTION:
                return self._evaluate_function(node, track)
                
            raise EvaluatorError(f"Tipo de nodo no soportado: {node.type}")
            
        except Exception as e:
            raise EvaluatorError(f"Error evaluando nodo: {str(e)}")
            
    def _evaluate_comparison(self, node: ASTNode, track: Dict[str, Any]) -> bool:
        """
        Evalúa una comparación simple.
        
        Args:
            node: Nodo de comparación
            track: Track a evaluar
            
        Returns:
            bool: Resultado de la comparación
        """
        # Obtener valores a comparar
        left_val = self._get_value(node.left, track)
        right_val = self._get_value(node.right, track)
        
        # Convertir tipos si es necesario
        if isinstance(left_val, str) and isinstance(right_val, (int, float)):
            try:
                left_val = float(left_val)
            except ValueError:
                pass
        
        if isinstance(right_val, str) and isinstance(left_val, (int, float)):
            try:
                right_val = float(right_val)
            except ValueError:
                pass
                
        # Realizar comparación
        if node.value == '=':
            return left_val == right_val
        if node.value == '!=':
            return left_val != right_val
        if node.value == '>':
            return left_val > right_val
        if node.value == '<':
            return left_val < right_val
        if node.value == '>=':
            return left_val >= right_val
        if node.value == '<=':
            return left_val <= right_val
            
        raise EvaluatorError(f"Operador no soportado: {node.value}")
        
    def _evaluate_compatibility(self, node: ASTNode, track: Dict[str, Any]) -> bool:
        """
        Evalúa compatibilidad entre claves musicales.
        
        Args:
            node: Nodo de compatibilidad
            track: Track a evaluar
            
        Returns:
            bool: True si las claves son compatibles
        """
        # Obtener claves a comparar
        track_key = track.get('key')
        if not track_key:
            return False
            
        target_key = node.value
        
        # Obtener claves compatibles
        compatible_keys = self.wheel.get_compatible_keys(
            target_key,
            CompatibilityMode.PERFECT
        )
        
        # Verificar todas las reglas de compatibilidad
        for mode in CompatibilityMode:
            if mode != CompatibilityMode.CUSTOM:
                compatible_keys.update(
                    self.wheel.get_compatible_keys(target_key, mode)
                )
                
        # La clave del track debe estar entre las compatibles
        return track_key in compatible_keys
        
    def _evaluate_between(self, node: ASTNode, track: Dict[str, Any]) -> bool:
        """
        Evalúa si un valor está en un rango.
        
        Args:
            node: Nodo BETWEEN
            track: Track a evaluar
            
        Returns:
            bool: True si el valor está en el rango
        """
        value = self._get_value(node.left, track)
        min_val, max_val = node.value
        
        try:
            value = float(value)
            return min_val <= value <= max_val
        except (TypeError, ValueError):
            return False
            
    def _evaluate_in(self, node: ASTNode, track: Dict[str, Any]) -> bool:
        """
        Evalúa si un valor está en una lista.
        
        Args:
            node: Nodo IN
            track: Track a evaluar
            
        Returns:
            bool: True si el valor está en la lista
        """
        value = self._get_value(node.left, track)
        return value in node.value
        
    def _evaluate_matches(self, node: ASTNode, track: Dict[str, Any]) -> bool:
        """
        Evalúa si un valor coincide con un patrón.
        
        Args:
            node: Nodo MATCHES
            track: Track a evaluar
            
        Returns:
            bool: True si el valor coincide con el patrón
        """
        value = self._get_value(node.left, track)
        pattern = node.value
        
        # TODO: Implementar matching de patrones
        return False
        
    def _evaluate_function(self, node: ASTNode, track: Dict[str, Any]) -> bool:
        """
        Evalúa una función.
        
        Args:
            node: Nodo de función
            track: Track a evaluar
            
        Returns:
            bool: Resultado de la función
        """
        # TODO: Implementar evaluación de funciones
        return False
        
    def _get_value(self, node: ASTNode, track: Dict[str, Any]) -> Any:
        """
        Obtiene el valor de un nodo.
        
        Args:
            node: Nodo a evaluar
            track: Track actual
            
        Returns:
            Valor del nodo
        """
        if node.type == NodeType.NUMBER:
            return node.value
            
        if node.type == NodeType.STRING:
            return node.value
            
        if node.type == NodeType.IDENTIFIER:
            return track.get(node.value)
            
        raise EvaluatorError(f"Tipo de nodo no soportado para valor: {node.type}") 
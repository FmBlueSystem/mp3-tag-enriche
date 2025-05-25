"""
Evaluador de reglas musicales.

Este módulo implementa un evaluador que puede ejecutar ASTs de expresiones
contra datos musicales reales.
"""

from typing import Dict, Any, Union
from ..parser.expression_parser import (
    ExpressionNode, 
    ComparisonNode, 
    LogicalNode,
    ComparisonOperator,
    LogicalOperator
)


class EvaluationError(Exception):
    """Error durante la evaluación de una regla."""
    pass


class RuleEvaluator:
    """Evaluador de reglas musicales."""
    
    def __init__(self):
        """Inicializa el evaluador."""
        self._comparison_handlers = {
            ComparisonOperator.EQUALS: self._evaluate_equals,
            ComparisonOperator.NOT_EQUALS: self._evaluate_not_equals,
            ComparisonOperator.GREATER: self._evaluate_greater,
            ComparisonOperator.GREATER_EQUAL: self._evaluate_greater_equal,
            ComparisonOperator.LESS: self._evaluate_less,
            ComparisonOperator.LESS_EQUAL: self._evaluate_less_equal,
            ComparisonOperator.CONTAINS: self._evaluate_contains,
            ComparisonOperator.NOT_CONTAINS: self._evaluate_not_contains,
            ComparisonOperator.STARTS_WITH: self._evaluate_starts_with,
            ComparisonOperator.ENDS_WITH: self._evaluate_ends_with,
        }
    
    def evaluate(self, node: ExpressionNode, data: Dict[str, Any]) -> bool:
        """
        Evalúa un nodo del AST contra datos musicales.
        
        Args:
            node: Nodo del AST a evaluar
            data: Datos musicales (ej: {"genre": "rock", "year": 2000})
        
        Returns:
            True si la regla se cumple, False en caso contrario
        
        Raises:
            EvaluationError: Si hay un error durante la evaluación
        """
        if isinstance(node, ComparisonNode):
            return self._evaluate_comparison(node, data)
        elif isinstance(node, LogicalNode):
            return self._evaluate_logical(node, data)
        else:
            raise EvaluationError(f"Tipo de nodo no soportado: {type(node)}")
    
    def _evaluate_comparison(self, node: ComparisonNode, data: Dict[str, Any]) -> bool:
        """Evalúa un nodo de comparación."""
        field_value = data.get(node.field)
        
        if field_value is None:
            # Campo no existe en los datos
            return False
        
        handler = self._comparison_handlers.get(node.operator)
        if not handler:
            raise EvaluationError(f"Operador no soportado: {node.operator}")
        
        return handler(field_value, node.value)
    
    def _evaluate_logical(self, node: LogicalNode, data: Dict[str, Any]) -> bool:
        """Evalúa un nodo lógico."""
        if node.operator == LogicalOperator.AND:
            left_result = self.evaluate(node.left, data)
            right_result = self.evaluate(node.right, data)
            return left_result and right_result
        
        elif node.operator == LogicalOperator.OR:
            left_result = self.evaluate(node.left, data)
            right_result = self.evaluate(node.right, data)
            return left_result or right_result
        
        elif node.operator == LogicalOperator.NOT:
            operand_result = self.evaluate(node.left, data)
            return not operand_result
        
        else:
            raise EvaluationError(f"Operador lógico no soportado: {node.operator}")
    
    # Handlers para operadores de comparación
    
    def _evaluate_equals(self, field_value: Any, rule_value: Any) -> bool:
        """Evalúa igualdad."""
        return self._normalize_value(field_value) == self._normalize_value(rule_value)
    
    def _evaluate_not_equals(self, field_value: Any, rule_value: Any) -> bool:
        """Evalúa desigualdad."""
        return self._normalize_value(field_value) != self._normalize_value(rule_value)
    
    def _evaluate_greater(self, field_value: Any, rule_value: Any) -> bool:
        """Evalúa mayor que."""
        try:
            return float(field_value) > float(rule_value)
        except (ValueError, TypeError):
            return False
    
    def _evaluate_greater_equal(self, field_value: Any, rule_value: Any) -> bool:
        """Evalúa mayor o igual que."""
        try:
            return float(field_value) >= float(rule_value)
        except (ValueError, TypeError):
            return False
    
    def _evaluate_less(self, field_value: Any, rule_value: Any) -> bool:
        """Evalúa menor que."""
        try:
            return float(field_value) < float(rule_value)
        except (ValueError, TypeError):
            return False
    
    def _evaluate_less_equal(self, field_value: Any, rule_value: Any) -> bool:
        """Evalúa menor o igual que."""
        try:
            return float(field_value) <= float(rule_value)
        except (ValueError, TypeError):
            return False
    
    def _evaluate_contains(self, field_value: Any, rule_value: Any) -> bool:
        """Evalúa si contiene."""
        field_str = self._normalize_value(field_value)
        rule_str = self._normalize_value(rule_value)
        return rule_str in field_str
    
    def _evaluate_not_contains(self, field_value: Any, rule_value: Any) -> bool:
        """Evalúa si no contiene."""
        return not self._evaluate_contains(field_value, rule_value)
    
    def _evaluate_starts_with(self, field_value: Any, rule_value: Any) -> bool:
        """Evalúa si empieza con."""
        field_str = self._normalize_value(field_value)
        rule_str = self._normalize_value(rule_value)
        return field_str.startswith(rule_str)
    
    def _evaluate_ends_with(self, field_value: Any, rule_value: Any) -> bool:
        """Evalúa si termina con."""
        field_str = self._normalize_value(field_value)
        rule_str = self._normalize_value(rule_value)
        return field_str.endswith(rule_str)
    
    def _normalize_value(self, value: Any) -> str:
        """Normaliza un valor para comparación de strings."""
        if value is None:
            return ""
        return str(value).lower().strip()


def evaluate_rule(expression: str, data: Dict[str, Any]) -> bool:
    """
    Función de conveniencia para evaluar una expresión contra datos.
    
    Args:
        expression: Expresión a evaluar (ej: "genre = 'rock'")
        data: Datos musicales
    
    Returns:
        True si la regla se cumple, False en caso contrario
    """
    from ..parser.expression_parser import parse_expression
    
    ast = parse_expression(expression)
    evaluator = RuleEvaluator()
    return evaluator.evaluate(ast, data) 
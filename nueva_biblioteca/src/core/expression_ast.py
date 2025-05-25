"""
Abstract Syntax Tree para expresiones de reglas musicales.
Representa la estructura lógica de las reglas de playlists inteligentes.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union
from enum import Enum


class NodeType(Enum):
    """Tipos de nodos en el AST."""
    BINARY_OP = "binary_op"
    UNARY_OP = "unary_op"
    COMPARISON = "comparison"
    FIELD = "field"
    VALUE = "value"
    FUNCTION = "function"


class Operator(Enum):
    """Operadores soportados."""
    # Lógicos
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    
    # Comparación
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER = ">"
    GREATER_EQUAL = ">="
    LESS = "<"
    LESS_EQUAL = "<="
    
    # Especiales
    BETWEEN = "BETWEEN"
    IN = "IN"
    CONTAINS = "CONTAINS"
    COMPATIBLE_WITH = "COMPATIBLE_WITH"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"


class ASTNode(ABC):
    """Nodo base del Abstract Syntax Tree."""
    
    def __init__(self, node_type: NodeType):
        self.node_type = node_type
        self.parent = None
        
    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> Any:
        """Evalúa el nodo con el contexto dado."""
        pass
        
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el nodo a diccionario para serialización."""
        pass
        
    @abstractmethod
    def __str__(self) -> str:
        """Representación en string del nodo."""
        pass


class BinaryOpNode(ASTNode):
    """Nodo para operaciones binarias (AND, OR)."""
    
    def __init__(self, operator: Operator, left: ASTNode, right: ASTNode):
        super().__init__(NodeType.BINARY_OP)
        self.operator = operator
        self.left = left
        self.right = right
        left.parent = self
        right.parent = self
        
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evalúa la operación binaria."""
        left_result = self.left.evaluate(context)
        
        # Optimización: short-circuit evaluation
        if self.operator == Operator.AND and not left_result:
            return False
        elif self.operator == Operator.OR and left_result:
            return True
            
        right_result = self.right.evaluate(context)
        
        if self.operator == Operator.AND:
            return left_result and right_result
        elif self.operator == Operator.OR:
            return left_result or right_result
        else:
            raise ValueError(f"Operador binario no soportado: {self.operator}")
            
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "type": self.node_type.value,
            "operator": self.operator.value,
            "left": self.left.to_dict(),
            "right": self.right.to_dict()
        }
        
    def __str__(self) -> str:
        """Representación en string."""
        return f"({self.left} {self.operator.value} {self.right})"


class UnaryOpNode(ASTNode):
    """Nodo para operaciones unarias (NOT)."""
    
    def __init__(self, operator: Operator, operand: ASTNode):
        super().__init__(NodeType.UNARY_OP)
        self.operator = operator
        self.operand = operand
        operand.parent = self
        
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evalúa la operación unaria."""
        operand_result = self.operand.evaluate(context)
        
        if self.operator == Operator.NOT:
            return not operand_result
        else:
            raise ValueError(f"Operador unario no soportado: {self.operator}")
            
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "type": self.node_type.value,
            "operator": self.operator.value,
            "operand": self.operand.to_dict()
        }
        
    def __str__(self) -> str:
        """Representación en string."""
        return f"{self.operator.value} {self.operand}"


class ComparisonNode(ASTNode):
    """Nodo para comparaciones (=, >, <, BETWEEN, etc.)."""
    
    def __init__(self, operator: Operator, field: str, value: Any):
        super().__init__(NodeType.COMPARISON)
        self.operator = operator
        self.field = field
        self.value = value
        
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evalúa la comparación."""
        field_value = context.get(self.field)
        
        if field_value is None:
            return False
            
        try:
            if self.operator == Operator.EQUALS:
                return field_value == self.value
            elif self.operator == Operator.NOT_EQUALS:
                return field_value != self.value
            elif self.operator == Operator.GREATER:
                return field_value > self.value
            elif self.operator == Operator.GREATER_EQUAL:
                return field_value >= self.value
            elif self.operator == Operator.LESS:
                return field_value < self.value
            elif self.operator == Operator.LESS_EQUAL:
                return field_value <= self.value
            elif self.operator == Operator.BETWEEN:
                if isinstance(self.value, (list, tuple)) and len(self.value) == 2:
                    return self.value[0] <= field_value <= self.value[1]
                return False
            elif self.operator == Operator.IN:
                if isinstance(self.value, (list, tuple, set)):
                    return field_value in self.value
                return False
            elif self.operator == Operator.CONTAINS:
                return str(self.value).lower() in str(field_value).lower()
            elif self.operator == Operator.STARTS_WITH:
                return str(field_value).lower().startswith(str(self.value).lower())
            elif self.operator == Operator.ENDS_WITH:
                return str(field_value).lower().endswith(str(self.value).lower())
            elif self.operator == Operator.COMPATIBLE_WITH:
                # Lógica específica para compatibilidad Camelot
                return self._check_camelot_compatibility(field_value, self.value)
            else:
                raise ValueError(f"Operador de comparación no soportado: {self.operator}")
                
        except (TypeError, ValueError) as e:
            # Error en comparación, retornar False
            return False
            
    def _check_camelot_compatibility(self, field_value: str, target_key: str) -> bool:
        """Verifica compatibilidad armónica usando notación Camelot."""
        # Tabla de compatibilidad Camelot simplificada
        camelot_compatibility = {
            '1A': ['1A', '1B', '2A', '12A'],
            '1B': ['1A', '1B', '2B', '12B'],
            '2A': ['1A', '2A', '2B', '3A'],
            '2B': ['1B', '2A', '2B', '3B'],
            '3A': ['2A', '3A', '3B', '4A'],
            '3B': ['2B', '3A', '3B', '4B'],
            '4A': ['3A', '4A', '4B', '5A'],
            '4B': ['3B', '4A', '4B', '5B'],
            '5A': ['4A', '5A', '5B', '6A'],
            '5B': ['4B', '5A', '5B', '6B'],
            '6A': ['5A', '6A', '6B', '7A'],
            '6B': ['5B', '6A', '6B', '7B'],
            '7A': ['6A', '7A', '7B', '8A'],
            '7B': ['6B', '7A', '7B', '8B'],
            '8A': ['7A', '8A', '8B', '9A'],
            '8B': ['7B', '8A', '8B', '9B'],
            '9A': ['8A', '9A', '9B', '10A'],
            '9B': ['8B', '9A', '9B', '10B'],
            '10A': ['9A', '10A', '10B', '11A'],
            '10B': ['9B', '10A', '10B', '11B'],
            '11A': ['10A', '11A', '11B', '12A'],
            '11B': ['10B', '11A', '11B', '12B'],
            '12A': ['11A', '12A', '12B', '1A'],
            '12B': ['11B', '12A', '12B', '1B'],
        }
        
        compatible_keys = camelot_compatibility.get(str(target_key), [])
        return str(field_value) in compatible_keys
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "type": self.node_type.value,
            "operator": self.operator.value,
            "field": self.field,
            "value": self.value
        }
        
    def __str__(self) -> str:
        """Representación en string."""
        if self.operator == Operator.BETWEEN and isinstance(self.value, (list, tuple)):
            return f"{self.field} BETWEEN {self.value[0]} AND {self.value[1]}"
        elif self.operator == Operator.IN and isinstance(self.value, (list, tuple)):
            values_str = ", ".join(str(v) for v in self.value)
            return f"{self.field} IN ({values_str})"
        else:
            return f"{self.field} {self.operator.value} {self.value}"


class FieldNode(ASTNode):
    """Nodo para campos de metadatos."""
    
    def __init__(self, field_name: str):
        super().__init__(NodeType.FIELD)
        self.field_name = field_name
        
    def evaluate(self, context: Dict[str, Any]) -> Any:
        """Obtiene el valor del campo del contexto."""
        return context.get(self.field_name)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "type": self.node_type.value,
            "field_name": self.field_name
        }
        
    def __str__(self) -> str:
        """Representación en string."""
        return self.field_name


class ValueNode(ASTNode):
    """Nodo para valores literales."""
    
    def __init__(self, value: Any):
        super().__init__(NodeType.VALUE)
        self.value = value
        
    def evaluate(self, context: Dict[str, Any]) -> Any:
        """Retorna el valor literal."""
        return self.value
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "type": self.node_type.value,
            "value": self.value
        }
        
    def __str__(self) -> str:
        """Representación en string."""
        if isinstance(self.value, str):
            return f"'{self.value}'"
        return str(self.value)


class ExpressionAST:
    """Árbol de sintaxis abstracta para expresiones de reglas."""
    
    def __init__(self, root: ASTNode = None):
        self.root = root
        
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evalúa toda la expresión."""
        if self.root is None:
            return True
        return bool(self.root.evaluate(context))
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el AST completo a diccionario."""
        return {
            "ast_version": "1.0",
            "root": self.root.to_dict() if self.root else None
        }
        
    def __str__(self) -> str:
        """Representación en string del AST."""
        if self.root is None:
            return "Empty AST"
        return str(self.root)
        
    def get_fields_used(self) -> List[str]:
        """Obtiene lista de campos utilizados en la expresión."""
        fields = set()
        self._collect_fields(self.root, fields)
        return list(fields)
        
    def _collect_fields(self, node: ASTNode, fields: set):
        """Recolecta recursivamente los campos utilizados."""
        if node is None:
            return
            
        if isinstance(node, ComparisonNode):
            fields.add(node.field)
        elif isinstance(node, FieldNode):
            fields.add(node.field_name)
        elif isinstance(node, BinaryOpNode):
            self._collect_fields(node.left, fields)
            self._collect_fields(node.right, fields)
        elif isinstance(node, UnaryOpNode):
            self._collect_fields(node.operand, fields)
            
    def optimize(self) -> 'ExpressionAST':
        """Optimiza el AST eliminando redundancias."""
        if self.root is None:
            return self
            
        optimized_root = self._optimize_node(self.root)
        return ExpressionAST(optimized_root)
        
    def _optimize_node(self, node: ASTNode) -> ASTNode:
        """Optimiza un nodo específico."""
        # Implementar optimizaciones como:
        # - Eliminar dobles negaciones: NOT NOT x -> x
        # - Simplificar constantes: True AND x -> x
        # - Reordenar para eficiencia
        return node  # Por ahora retorna sin optimizar 
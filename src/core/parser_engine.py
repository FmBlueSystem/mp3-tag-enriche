"""
Parser para expresiones de reglas de playlist.
Soporta operadores lógicos, comparaciones y funciones especiales.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum, auto

class NodeType(Enum):
    """Tipos de nodos en el AST."""
    AND = auto()
    OR = auto()
    COMPARISON = auto()
    COMPATIBILITY = auto()  # Para reglas de clave musical
    BETWEEN = auto()
    IN = auto()
    MATCHES = auto()
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    FUNCTION = auto()

@dataclass
class ASTNode:
    """Nodo del árbol de sintaxis abstracta."""
    type: NodeType
    value: Any = None
    left: Optional['ASTNode'] = None
    right: Optional['ASTNode'] = None
    args: List[Any] = None

class ParserError(Exception):
    """Error durante el parsing de una regla."""
    pass

class Parser:
    """Parser para reglas de playlist."""
    
    def __init__(self):
        # Operadores soportados y su precedencia
        self.operators = {
            'AND': 1,
            'OR': 1,
            '>': 2,
            '<': 2,
            '>=': 2,
            '<=': 2,
            '=': 2,
            '!=': 2,
            'IN': 2,
            'BETWEEN': 2,
            'MATCHES': 2,
            'COMPATIBLE_WITH': 2  # Nuevo operador para claves
        }
        
    def parse(self, rule: str) -> ASTNode:
        """
        Parsea una regla y retorna su AST.
        
        Args:
            rule: Regla en formato texto
            
        Returns:
            ASTNode raíz del AST
            
        Raises:
            ParserError: Si hay errores de sintaxis
        """
        try:
            # Tokenizar
            tokens = self._tokenize(rule)
            if not tokens:
                raise ParserError("Regla vacía")
                
            # Parsear
            ast = self._parse_expression(tokens)
            
            # Verificar que se consumieron todos los tokens
            if tokens:
                raise ParserError(f"Tokens no procesados: {tokens}")
                
            return ast
            
        except Exception as e:
            raise ParserError(f"Error parseando regla: {str(e)}")
            
    def _tokenize(self, rule: str) -> List[str]:
        """
        Convierte una regla en tokens.
        
        Args:
            rule: Regla a tokenizar
            
        Returns:
            Lista de tokens
        """
        # Reemplazar operadores especiales
        rule = rule.replace(">=", " >= ")
        rule = rule.replace("<=", " <= ")
        rule = rule.replace("!=", " != ")
        rule = rule.replace("(", " ( ")
        rule = rule.replace(")", " ) ")
        
        # Separar tokens
        tokens = rule.split()
        
        # Procesar strings entre comillas
        result = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Si comienza con comilla pero no termina
            if token.startswith("'") and not token.endswith("'"):
                # Unir tokens hasta encontrar comilla final
                string_tokens = [token]
                i += 1
                while i < len(tokens):
                    next_token = tokens[i]
                    string_tokens.append(next_token)
                    if next_token.endswith("'"):
                        break
                    i += 1
                token = " ".join(string_tokens)
                
            result.append(token)
            i += 1
            
        return result
        
    def _parse_expression(self, tokens: List[str], precedence: int = 0) -> ASTNode:
        """
        Parsea una expresión usando el algoritmo de Pratt.
        
        Args:
            tokens: Lista de tokens
            precedence: Precedencia mínima a considerar
            
        Returns:
            ASTNode raíz de la expresión
        """
        # Obtener primer token
        token = tokens.pop(0)
        
        # Parsear término izquierdo
        left = self._parse_atom(token, tokens)
        
        while tokens and self._get_precedence(tokens[0]) > precedence:
            # Obtener operador
            operator = tokens.pop(0)
            
            # Parsear operador especial BETWEEN
            if operator == "BETWEEN":
                left = self._parse_between(left, tokens)
                continue
                
            # Parsear COMPATIBLE_WITH para claves musicales
            if operator == "COMPATIBLE_WITH":
                left = self._parse_compatibility(left, tokens)
                continue
                
            # Obtener precedencia del operador
            op_precedence = self._get_precedence(operator)
            
            # Parsear término derecho con mayor precedencia
            right = self._parse_expression(tokens, op_precedence)
            
            # Crear nodo según operador
            if operator in ('AND', 'OR'):
                left = ASTNode(
                    type=NodeType[operator],
                    left=left,
                    right=right
                )
            else:
                left = ASTNode(
                    type=NodeType.COMPARISON,
                    value=operator,
                    left=left,
                    right=right
                )
                
        return left
        
    def _parse_atom(self, token: str, tokens: List[str]) -> ASTNode:
        """
        Parsea un átomo (número, string, identificador o subexpresión).
        
        Args:
            token: Token actual
            tokens: Lista de tokens restantes
            
        Returns:
            ASTNode del átomo
        """
        # Subexpresión entre paréntesis
        if token == '(':
            expr = self._parse_expression(tokens)
            if not tokens or tokens.pop(0) != ')':
                raise ParserError("Falta paréntesis de cierre")
            return expr
            
        # String literal
        if token.startswith("'"):
            if not token.endswith("'"):
                raise ParserError("Falta comilla de cierre")
            return ASTNode(
                type=NodeType.STRING,
                value=token[1:-1]
            )
            
        # Número
        try:
            value = float(token)
            return ASTNode(
                type=NodeType.NUMBER,
                value=value
            )
        except ValueError:
            pass
            
        # Identificador
        return ASTNode(
            type=NodeType.IDENTIFIER,
            value=token
        )
        
    def _parse_between(self, left: ASTNode, tokens: List[str]) -> ASTNode:
        """
        Parsea una expresión BETWEEN.
        
        Args:
            left: Nodo izquierdo
            tokens: Lista de tokens restantes
            
        Returns:
            ASTNode de tipo BETWEEN
        """
        if len(tokens) < 3:
            raise ParserError("Expresión BETWEEN incompleta")
            
        # Obtener rango
        range_str = tokens.pop(0)
        if not range_str.count('-') == 1:
            raise ParserError("Rango BETWEEN inválido")
            
        min_val, max_val = range_str.split('-')
        
        try:
            min_val = float(min_val)
            max_val = float(max_val)
        except ValueError:
            raise ParserError("Rango BETWEEN debe ser numérico")
            
        return ASTNode(
            type=NodeType.BETWEEN,
            value=(min_val, max_val),
            left=left
        )
        
    def _parse_compatibility(self, left: ASTNode, tokens: List[str]) -> ASTNode:
        """
        Parsea una expresión de compatibilidad de claves.
        
        Args:
            left: Nodo izquierdo (debe ser campo 'key')
            tokens: Lista de tokens restantes
            
        Returns:
            ASTNode de tipo COMPATIBILITY
        """
        if not tokens:
            raise ParserError("Falta valor para COMPATIBLE_WITH")
            
        # El valor debe ser una clave musical entre comillas
        value = tokens.pop(0)
        if not (value.startswith("'") and value.endswith("'")):
            raise ParserError("Clave musical debe estar entre comillas")
            
        return ASTNode(
            type=NodeType.COMPATIBILITY,
            value=value[1:-1],  # Quitar comillas
            left=left
        )
        
    def _get_precedence(self, operator: str) -> int:
        """
        Retorna la precedencia de un operador.
        
        Args:
            operator: Operador a evaluar
            
        Returns:
            Precedencia del operador (mayor número = mayor precedencia)
        """
        return self.operators.get(operator, 0) 
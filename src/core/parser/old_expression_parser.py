"""
Parser de expresiones para reglas musicales.

Este módulo implementa un parser que puede analizar expresiones de filtros musicales
como: "genre = 'rock' AND year > 2000 OR artist CONTAINS 'beatles'"
"""

import re
from enum import Enum
from typing import List, Dict, Any, Union, Optional
from dataclasses import dataclass


class TokenType(Enum):
    """Tipos de tokens para el parser."""
    STRING = "STRING"
    NUMBER = "NUMBER"
    IDENTIFIER = "IDENTIFIER"
    OPERATOR = "OPERATOR"
    LOGICAL = "LOGICAL"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EOF = "EOF"


class ComparisonOperator(Enum):
    """Operadores de comparación soportados."""
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER = ">"
    GREATER_EQUAL = ">="
    LESS = "<"
    LESS_EQUAL = "<="
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"


class LogicalOperator(Enum):
    """Operadores lógicos soportados."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


@dataclass
class Token:
    """Representa un token en la expresión."""
    type: TokenType
    value: str
    position: int


@dataclass
class ComparisonNode:
    """Nodo que representa una comparación (ej: genre = 'rock')."""
    field: str
    operator: ComparisonOperator
    value: Union[str, int, float]


@dataclass
class LogicalNode:
    """Nodo que representa una operación lógica (AND, OR, NOT)."""
    operator: LogicalOperator
    left: Optional['ExpressionNode']
    right: Optional['ExpressionNode']


# Tipo unión para nodos del AST
ExpressionNode = Union[ComparisonNode, LogicalNode]


class ParseError(Exception):
    """Error durante el parsing de la expresión."""
    pass


class ExpressionLexer:
    """Lexer para tokenizar expresiones musicales."""
    
    # Patrones regex para diferentes tipos de tokens
    TOKEN_PATTERNS = [
        (r'\s+', None),  # Whitespace (ignorar)
        (r"'[^']*'", TokenType.STRING),  # Strings con comillas simples
        (r'"[^"]*"', TokenType.STRING),  # Strings con comillas dobles
        (r'\d+\.\d+', TokenType.NUMBER),  # Números flotantes
        (r'\d+', TokenType.NUMBER),  # Números enteros
        (r'>=|<=|!=|CONTAINS|NOT_CONTAINS|STARTS_WITH|ENDS_WITH', TokenType.OPERATOR),  # Operadores complejos
        (r'[><=]', TokenType.OPERATOR),  # Operadores simples
        (r'AND|OR|NOT', TokenType.LOGICAL),  # Operadores lógicos
        (r'\(', TokenType.LPAREN),  # Paréntesis izquierdo
        (r'\)', TokenType.RPAREN),  # Paréntesis derecho
        (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENTIFIER),  # Identificadores
    ]
    
    def __init__(self, expression: str):
        """Inicializa el lexer con la expresión a analizar."""
        self.expression = expression.strip()
        self.position = 0
        self.tokens: List[Token] = []
        
    def tokenize(self) -> List[Token]:
        """Tokeniza la expresión completa."""
        while self.position < len(self.expression):
            self._next_token()
        
        # Agregar token EOF
        self.tokens.append(Token(TokenType.EOF, "", self.position))
        return self.tokens
    
    def _next_token(self) -> None:
        """Obtiene el siguiente token de la expresión."""
        current_text = self.expression[self.position:]
        
        for pattern, token_type in self.TOKEN_PATTERNS:
            match = re.match(pattern, current_text, re.IGNORECASE)
            if match:
                value = match.group(0)
                
                # Ignorar whitespace
                if token_type is None:
                    self.position += len(value)
                    return
                
                # Limpiar strings (quitar comillas)
                if token_type == TokenType.STRING:
                    value = value[1:-1]  # Remover comillas
                
                self.tokens.append(Token(token_type, value, self.position))
                self.position += len(match.group(0))
                return
        
        # Si no hay match, error
        raise ParseError(f"Token inválido en posición {self.position}: '{current_text[:10]}'")


class ExpressionParser:
    """Parser para convertir tokens en un AST (Abstract Syntax Tree)."""
    
    def __init__(self, tokens: List[Token]):
        """Inicializa el parser con la lista de tokens."""
        self.tokens = tokens
        self.position = 0
        self.current_token = tokens[0] if tokens else Token(TokenType.EOF, "", 0)
    
    def parse(self) -> ExpressionNode:
        """Parsea los tokens y retorna el AST raíz."""
        if not self.tokens or self.tokens[0].type == TokenType.EOF:
            raise ParseError("Expresión vacía")
        
        result = self._parse_or_expression()
        
        if self.current_token.type != TokenType.EOF:
            raise ParseError(f"Tokens inesperados después del final: {self.current_token.value}")
        
        return result
    
    def _advance(self) -> None:
        """Avanza al siguiente token."""
        if self.position < len(self.tokens) - 1:
            self.position += 1
            self.current_token = self.tokens[self.position]
    
    def _parse_or_expression(self) -> ExpressionNode:
        """Parsea expresiones con OR (menor precedencia)."""
        left = self._parse_and_expression()
        
        while self.current_token.type == TokenType.LOGICAL and self.current_token.value.upper() == "OR":
            self._advance()  # consumir OR
            right = self._parse_and_expression()
            left = LogicalNode(LogicalOperator.OR, left, right)
        
        return left
    
    def _parse_and_expression(self) -> ExpressionNode:
        """Parsea expresiones con AND (mayor precedencia que OR)."""
        left = self._parse_not_expression()
        
        while self.current_token.type == TokenType.LOGICAL and self.current_token.value.upper() == "AND":
            self._advance()  # consumir AND
            right = self._parse_not_expression()
            left = LogicalNode(LogicalOperator.AND, left, right)
        
        return left
    
    def _parse_not_expression(self) -> ExpressionNode:
        """Parsea expresiones con NOT (mayor precedencia)."""
        if self.current_token.type == TokenType.LOGICAL and self.current_token.value.upper() == "NOT":
            self._advance()  # consumir NOT
            operand = self._parse_primary_expression()
            return LogicalNode(LogicalOperator.NOT, operand, None)
        
        return self._parse_primary_expression()
    
    def _parse_primary_expression(self) -> ExpressionNode:
        """Parsea expresiones primarias (comparaciones o paréntesis)."""
        if self.current_token.type == TokenType.LPAREN:
            self._advance()  # consumir (
            expr = self._parse_or_expression()
            if self.current_token.type != TokenType.RPAREN:
                raise ParseError("Se esperaba ')'")
            self._advance()  # consumir )
            return expr
        
        return self._parse_comparison()
    
    def _parse_comparison(self) -> ComparisonNode:
        """Parsea una comparación (field operator value)."""
        if self.current_token.type != TokenType.IDENTIFIER:
            raise ParseError(f"Se esperaba un identificador, encontrado: {self.current_token.value}")
        
        field = self.current_token.value
        self._advance()
        
        if self.current_token.type != TokenType.OPERATOR:
            raise ParseError(f"Se esperaba un operador, encontrado: {self.current_token.value}")
        
        operator_str = self.current_token.value.upper()
        try:
            operator = ComparisonOperator(operator_str)
        except ValueError:
            raise ParseError(f"Operador no válido: {operator_str}")
        
        self._advance()
        
        # Obtener valor
        if self.current_token.type == TokenType.STRING:
            value = self.current_token.value
        elif self.current_token.type == TokenType.NUMBER:
            # Convertir a int o float según corresponda
            if '.' in self.current_token.value:
                value = float(self.current_token.value)
            else:
                value = int(self.current_token.value)
        else:
            raise ParseError(f"Se esperaba un valor, encontrado: {self.current_token.value}")
        
        self._advance()
        
        return ComparisonNode(field, operator, value)


def parse_expression(expression: str) -> ComparisonNode:
    expression = expression.strip()
    if not expression:
        raise ParseError("Expresión vacía")
    
    if " = " in expression and "'" in expression:
# Aquí termina el fragmento de 250 líneas.
# Las 16 líneas restantes de expression_parser.py no están incluidas.
# Faltarían las funciones expression_to_string y el if __name__ == "__main__":
        pass # Placeholder para el resto del código que no fue leído 
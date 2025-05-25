"""
Parser de reglas lógicas para Nueva Biblioteca.
Convierte expresiones de texto en Abstract Syntax Trees (AST).
"""
import re
from typing import List, Optional, Tuple, Any, Union
from .expression_ast import (
    ExpressionAST, ASTNode, BinaryOpNode, UnaryOpNode, ComparisonNode,
    Operator, NodeType
)


class RuleParseError(Exception):
    """Excepción para errores de parsing de reglas."""
    
    def __init__(self, message: str, position: int = -1, expression: str = ""):
        super().__init__(message)
        self.message = message
        self.position = position
        self.expression = expression
        
    def __str__(self):
        if self.position >= 0 and self.expression:
            return f"{self.message} en posición {self.position}: '{self.expression}'"
        return self.message


class Token:
    """Token para el lexer."""
    
    def __init__(self, type_: str, value: str, position: int):
        self.type = type_
        self.value = value
        self.position = position
        
    def __repr__(self):
        return f"Token({self.type}, '{self.value}', {self.position})"


class RuleLexer:
    """Lexer para tokenizar expresiones de reglas."""
    
    # Patrones de tokens
    TOKEN_PATTERNS = [
        ('WHITESPACE', r'\s+'),
        ('LPAREN', r'\('),
        ('RPAREN', r'\)'),
        ('AND', r'\bAND\b'),
        ('OR', r'\bOR\b'),
        ('NOT', r'\bNOT\b'),
        ('BETWEEN', r'\bBETWEEN\b'),
        ('IN', r'\bIN\b'),
        ('CONTAINS', r'\bCONTAINS\b'),
        ('COMPATIBLE_WITH', r'\bCOMPATIBLE_WITH\b'),
        ('STARTS_WITH', r'\bSTARTS_WITH\b'),
        ('ENDS_WITH', r'\bENDS_WITH\b'),
        ('GTE', r'>='),
        ('LTE', r'<='),
        ('NE', r'!='),
        ('GT', r'>'),
        ('LT', r'<'),
        ('EQ', r'='),
        ('STRING', r"'([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\""),
        ('NUMBER', r'-?\d+\.?\d*'),
        ('FIELD', r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('COMMA', r','),
        ('SEMICOLON', r';'),
    ]
    
    def __init__(self):
        self.compiled_patterns = [
            (name, re.compile(pattern, re.IGNORECASE))
            for name, pattern in self.TOKEN_PATTERNS
        ]
        
    def tokenize(self, expression: str) -> List[Token]:
        """Tokeniza una expresión en una lista de tokens."""
        tokens = []
        position = 0
        
        while position < len(expression):
            matched = False
            
            for token_type, pattern in self.compiled_patterns:
                match = pattern.match(expression, position)
                if match:
                    value = match.group(0)
                    
                    # Ignorar whitespace
                    if token_type != 'WHITESPACE':
                        tokens.append(Token(token_type, value, position))
                    
                    position = match.end()
                    matched = True
                    break
                    
            if not matched:
                raise RuleParseError(
                    f"Carácter inesperado: '{expression[position]}'",
                    position,
                    expression
                )
                
        return tokens


class RuleParser:
    """Parser recursivo descendente para reglas lógicas."""
    
    def __init__(self):
        self.lexer = RuleLexer()
        self.tokens = []
        self.current_token_index = 0
        self.current_expression = ""
        
    def parse(self, expression: str) -> ExpressionAST:
        """Parsea una expresión y retorna un AST."""
        if not expression or not expression.strip():
            return ExpressionAST()
            
        self.current_expression = expression
        self.tokens = self.lexer.tokenize(expression)
        self.current_token_index = 0
        
        if not self.tokens:
            return ExpressionAST()
            
        try:
            root = self._parse_or_expression()
            
            # Verificar que no queden tokens sin procesar
            if self.current_token_index < len(self.tokens):
                unexpected_token = self.tokens[self.current_token_index]
                raise RuleParseError(
                    f"Token inesperado: '{unexpected_token.value}'",
                    unexpected_token.position,
                    expression
                )
                
            return ExpressionAST(root)
            
        except RuleParseError:
            raise
        except Exception as e:
            raise RuleParseError(f"Error de parsing: {str(e)}", -1, expression)
            
    def _current_token(self) -> Optional[Token]:
        """Obtiene el token actual."""
        if self.current_token_index < len(self.tokens):
            return self.tokens[self.current_token_index]
        return None
        
    def _consume_token(self, expected_type: str = None) -> Token:
        """Consume el token actual y avanza al siguiente."""
        if self.current_token_index >= len(self.tokens):
            raise RuleParseError(
                f"Se esperaba token {expected_type or 'cualquiera'} pero se llegó al final",
                -1,
                self.current_expression
            )
            
        token = self.tokens[self.current_token_index]
        
        if expected_type and token.type != expected_type:
            raise RuleParseError(
                f"Se esperaba {expected_type} pero se encontró {token.type}",
                token.position,
                self.current_expression
            )
            
        self.current_token_index += 1
        return token
        
    def _parse_or_expression(self) -> ASTNode:
        """Parsea expresiones OR (menor precedencia)."""
        left = self._parse_and_expression()
        
        while (self._current_token() and 
               self._current_token().type == 'OR'):
            self._consume_token('OR')
            right = self._parse_and_expression()
            left = BinaryOpNode(Operator.OR, left, right)
            
        return left
        
    def _parse_and_expression(self) -> ASTNode:
        """Parsea expresiones AND (precedencia media)."""
        left = self._parse_not_expression()
        
        while (self._current_token() and 
               self._current_token().type == 'AND'):
            self._consume_token('AND')
            right = self._parse_not_expression()
            left = BinaryOpNode(Operator.AND, left, right)
            
        return left
        
    def _parse_not_expression(self) -> ASTNode:
        """Parsea expresiones NOT (alta precedencia)."""
        if (self._current_token() and 
            self._current_token().type == 'NOT'):
            self._consume_token('NOT')
            operand = self._parse_primary_expression()
            return UnaryOpNode(Operator.NOT, operand)
        else:
            return self._parse_primary_expression()
            
    def _parse_primary_expression(self) -> ASTNode:
        """Parsea expresiones primarias (comparaciones y paréntesis)."""
        token = self._current_token()
        
        if not token:
            raise RuleParseError(
                "Se esperaba expresión pero se llegó al final",
                -1,
                self.current_expression
            )
            
        # Paréntesis
        if token.type == 'LPAREN':
            self._consume_token('LPAREN')
            expr = self._parse_or_expression()
            self._consume_token('RPAREN')
            return expr
            
        # Campo (inicio de comparación)
        elif token.type == 'FIELD':
            return self._parse_comparison()
            
        else:
            raise RuleParseError(
                f"Token inesperado: '{token.value}'",
                token.position,
                self.current_expression
            )
            
    def _parse_comparison(self) -> ComparisonNode:
        """Parsea comparaciones (field operator value)."""
        field_token = self._consume_token('FIELD')
        field_name = field_token.value
        
        operator_token = self._current_token()
        if not operator_token:
            raise RuleParseError(
                f"Se esperaba operador después del campo '{field_name}'",
                field_token.position + len(field_name),
                self.current_expression
            )
            
        # Mapear tokens a operadores
        operator_map = {
            'EQ': Operator.EQUALS,
            'NE': Operator.NOT_EQUALS,
            'GT': Operator.GREATER,
            'GTE': Operator.GREATER_EQUAL,
            'LT': Operator.LESS,
            'LTE': Operator.LESS_EQUAL,
            'BETWEEN': Operator.BETWEEN,
            'IN': Operator.IN,
            'CONTAINS': Operator.CONTAINS,
            'COMPATIBLE_WITH': Operator.COMPATIBLE_WITH,
            'STARTS_WITH': Operator.STARTS_WITH,
            'ENDS_WITH': Operator.ENDS_WITH,
        }
        
        if operator_token.type not in operator_map:
            raise RuleParseError(
                f"Operador no válido: '{operator_token.value}'",
                operator_token.position,
                self.current_expression
            )
            
        operator = operator_map[operator_token.type]
        self._consume_token(operator_token.type)
        
        # Parsear valor según el operador
        if operator == Operator.BETWEEN:
            value = self._parse_between_value()
        elif operator == Operator.IN:
            value = self._parse_in_value()
        else:
            value = self._parse_single_value()
            
        return ComparisonNode(operator, field_name, value)
        
    def _parse_single_value(self) -> Any:
        """Parsea un valor simple (string, number)."""
        token = self._current_token()
        
        if not token:
            raise RuleParseError(
                "Se esperaba valor",
                -1,
                self.current_expression
            )
            
        if token.type == 'STRING':
            self._consume_token('STRING')
            # Remover comillas y procesar escapes
            value = token.value[1:-1]  # Quitar comillas
            value = value.replace("\\'", "'").replace('\\"', '"')
            return value
            
        elif token.type == 'NUMBER':
            self._consume_token('NUMBER')
            if '.' in token.value:
                return float(token.value)
            else:
                return int(token.value)
                
        elif token.type == 'FIELD':
            # Permitir campos como valores (para comparaciones entre campos)
            self._consume_token('FIELD')
            return token.value
            
        else:
            raise RuleParseError(
                f"Tipo de valor no válido: '{token.value}'",
                token.position,
                self.current_expression
            )
            
    def _parse_between_value(self) -> Tuple[Any, Any]:
        """Parsea valor BETWEEN (value1 AND value2)."""
        value1 = self._parse_single_value()
        
        # Consumir AND
        and_token = self._current_token()
        if not and_token or and_token.type != 'AND':
            raise RuleParseError(
                "Se esperaba 'AND' después del primer valor en BETWEEN",
                and_token.position if and_token else -1,
                self.current_expression
            )
        self._consume_token('AND')
        
        value2 = self._parse_single_value()
        return (value1, value2)
        
    def _parse_in_value(self) -> List[Any]:
        """Parsea valor IN (value1, value2, ...)."""
        values = []
        
        # Puede tener paréntesis opcionales
        has_parens = False
        if (self._current_token() and 
            self._current_token().type == 'LPAREN'):
            has_parens = True
            self._consume_token('LPAREN')
            
        # Primer valor
        values.append(self._parse_single_value())
        
        # Valores adicionales separados por comas
        while (self._current_token() and 
               self._current_token().type == 'COMMA'):
            self._consume_token('COMMA')
            values.append(self._parse_single_value())
            
        # Cerrar paréntesis si se abrió
        if has_parens:
            self._consume_token('RPAREN')
            
        return values
        
    def validate_syntax(self, expression: str) -> Tuple[bool, Optional[str]]:
        """Valida la sintaxis de una expresión sin crear el AST."""
        try:
            self.parse(expression)
            return True, None
        except RuleParseError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"
            
    def get_fields_from_expression(self, expression: str) -> List[str]:
        """Extrae los campos utilizados en una expresión."""
        try:
            ast = self.parse(expression)
            return ast.get_fields_used()
        except RuleParseError:
            return []
            
    def format_expression(self, expression: str) -> str:
        """Formatea una expresión para mejor legibilidad."""
        try:
            ast = self.parse(expression)
            return str(ast)
        except RuleParseError:
            return expression  # Retornar original si no se puede parsear


# Funciones de utilidad
def parse_rule(expression: str) -> ExpressionAST:
    """Función de conveniencia para parsear una regla."""
    parser = RuleParser()
    return parser.parse(expression)


def validate_rule_syntax(expression: str) -> Tuple[bool, Optional[str]]:
    """Función de conveniencia para validar sintaxis."""
    parser = RuleParser()
    return parser.validate_syntax(expression)


def get_rule_fields(expression: str) -> List[str]:
    """Función de conveniencia para obtener campos de una regla."""
    parser = RuleParser()
    return parser.get_fields_from_expression(expression)


# Ejemplos de uso y testing
if __name__ == "__main__":
    # Ejemplos de reglas válidas
    test_expressions = [
        "genre = 'House'",
        "bpm > 120",
        "bpm BETWEEN 120 AND 140",
        "genre IN ('House', 'Techno', 'Trance')",
        "artist CONTAINS 'deadmau5'",
        "key COMPATIBLE_WITH '8A'",
        "(genre = 'House' OR genre = 'Techno') AND bpm > 120",
        "NOT (year < 2010) AND energy > 0.7",
        "title STARTS_WITH 'The' AND duration > 180",
        "album ENDS_WITH 'Remix' OR artist = 'Skrillex'"
    ]
    
    parser = RuleParser()
    
    print("🧪 Testing Rule Parser")
    print("=" * 50)
    
    for expr in test_expressions:
        print(f"\n📝 Expresión: {expr}")
        try:
            ast = parser.parse(expr)
            print(f"✅ Parseado exitosamente")
            print(f"🌳 AST: {ast}")
            print(f"📊 Campos utilizados: {ast.get_fields_used()}")
            
            # Test de evaluación con datos de ejemplo
            test_context = {
                'genre': 'House',
                'bpm': 128,
                'year': 2020,
                'energy': 0.8,
                'key': '8A',
                'artist': 'deadmau5',
                'title': 'The Veldt',
                'album': 'Album Title Remix',
                'duration': 240
            }
            
            result = ast.evaluate(test_context)
            print(f"🎯 Evaluación con datos test: {result}")
            
        except RuleParseError as e:
            print(f"❌ Error de parsing: {e}")
        except Exception as e:
            print(f"💥 Error inesperado: {e}")
            
    print("\n" + "=" * 50)
    print("✅ Testing completado") 
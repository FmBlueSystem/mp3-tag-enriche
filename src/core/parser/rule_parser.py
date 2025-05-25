import re
from typing import Dict, List, Union, Any
from dataclasses import dataclass
from enum import Enum

class OperatorType(Enum):
    """Tipos de operadores soportados."""
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    STARTS_WITH = "STARTS WITH"
    ENDS_WITH = "ENDS WITH"
    BETWEEN = "BETWEEN"
    IN = "IN"
    NOT_IN = "NOT_IN"

class LogicalOperator(Enum):
    """Operadores lógicos."""
    AND = "AND"
    OR = "OR"

@dataclass
class Condition:
    """Representa una condición individual como 'genre = Rock'."""
    field: str
    operator: OperatorType
    value: Any
    
    def __str__(self):
        return f"{self.field} {self.operator.value} {self.value}"

@dataclass
class LogicalExpression:
    """Representa una expresión lógica completa."""
    conditions: List[Union[Condition, 'LogicalExpression']]
    operators: List[LogicalOperator]
    
    def __str__(self):
        if not self.conditions:
            return ""
        
        result = str(self.conditions[0])
        for i, op in enumerate(self.operators):
            if i + 1 < len(self.conditions):
                result += f" {op.value} {self.conditions[i + 1]}"
        return result

class RuleParser:
    """Parser para reglas de playlists inteligentes."""
    
    # Campos válidos en la base de datos
    VALID_FIELDS = {
        'title', 'artist', 'album', 'genre', 'year', 'duration', 
        'bpm', 'key', 'energy', 'rating', 'play_count', 'track_number',
        'danceability', 'moods'
    }
    
    # Mapeo de operadores de texto a enum
    OPERATOR_MAP = {
        '=': OperatorType.EQUALS,
        '!=': OperatorType.NOT_EQUALS,
        '>': OperatorType.GREATER_THAN,
        '<': OperatorType.LESS_THAN,
        '>=': OperatorType.GREATER_EQUAL,
        '<=': OperatorType.LESS_EQUAL,
        'contains': OperatorType.CONTAINS,
        'not contains': OperatorType.NOT_CONTAINS,
        'starts with': OperatorType.STARTS_WITH,
        'ends with': OperatorType.ENDS_WITH,
        'between': OperatorType.BETWEEN,  # Nuevo
        'in': OperatorType.IN,
        'not in': OperatorType.NOT_IN
    }
    
    def __init__(self):
        self.tokens = []
        self.current_token_index = 0
    
    def parse(self, rule_text: str) -> LogicalExpression:
        """
        Parsea una regla de texto y devuelve una LogicalExpression.
        
        Ejemplos de reglas soportadas:
        - "genre = 'Rock'"
        - "bpm > 120 AND energy >= 7"
        - "year >= 2020 OR (genre = 'Electronic' AND bpm > 128)"
        """
        if not rule_text or not rule_text.strip():
            raise ValueError("La regla no puede estar vacía")
        
        # Tokenizar la entrada
        self.tokens = self._tokenize(rule_text)
        self.current_token_index = 0
        
        # Parsear la expresión
        return self._parse_expression()
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokeniza el texto de la regla en componentes."""
        # Patrón para capturar: palabras, operadores, números, strings entre comillas, paréntesis, corchetes, comas
        pattern = r'''
            (?P<STRING>'[^']*'|"[^"]*")     |  # Strings entre comillas
            (?P<NUMBER>\d+\.?\d*)           |  # Números (enteros o decimales)
            (?P<OPERATOR>>=|<=|!=|>|<|=)    |  # Operadores de comparación
            (?P<LOGICAL>AND|OR)             |  # Operadores lógicos
            (?P<PAREN>\(|\))                |  # Paréntesis ( )
            (?P<BRACKET>\[|\])              |  # Corchetes [ ]
            (?P<COMMA>,)                    |  # Coma
            (?P<WORD>\w+)                   |  # Palabras (campos, valores, operadores textuales como CONTAINS)
            (?P<WHITESPACE>\s+)                # Espacios en blanco
        '''
        
        tokens = []
        for match in re.finditer(pattern, text, re.VERBOSE | re.IGNORECASE):
            token = match.group()
            # Ignorar espacios en blanco
            if match.lastgroup != 'WHITESPACE':
                tokens.append(token)
        
        return tokens
    
    def _current_token(self) -> str:
        """Devuelve el token actual."""
        if self.current_token_index < len(self.tokens):
            return self.tokens[self.current_token_index]
        return ""
    
    def _consume_token(self) -> str:
        """Consume y devuelve el token actual."""
        token = self._current_token()
        self.current_token_index += 1
        return token
    
    def _parse_expression(self) -> LogicalExpression:
        """Parsea una expresión lógica completa."""
        conditions = []
        operators = []
        
        # Parsear la primera condición o sub-expresión
        conditions.append(self._parse_term())
        
        # Parsear operadores lógicos y condiciones adicionales
        while self._current_token().upper() in ['AND', 'OR']:
            op_token = self._consume_token().upper()
            operators.append(LogicalOperator(op_token))
            conditions.append(self._parse_term())
        
        return LogicalExpression(conditions=conditions, operators=operators)
    
    def _parse_term(self) -> Union[Condition, LogicalExpression]:
        """Parsea un término (condición simple o expresión entre paréntesis)."""
        if self._current_token() == '(':
            # Expresión entre paréntesis
            self._consume_token()  # Consumir '('
            expr = self._parse_expression()
            if self._current_token() != ')':
                raise ValueError("Se esperaba ')' para cerrar la expresión")
            self._consume_token()  # Consumir ')'
            return expr
        else:
            # Condición simple
            return self._parse_condition()
    
    def _parse_condition(self) -> Condition:
        """Parsea una condición individual como 'genre = Rock'."""
        # Parsear campo
        field = self._consume_token()
        if field.lower() not in self.VALID_FIELDS:
            raise ValueError(f"Campo no válido: {field}. Campos válidos: {', '.join(self.VALID_FIELDS)}")
        
        # Parsear operador
        op_part1 = self._consume_token().lower()
        operator_str = op_part1
        
        # Verificar operadores de dos palabras (ej. "starts with", "not in") y operador "between"
        if op_part1 in ['starts', 'ends', 'not', 'between']:
            if self.current_token_index < len(self.tokens):
                op_part2 = self.tokens[self.current_token_index].lower() # No consumir aún, solo peek
                potential_double_op = f"{op_part1} {op_part2}"
                if potential_double_op in self.OPERATOR_MAP:
                    self._consume_token() # Ahora sí consumir la segunda parte
                    operator_str = potential_double_op
        
        if operator_str not in self.OPERATOR_MAP:
            # Si después de intentar componer, no es válido, o si era de una sola palabra y no es válido
            raise ValueError(f"Operador no válido: {operator_str} (original: {op_part1}). Válidos: {list(self.OPERATOR_MAP.keys())}")
        operator = self.OPERATOR_MAP[operator_str]
        
        # Parsear valor(es) - BETWEEN requiere tratamiento especial
        if operator == OperatorType.BETWEEN:
            # Para BETWEEN, esperamos: valor1 AND valor2
            value1 = self._parse_value()
            
            # Verificar que el siguiente token sea AND
            and_token = self._consume_token()
            if and_token.upper() != 'AND':
                raise ValueError(f"Se esperaba 'AND' después del primer valor en BETWEEN, pero se encontró: {and_token}")
            
            value2 = self._parse_value()
            value = [value1, value2]  # Almacenar como lista de dos elementos
        else:
            value = self._parse_value()
        
        # Validar tipo de valor para ciertos operadores
        if operator in [OperatorType.IN, OperatorType.NOT_IN] and not isinstance(value, list):
            raise ValueError(f"El operador {operator.value} requiere una lista de valores. Ej: field IN ['val1', 'val2']")
        
        if operator == OperatorType.BETWEEN and (not isinstance(value, list) or len(value) != 2):
            raise ValueError(f"El operador BETWEEN requiere exactamente dos valores. Ej: field BETWEEN valor1 AND valor2")

        return Condition(field=field.lower(), operator=operator, value=value)
    
    def _parse_value(self) -> Any:
        """Parsea un valor (string, número, lista)."""
        token = self._consume_token()
        
        # Verificar que hay un token válido
        if not token:
            raise ValueError("Se esperaba un valor pero no se encontró ninguno")
        
        # String entre comillas
        if token.startswith(("'", '"')) and token.endswith(("'", '"')):
            return token[1:-1]  # Remover comillas
        
        # Número
        if re.match(r'^\d+\.?\d*$', token):
            return float(token) if '.' in token else int(token)
        
        # Lista (para operadores IN/NOT_IN)
        if token == '[':
            values = []
            # Manejar lista vacía: []
            if self._current_token() == ']':
                self._consume_token() # Consumir ']'
                return values

            while True:
                values.append(self._parse_value()) # Parsea el primer valor o el siguiente después de una coma
                
                next_token_after_value = self._current_token()
                
                if next_token_after_value == ']':
                    self._consume_token() # Consumir ']'
                    return values
                elif next_token_after_value == ',':
                    self._consume_token() # Consumir ','
                    # Si después de la coma viene el cierre, es una coma opcional al final
                    if self._current_token() == ']':
                        self._consume_token() # Consumir ']'
                        return values
                    # Si después de la coma viene otro token que no es ']', continuamos el bucle
                    # para parsear el siguiente valor. No hacer nada aquí, el bucle continuará.
                    continue # Asegura que volvemos al inicio del while para parsear el siguiente valor
                else:
                    # Si después de un valor no viene ni ']' ni ',', es un error.
                    raise ValueError(f"Se esperaba ',' o ']' después del valor en la lista, pero se encontró: {next_token_after_value}")
        
        # Valor sin comillas (asumimos string para campos, o podría ser error si no es campo)
        # Esta parte podría necesitar revisión dependiendo de si los valores siempre deben estar entre comillas
        return token

def validate_rule(rule_text: str) -> bool:
    """
    Valida si una regla es sintácticamente correcta.
    
    Args:
        rule_text: Texto de la regla a validar
        
    Returns:
        True si la regla es válida, False en caso contrario
    """
    try:
        parser = RuleParser()
        parser.parse(rule_text)
        return True
    except Exception:
        return False

def parse_rule(rule_text: str) -> LogicalExpression:
    """
    Función de conveniencia para parsear una regla.
    
    Args:
        rule_text: Texto de la regla a parsear
        
    Returns:
        LogicalExpression parseada
        
    Raises:
        ValueError: Si la regla no es válida
    """
    parser = RuleParser()
    return parser.parse(rule_text)

# Ejemplos de uso
if __name__ == "__main__":
    # Ejemplos de reglas
    test_rules = [
        "genre = 'Rock'",
        "bpm > 120",
        "year >= 2020 AND energy > 5",
        "genre = 'Electronic' OR genre = 'Techno'",
        "(year > 2020 AND bpm > 128) OR rating >= 4"
    ]
    
    parser = RuleParser()
    
    for rule in test_rules:
        print(f"\nRegla: {rule}")
        try:
            parsed = parser.parse(rule)
            print(f"Parseada: {parsed}")
            print(f"Válida: {validate_rule(rule)}")
        except Exception as e:
            print(f"Error: {e}") 
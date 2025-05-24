"""
Parser y evaluador de expresiones lógicas para reglas musicales avanzadas.

Permite analizar y evaluar expresiones tipo:
    (BPM BETWEEN 120 140) AND (key COMPATIBLE_WITH '8A') AND (energy > 0.7)
Soporta operadores: AND, OR, NOT, BETWEEN, IN, =, !=, >, <, >=, <=, COMPATIBLE_WITH

Cumple PEP8 y PEP257.
"""

import re
from typing import Any, Dict, List, Tuple, Callable, Union

class ParseError(Exception):
    """Excepción para errores de parsing de reglas."""
    pass

class Token:
    """Representa un token en la expresión."""
    def __init__(self, type_: str, value: Any):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value})"

def tokenize(expr: str) -> List[Token]:
    """
    Convierte una expresión en una lista de tokens.
    """
    token_specification = [
        ('NUMBER',   r'\d+(\.\d+)?'),
        ('AND',      r'\bAND\b'),
        ('OR',       r'\bOR\b'),
        ('NOT',      r'\bNOT\b'),
        ('BETWEEN',  r'\bBETWEEN\b'),
        ('IN',       r'\bIN\b'),
        ('COMPATIBLE_WITH', r'\bCOMPATIBLE_WITH\b'),
        ('GE',       r'>='),
        ('LE',       r'<='),
        ('GT',       r'>'),
        ('LT',       r'<'),
        ('EQ',       r'='),
        ('NEQ',      r'!='),
        ('LPAREN',   r'\('),
        ('RPAREN',   r'\)'),
        ('COMMA',    r','),
        ('STRING',   r"'[^']*'|\"[^\"]*\""),
        ('IDENT',    r'[A-Za-z_][A-Za-z0-9_]*'),
        ('SKIP',     r'[ \t]+'),
        ('MISMATCH', r'.'),
    ]
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
    get_token = re.compile(tok_regex).match
    pos = 0
    tokens = []
    mo = get_token(expr, pos)
    while mo:
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'NUMBER':
            value = float(value) if '.' in value else int(value)
            tokens.append(Token('NUMBER', value))
        elif kind in ('AND', 'OR', 'NOT', 'BETWEEN', 'IN', 'COMPATIBLE_WITH', 'GE', 'LE', 'GT', 'LT', 'EQ', 'NEQ', 'LPAREN', 'RPAREN', 'COMMA'):
            tokens.append(Token(kind, value))
        elif kind == 'STRING':
            tokens.append(Token('STRING', value.strip("'\"")))
        elif kind == 'IDENT':
            tokens.append(Token('IDENT', value))
        elif kind == 'SKIP':
            pass
        elif kind == 'MISMATCH':
            raise ParseError(f"Caracter inesperado: {value!r}")
        pos = mo.end()
        mo = get_token(expr, pos)
    return tokens

class ASTNode:
    """Nodo del árbol de sintaxis abstracta."""
    def __init__(self, type_: str, value: Any = None, children: List['ASTNode'] = None):
        self.type = type_
        self.value = value
        self.children = children or []

    def __repr__(self):
        return f"ASTNode({self.type}, {self.value}, {self.children})"

class RuleParser:
    """
    Parser recursivo descendente para expresiones lógicas musicales.
    """
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token('EOF', None)

    def eat(self, type_: str) -> Token:
        token = self.current()
        if token.type == type_:
            self.pos += 1
            return token
        raise ParseError(f"Esperado {type_}, encontrado {token.type}")

    def parse(self) -> ASTNode:
        node = self.expr()
        if self.current().type != 'EOF':
            raise ParseError("Tokens restantes después del parseo")
        return node

    def expr(self) -> ASTNode:
        node = self.term()
        while self.current().type in ('OR',):
            op = self.eat(self.current().type)
            right = self.term()
            node = ASTNode('OR', op.value, [node, right])
        return node

    def term(self) -> ASTNode:
        node = self.factor()
        while self.current().type in ('AND',):
            op = self.eat(self.current().type)
            right = self.factor()
            node = ASTNode('AND', op.value, [node, right])
        return node

    def factor(self) -> ASTNode:
        token = self.current()
        if token.type == 'NOT':
            self.eat('NOT')
            node = self.factor()
            return ASTNode('NOT', 'NOT', [node])
        elif token.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.expr()
            self.eat('RPAREN')
            return node
        else:
            return self.condition()

    def condition(self) -> ASTNode:
        field = self.eat('IDENT').value
        op_token = self.current()
        if op_token.type in ('EQ', 'NEQ', 'GT', 'LT', 'GE', 'LE'):
            op = self.eat(op_token.type).type
            value = self.value()
            return ASTNode('COND', (field, op), [ASTNode('VALUE', value)])
        elif op_token.type == 'BETWEEN':
            self.eat('BETWEEN')
            low = self.value()
            high = self.value()
            return ASTNode('BETWEEN', field, [ASTNode('VALUE', low), ASTNode('VALUE', high)])
        elif op_token.type == 'IN':
            self.eat('IN')
            self.eat('LPAREN')
            values = []
            while True:
                values.append(self.value())
                if self.current().type == 'COMMA':
                    self.eat('COMMA')
                else:
                    break
            self.eat('RPAREN')
            return ASTNode('IN', field, [ASTNode('VALUE', values)])
        elif op_token.type == 'COMPATIBLE_WITH':
            self.eat('COMPATIBLE_WITH')
            value = self.value()
            return ASTNode('COMPATIBLE_WITH', field, [ASTNode('VALUE', value)])
        else:
            raise ParseError(f"Operador desconocido: {op_token.type}")

    def value(self) -> Any:
        token = self.current()
        if token.type == 'NUMBER':
            return self.eat('NUMBER').value
        elif token.type == 'STRING':
            return self.eat('STRING').value
        elif token.type == 'IDENT':
            return self.eat('IDENT').value
        else:
            raise ParseError(f"Valor inesperado: {token.type}")

def parse_rule_expression(expr: str) -> ASTNode:
    """
    Parsea una expresión de regla y devuelve el AST.
    """
    tokens = tokenize(expr)
    parser = RuleParser(tokens)
    return parser.parse()

def evaluate_ast(node: ASTNode, track: Dict[str, Any], compat_func: Callable[[str, str], bool] = None) -> bool:
    """
    Evalúa el AST de una regla sobre un track.
    """
    if node.type == 'AND':
        return all(evaluate_ast(child, track, compat_func) for child in node.children)
    elif node.type == 'OR':
        return any(evaluate_ast(child, track, compat_func) for child in node.children)
    elif node.type == 'NOT':
        return not evaluate_ast(node.children[0], track, compat_func)
    elif node.type == 'COND':
        field, op = node.value
        value = node.children[0].value
        track_value = track.get(field)
        if op == 'EQ':
            return track_value == value
        elif op == 'NEQ':
            return track_value != value
        elif op == 'GT':
            return track_value is not None and track_value > value
        elif op == 'LT':
            return track_value is not None and track_value < value
        elif op == 'GE':
            return track_value is not None and track_value >= value
        elif op == 'LE':
            return track_value is not None and track_value <= value
        else:
            return False
    elif node.type == 'BETWEEN':
        field = node.value
        low = node.children[0].value
        high = node.children[1].value
        track_value = track.get(field)
        return track_value is not None and low <= track_value <= high
    elif node.type == 'IN':
        field = node.value
        values = node.children[0].value
        track_value = track.get(field)
        return track_value in values
    elif node.type == 'COMPATIBLE_WITH':
        field = node.value
        value = node.children[0].value
        track_value = track.get(field)
        if compat_func:
            return compat_func(track_value, value)
        return False
    else:
        raise ValueError(f"Tipo de nodo desconocido: {node.type}")

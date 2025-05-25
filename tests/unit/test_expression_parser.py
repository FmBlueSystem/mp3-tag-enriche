"""
Tests unitarios para el parser de expresiones musicales.
"""

import pytest
from src.core.parser.expression_parser import (
    parse_expression,
    expression_to_string,
    ParseError,
    ComparisonNode,
    LogicalNode,
    ComparisonOperator,
    LogicalOperator,
    ExpressionLexer,
    TokenType
)


class TestExpressionLexer:
    """Tests para el lexer de expresiones."""
    
    def test_tokenize_simple_comparison(self):
        """Test tokenización de comparación simple."""
        lexer = ExpressionLexer("genre = 'rock'")
        tokens = lexer.tokenize()
        
        assert len(tokens) == 4  # identifier, operator, string, EOF
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "genre"
        assert tokens[1].type == TokenType.OPERATOR
        assert tokens[1].value == "="
        assert tokens[2].type == TokenType.STRING
        assert tokens[2].value == "rock"
        assert tokens[3].type == TokenType.EOF
    
    def test_tokenize_number_comparison(self):
        """Test tokenización con números."""
        lexer = ExpressionLexer("year > 2000")
        tokens = lexer.tokenize()
        
        assert tokens[0].value == "year"
        assert tokens[1].value == ">"
        assert tokens[2].type == TokenType.NUMBER
        assert tokens[2].value == "2000"
    
    def test_tokenize_float_number(self):
        """Test tokenización con números flotantes."""
        lexer = ExpressionLexer("rating >= 4.5")
        tokens = lexer.tokenize()
        
        assert tokens[2].type == TokenType.NUMBER
        assert tokens[2].value == "4.5"
    
    def test_tokenize_complex_operators(self):
        """Test tokenización de operadores complejos."""
        lexer = ExpressionLexer("artist CONTAINS 'beatles'")
        tokens = lexer.tokenize()
        
        assert tokens[1].type == TokenType.OPERATOR
        assert tokens[1].value == "CONTAINS"
    
    def test_tokenize_logical_operators(self):
        """Test tokenización de operadores lógicos."""
        lexer = ExpressionLexer("genre = 'rock' AND year > 2000")
        tokens = lexer.tokenize()
        
        logical_token = next(t for t in tokens if t.type == TokenType.LOGICAL)
        assert logical_token.value == "AND"
    
    def test_tokenize_parentheses(self):
        """Test tokenización de paréntesis."""
        lexer = ExpressionLexer("(genre = 'rock')")
        tokens = lexer.tokenize()
        
        assert tokens[0].type == TokenType.LPAREN
        assert tokens[-2].type == TokenType.RPAREN  # -1 es EOF
    
    def test_tokenize_double_quotes(self):
        """Test tokenización con comillas dobles."""
        lexer = ExpressionLexer('artist = "The Beatles"')
        tokens = lexer.tokenize()
        
        string_token = next(t for t in tokens if t.type == TokenType.STRING)
        assert string_token.value == "The Beatles"


class TestExpressionParser:
    """Tests para el parser de expresiones."""
    
    def test_parse_simple_comparison(self):
        """Test parsing de comparación simple."""
        ast = parse_expression("genre = 'rock'")
        
        assert isinstance(ast, ComparisonNode)
        assert ast.field == "genre"
        assert ast.operator == ComparisonOperator.EQUALS
        assert ast.value == "rock"
    
    def test_parse_number_comparison(self):
        """Test parsing con números."""
        ast = parse_expression("year > 2000")
        
        assert isinstance(ast, ComparisonNode)
        assert ast.field == "year"
        assert ast.operator == ComparisonOperator.GREATER
        assert ast.value == 2000
        assert isinstance(ast.value, int)
    
    def test_parse_float_comparison(self):
        """Test parsing con números flotantes."""
        ast = parse_expression("rating >= 4.5")
        
        assert isinstance(ast, ComparisonNode)
        assert ast.value == 4.5
        assert isinstance(ast.value, float)
    
    def test_parse_contains_operator(self):
        """Test parsing del operador CONTAINS."""
        ast = parse_expression("artist CONTAINS 'beatles'")
        
        assert isinstance(ast, ComparisonNode)
        assert ast.operator == ComparisonOperator.CONTAINS
    
    def test_parse_and_expression(self):
        """Test parsing de expresión con AND."""
        ast = parse_expression("genre = 'rock' AND year > 2000")
        
        assert isinstance(ast, LogicalNode)
        assert ast.operator == LogicalOperator.AND
        assert isinstance(ast.left, ComparisonNode)
        assert isinstance(ast.right, ComparisonNode)
        assert ast.left.field == "genre"
        assert ast.right.field == "year"
    
    def test_parse_or_expression(self):
        """Test parsing de expresión con OR."""
        ast = parse_expression("genre = 'rock' OR genre = 'pop'")
        
        assert isinstance(ast, LogicalNode)
        assert ast.operator == LogicalOperator.OR
    
    def test_parse_not_expression(self):
        """Test parsing de expresión con NOT."""
        ast = parse_expression("NOT genre = 'rock'")
        
        assert isinstance(ast, LogicalNode)
        assert ast.operator == LogicalOperator.NOT
        assert isinstance(ast.left, ComparisonNode)
        assert ast.right is None
    
    def test_parse_parentheses(self):
        """Test parsing con paréntesis."""
        ast = parse_expression("(genre = 'rock' OR genre = 'pop') AND year > 2000")
        
        assert isinstance(ast, LogicalNode)
        assert ast.operator == LogicalOperator.AND
        assert isinstance(ast.left, LogicalNode)  # El OR entre paréntesis
        assert ast.left.operator == LogicalOperator.OR
    
    def test_parse_complex_expression(self):
        """Test parsing de expresión compleja."""
        expression = "genre = 'rock' AND year > 2000 OR (artist CONTAINS 'beatles' AND rating >= 4.0)"
        ast = parse_expression(expression)
        
        assert isinstance(ast, LogicalNode)
        assert ast.operator == LogicalOperator.OR
    
    def test_operator_precedence(self):
        """Test precedencia de operadores (AND antes que OR)."""
        ast = parse_expression("genre = 'rock' OR genre = 'pop' AND year > 2000")
        
        # Debería interpretar como: genre = 'rock' OR (genre = 'pop' AND year > 2000)
        assert isinstance(ast, LogicalNode)
        assert ast.operator == LogicalOperator.OR
        assert isinstance(ast.left, ComparisonNode)  # genre = 'rock'
        assert isinstance(ast.right, LogicalNode)   # genre = 'pop' AND year > 2000
        assert ast.right.operator == LogicalOperator.AND


class TestParseErrors:
    """Tests para errores de parsing."""
    
    def test_empty_expression(self):
        """Test error con expresión vacía."""
        with pytest.raises(ParseError, match="Expresión vacía"):
            parse_expression("")
    
    def test_invalid_token(self):
        """Test error con token inválido."""
        with pytest.raises(ParseError, match="Token inválido"):
            parse_expression("genre = 'rock' @@ year > 2000")
    
    def test_missing_operator(self):
        """Test error con operador faltante."""
        with pytest.raises(ParseError, match="Se esperaba un operador"):
            parse_expression("genre 'rock'")
    
    def test_missing_value(self):
        """Test error con valor faltante."""
        with pytest.raises(ParseError, match="Se esperaba un valor"):
            parse_expression("genre =")
    
    def test_missing_identifier(self):
        """Test error con identificador faltante."""
        with pytest.raises(ParseError, match="Se esperaba un identificador"):
            parse_expression("= 'rock'")
    
    def test_unclosed_parentheses(self):
        """Test error con paréntesis sin cerrar."""
        with pytest.raises(ParseError, match="Se esperaba '\\)'"):
            parse_expression("(genre = 'rock'")
    
    def test_invalid_operator(self):
        """Test error con operador inválido."""
        with pytest.raises(ParseError, match="Operador no válido"):
            parse_expression("genre === 'rock'")


class TestExpressionToString:
    """Tests para conversión de AST a string."""
    
    def test_comparison_to_string(self):
        """Test conversión de comparación a string."""
        ast = parse_expression("genre = 'rock'")
        result = expression_to_string(ast)
        
        assert result == "genre = 'rock'"
    
    def test_number_comparison_to_string(self):
        """Test conversión con números."""
        ast = parse_expression("year > 2000")
        result = expression_to_string(ast)
        
        assert result == "year > 2000"
    
    def test_logical_expression_to_string(self):
        """Test conversión de expresión lógica."""
        ast = parse_expression("genre = 'rock' AND year > 2000")
        result = expression_to_string(ast)
        
        assert "AND" in result
        assert "genre = 'rock'" in result
        assert "year > 2000" in result
    
    def test_not_expression_to_string(self):
        """Test conversión de expresión NOT."""
        ast = parse_expression("NOT genre = 'rock'")
        result = expression_to_string(ast)
        
        assert result == "NOT (genre = 'rock')"
    
    def test_complex_expression_roundtrip(self):
        """Test que una expresión compleja se pueda convertir ida y vuelta."""
        original = "genre = 'rock' AND year > 2000"
        ast = parse_expression(original)
        result = expression_to_string(ast)
        
        # Parsear el resultado y verificar que es equivalente
        ast2 = parse_expression(result.replace("(", "").replace(")", ""))
        assert isinstance(ast2, LogicalNode)
        assert ast2.operator == LogicalOperator.AND


class TestRealWorldExpressions:
    """Tests con expresiones del mundo real."""
    
    def test_music_filter_expressions(self):
        """Test expresiones típicas de filtros musicales."""
        expressions = [
            "genre = 'rock'",
            "year >= 1990 AND year <= 2000",
            "artist CONTAINS 'beatles' OR artist CONTAINS 'stones'",
            "rating > 4.0 AND genre != 'classical'",
            "(genre = 'rock' OR genre = 'pop') AND year > 2000",
            "NOT genre = 'country'",
            "duration > 180 AND duration < 300",
            "album STARTS_WITH 'The'",
        ]
        
        for expr in expressions:
            # Verificar que se puede parsear sin errores
            ast = parse_expression(expr)
            assert ast is not None
            
            # Verificar que se puede convertir de vuelta a string
            result = expression_to_string(ast)
            assert result is not None
    
    def test_complex_nested_expression(self):
        """Test expresión compleja anidada."""
        expr = ("(genre = 'rock' AND year > 1970) OR "
                "(genre = 'pop' AND rating >= 4.0) OR "
                "(artist CONTAINS 'elvis' AND NOT genre = 'country')")
        
        ast = parse_expression(expr)
        assert isinstance(ast, LogicalNode)
        
        # Verificar estructura básica
        assert ast.operator == LogicalOperator.OR 
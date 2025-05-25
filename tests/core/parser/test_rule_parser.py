import unittest
from src.core.parser import RuleParser, OperatorType, Condition, LogicalExpression, LogicalOperator, parse_rule

class TestRuleParser(unittest.TestCase):

    def setUp(self):
        self.parser = RuleParser()

    def test_parse_starts_with(self):
        rule_text = "title STARTS WITH 'The'"
        expected_condition = Condition(field='title', operator=OperatorType.STARTS_WITH, value='The')
        
        parsed_expression = self.parser.parse(rule_text)
        
        self.assertIsInstance(parsed_expression, LogicalExpression)
        self.assertEqual(len(parsed_expression.conditions), 1)
        self.assertIsInstance(parsed_expression.conditions[0], Condition)
        
        condition = parsed_expression.conditions[0]
        self.assertEqual(condition.field, expected_condition.field)
        self.assertEqual(condition.operator, expected_condition.operator)
        self.assertEqual(condition.value, expected_condition.value)

    def test_parse_ends_with(self):
        rule_text = "artist ENDS WITH 'Band'"
        expected_condition = Condition(field='artist', operator=OperatorType.ENDS_WITH, value='Band')
        
        parsed_expression = self.parser.parse(rule_text)
        
        self.assertEqual(len(parsed_expression.conditions), 1)
        condition = parsed_expression.conditions[0]
        self.assertEqual(condition.field, expected_condition.field)
        self.assertEqual(condition.operator, expected_condition.operator)
        self.assertEqual(condition.value, expected_condition.value)

    def test_parse_contains(self):
        # CONTAINS ya existía, pero probamos que el parser con espacios en OPERATOR_MAP lo sigue manejando
        rule_text = "genre CONTAINS 'Rock'"
        expected_condition = Condition(field='genre', operator=OperatorType.CONTAINS, value='Rock')
        
        parsed_expression = self.parser.parse(rule_text)
        
        self.assertEqual(len(parsed_expression.conditions), 1)
        condition = parsed_expression.conditions[0]
        self.assertEqual(condition.field, expected_condition.field)
        self.assertEqual(condition.operator, expected_condition.operator)
        self.assertEqual(condition.value, expected_condition.value)

    def test_parse_not_contains(self):
        rule_text = "album NOT CONTAINS 'Live'"
        expected_condition = Condition(field='album', operator=OperatorType.NOT_CONTAINS, value='Live')
        
        parsed_expression = self.parser.parse(rule_text)
        
        self.assertEqual(len(parsed_expression.conditions), 1)
        condition = parsed_expression.conditions[0]
        self.assertEqual(condition.field, expected_condition.field)
        self.assertEqual(condition.operator, expected_condition.operator)
        self.assertEqual(condition.value, expected_condition.value)

    def test_parse_in_list(self):
        rule_text = "year IN [2020, 2021, '2022']" # Probar mezcla de tipos si es relevante, o asegurar consistencia
        # El parser actual convierte números a int/float, strings quedan como strings.
        # Para IN, el motor SQL probablemente maneje la conversión si la columna es numérica.
        expected_value = [2020, 2021, "2022"]
        expected_condition = Condition(field='year', operator=OperatorType.IN, value=expected_value)
        
        parsed_expression = self.parser.parse(rule_text)
        
        self.assertEqual(len(parsed_expression.conditions), 1)
        condition = parsed_expression.conditions[0]
        self.assertEqual(condition.field, expected_condition.field)
        self.assertEqual(condition.operator, expected_condition.operator)
        self.assertListEqual(condition.value, expected_condition.value)

    def test_parse_not_in_list(self):
        rule_text = "genre NOT IN ['Pop', 'Country']"
        expected_value = ["Pop", "Country"]
        expected_condition = Condition(field='genre', operator=OperatorType.NOT_IN, value=expected_value)
        
        parsed_expression = self.parser.parse(rule_text)
        
        self.assertEqual(len(parsed_expression.conditions), 1)
        condition = parsed_expression.conditions[0]
        self.assertEqual(condition.field, expected_condition.field)
        self.assertEqual(condition.operator, expected_condition.operator)
        self.assertListEqual(condition.value, expected_condition.value)

    def test_parse_case_insensitivity_for_operators(self):
        rule_text = "title starts with 'A'" # 'starts with' en minúscula
        parsed_expression = self.parser.parse(rule_text)
        condition = parsed_expression.conditions[0]
        self.assertEqual(condition.operator, OperatorType.STARTS_WITH)

        rule_text = "title CONTAINS 'Song'" # 'CONTAINS' en mayúscula
        parsed_expression = self.parser.parse(rule_text)
        condition = parsed_expression.conditions[0]
        self.assertEqual(condition.operator, OperatorType.CONTAINS)

    def test_parse_error_incomplete_operator(self):
        with self.assertRaisesRegex(ValueError, "Operador no válido: starts"):
            self.parser.parse("title STARTS 'Word'") # Falta WITH

        with self.assertRaisesRegex(ValueError, "Operador no válido: not"):
            self.parser.parse("album NOT 'Word'") # Falta CONTAINS o IN

    def test_parse_error_in_without_list(self):
        with self.assertRaisesRegex(ValueError, "El operador IN requiere una lista de valores"):
            self.parser.parse("year IN 2020")
            
    def test_parse_complex_rule_with_new_operators(self):
        rule_text = "(title STARTS WITH 'The' AND artist ENDS WITH 's') OR genre NOT IN ['Disco', 'Reggae']"
        parsed_expression = self.parser.parse(rule_text)
        
        self.assertIsInstance(parsed_expression, LogicalExpression)
        self.assertEqual(len(parsed_expression.operators), 1)
        self.assertEqual(parsed_expression.operators[0], LogicalOperator.OR)
        
        # Primera parte: (title STARTS WITH 'The' AND artist ENDS WITH 's')
        expr1 = parsed_expression.conditions[0]
        self.assertIsInstance(expr1, LogicalExpression)
        self.assertEqual(len(expr1.conditions), 2)
        self.assertEqual(len(expr1.operators), 1)
        self.assertEqual(expr1.operators[0], LogicalOperator.AND)
        
        cond1_1 = expr1.conditions[0]
        self.assertEqual(cond1_1.field, 'title')
        self.assertEqual(cond1_1.operator, OperatorType.STARTS_WITH)
        self.assertEqual(cond1_1.value, 'The')
        
        cond1_2 = expr1.conditions[1]
        self.assertEqual(cond1_2.field, 'artist')
        self.assertEqual(cond1_2.operator, OperatorType.ENDS_WITH)
        self.assertEqual(cond1_2.value, 's')
        
        # Segunda parte: genre NOT IN ['Disco', 'Reggae']
        cond2 = parsed_expression.conditions[1]
        self.assertIsInstance(cond2, Condition)
        self.assertEqual(cond2.field, 'genre')
        self.assertEqual(cond2.operator, OperatorType.NOT_IN)
        self.assertListEqual(cond2.value, ['Disco', 'Reggae'])

    def test_parse_between_numeric(self):
        rule_text = "bpm BETWEEN 120 AND 140"
        expected_condition = Condition(field='bpm', operator=OperatorType.BETWEEN, value=[120, 140])
        
        parsed_expression = self.parser.parse(rule_text)
        
        self.assertEqual(len(parsed_expression.conditions), 1)
        condition = parsed_expression.conditions[0]
        self.assertEqual(condition.field, expected_condition.field)
        self.assertEqual(condition.operator, expected_condition.operator)
        self.assertListEqual(condition.value, expected_condition.value)

    def test_parse_between_mixed_types(self):
        rule_text = "year BETWEEN 2020 AND '2024'"
        expected_condition = Condition(field='year', operator=OperatorType.BETWEEN, value=[2020, "2024"])
        
        parsed_expression = self.parser.parse(rule_text)
        
        self.assertEqual(len(parsed_expression.conditions), 1)
        condition = parsed_expression.conditions[0]
        self.assertEqual(condition.field, expected_condition.field)
        self.assertEqual(condition.operator, expected_condition.operator)
        self.assertListEqual(condition.value, expected_condition.value)

    def test_parse_between_case_insensitive(self):
        rule_text = "rating between 3 and 5"  # 'between' y 'and' en minúscula
        parsed_expression = self.parser.parse(rule_text)
        condition = parsed_expression.conditions[0]
        self.assertEqual(condition.operator, OperatorType.BETWEEN)
        self.assertListEqual(condition.value, [3, 5])

    def test_parse_between_error_missing_and(self):
        with self.assertRaisesRegex(ValueError, "Se esperaba 'AND' después del primer valor en BETWEEN"):
            self.parser.parse("bpm BETWEEN 120 140")  # Falta AND

    def test_parse_between_error_missing_second_value(self):
        with self.assertRaises(ValueError):  # Simplificado para cualquier ValueError
            self.parser.parse("bpm BETWEEN 120 AND")  # Falta segundo valor

    def test_parse_complex_rule_with_between(self):
        rule_text = "genre = 'Electronic' AND bpm BETWEEN 128 AND 140 AND energy > 7"
        parsed_expression = self.parser.parse(rule_text)
        
        self.assertEqual(len(parsed_expression.conditions), 3)
        self.assertEqual(len(parsed_expression.operators), 2)
        
        # Primera condición: genre = 'Electronic'
        cond1 = parsed_expression.conditions[0]
        self.assertEqual(cond1.field, 'genre')
        self.assertEqual(cond1.operator, OperatorType.EQUALS)
        self.assertEqual(cond1.value, 'Electronic')
        
        # Segunda condición: bpm BETWEEN 128 AND 140
        cond2 = parsed_expression.conditions[1]
        self.assertEqual(cond2.field, 'bpm')
        self.assertEqual(cond2.operator, OperatorType.BETWEEN)
        self.assertListEqual(cond2.value, [128, 140])
        
        # Tercera condición: energy > 7
        cond3 = parsed_expression.conditions[2]
        self.assertEqual(cond3.field, 'energy')
        self.assertEqual(cond3.operator, OperatorType.GREATER_THAN)
        self.assertEqual(cond3.value, 7)

if __name__ == '__main__':
    unittest.main() 
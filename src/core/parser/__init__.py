"""
Parser de expresiones para reglas musicales.

Este módulo proporciona funcionalidades para parsear expresiones de filtros
musicales como "genre = 'rock' AND year > 2000".
"""

from .rule_parser import (
    parse_rule,
    validate_rule,
    LogicalExpression,
    Condition,
    OperatorType,
    LogicalOperator,
    RuleParser
)

# Comentado para evitar conflictos - NodeType y ASTNode están ahora en parser_engine.py
# from ..parser_engine import NodeType, ASTNode

__all__ = [
    'parse_rule',
    'validate_rule',
    'LogicalExpression',
    'Condition',
    'OperatorType',
    'LogicalOperator',
    'RuleParser'
    # 'NodeType',  # Comentado
    # 'ASTNode'    # Comentado
] 
"""
Capa de persistencia avanzada para Nueva Biblioteca.
"""

from .database_manager import DatabaseManager
from .unit_of_work import UnitOfWork
from .connection_pool import ConnectionPool
from .transaction_manager import TransactionManager

__all__ = [
    'DatabaseManager',
    'UnitOfWork', 
    'ConnectionPool',
    'TransactionManager'
]
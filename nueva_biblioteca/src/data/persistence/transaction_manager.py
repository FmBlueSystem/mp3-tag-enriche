"""
Gestor avanzado de transacciones con soporte para savepoints y rollback.
"""

import threading
import uuid
from typing import Dict, Any, List, Optional, Callable
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Savepoint:
    """Representa un savepoint dentro de una transacción."""
    
    def __init__(self, name: str, session: Session):
        self.name = name
        self.session = session
        self.created_at = datetime.now()
        self._savepoint = None
        self._released = False
    
    def create(self):
        """Crea el savepoint en la base de datos."""
        if self._savepoint is None:
            self._savepoint = self.session.begin_nested()
            logger.debug(f"Savepoint '{self.name}' creado")
    
    def rollback(self):
        """Hace rollback al savepoint."""
        if self._savepoint and not self._released:
            self._savepoint.rollback()
            self._released = True
            logger.debug(f"Rollback a savepoint '{self.name}'")
    
    def commit(self):
        """Confirma el savepoint."""
        if self._savepoint and not self._released:
            self._savepoint.commit()
            self._released = True
            logger.debug(f"Savepoint '{self.name}' confirmado")
    
    def __enter__(self):
        self.create()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()

class TransactionContext:
    """Contexto de transacción con métricas y logging."""
    
    def __init__(self, name: str, session: Session):
        self.name = name
        self.session = session
        self.started_at = datetime.now()
        self.savepoints: List[Savepoint] = []
        self._completed = False
        self._committed = False
        self._rolled_back = False
        self.metadata: Dict[str, Any] = {}
    
    def create_savepoint(self, name: Optional[str] = None) -> Savepoint:
        """
        Crea un savepoint dentro de la transacción.
        
        Args:
            name: Nombre del savepoint (se genera automáticamente si no se proporciona)
            
        Returns:
            Savepoint: El savepoint creado
        """
        if name is None:
            name = f"sp_{len(self.savepoints) + 1}_{uuid.uuid4().hex[:8]}"
        
        savepoint = Savepoint(name, self.session)
        self.savepoints.append(savepoint)
        return savepoint
    
    def commit(self):
        """Confirma la transacción."""
        if not self._completed:
            try:
                self.session.commit()
                self._committed = True
                self._completed = True
                
                duration = (datetime.now() - self.started_at).total_seconds()
                logger.info(f"Transacción '{self.name}' confirmada en {duration:.3f}s")
                
            except SQLAlchemyError as e:
                logger.error(f"Error confirmando transacción '{self.name}': {e}")
                self.rollback()
                raise
    
    def rollback(self):
        """Hace rollback de la transacción."""
        if not self._completed:
            try:
                self.session.rollback()
                self._rolled_back = True
                self._completed = True
                
                duration = (datetime.now() - self.started_at).total_seconds()
                logger.info(f"Transacción '{self.name}' revertida en {duration:.3f}s")
                
            except SQLAlchemyError as e:
                logger.error(f"Error revirtiendo transacción '{self.name}': {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado de la transacción."""
        duration = (datetime.now() - self.started_at).total_seconds()
        
        return {
            'name': self.name,
            'started_at': self.started_at,
            'duration': duration,
            'completed': self._completed,
            'committed': self._committed,
            'rolled_back': self._rolled_back,
            'savepoints_count': len(self.savepoints),
            'metadata': self.metadata
        }

class TransactionManager:
    """
    Gestor avanzado de transacciones con soporte para savepoints,
    métricas y recuperación de errores.
    """
    
    def __init__(self):
        self._active_transactions: Dict[str, TransactionContext] = {}
        self._transaction_history: List[Dict[str, Any]] = []
        self._stats = {
            'total_transactions': 0,
            'committed_transactions': 0,
            'rolled_back_transactions': 0,
            'failed_transactions': 0,
            'total_savepoints': 0,
            'avg_transaction_duration': 0.0
        }
        self._lock = threading.Lock()
    
    @contextmanager
    def transaction(self, session: Session, name: Optional[str] = None):
        """
        Context manager para transacciones con gestión automática.
        
        Args:
            session: Sesión de SQLAlchemy
            name: Nombre de la transacción (opcional)
            
        Yields:
            TransactionContext: Contexto de la transacción
        """
        if name is None:
            name = f"tx_{uuid.uuid4().hex[:8]}"
        
        ctx = TransactionContext(name, session)
        
        with self._lock:
            self._active_transactions[name] = ctx
            self._stats['total_transactions'] += 1
        
        try:
            yield ctx
            
            # Auto-commit si no se hizo explícitamente
            if not ctx._completed:
                ctx.commit()
                
        except Exception as e:
            # Auto-rollback en caso de error
            if not ctx._completed:
                ctx.rollback()
            
            with self._lock:
                self._stats['failed_transactions'] += 1
            
            logger.error(f"Transacción '{name}' falló: {e}")
            raise
            
        finally:
            # Actualizar estadísticas
            with self._lock:
                if ctx._committed:
                    self._stats['committed_transactions'] += 1
                elif ctx._rolled_back:
                    self._stats['rolled_back_transactions'] += 1
                
                self._stats['total_savepoints'] += len(ctx.savepoints)
                
                # Calcular duración promedio
                total_duration = sum(
                    (tx['completed_at'] - tx['started_at']).total_seconds() 
                    for tx in self._transaction_history
                ) + (datetime.now() - ctx.started_at).total_seconds()
                
                self._stats['avg_transaction_duration'] = (
                    total_duration / self._stats['total_transactions']
                )
                
                # Mover a historial
                tx_record = ctx.get_status()
                tx_record['completed_at'] = datetime.now()
                self._transaction_history.append(tx_record)
                
                # Limpiar de transacciones activas
                if name in self._active_transactions:
                    del self._active_transactions[name]
                
                # Mantener solo las últimas 1000 transacciones en el historial
                if len(self._transaction_history) > 1000:
                    self._transaction_history = self._transaction_history[-1000:]
    
    def execute_in_transaction(
        self, 
        session: Session, 
        operation: Callable[[TransactionContext], Any],
        name: Optional[str] = None,
        retry_count: int = 0
    ) -> Any:
        """
        Ejecuta una operación dentro de una transacción con retry automático.
        
        Args:
            session: Sesión de SQLAlchemy
            operation: Función a ejecutar (recibe TransactionContext)
            name: Nombre de la transacción
            retry_count: Número de reintentos en caso de error
            
        Returns:
            Any: Resultado de la operación
        """
        last_exception = None
        
        for attempt in range(retry_count + 1):
            try:
                with self.transaction(session, name) as ctx:
                    ctx.metadata['attempt'] = attempt + 1
                    ctx.metadata['max_retries'] = retry_count
                    
                    result = operation(ctx)
                    return result
                    
            except Exception as e:
                last_exception = e
                
                if attempt < retry_count:
                    logger.warning(f"Intento {attempt + 1} falló para transacción '{name}': {e}. Reintentando...")
                    # Pequeña pausa antes del retry
                    import time
                    time.sleep(0.1 * (attempt + 1))
                else:
                    logger.error(f"Transacción '{name}' falló después de {retry_count + 1} intentos")
        
        # Si llegamos aquí, todos los intentos fallaron
        raise last_exception
    
    def get_active_transactions(self) -> List[Dict[str, Any]]:
        """
        Obtiene información de las transacciones activas.
        
        Returns:
            List con información de transacciones activas
        """
        with self._lock:
            return [ctx.get_status() for ctx in self._active_transactions.values()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del gestor de transacciones.
        
        Returns:
            Dict con estadísticas
        """
        with self._lock:
            stats = self._stats.copy()
            stats['active_transactions_count'] = len(self._active_transactions)
            stats['history_size'] = len(self._transaction_history)
            
            if self._transaction_history:
                # Estadísticas adicionales del historial
                durations = [
                    (tx['completed_at'] - tx['started_at']).total_seconds()
                    for tx in self._transaction_history
                    if 'completed_at' in tx
                ]
                
                if durations:
                    stats['min_duration'] = min(durations)
                    stats['max_duration'] = max(durations)
                    stats['median_duration'] = sorted(durations)[len(durations) // 2]
            
            return stats
    
    def reset_statistics(self):
        """Reinicia las estadísticas del gestor."""
        with self._lock:
            self._stats = {
                'total_transactions': 0,
                'committed_transactions': 0,
                'rolled_back_transactions': 0,
                'failed_transactions': 0,
                'total_savepoints': 0,
                'avg_transaction_duration': 0.0
            }
            self._transaction_history.clear()
    
    def force_rollback_active_transactions(self):
        """
        Fuerza el rollback de todas las transacciones activas.
        Útil para shutdown o situaciones de emergencia.
        """
        with self._lock:
            active_names = list(self._active_transactions.keys())
        
        for name in active_names:
            try:
                ctx = self._active_transactions.get(name)
                if ctx and not ctx._completed:
                    ctx.rollback()
                    logger.warning(f"Transacción activa '{name}' fue forzada a rollback")
            except Exception as e:
                logger.error(f"Error forzando rollback de transacción '{name}': {e}")
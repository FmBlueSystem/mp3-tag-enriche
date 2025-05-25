"""
Gestión de pool de conexiones para base de datos.
"""

import threading
import time
from typing import Dict, Any, Optional
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool
import logging

logger = logging.getLogger(__name__)

class ConnectionPool:
    """
    Gestor de pool de conexiones con métricas y monitoreo.
    """
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self._stats = {
            'connections_created': 0,
            'connections_checked_out': 0,
            'connections_checked_in': 0,
            'connections_invalidated': 0,
            'pool_size': 0,
            'checked_out_connections': 0,
            'overflow_connections': 0,
            'invalid_connections': 0
        }
        self._lock = threading.Lock()
        self._setup_pool_events()
    
    def _setup_pool_events(self):
        """Configura eventos del pool de conexiones."""
        if hasattr(self.engine.pool, 'add_listener'):
            from sqlalchemy import event
            
            @event.listens_for(self.engine.pool, "connect")
            def on_connect(dbapi_connection, connection_record):
                with self._lock:
                    self._stats['connections_created'] += 1
            
            @event.listens_for(self.engine.pool, "checkout")
            def on_checkout(dbapi_connection, connection_record, connection_proxy):
                with self._lock:
                    self._stats['connections_checked_out'] += 1
            
            @event.listens_for(self.engine.pool, "checkin")
            def on_checkin(dbapi_connection, connection_record):
                with self._lock:
                    self._stats['connections_checked_in'] += 1
            
            @event.listens_for(self.engine.pool, "invalidate")
            def on_invalidate(dbapi_connection, connection_record, exception):
                with self._lock:
                    self._stats['connections_invalidated'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del pool de conexiones.
        
        Returns:
            Dict con estadísticas del pool
        """
        with self._lock:
            stats = self._stats.copy()
        
        # Agregar estadísticas del pool de SQLAlchemy
        pool = self.engine.pool
        stats.update({
            'pool_size': getattr(pool, 'size', lambda: 0)(),
            'checked_out_connections': getattr(pool, 'checkedout', lambda: 0)(),
            'overflow_connections': getattr(pool, 'overflow', lambda: 0)(),
            'invalid_connections': getattr(pool, 'invalidated', lambda: 0)()
        })
        
        return stats
    
    def get_pool_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del pool.
        
        Returns:
            Dict con estado del pool
        """
        pool = self.engine.pool
        
        return {
            'pool_class': pool.__class__.__name__,
            'size': getattr(pool, 'size', lambda: 0)(),
            'checked_out': getattr(pool, 'checkedout', lambda: 0)(),
            'overflow': getattr(pool, 'overflow', lambda: 0)(),
            'checked_in': getattr(pool, 'checkedin', lambda: 0)(),
            'is_valid': True  # Placeholder para validaciones futuras
        }
    
    def close_all(self):
        """Cierra todas las conexiones del pool."""
        try:
            if hasattr(self.engine.pool, 'dispose'):
                self.engine.pool.dispose()
                logger.info("Pool de conexiones cerrado")
        except Exception as e:
            logger.error(f"Error cerrando pool de conexiones: {e}")
    
    def reset_stats(self):
        """Reinicia las estadísticas del pool."""
        with self._lock:
            for key in self._stats:
                self._stats[key] = 0
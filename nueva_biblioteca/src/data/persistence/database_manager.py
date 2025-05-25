"""
Gestor principal de base de datos con funcionalidades avanzadas.
"""

import logging
import threading
from typing import Optional, Dict, Any, List, Callable
from contextlib import contextmanager
from sqlalchemy import event, pool
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from datetime import datetime
import json
import os

from ..models.base import engine, SessionLocal, Base
from ..migrations.migration_manager import MigrationManager, get_database_info
from .connection_pool import ConnectionPool
from .transaction_manager import TransactionManager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Gestor principal de base de datos con características empresariales.
    """
    
    def __init__(self):
        self.engine = engine
        self.session_factory = SessionLocal
        self.connection_pool = ConnectionPool(self.engine)
        self.transaction_manager = TransactionManager()
        self._setup_event_listeners()
        self._stats = {
            'connections_opened': 0,
            'connections_closed': 0,
            'queries_executed': 0,
            'transactions_committed': 0,
            'transactions_rolled_back': 0,
            'last_reset': datetime.now()
        }
        self._lock = threading.Lock()
    
    def _setup_event_listeners(self):
        """Configura listeners para eventos de SQLAlchemy."""
        
        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Evento cuando se abre una conexión."""
            with self._lock:
                self._stats['connections_opened'] += 1
            
            # Configuraciones específicas para SQLite
            if 'sqlite' in str(self.engine.url):
                dbapi_connection.execute('PRAGMA foreign_keys=ON')
                dbapi_connection.execute('PRAGMA journal_mode=WAL')
                dbapi_connection.execute('PRAGMA synchronous=NORMAL')
                dbapi_connection.execute('PRAGMA cache_size=10000')
                dbapi_connection.execute('PRAGMA temp_store=MEMORY')
        
        @event.listens_for(self.engine, "close")
        def on_close(dbapi_connection, connection_record):
            """Evento cuando se cierra una conexión."""
            with self._lock:
                self._stats['connections_closed'] += 1
        
        @event.listens_for(Session, "before_flush")
        def on_before_flush(session, flush_context, instances):
            """Evento antes de hacer flush de la sesión."""
            # Aquí se pueden agregar validaciones automáticas
            pass
        
        @event.listens_for(Session, "after_commit")
        def on_after_commit(session):
            """Evento después de commit."""
            with self._lock:
                self._stats['transactions_committed'] += 1
        
        @event.listens_for(Session, "after_rollback")
        def on_after_rollback(session):
            """Evento después de rollback."""
            with self._lock:
                self._stats['transactions_rolled_back'] += 1
    
    @contextmanager
    def get_session(self):
        """
        Context manager para obtener una sesión de base de datos.
        
        Yields:
            Session: Sesión de SQLAlchemy
        """
        session = self.session_factory()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Error en sesión de base de datos: {e}")
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_transaction(self):
        """
        Context manager para transacciones automáticas.
        
        Yields:
            Session: Sesión con transacción automática
        """
        with self.get_session() as session:
            try:
                yield session
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Error en transacción: {e}")
                raise
    
    def initialize(self) -> bool:
        """
        Inicializa la base de datos aplicando migraciones.
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            logger.info("Inicializando base de datos...")
            
            # Verificar conectividad
            if not self.test_connection():
                logger.error("No se pudo conectar a la base de datos")
                return False
            
            # Aplicar migraciones
            migration_manager = MigrationManager()
            if not migration_manager.apply_migrations():
                logger.error("Error aplicando migraciones")
                return False
            
            # Validar integridad
            if not self.validate_integrity():
                logger.error("Validación de integridad fallida")
                return False
            
            logger.info("Base de datos inicializada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Prueba la conectividad con la base de datos.
        
        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Error probando conexión: {e}")
            return False
    
    def validate_integrity(self) -> bool:
        """
        Valida la integridad de la base de datos.
        
        Returns:
            bool: True si la integridad es válida
        """
        try:
            with self.get_session() as session:
                # Verificar integridad referencial para SQLite
                if 'sqlite' in str(self.engine.url):
                    result = session.execute("PRAGMA integrity_check").fetchone()
                    if result[0] != 'ok':
                        logger.error(f"Fallo en integrity_check: {result[0]}")
                        return False
                    
                    result = session.execute("PRAGMA foreign_key_check").fetchall()
                    if result:
                        logger.error(f"Fallo en foreign_key_check: {result}")
                        return False
                
                return True
                
        except Exception as e:
            logger.error(f"Error validando integridad: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Crea un backup de la base de datos.
        
        Args:
            backup_path: Ruta donde guardar el backup
            
        Returns:
            bool: True si el backup fue exitoso
        """
        try:
            if 'sqlite' in str(self.engine.url):
                import shutil
                db_path = str(self.engine.url).replace('sqlite:///', '')
                
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                
                # Copiar archivo de base de datos
                shutil.copy2(db_path, backup_path)
                
                # Guardar metadata del backup
                metadata = {
                    'created_at': datetime.now().isoformat(),
                    'original_path': db_path,
                    'database_info': get_database_info()
                }
                
                metadata_path = backup_path + '.metadata.json'
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"Backup creado exitosamente: {backup_path}")
                return True
            else:
                logger.error("Backup solo soportado para SQLite")
                return False
                
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """
        Restaura la base de datos desde un backup.
        
        Args:
            backup_path: Ruta del backup a restaurar
            
        Returns:
            bool: True si la restauración fue exitosa
        """
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Archivo de backup no encontrado: {backup_path}")
                return False
            
            if 'sqlite' in str(self.engine.url):
                import shutil
                db_path = str(self.engine.url).replace('sqlite:///', '')
                
                # Crear backup del estado actual
                current_backup = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if os.path.exists(db_path):
                    shutil.copy2(db_path, current_backup)
                    logger.info(f"Backup del estado actual: {current_backup}")
                
                # Restaurar desde backup
                shutil.copy2(backup_path, db_path)
                
                # Validar restauración
                if self.validate_integrity():
                    logger.info(f"Base de datos restaurada exitosamente desde: {backup_path}")
                    return True
                else:
                    # Restaurar estado anterior si la validación falla
                    if os.path.exists(current_backup):
                        shutil.copy2(current_backup, db_path)
                    logger.error("Validación post-restauración fallida")
                    return False
            else:
                logger.error("Restore solo soportado para SQLite")
                return False
                
        except Exception as e:
            logger.error(f"Error restaurando backup: {e}")
            return False
    
    def optimize_database(self) -> bool:
        """
        Optimiza la base de datos (vacuum, reindex, etc.).
        
        Returns:
            bool: True si la optimización fue exitosa
        """
        try:
            with self.get_session() as session:
                if 'sqlite' in str(self.engine.url):
                    logger.info("Optimizando base de datos SQLite...")
                    
                    # VACUUM para compactar
                    session.execute("VACUUM")
                    
                    # ANALYZE para actualizar estadísticas
                    session.execute("ANALYZE")
                    
                    # REINDEX para optimizar índices
                    session.execute("REINDEX")
                    
                    session.commit()
                    
                logger.info("Optimización completada")
                return True
                
        except Exception as e:
            logger.error(f"Error optimizando base de datos: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas detalladas de la base de datos.
        
        Returns:
            Dict con estadísticas
        """
        with self._lock:
            stats = self._stats.copy()
        
        try:
            # Agregar información de la base de datos
            db_info = get_database_info()
            stats.update(db_info)
            
            # Estadísticas del pool de conexiones
            pool_stats = self.connection_pool.get_stats()
            stats['connection_pool'] = pool_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return stats
    
    def reset_statistics(self):
        """Reinicia las estadísticas."""
        with self._lock:
            self._stats = {
                'connections_opened': 0,
                'connections_closed': 0,
                'queries_executed': 0,
                'transactions_committed': 0,
                'transactions_rolled_back': 0,
                'last_reset': datetime.now()
            }
    
    def execute_maintenance(self) -> Dict[str, Any]:
        """
        Ejecuta tareas de mantenimiento de la base de datos.
        
        Returns:
            Dict con resultados del mantenimiento
        """
        results = {
            'started_at': datetime.now(),
            'tasks': {}
        }
        
        # Validar integridad
        results['tasks']['integrity_check'] = self.validate_integrity()
        
        # Optimizar base de datos
        results['tasks']['optimization'] = self.optimize_database()
        
        # Limpiar caché expirado
        with self.get_transaction() as session:
            from ..models.playlist import MetadataCache
            expired_count = session.query(MetadataCache).filter(
                MetadataCache.expires_at < datetime.now()
            ).count()
            
            if expired_count > 0:
                session.query(MetadataCache).filter(
                    MetadataCache.expires_at < datetime.now()
                ).delete()
                results['tasks']['cache_cleanup'] = {
                    'success': True,
                    'expired_entries_removed': expired_count
                }
            else:
                results['tasks']['cache_cleanup'] = {
                    'success': True,
                    'expired_entries_removed': 0
                }
        
        results['completed_at'] = datetime.now()
        results['duration'] = (results['completed_at'] - results['started_at']).total_seconds()
        
        return results
    
    def close(self):
        """Cierra todas las conexiones y limpia recursos."""
        try:
            self.connection_pool.close_all()
            if hasattr(self.engine, 'dispose'):
                self.engine.dispose()
            logger.info("DatabaseManager cerrado exitosamente")
        except Exception as e:
            logger.error(f"Error cerrando DatabaseManager: {e}")

# Instancia global del gestor de base de datos
db_manager = DatabaseManager()
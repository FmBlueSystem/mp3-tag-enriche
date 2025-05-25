"""
Sistema de migración y versionado de base de datos.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from pathlib import Path
import json
import logging

from ..models.base import engine, SessionLocal
from ..models.music import Track, Artist, Album, Genre
from ..models.playlist import SmartPlaylist, PlaylistRule, PlaylistTrack, SyncHistory, MetadataCache

logger = logging.getLogger(__name__)

class DatabaseVersion:
    """Gestión de versiones de base de datos."""
    
    def __init__(self, db: Session):
        self.db = db
        self._ensure_version_table()
    
    def _ensure_version_table(self):
        """Asegura que existe la tabla de versiones."""
        self.db.execute(text("""
            CREATE TABLE IF NOT EXISTS db_version (
                id INTEGER PRIMARY KEY,
                version INTEGER NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                checksum TEXT
            )
        """))
        self.db.commit()
    
    def get_current_version(self) -> int:
        """Obtiene la versión actual de la base de datos."""
        result = self.db.execute(text(
            "SELECT MAX(version) FROM db_version"
        )).fetchone()
        return result[0] if result[0] is not None else 0
    
    def set_version(self, version: int, description: str = "", checksum: str = ""):
        """Establece una nueva versión en la base de datos."""
        self.db.execute(text("""
            INSERT INTO db_version (version, description, checksum)
            VALUES (:version, :description, :checksum)
        """), {
            'version': version,
            'description': description,
            'checksum': checksum
        })
        self.db.commit()
    
    def get_version_history(self) -> List[Dict[str, Any]]:
        """Obtiene el historial de versiones."""
        result = self.db.execute(text("""
            SELECT version, applied_at, description, checksum
            FROM db_version
            ORDER BY version ASC
        """)).fetchall()
        
        return [
            {
                'version': row[0],
                'applied_at': row[1],
                'description': row[2],
                'checksum': row[3]
            }
            for row in result
        ]

class Migration:
    """Clase base para migraciones."""
    
    def __init__(self, version: int, description: str):
        self.version = version
        self.description = description
    
    def up(self, db: Session) -> None:
        """Aplica la migración."""
        raise NotImplementedError
    
    def down(self, db: Session) -> None:
        """Revierte la migración."""
        raise NotImplementedError
    
    def validate(self, db: Session) -> bool:
        """Valida que la migración se aplicó correctamente."""
        return True

class MigrationManager:
    """Gestor principal de migraciones."""
    
    def __init__(self):
        self.migrations: List[Migration] = []
        self._register_migrations()
    
    def _register_migrations(self):
        """Registra todas las migraciones disponibles."""
        # Migración inicial - creación de tablas base
        self.migrations.append(InitialMigration())
        self.migrations.append(PlaylistsMigration())
        self.migrations.append(IndexOptimizationMigration())
        self.migrations.append(MetadataCacheMigration())
    
    def get_pending_migrations(self, current_version: int) -> List[Migration]:
        """Obtiene las migraciones pendientes."""
        return [m for m in self.migrations if m.version > current_version]
    
    def apply_migrations(self, target_version: Optional[int] = None) -> bool:
        """
        Aplica las migraciones pendientes.
        
        Args:
            target_version: Versión objetivo (None para aplicar todas)
        
        Returns:
            bool: True si todas las migraciones se aplicaron exitosamente
        """
        db = SessionLocal()
        db_version = DatabaseVersion(db)
        
        try:
            current_version = db_version.get_current_version()
            pending = self.get_pending_migrations(current_version)
            
            if target_version:
                pending = [m for m in pending if m.version <= target_version]
            
            if not pending:
                logger.info("No hay migraciones pendientes")
                return True
            
            logger.info(f"Aplicando {len(pending)} migraciones...")
            
            for migration in pending:
                logger.info(f"Aplicando migración {migration.version}: {migration.description}")
                
                try:
                    # Aplicar migración
                    migration.up(db)
                    
                    # Validar migración
                    if not migration.validate(db):
                        raise Exception(f"Validación fallida para migración {migration.version}")
                    
                    # Actualizar versión
                    db_version.set_version(migration.version, migration.description)
                    
                    logger.info(f"Migración {migration.version} aplicada exitosamente")
                    
                except Exception as e:
                    logger.error(f"Error aplicando migración {migration.version}: {e}")
                    db.rollback()
                    return False
            
            logger.info("Todas las migraciones aplicadas exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error en el proceso de migración: {e}")
            return False
        finally:
            db.close()
    
    def rollback_to_version(self, target_version: int) -> bool:
        """
        Revierte la base de datos a una versión específica.
        
        Args:
            target_version: Versión objetivo para el rollback
        
        Returns:
            bool: True si el rollback fue exitoso
        """
        db = SessionLocal()
        db_version = DatabaseVersion(db)
        
        try:
            current_version = db_version.get_current_version()
            
            if target_version >= current_version:
                logger.warning("La versión objetivo es igual o mayor que la actual")
                return True
            
            # Obtener migraciones a revertir (en orden inverso)
            to_rollback = [m for m in self.migrations 
                          if target_version < m.version <= current_version]
            to_rollback.reverse()
            
            logger.info(f"Revirtiendo {len(to_rollback)} migraciones...")
            
            for migration in to_rollback:
                logger.info(f"Revirtiendo migración {migration.version}: {migration.description}")
                
                try:
                    migration.down(db)
                    
                    # Remover entrada de versión
                    db.execute(text(
                        "DELETE FROM db_version WHERE version = :version"
                    ), {'version': migration.version})
                    db.commit()
                    
                    logger.info(f"Migración {migration.version} revertida exitosamente")
                    
                except Exception as e:
                    logger.error(f"Error revirtiendo migración {migration.version}: {e}")
                    db.rollback()
                    return False
            
            logger.info(f"Rollback completado. Versión actual: {target_version}")
            return True
            
        except Exception as e:
            logger.error(f"Error en el proceso de rollback: {e}")
            return False
        finally:
            db.close()

# Migraciones específicas

class InitialMigration(Migration):
    """Migración inicial - creación de tablas básicas."""
    
    def __init__(self):
        super().__init__(1, "Creación de tablas básicas de música")
    
    def up(self, db: Session):
        """Crea las tablas básicas."""
        # Las tablas se crean automáticamente con create_all()
        from ..models.base import Base, engine
        Base.metadata.create_all(bind=engine, tables=[
            Artist.__table__,
            Album.__table__,
            Genre.__table__,
            Track.__table__,
        ])
    
    def down(self, db: Session):
        """Elimina las tablas básicas."""
        db.execute(text("DROP TABLE IF EXISTS track_genres"))
        db.execute(text("DROP TABLE IF EXISTS track_artists"))
        db.execute(text("DROP TABLE IF EXISTS tracks"))
        db.execute(text("DROP TABLE IF EXISTS albums"))
        db.execute(text("DROP TABLE IF EXISTS genres"))
        db.execute(text("DROP TABLE IF EXISTS artists"))
        db.commit()
    
    def validate(self, db: Session) -> bool:
        """Valida que las tablas existen."""
        inspector = inspect(engine)
        required_tables = ['artists', 'albums', 'genres', 'tracks', 'track_artists', 'track_genres']
        existing_tables = inspector.get_table_names()
        return all(table in existing_tables for table in required_tables)

class PlaylistsMigration(Migration):
    """Migración para playlists inteligentes."""
    
    def __init__(self):
        super().__init__(2, "Creación de tablas para playlists inteligentes")
    
    def up(self, db: Session):
        """Crea las tablas de playlists."""
        from ..models.base import Base, engine
        Base.metadata.create_all(bind=engine, tables=[
            SmartPlaylist.__table__,
            PlaylistRule.__table__,
            PlaylistTrack.__table__,
        ])
    
    def down(self, db: Session):
        """Elimina las tablas de playlists."""
        db.execute(text("DROP TABLE IF EXISTS playlist_tracks"))
        db.execute(text("DROP TABLE IF EXISTS playlist_rules"))
        db.execute(text("DROP TABLE IF EXISTS smart_playlists"))
        db.commit()
    
    def validate(self, db: Session) -> bool:
        """Valida que las tablas de playlists existen."""
        inspector = inspect(engine)
        required_tables = ['smart_playlists', 'playlist_rules', 'playlist_tracks']
        existing_tables = inspector.get_table_names()
        return all(table in existing_tables for table in required_tables)

class IndexOptimizationMigration(Migration):
    """Migración para optimización de índices."""
    
    def __init__(self):
        super().__init__(3, "Optimización de índices para rendimiento")
    
    def up(self, db: Session):
        """Crea índices adicionales para optimización."""
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_tracks_composite_search ON tracks(normalized_title, duration, bpm)",
            "CREATE INDEX IF NOT EXISTS idx_tracks_analysis_status ON tracks(is_analyzed, has_metadata)",
            "CREATE INDEX IF NOT EXISTS idx_albums_year_artist ON albums(year, artist_id)",
            "CREATE INDEX IF NOT EXISTS idx_playlist_rules_composite ON playlist_rules(playlist_id, is_active, order_index)",
        ]
        
        for index_sql in indices:
            db.execute(text(index_sql))
        db.commit()
    
    def down(self, db: Session):
        """Elimina los índices adicionales."""
        indices = [
            "DROP INDEX IF EXISTS idx_tracks_composite_search",
            "DROP INDEX IF EXISTS idx_tracks_analysis_status",
            "DROP INDEX IF EXISTS idx_albums_year_artist", 
            "DROP INDEX IF EXISTS idx_playlist_rules_composite",
        ]
        
        for index_sql in indices:
            db.execute(text(index_sql))
        db.commit()

class MetadataCacheMigration(Migration):
    """Migración para sistema de caché y auditoría."""
    
    def __init__(self):
        super().__init__(4, "Creación de tablas para caché y auditoría")
    
    def up(self, db: Session):
        """Crea las tablas de caché y auditoría."""
        from ..models.base import Base, engine
        Base.metadata.create_all(bind=engine, tables=[
            SyncHistory.__table__,
            MetadataCache.__table__,
        ])
    
    def down(self, db: Session):
        """Elimina las tablas de caché y auditoría."""
        db.execute(text("DROP TABLE IF EXISTS metadata_cache"))
        db.execute(text("DROP TABLE IF EXISTS sync_history"))
        db.commit()
    
    def validate(self, db: Session) -> bool:
        """Valida que las tablas de caché existen."""
        inspector = inspect(engine)
        required_tables = ['sync_history', 'metadata_cache']
        existing_tables = inspector.get_table_names()
        return all(table in existing_tables for table in required_tables)

def initialize_database():
    """Inicializa la base de datos con todas las migraciones."""
    manager = MigrationManager()
    return manager.apply_migrations()

def get_database_info() -> Dict[str, Any]:
    """Obtiene información sobre el estado de la base de datos."""
    db = SessionLocal()
    db_version = DatabaseVersion(db)
    
    try:
        current_version = db_version.get_current_version()
        version_history = db_version.get_version_history()
        
        # Estadísticas de tablas
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        stats = {}
        for table in tables:
            try:
                count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                stats[table] = count
            except:
                stats[table] = 0
        
        return {
            'current_version': current_version,
            'total_versions': len(version_history),
            'version_history': version_history,
            'tables': tables,
            'table_stats': stats,
            'database_file': str(engine.url.database) if hasattr(engine.url, 'database') else 'unknown'
        }
        
    finally:
        db.close()
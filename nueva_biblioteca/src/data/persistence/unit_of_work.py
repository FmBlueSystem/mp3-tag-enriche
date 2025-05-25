"""
Implementación del patrón Unit of Work para gestión de transacciones.
"""

from typing import Dict, Any, List, Optional, Type, TypeVar, Generic
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

from ..models.base import Base
from ..repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)

class UnitOfWork:
    """
    Patrón Unit of Work para gestionar transacciones complejas
    que involucran múltiples repositorios.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self._repositories: Dict[str, BaseRepository] = {}
        self._new_objects: List[Base] = []
        self._dirty_objects: List[Base] = []
        self._removed_objects: List[Base] = []
        self._committed = False
        self._rolled_back = False
        self._started_at = datetime.now()
    
    def register_repository(self, name: str, repository: BaseRepository):
        """
        Registra un repositorio en la unidad de trabajo.
        
        Args:
            name: Nombre del repositorio
            repository: Instancia del repositorio
        """
        self._repositories[name] = repository
    
    def get_repository(self, name: str) -> Optional[BaseRepository]:
        """
        Obtiene un repositorio registrado.
        
        Args:
            name: Nombre del repositorio
            
        Returns:
            BaseRepository o None si no existe
        """
        return self._repositories.get(name)
    
    def register_new(self, obj: Base):
        """
        Registra un objeto como nuevo para ser insertado.
        
        Args:
            obj: Objeto a insertar
        """
        if obj not in self._new_objects:
            self._new_objects.append(obj)
            logger.debug(f"Objeto registrado como nuevo: {obj}")
    
    def register_dirty(self, obj: Base):
        """
        Registra un objeto como modificado para ser actualizado.
        
        Args:
            obj: Objeto a actualizar
        """
        if obj not in self._dirty_objects and obj not in self._new_objects:
            self._dirty_objects.append(obj)
            logger.debug(f"Objeto registrado como modificado: {obj}")
    
    def register_removed(self, obj: Base):
        """
        Registra un objeto para ser eliminado.
        
        Args:
            obj: Objeto a eliminar
        """
        if obj in self._new_objects:
            self._new_objects.remove(obj)
        elif obj in self._dirty_objects:
            self._dirty_objects.remove(obj)
        
        if obj not in self._removed_objects:
            self._removed_objects.append(obj)
            logger.debug(f"Objeto registrado para eliminación: {obj}")
    
    def commit(self) -> bool:
        """
        Confirma todos los cambios pendientes.
        
        Returns:
            bool: True si el commit fue exitoso
        """
        if self._committed:
            logger.warning("UnitOfWork ya fue confirmada")
            return True
        
        if self._rolled_back:
            logger.error("No se puede confirmar una UnitOfWork que fue revertida")
            return False
        
        try:
            logger.debug(f"Iniciando commit: {len(self._new_objects)} nuevos, "
                        f"{len(self._dirty_objects)} modificados, "
                        f"{len(self._removed_objects)} eliminados")
            
            # Insertar objetos nuevos
            for obj in self._new_objects:
                self.session.add(obj)
            
            # Los objetos modificados ya están en la sesión,
            # SQLAlchemy los detecta automáticamente
            
            # Eliminar objetos marcados para eliminación
            for obj in self._removed_objects:
                self.session.delete(obj)
            
            # Confirmar cambios
            self.session.commit()
            self._committed = True
            
            duration = (datetime.now() - self._started_at).total_seconds()
            logger.info(f"UnitOfWork confirmada exitosamente en {duration:.3f}s")
            
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Error confirmando UnitOfWork: {e}")
            self.rollback()
            return False
    
    def rollback(self):
        """Revierte todos los cambios pendientes."""
        if self._rolled_back:
            logger.warning("UnitOfWork ya fue revertida")
            return
        
        try:
            self.session.rollback()
            self._rolled_back = True
            
            # Limpiar listas de objetos
            self._new_objects.clear()
            self._dirty_objects.clear()
            self._removed_objects.clear()
            
            duration = (datetime.now() - self._started_at).total_seconds()
            logger.info(f"UnitOfWork revertida en {duration:.3f}s")
            
        except SQLAlchemyError as e:
            logger.error(f"Error revirtiendo UnitOfWork: {e}")
    
    def clear(self):
        """Limpia todos los objetos pendientes sin confirmar ni revertir."""
        self._new_objects.clear()
        self._dirty_objects.clear()
        self._removed_objects.clear()
        logger.debug("UnitOfWork limpiada")
    
    @property
    def has_pending_changes(self) -> bool:
        """
        Verifica si hay cambios pendientes.
        
        Returns:
            bool: True si hay cambios pendientes
        """
        return bool(self._new_objects or self._dirty_objects or self._removed_objects)
    
    @property
    def pending_changes_count(self) -> Dict[str, int]:
        """
        Obtiene el conteo de cambios pendientes.
        
        Returns:
            Dict con conteos por tipo de cambio
        """
        return {
            'new': len(self._new_objects),
            'dirty': len(self._dirty_objects),
            'removed': len(self._removed_objects)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual de la unidad de trabajo.
        
        Returns:
            Dict con información de estado
        """
        duration = (datetime.now() - self._started_at).total_seconds()
        
        return {
            'started_at': self._started_at,
            'duration': duration,
            'committed': self._committed,
            'rolled_back': self._rolled_back,
            'has_pending_changes': self.has_pending_changes,
            'pending_changes': self.pending_changes_count,
            'repositories_count': len(self._repositories)
        }
    
    def __enter__(self):
        """Entrada del context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Salida del context manager."""
        if exc_type is not None:
            # Si hubo una excepción, revertir
            self.rollback()
        elif not self._committed and not self._rolled_back:
            # Si no se confirmó explícitamente, confirmar automáticamente
            self.commit()

class UnitOfWorkFactory:
    """Factory para crear instancias de UnitOfWork con repositorios preconfigurados."""
    
    def __init__(self):
        self._repository_configs: Dict[str, Type[BaseRepository]] = {}
    
    def register_repository(self, name: str, repository_class: Type[BaseRepository]):
        """
        Registra una configuración de repositorio.
        
        Args:
            name: Nombre del repositorio
            repository_class: Clase del repositorio
        """
        self._repository_configs[name] = repository_class
    
    @contextmanager
    def create_unit_of_work(self, session: Session):
        """
        Crea una nueva UnitOfWork con todos los repositorios registrados.
        
        Args:
            session: Sesión de SQLAlchemy
            
        Yields:
            UnitOfWork: Instancia configurada
        """
        uow = UnitOfWork(session)
        
        # Registrar repositorios configurados
        for name, repo_class in self._repository_configs.items():
            repository = repo_class(session)
            uow.register_repository(name, repository)
        
        try:
            yield uow
        finally:
            if not uow._committed and not uow._rolled_back:
                uow.rollback()

class BatchProcessor:
    """
    Procesador de lotes para operaciones masivas eficientes.
    """
    
    def __init__(self, session: Session, batch_size: int = 1000):
        self.session = session
        self.batch_size = batch_size
        self._current_batch: List[Base] = []
        self._processed_count = 0
        self._started_at = datetime.now()
    
    def add(self, obj: Base):
        """
        Agrega un objeto al lote actual.
        
        Args:
            obj: Objeto a agregar
        """
        self._current_batch.append(obj)
        
        if len(self._current_batch) >= self.batch_size:
            self._flush_batch()
    
    def _flush_batch(self):
        """Procesa el lote actual."""
        if not self._current_batch:
            return
        
        try:
            self.session.add_all(self._current_batch)
            self.session.commit()
            
            self._processed_count += len(self._current_batch)
            logger.debug(f"Lote procesado: {len(self._current_batch)} objetos. "
                        f"Total procesado: {self._processed_count}")
            
            self._current_batch.clear()
            
        except SQLAlchemyError as e:
            logger.error(f"Error procesando lote: {e}")
            self.session.rollback()
            self._current_batch.clear()
            raise
    
    def finish(self) -> int:
        """
        Procesa cualquier objeto pendiente y finaliza.
        
        Returns:
            int: Número total de objetos procesados
        """
        if self._current_batch:
            self._flush_batch()
        
        duration = (datetime.now() - self._started_at).total_seconds()
        logger.info(f"BatchProcessor finalizado: {self._processed_count} objetos "
                   f"procesados en {duration:.3f}s")
        
        return self._processed_count
    
    def __enter__(self):
        """Entrada del context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Salida del context manager."""
        if exc_type is None:
            self.finish()
        else:
            # Si hubo error, limpiar lote sin procesar
            self._current_batch.clear()

# Factory global para UnitOfWork
uow_factory = UnitOfWorkFactory()

# Configurar repositorios comunes
from ..repositories.track_repository import TrackRepository
from ..repositories.artist_repository import ArtistRepository
from ..repositories.album_repository import AlbumRepository
from ..repositories.playlist_repository import SmartPlaylistRepository

uow_factory.register_repository('tracks', TrackRepository)
uow_factory.register_repository('artists', ArtistRepository)
uow_factory.register_repository('albums', AlbumRepository)
uow_factory.register_repository('playlists', SmartPlaylistRepository)
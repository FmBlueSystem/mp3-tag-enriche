"""
Repositorio base con operaciones CRUD comunes.
"""

from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, func
from ..models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    Repositorio base con operaciones CRUD genéricas.
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def create(self, **kwargs) -> ModelType:
        """
        Crea un nuevo registro.
        """
        try:
            obj = self.model(**kwargs)
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Obtiene un registro por su ID.
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Obtiene todos los registros con paginación.
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """
        Actualiza un registro por su ID.
        """
        try:
            obj = self.get_by_id(id)
            if obj:
                for key, value in kwargs.items():
                    if hasattr(obj, key):
                        setattr(obj, key, value)
                self.db.commit()
                self.db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def delete(self, id: int) -> bool:
        """
        Elimina un registro por su ID.
        """
        try:
            obj = self.get_by_id(id)
            if obj:
                self.db.delete(obj)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def count(self) -> int:
        """
        Cuenta todos los registros.
        """
        return self.db.query(func.count(self.model.id)).scalar()
    
    def exists(self, **kwargs) -> bool:
        """
        Verifica si existe un registro con los criterios dados.
        """
        query = self.db.query(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.first() is not None
    
    def find_by(self, **kwargs) -> List[ModelType]:
        """
        Busca registros que coincidan con los criterios dados.
        """
        query = self.db.query(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.all()
    
    def find_one_by(self, **kwargs) -> Optional[ModelType]:
        """
        Busca un registro que coincida con los criterios dados.
        """
        query = self.db.query(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.first()
    
    def search(self, search_term: str, fields: List[str]) -> List[ModelType]:
        """
        Busca registros que contengan el término en los campos especificados.
        """
        if not search_term or not fields:
            return []
        
        search_pattern = f"%{search_term.lower()}%"
        conditions = []
        
        for field in fields:
            if hasattr(self.model, field):
                attr = getattr(self.model, field)
                conditions.append(func.lower(attr).like(search_pattern))
        
        if conditions:
            return self.db.query(self.model).filter(or_(*conditions)).all()
        return []
    
    def bulk_create(self, objects_data: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Crea múltiples registros de forma eficiente.
        """
        try:
            objects = [self.model(**data) for data in objects_data]
            self.db.add_all(objects)
            self.db.commit()
            for obj in objects:
                self.db.refresh(obj)
            return objects
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def bulk_update(self, updates: List[Dict[str, Any]]) -> bool:
        """
        Actualiza múltiples registros de forma eficiente.
        Cada dict debe contener 'id' y los campos a actualizar.
        """
        try:
            for update_data in updates:
                if 'id' not in update_data:
                    continue
                
                obj_id = update_data.pop('id')
                self.db.query(self.model).filter(
                    self.model.id == obj_id
                ).update(update_data)
            
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
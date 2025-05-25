"""
Modelos base para la base de datos de Nueva Biblioteca.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional
import os

# Configuración de la base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///nueva_biblioteca.db')

# Configuración de SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Cambiar a True para debug SQL
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Metadata y base para modelos
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Generador de sesiones de base de datos.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Crea todas las tablas en la base de datos.
    """
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """
    Elimina todas las tablas de la base de datos.
    """
    Base.metadata.drop_all(bind=engine)
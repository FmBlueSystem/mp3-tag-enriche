"""
Modelos de datos para playlists inteligentes y reglas.
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, JSON,
    ForeignKey, Table, Index, UniqueConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from .base import Base

class RuleOperator(Enum):
    """Operadores para reglas de playlist."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    IN_RANGE = "in_range"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"

class RuleLogic(Enum):
    """Lógica para combinación de reglas."""
    AND = "and"
    OR = "or"

class SmartPlaylist(Base):
    """
    Modelo para playlists inteligentes basadas en reglas.
    """
    __tablename__ = 'smart_playlists'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Configuración de la playlist
    is_active = Column(Boolean, nullable=False, default=True)
    auto_update = Column(Boolean, nullable=False, default=True)
    max_tracks = Column(Integer, nullable=True)  # Límite de tracks (None = sin límite)
    
    # Configuración de ordenamiento
    sort_field = Column(String(100), nullable=True)  # Campo por el que ordenar
    sort_order = Column(String(4), nullable=False, default='ASC')  # ASC o DESC
    
    # Lógica de combinación de reglas
    rules_logic = Column(SQLEnum(RuleLogic), nullable=False, default=RuleLogic.AND)
    
    # Metadatos de ejecución
    last_updated = Column(DateTime, nullable=True)
    track_count = Column(Integer, nullable=False, default=0)
    last_execution_duration = Column(Float, nullable=True)  # Duración en segundos
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relaciones
    rules = relationship("PlaylistRule", back_populates="playlist", cascade="all, delete-orphan")
    tracks = relationship("PlaylistTrack", back_populates="playlist", cascade="all, delete-orphan")
    
    # Índices
    __table_args__ = (
        Index('idx_smart_playlist_name', 'name'),
        Index('idx_smart_playlist_active', 'is_active'),
        Index('idx_smart_playlist_auto_update', 'auto_update'),
    )
    
    def __repr__(self):
        return f"<SmartPlaylist(id={self.id}, name='{self.name}', rules={len(self.rules)})>"

class PlaylistRule(Base):
    """
    Modelo para reglas individuales de playlists inteligentes.
    """
    __tablename__ = 'playlist_rules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_id = Column(Integer, ForeignKey('smart_playlists.id'), nullable=False, index=True)
    
    # Definición de la regla
    field_name = Column(String(100), nullable=False)  # Campo del modelo Track/Artist/Album/Genre
    operator = Column(SQLEnum(RuleOperator), nullable=False)
    value = Column(Text, nullable=True)  # Valor a comparar (puede ser JSON para ranges)
    value_type = Column(String(20), nullable=False, default='string')  # string, number, boolean, date
    
    # Metadatos de la regla
    is_active = Column(Boolean, nullable=False, default=True)
    order_index = Column(Integer, nullable=False, default=0)  # Orden de evaluación
    
    # Información adicional para UI
    display_name = Column(String(255), nullable=True)  # Nombre amigable para mostrar
    help_text = Column(Text, nullable=True)  # Texto de ayuda
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relaciones
    playlist = relationship("SmartPlaylist", back_populates="rules")
    
    # Índices
    __table_args__ = (
        Index('idx_playlist_rule_playlist', 'playlist_id'),
        Index('idx_playlist_rule_field', 'field_name'),
        Index('idx_playlist_rule_active', 'is_active'),
        Index('idx_playlist_rule_order', 'playlist_id', 'order_index'),
    )
    
    def __repr__(self):
        return f"<PlaylistRule(id={self.id}, field='{self.field_name}', operator='{self.operator.value}')>"
    
    @property
    def parsed_value(self) -> Any:
        """
        Retorna el valor parseado según su tipo.
        """
        if not self.value:
            return None
        
        try:
            if self.value_type == 'number':
                return float(self.value) if '.' in self.value else int(self.value)
            elif self.value_type == 'boolean':
                return self.value.lower() in ('true', '1', 'yes')
            elif self.value_type == 'date':
                return datetime.fromisoformat(self.value)
            elif self.value_type == 'json':
                import json
                return json.loads(self.value)
            else:
                return self.value
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.value

class PlaylistTrack(Base):
    """
    Tabla de asociación para tracks en playlists inteligentes.
    Incluye metadatos adicionales sobre cuándo se agregó el track.
    """
    __tablename__ = 'playlist_tracks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_id = Column(Integer, ForeignKey('smart_playlists.id'), nullable=False, index=True)
    track_id = Column(Integer, ForeignKey('tracks.id'), nullable=False, index=True)
    
    # Metadatos de la asociación
    position = Column(Integer, nullable=False)  # Posición en la playlist
    added_at = Column(DateTime, default=func.now(), nullable=False)
    score = Column(Float, nullable=True)  # Puntuación de relevancia (para ordenamiento)
    
    # Relaciones
    playlist = relationship("SmartPlaylist", back_populates="tracks")
    track = relationship("Track")
    
    # Índices
    __table_args__ = (
        Index('idx_playlist_track_playlist', 'playlist_id'),
        Index('idx_playlist_track_track', 'track_id'),
        Index('idx_playlist_track_position', 'playlist_id', 'position'),
        UniqueConstraint('playlist_id', 'track_id', name='uq_playlist_track'),
        UniqueConstraint('playlist_id', 'position', name='uq_playlist_position'),
    )
    
    def __repr__(self):
        return f"<PlaylistTrack(playlist_id={self.playlist_id}, track_id={self.track_id}, position={self.position})>"

class SyncHistory(Base):
    """
    Modelo para historial de sincronización y auditoría.
    """
    __tablename__ = 'sync_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Tipo de operación
    operation_type = Column(String(50), nullable=False, index=True)  # import, update, delete, analyze, etc.
    entity_type = Column(String(50), nullable=False)  # track, playlist, artist, etc.
    entity_id = Column(Integer, nullable=True, index=True)  # ID de la entidad afectada
    
    # Detalles de la operación
    operation_data = Column(JSON, nullable=True)  # Datos adicionales de la operación
    file_path = Column(String(500), nullable=True)  # Ruta del archivo (si aplica)
    
    # Resultado de la operación
    status = Column(String(20), nullable=False)  # success, error, warning
    error_message = Column(Text, nullable=True)
    duration = Column(Float, nullable=True)  # Duración en segundos
    
    # Metadatos del sistema
    user_agent = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Índices
    __table_args__ = (
        Index('idx_sync_history_operation', 'operation_type'),
        Index('idx_sync_history_entity', 'entity_type', 'entity_id'),
        Index('idx_sync_history_status', 'status'),
        Index('idx_sync_history_timestamp', 'timestamp'),
        Index('idx_sync_history_file_path', 'file_path'),
    )
    
    def __repr__(self):
        return f"<SyncHistory(id={self.id}, operation='{self.operation_type}', status='{self.status}')>"

class MetadataCache(Base):
    """
    Caché de metadatos externos (Spotify, Last.fm, etc.).
    """
    __tablename__ = 'metadata_cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Clave de identificación
    cache_key = Column(String(255), nullable=False, unique=True, index=True)
    cache_type = Column(String(50), nullable=False, index=True)  # spotify, lastfm, musicbrainz, etc.
    
    # Entidad relacionada
    entity_type = Column(String(50), nullable=False)  # track, artist, album
    entity_id = Column(Integer, nullable=True, index=True)
    
    # Datos del caché
    cached_data = Column(JSON, nullable=False)
    
    # Metadatos del caché
    expires_at = Column(DateTime, nullable=True, index=True)
    hit_count = Column(Integer, nullable=False, default=0)
    last_accessed = Column(DateTime, default=func.now(), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Índices
    __table_args__ = (
        Index('idx_metadata_cache_key', 'cache_key'),
        Index('idx_metadata_cache_type', 'cache_type'),
        Index('idx_metadata_cache_entity', 'entity_type', 'entity_id'),
        Index('idx_metadata_cache_expires', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<MetadataCache(id={self.id}, key='{self.cache_key}', type='{self.cache_type}')>"
    
    @property
    def is_expired(self) -> bool:
        """
        Verifica si el caché ha expirado.
        """
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
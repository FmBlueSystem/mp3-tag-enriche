"""
Repositorio especializado para playlists inteligentes.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc, text
from datetime import datetime, timedelta
import json
import logging

from .base_repository import BaseRepository
from ..models.playlist import (
    SmartPlaylist, PlaylistRule, PlaylistTrack, RuleOperator, RuleLogic
)
from ..models.music import Track, Artist, Album, Genre

logger = logging.getLogger(__name__)

class SmartPlaylistRepository(BaseRepository[SmartPlaylist]):
    """
    Repositorio especializado para playlists inteligentes.
    """
    
    def __init__(self, db: Session):
        super().__init__(SmartPlaylist, db)
    
    def get_with_rules(self, playlist_id: int) -> Optional[SmartPlaylist]:
        """
        Obtiene una playlist con todas sus reglas cargadas.
        
        Args:
            playlist_id: ID de la playlist
            
        Returns:
            SmartPlaylist con reglas cargadas o None
        """
        return (
            self.db.query(SmartPlaylist)
            .options(
                joinedload(SmartPlaylist.rules).joinedload(PlaylistRule.playlist),
                joinedload(SmartPlaylist.tracks).joinedload(PlaylistTrack.track)
            )
            .filter(SmartPlaylist.id == playlist_id)
            .first()
        )
    
    def get_active_playlists(self) -> List[SmartPlaylist]:
        """
        Obtiene todas las playlists activas.
        
        Returns:
            Lista de playlists activas
        """
        return (
            self.db.query(SmartPlaylist)
            .options(joinedload(SmartPlaylist.rules))
            .filter(SmartPlaylist.is_active == True)
            .order_by(SmartPlaylist.name)
            .all()
        )
    
    def get_auto_update_playlists(self) -> List[SmartPlaylist]:
        """
        Obtiene playlists que requieren actualización automática.
        
        Returns:
            Lista de playlists con auto-update habilitado
        """
        return (
            self.db.query(SmartPlaylist)
            .options(joinedload(SmartPlaylist.rules))
            .filter(
                and_(
                    SmartPlaylist.is_active == True,
                    SmartPlaylist.auto_update == True
                )
            )
            .all()
        )
    
    def create_playlist_with_rules(
        self, 
        name: str, 
        rules_data: List[Dict[str, Any]], 
        description: str = "",
        max_tracks: Optional[int] = None,
        sort_field: str = "date_added",
        sort_order: str = "DESC",
        rules_logic: RuleLogic = RuleLogic.AND
    ) -> SmartPlaylist:
        """
        Crea una playlist inteligente con sus reglas.
        
        Args:
            name: Nombre de la playlist
            rules_data: Lista de datos de reglas
            description: Descripción opcional
            max_tracks: Límite máximo de tracks
            sort_field: Campo para ordenamiento
            sort_order: Orden (ASC/DESC)
            rules_logic: Lógica de combinación de reglas
            
        Returns:
            SmartPlaylist creada
        """
        try:
            # Crear playlist
            playlist = SmartPlaylist(
                name=name,
                description=description,
                max_tracks=max_tracks,
                sort_field=sort_field,
                sort_order=sort_order,
                rules_logic=rules_logic
            )
            
            self.db.add(playlist)
            self.db.flush()  # Para obtener el ID
            
            # Crear reglas
            for i, rule_data in enumerate(rules_data):
                rule = PlaylistRule(
                    playlist_id=playlist.id,
                    field_name=rule_data['field_name'],
                    operator=RuleOperator(rule_data['operator']),
                    value=rule_data.get('value'),
                    value_type=rule_data.get('value_type', 'string'),
                    order_index=i,
                    display_name=rule_data.get('display_name'),
                    help_text=rule_data.get('help_text')
                )
                self.db.add(rule)
            
            self.db.commit()
            
            # Ejecutar la playlist para generar tracks iniciales
            self.execute_playlist(playlist.id)
            
            return playlist
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando playlist con reglas: {e}")
            raise
    
    def execute_playlist(self, playlist_id: int) -> int:
        """
        Ejecuta una playlist inteligente aplicando sus reglas.
        
        Args:
            playlist_id: ID de la playlist a ejecutar
            
        Returns:
            int: Número de tracks en la playlist resultante
        """
        start_time = datetime.now()
        
        try:
            playlist = self.get_with_rules(playlist_id)
            if not playlist or not playlist.is_active:
                return 0
            
            # Limpiar tracks existentes
            self.db.query(PlaylistTrack).filter(
                PlaylistTrack.playlist_id == playlist_id
            ).delete()
            
            # Construir query base
            query = self.db.query(Track).options(
                joinedload(Track.artists),
                joinedload(Track.album),
                joinedload(Track.genres)
            )
            
            # Aplicar reglas
            conditions = []
            for rule in playlist.rules:
                if not rule.is_active:
                    continue
                
                condition = self._build_rule_condition(rule)
                if condition is not None:
                    conditions.append(condition)
            
            # Combinar condiciones según la lógica
            if conditions:
                if playlist.rules_logic == RuleLogic.AND:
                    query = query.filter(and_(*conditions))
                else:  # OR
                    query = query.filter(or_(*conditions))
            
            # Aplicar ordenamiento
            if playlist.sort_field and hasattr(Track, playlist.sort_field):
                sort_attr = getattr(Track, playlist.sort_field)
                if playlist.sort_order.upper() == 'DESC':
                    query = query.order_by(desc(sort_attr))
                else:
                    query = query.order_by(asc(sort_attr))
            
            # Aplicar límite
            if playlist.max_tracks:
                query = query.limit(playlist.max_tracks)
            
            # Ejecutar query
            tracks = query.all()
            
            # Agregar tracks a la playlist
            for position, track in enumerate(tracks):
                playlist_track = PlaylistTrack(
                    playlist_id=playlist_id,
                    track_id=track.id,
                    position=position
                )
                self.db.add(playlist_track)
            
            # Actualizar metadata de la playlist
            execution_duration = (datetime.now() - start_time).total_seconds()
            playlist.last_updated = datetime.now()
            playlist.track_count = len(tracks)
            playlist.last_execution_duration = execution_duration
            
            self.db.commit()
            
            logger.info(f"Playlist '{playlist.name}' ejecutada: {len(tracks)} tracks en {execution_duration:.3f}s")
            return len(tracks)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error ejecutando playlist {playlist_id}: {e}")
            raise
    
    def _build_rule_condition(self, rule: PlaylistRule):
        """
        Construye una condición SQLAlchemy para una regla.
        
        Args:
            rule: Regla a convertir
            
        Returns:
            Condición SQLAlchemy o None si no es válida
        """
        try:
            # Mapear campos a atributos del modelo
            field_mapping = {
                'title': Track.normalized_title,
                'duration': Track.duration,
                'bpm': Track.bpm,
                'key': Track.key,
                'energy': Track.energy,
                'danceability': Track.danceability,
                'valence': Track.valence,
                'play_count': Track.play_count,
                'is_favorite': Track.is_favorite,
                'date_added': Track.date_added,
                'last_played': Track.last_played,
                'artist_name': Artist.normalized_name,
                'album_title': Album.normalized_title,
                'genre_name': Genre.normalized_name,
                'year': Album.year
            }
            
            if rule.field_name not in field_mapping:
                logger.warning(f"Campo no reconocido en regla: {rule.field_name}")
                return None
            
            field_attr = field_mapping[rule.field_name]
            value = rule.parsed_value
            
            # Construir condición según el operador
            if rule.operator == RuleOperator.EQUALS:
                return field_attr == value
            
            elif rule.operator == RuleOperator.NOT_EQUALS:
                return field_attr != value
            
            elif rule.operator == RuleOperator.CONTAINS:
                if isinstance(value, str):
                    return func.lower(field_attr).like(f"%{value.lower()}%")
                return field_attr.like(f"%{value}%")
            
            elif rule.operator == RuleOperator.NOT_CONTAINS:
                if isinstance(value, str):
                    return ~func.lower(field_attr).like(f"%{value.lower()}%")
                return ~field_attr.like(f"%{value}%")
            
            elif rule.operator == RuleOperator.STARTS_WITH:
                if isinstance(value, str):
                    return func.lower(field_attr).like(f"{value.lower()}%")
                return field_attr.like(f"{value}%")
            
            elif rule.operator == RuleOperator.ENDS_WITH:
                if isinstance(value, str):
                    return func.lower(field_attr).like(f"%{value.lower()}")
                return field_attr.like(f"%{value}")
            
            elif rule.operator == RuleOperator.GREATER_THAN:
                return field_attr > value
            
            elif rule.operator == RuleOperator.LESS_THAN:
                return field_attr < value
            
            elif rule.operator == RuleOperator.GREATER_EQUAL:
                return field_attr >= value
            
            elif rule.operator == RuleOperator.LESS_EQUAL:
                return field_attr <= value
            
            elif rule.operator == RuleOperator.IN_RANGE:
                if isinstance(value, dict) and 'min' in value and 'max' in value:
                    return and_(field_attr >= value['min'], field_attr <= value['max'])
            
            elif rule.operator == RuleOperator.IS_NULL:
                return field_attr.is_(None)
            
            elif rule.operator == RuleOperator.IS_NOT_NULL:
                return field_attr.isnot(None)
            
            else:
                logger.warning(f"Operador no implementado: {rule.operator}")
                return None
                
        except Exception as e:
            logger.error(f"Error construyendo condición para regla {rule.id}: {e}")
            return None
    
    def update_all_auto_playlists(self) -> Dict[str, Any]:
        """
        Actualiza todas las playlists con auto-update habilitado.
        
        Returns:
            Dict con resultados de la actualización
        """
        start_time = datetime.now()
        results = {
            'updated_playlists': [],
            'failed_playlists': [],
            'total_tracks': 0
        }
        
        try:
            playlists = self.get_auto_update_playlists()
            
            for playlist in playlists:
                try:
                    track_count = self.execute_playlist(playlist.id)
                    results['updated_playlists'].append({
                        'id': playlist.id,
                        'name': playlist.name,
                        'track_count': track_count
                    })
                    results['total_tracks'] += track_count
                    
                except Exception as e:
                    results['failed_playlists'].append({
                        'id': playlist.id,
                        'name': playlist.name,
                        'error': str(e)
                    })
                    logger.error(f"Error actualizando playlist {playlist.name}: {e}")
            
            duration = (datetime.now() - start_time).total_seconds()
            results['duration'] = duration
            results['updated_count'] = len(results['updated_playlists'])
            results['failed_count'] = len(results['failed_playlists'])
            
            logger.info(f"Actualización masiva completada: {results['updated_count']} exitosas, "
                       f"{results['failed_count']} fallidas en {duration:.3f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Error en actualización masiva de playlists: {e}")
            results['error'] = str(e)
            return results
    
    def get_playlist_tracks(self, playlist_id: int) -> List[Track]:
        """
        Obtiene los tracks de una playlist en orden.
        
        Args:
            playlist_id: ID de la playlist
            
        Returns:
            Lista de tracks ordenados por posición
        """
        return (
            self.db.query(Track)
            .join(PlaylistTrack)
            .options(
                joinedload(Track.artists),
                joinedload(Track.album)
            )
            .filter(PlaylistTrack.playlist_id == playlist_id)
            .order_by(PlaylistTrack.position)
            .all()
        )
    
    def export_playlist(self, playlist_id: int, format: str = 'json') -> Dict[str, Any]:
        """
        Exporta una playlist con sus reglas y tracks.
        
        Args:
            playlist_id: ID de la playlist
            format: Formato de exportación ('json', 'm3u', etc.)
            
        Returns:
            Dict con datos de exportación
        """
        playlist = self.get_with_rules(playlist_id)
        if not playlist:
            raise ValueError(f"Playlist {playlist_id} no encontrada")
        
        export_data = {
            'playlist': {
                'name': playlist.name,
                'description': playlist.description,
                'max_tracks': playlist.max_tracks,
                'sort_field': playlist.sort_field,
                'sort_order': playlist.sort_order,
                'rules_logic': playlist.rules_logic.value,
                'created_at': playlist.created_at.isoformat(),
                'track_count': playlist.track_count
            },
            'rules': [
                {
                    'field_name': rule.field_name,
                    'operator': rule.operator.value,
                    'value': rule.value,
                    'value_type': rule.value_type,
                    'display_name': rule.display_name,
                    'order_index': rule.order_index
                }
                for rule in sorted(playlist.rules, key=lambda r: r.order_index)
            ],
            'tracks': [
                {
                    'title': track.track.title,
                    'artist': track.track.artist_names[0] if track.track.artist_names else '',
                    'album': track.track.album.title if track.track.album else '',
                    'file_path': track.track.file_path,
                    'duration': track.track.duration,
                    'position': track.position
                }
                for track in sorted(playlist.tracks, key=lambda t: t.position)
            ],
            'exported_at': datetime.now().isoformat(),
            'format': format
        }
        
        return export_data
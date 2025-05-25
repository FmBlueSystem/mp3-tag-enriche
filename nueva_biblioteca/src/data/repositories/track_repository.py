"""
Repositorio especializado para gestión de tracks musicales.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta

from .base_repository import BaseRepository
from ..models.music import Track, Artist, Album, Genre

class TrackRepository(BaseRepository[Track]):
    """
    Repositorio especializado para operaciones con tracks musicales.
    """
    
    def __init__(self, db: Session):
        super().__init__(Track, db)
    
    def get_by_file_path(self, file_path: str) -> Optional[Track]:
        """
        Obtiene un track por su ruta de archivo.
        """
        return self.db.query(Track).filter(Track.file_path == file_path).first()
    
    def get_with_relations(self, track_id: int) -> Optional[Track]:
        """
        Obtiene un track con todas sus relaciones cargadas.
        """
        return (
            self.db.query(Track)
            .options(
                joinedload(Track.artists),
                joinedload(Track.album).joinedload(Album.artist),
                joinedload(Track.genres)
            )
            .filter(Track.id == track_id)
            .first()
        )
    
    def search_tracks(
        self, 
        query: str = "", 
        artist: str = "", 
        album: str = "", 
        genre: str = "",
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        min_bpm: Optional[float] = None,
        max_bpm: Optional[float] = None,
        key: str = "",
        is_favorite: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Track]:
        """
        Búsqueda avanzada de tracks con múltiples filtros.
        """
        query_obj = (
            self.db.query(Track)
            .options(
                joinedload(Track.artists),
                joinedload(Track.album).joinedload(Album.artist),
                joinedload(Track.genres)
            )
        )
        
        # Búsqueda por texto en título
        if query:
            search_pattern = f"%{query.lower()}%"
            query_obj = query_obj.filter(
                func.lower(Track.normalized_title).like(search_pattern)
            )
        
        # Filtro por artista
        if artist:
            artist_pattern = f"%{artist.lower()}%"
            query_obj = query_obj.join(Track.artists).filter(
                func.lower(Artist.normalized_name).like(artist_pattern)
            )
        
        # Filtro por álbum
        if album:
            album_pattern = f"%{album.lower()}%"
            query_obj = query_obj.join(Track.album).filter(
                func.lower(Album.normalized_title).like(album_pattern)
            )
        
        # Filtro por género
        if genre:
            genre_pattern = f"%{genre.lower()}%"
            query_obj = query_obj.join(Track.genres).filter(
                func.lower(Genre.normalized_name).like(genre_pattern)
            )
        
        # Filtros por duración
        if min_duration is not None:
            query_obj = query_obj.filter(Track.duration >= min_duration)
        if max_duration is not None:
            query_obj = query_obj.filter(Track.duration <= max_duration)
        
        # Filtros por BPM
        if min_bpm is not None:
            query_obj = query_obj.filter(Track.bpm >= min_bpm)
        if max_bpm is not None:
            query_obj = query_obj.filter(Track.bpm <= max_bpm)
        
        # Filtro por clave musical
        if key:
            query_obj = query_obj.filter(Track.key == key)
        
        # Filtro por favoritos
        if is_favorite is not None:
            query_obj = query_obj.filter(Track.is_favorite == is_favorite)
        
        return query_obj.offset(skip).limit(limit).all()
    
    def get_recent_tracks(self, days: int = 7, limit: int = 50) -> List[Track]:
        """
        Obtiene tracks agregados recientemente.
        """
        since_date = datetime.now() - timedelta(days=days)
        return (
            self.db.query(Track)
            .options(joinedload(Track.artists))
            .filter(Track.date_added >= since_date)
            .order_by(desc(Track.date_added))
            .limit(limit)
            .all()
        )
    
    def get_most_played(self, limit: int = 50) -> List[Track]:
        """
        Obtiene los tracks más reproducidos.
        """
        return (
            self.db.query(Track)
            .options(joinedload(Track.artists))
            .filter(Track.play_count > 0)
            .order_by(desc(Track.play_count))
            .limit(limit)
            .all()
        )
    
    def get_favorites(self, limit: int = 100) -> List[Track]:
        """
        Obtiene tracks marcados como favoritos.
        """
        return (
            self.db.query(Track)
            .options(joinedload(Track.artists))
            .filter(Track.is_favorite == True)
            .order_by(desc(Track.date_added))
            .limit(limit)
            .all()
        )
    
    def get_by_genre(self, genre_name: str, limit: int = 100) -> List[Track]:
        """
        Obtiene tracks de un género específico.
        """
        return (
            self.db.query(Track)
            .options(joinedload(Track.artists))
            .join(Track.genres)
            .filter(func.lower(Genre.name) == genre_name.lower())
            .limit(limit)
            .all()
        )
    
    def get_by_artist(self, artist_name: str, limit: int = 100) -> List[Track]:
        """
        Obtiene tracks de un artista específico.
        """
        return (
            self.db.query(Track)
            .options(joinedload(Track.artists))
            .join(Track.artists)
            .filter(func.lower(Artist.normalized_name) == artist_name.lower())
            .limit(limit)
            .all()
        )
    
    def get_by_album(self, album_id: int) -> List[Track]:
        """
        Obtiene todos los tracks de un álbum ordenados por número de track.
        """
        return (
            self.db.query(Track)
            .options(joinedload(Track.artists))
            .filter(Track.album_id == album_id)
            .order_by(asc(Track.disc_number), asc(Track.track_number))
            .all()
        )
    
    def get_similar_tracks(
        self, 
        track_id: int, 
        limit: int = 20
    ) -> List[Track]:
        """
        Encuentra tracks similares basados en características musicales.
        """
        reference_track = self.get_by_id(track_id)
        if not reference_track:
            return []
        
        query_obj = self.db.query(Track).filter(Track.id != track_id)
        
        # Filtros de similaridad
        if reference_track.bpm:
            bpm_range = reference_track.bpm * 0.1  # ±10%
            query_obj = query_obj.filter(
                and_(
                    Track.bpm >= reference_track.bpm - bpm_range,
                    Track.bpm <= reference_track.bpm + bpm_range
                )
            )
        
        if reference_track.key:
            query_obj = query_obj.filter(Track.key == reference_track.key)
        
        # Buscar tracks del mismo género
        if reference_track.genres:
            genre_ids = [g.id for g in reference_track.genres]
            query_obj = query_obj.join(Track.genres).filter(
                Genre.id.in_(genre_ids)
            )
        
        return query_obj.limit(limit).all()
    
    def increment_play_count(self, track_id: int) -> bool:
        """
        Incrementa el contador de reproducciones y actualiza la fecha de última reproducción.
        """
        try:
            track = self.get_by_id(track_id)
            if track:
                track.play_count += 1
                track.last_played = datetime.now()
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            raise e
    
    def toggle_favorite(self, track_id: int) -> bool:
        """
        Alterna el estado de favorito de un track.
        """
        try:
            track = self.get_by_id(track_id)
            if track:
                track.is_favorite = not track.is_favorite
                self.db.commit()
                return track.is_favorite
            return False
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_tracks_needing_analysis(self, limit: int = 100) -> List[Track]:
        """
        Obtiene tracks que necesitan análisis de audio.
        """
        return (
            self.db.query(Track)
            .filter(Track.is_analyzed == False)
            .limit(limit)
            .all()
        )
    
    def get_tracks_missing_metadata(self, limit: int = 100) -> List[Track]:
        """
        Obtiene tracks que necesitan enriquecimiento de metadatos.
        """
        return (
            self.db.query(Track)
            .filter(Track.has_metadata == False)
            .limit(limit)
            .all()
        )
    
    def get_duplicate_tracks(self) -> List[List[Track]]:
        """
        Encuentra tracks duplicados basados en título y artista.
        """
        # Esta es una consulta compleja que agrupa por título normalizado
        # y luego filtra grupos con más de un elemento
        subquery = (
            self.db.query(
                Track.normalized_title,
                func.count(Track.id).label('count')
            )
            .group_by(Track.normalized_title)
            .having(func.count(Track.id) > 1)
            .subquery()
        )
        
        duplicate_titles = [row.normalized_title for row in self.db.query(subquery).all()]
        
        duplicates = []
        for title in duplicate_titles:
            tracks = (
                self.db.query(Track)
                .options(joinedload(Track.artists))
                .filter(Track.normalized_title == title)
                .all()
            )
            if len(tracks) > 1:
                duplicates.append(tracks)
        
        return duplicates
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de la biblioteca.
        """
        total_tracks = self.count()
        total_duration = self.db.query(func.sum(Track.duration)).scalar() or 0
        total_plays = self.db.query(func.sum(Track.play_count)).scalar() or 0
        favorites_count = self.db.query(func.count(Track.id)).filter(Track.is_favorite == True).scalar()
        
        # Formato más común
        most_common_format = (
            self.db.query(Track.file_format, func.count(Track.id).label('count'))
            .group_by(Track.file_format)
            .order_by(desc('count'))
            .first()
        )
        
        return {
            'total_tracks': total_tracks,
            'total_duration_seconds': total_duration,
            'total_duration_formatted': f"{int(total_duration // 3600)}h {int((total_duration % 3600) // 60)}m",
            'total_plays': total_plays,
            'favorites_count': favorites_count,
            'most_common_format': most_common_format[0] if most_common_format else None,
            'avg_track_duration': total_duration / total_tracks if total_tracks > 0 else 0
        }
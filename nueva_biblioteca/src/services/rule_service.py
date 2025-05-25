"""
Servicio de reglas para Nueva Biblioteca.
Integra el motor de reglas con la interfaz de usuario.
"""
from typing import List, Dict, Any, Optional, Tuple
from PySide6.QtCore import QObject, Signal

from ..core.rule_engine import RuleEngine, SmartPlaylist
from .music_service import MusicService


class RuleService(QObject):
    """Servicio para gestionar reglas y playlists inteligentes."""
    
    # Señales
    playlist_created = Signal(str, str)  # id, name
    playlist_updated = Signal(str, str)  # id, name
    playlist_deleted = Signal(str, str)  # id, name
    rule_validated = Signal(bool, str)   # valid, message
    tracks_filtered = Signal(list)       # filtered_tracks
    
    def __init__(self, music_service: MusicService, parent=None):
        super().__init__(parent)
        self.music_service = music_service
        self.rule_engine = RuleEngine()
        self._current_filter_rule = ""
        self._filtered_tracks = []
        
    def validate_rule_expression(self, expression: str) -> Tuple[bool, str, List[str]]:
        """Valida una expresión de regla."""
        if not expression.strip():
            return True, "Regla vacía (mostrará todos los tracks)", []
        
        is_valid, error, used_fields = self.rule_engine.validate_rule(expression)
        
        if is_valid:
            message = f"Regla válida. Campos utilizados: {', '.join(used_fields)}"
        else:
            message = error
        
        self.rule_validated.emit(is_valid, message)
        return is_valid, message, used_fields
    
    def apply_filter_rule(self, expression: str) -> List[Dict[str, Any]]:
        """Aplica una regla de filtro a todos los tracks."""
        all_tracks = self.music_service.get_all_tracks()
        
        if not expression.strip():
            self._filtered_tracks = all_tracks
            self._current_filter_rule = ""
        else:
            try:
                filtered = self.rule_engine.evaluator.filter_tracks(expression, all_tracks)
                self._filtered_tracks = filtered
                self._current_filter_rule = expression
            except Exception as e:
                # En caso de error, mostrar todos los tracks
                self._filtered_tracks = all_tracks
                self._current_filter_rule = ""
        
        self.tracks_filtered.emit(self._filtered_tracks)
        return self._filtered_tracks
    
    def get_current_filtered_tracks(self) -> List[Dict[str, Any]]:
        """Obtiene los tracks actualmente filtrados."""
        return self._filtered_tracks.copy()
    
    def get_current_filter_rule(self) -> str:
        """Obtiene la regla de filtro actual."""
        return self._current_filter_rule
    
    def create_smart_playlist(self, name: str, rule_expression: str, 
                            description: str = "", color: str = "#6750A4", 
                            icon: str = "🎵") -> Tuple[bool, str, Optional[SmartPlaylist]]:
        """Crea una nueva playlist inteligente."""
        success, message, playlist = self.rule_engine.create_smart_playlist(
            name, rule_expression, description, color, icon
        )
        
        if success and playlist:
            self.playlist_created.emit(playlist.id, playlist.name)
        
        return success, message, playlist
    
    def update_smart_playlist(self, playlist_id: str, **kwargs) -> Tuple[bool, str]:
        """Actualiza una playlist inteligente."""
        success, message = self.rule_engine.update_smart_playlist(playlist_id, **kwargs)
        
        if success:
            playlist = self.rule_engine.get_smart_playlist(playlist_id)
            if playlist:
                self.playlist_updated.emit(playlist.id, playlist.name)
        
        return success, message
    
    def delete_smart_playlist(self, playlist_id: str) -> Tuple[bool, str]:
        """Elimina una playlist inteligente."""
        playlist = self.rule_engine.get_smart_playlist(playlist_id)
        playlist_name = playlist.name if playlist else "Desconocida"
        
        success, message = self.rule_engine.delete_smart_playlist(playlist_id)
        
        if success:
            self.playlist_deleted.emit(playlist_id, playlist_name)
        
        return success, message
    
    def get_smart_playlist(self, playlist_id: str) -> Optional[SmartPlaylist]:
        """Obtiene una playlist inteligente por ID."""
        return self.rule_engine.get_smart_playlist(playlist_id)
    
    def list_smart_playlists(self, active_only: bool = True) -> List[SmartPlaylist]:
        """Lista todas las playlists inteligentes."""
        return self.rule_engine.list_smart_playlists(active_only)
    
    def generate_playlist_tracks(self, playlist_id: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """Genera los tracks para una playlist inteligente."""
        all_tracks = self.music_service.get_all_tracks()
        return self.rule_engine.generate_playlist_tracks(playlist_id, all_tracks)
    
    def analyze_playlist_performance(self, playlist_id: str) -> Dict[str, Any]:
        """Analiza el rendimiento de una playlist."""
        all_tracks = self.music_service.get_all_tracks()
        return self.rule_engine.analyze_playlist_rule(playlist_id, all_tracks)
    
    def get_rule_suggestions(self) -> List[str]:
        """Obtiene sugerencias de reglas basadas en los datos."""
        all_tracks = self.music_service.get_all_tracks()
        return self.rule_engine.suggest_rule_templates(all_tracks)
    
    def create_rule_from_template(self, template_type: str, **params) -> str:
        """Crea una regla desde una plantilla."""
        return self.rule_engine.create_rule_from_template(template_type, **params)
    
    def get_available_fields(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene los campos disponibles para reglas."""
        return self.rule_engine.get_available_fields()
    
    def get_field_operators(self, field_name: str) -> List[str]:
        """Obtiene los operadores válidos para un campo."""
        return self.rule_engine.get_field_operators(field_name)
    
    def get_field_values(self, field_name: str) -> List[Any]:
        """Obtiene los valores únicos de un campo de la biblioteca."""
        if field_name == "genre":
            return self.music_service.get_genres()
        elif field_name == "artist":
            return self.music_service.get_artists()
        elif field_name == "album":
            return self.music_service.get_albums()
        elif field_name == "year":
            return self.music_service.get_years()
        elif field_name == "key":
            return self.music_service.get_keys()
        else:
            # Para campos numéricos, obtener rango
            all_tracks = self.music_service.get_all_tracks()
            values = []
            for track in all_tracks:
                if field_name in track and track[field_name] is not None:
                    values.append(track[field_name])
            
            if values and all(isinstance(v, (int, float)) for v in values):
                return [min(values), max(values)]
            
            return list(set(values)) if values else []
    
    def get_library_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la biblioteca para ayudar en reglas."""
        all_tracks = self.music_service.get_all_tracks()
        return self.rule_engine.get_rule_statistics(all_tracks)
    
    def export_playlists(self, file_path: str) -> Tuple[bool, str]:
        """Exporta todas las playlists a un archivo."""
        return self.rule_engine.export_playlists(file_path)
    
    def import_playlists(self, file_path: str, overwrite: bool = False) -> Tuple[bool, str]:
        """Importa playlists desde un archivo."""
        return self.rule_engine.import_playlists(file_path, overwrite)
    
    def get_quick_filters(self) -> List[Dict[str, str]]:
        """Obtiene filtros rápidos predefinidos."""
        return [
            {
                "name": "Alta Energía",
                "rule": "energy > 0.8",
                "description": "Tracks con alta energía",
                "icon": "⚡"
            },
            {
                "name": "House Music",
                "rule": "genre CONTAINS 'House'",
                "description": "Todos los subgéneros de House",
                "icon": "🏠"
            },
            {
                "name": "Tracks Recientes",
                "rule": "year > 2015",
                "description": "Música de los últimos años",
                "icon": "🆕"
            },
            {
                "name": "BPM Medio",
                "rule": "bpm BETWEEN 120 AND 140",
                "description": "Tempo medio para mezclar",
                "icon": "🎵"
            },
            {
                "name": "Favoritos",
                "rule": "rating >= 4",
                "description": "Tracks con 4+ estrellas",
                "icon": "⭐"
            },
            {
                "name": "Muy Reproducidos",
                "rule": "play_count > 30",
                "description": "Tracks populares",
                "icon": "🔥"
            },
            {
                "name": "Chill Vibes",
                "rule": "energy < 0.5 AND valence > 0.4",
                "description": "Música relajante y positiva",
                "icon": "😌"
            },
            {
                "name": "Workout",
                "rule": "energy > 0.8 AND bpm BETWEEN 120 AND 140",
                "description": "Perfecta para ejercicio",
                "icon": "💪"
            },
            {
                "name": "Clásicos",
                "rule": "year < 2010 AND rating >= 4",
                "description": "Clásicos bien valorados",
                "icon": "🎖️"
            },
            {
                "name": "Compatibles 8A",
                "rule": "key COMPATIBLE_WITH '8A'",
                "description": "Claves compatibles con 8A",
                "icon": "🎹"
            }
        ]
    
    def search_with_rule(self, search_query: str, rule_expression: str = "") -> List[Dict[str, Any]]:
        """Combina búsqueda de texto con reglas."""
        # Primero aplicar búsqueda de texto
        if search_query:
            text_results = self.music_service.search_tracks(search_query)
        else:
            text_results = self.music_service.get_all_tracks()
        
        # Luego aplicar regla si existe
        if rule_expression.strip():
            try:
                filtered_results = self.rule_engine.evaluator.filter_tracks(rule_expression, text_results)
                return filtered_results
            except Exception:
                return text_results
        
        return text_results
    
    def get_rule_examples(self) -> List[Dict[str, str]]:
        """Obtiene ejemplos de reglas para ayuda al usuario."""
        return [
            {
                "rule": "genre = 'House'",
                "description": "Tracks del género House exacto"
            },
            {
                "rule": "bpm BETWEEN 120 AND 140",
                "description": "Tracks con BPM entre 120 y 140"
            },
            {
                "rule": "artist CONTAINS 'deadmau5'",
                "description": "Tracks que contengan 'deadmau5' en el artista"
            },
            {
                "rule": "energy > 0.7 AND danceability > 0.6",
                "description": "Tracks energéticos y bailables"
            },
            {
                "rule": "year > 2015 OR rating >= 5",
                "description": "Tracks recientes o con máxima calificación"
            },
            {
                "rule": "key COMPATIBLE_WITH '8A'",
                "description": "Claves compatibles para mezcla armónica"
            },
            {
                "rule": "NOT (genre = 'Dubstep') AND bpm < 130",
                "description": "Excluir Dubstep y limitar BPM"
            },
            {
                "rule": "title STARTS_WITH 'The' AND duration > 300",
                "description": "Títulos que empiecen con 'The' y sean largos"
            }
        ] 
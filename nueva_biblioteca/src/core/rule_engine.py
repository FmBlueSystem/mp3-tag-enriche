"""
Motor de reglas principal para Nueva Biblioteca.
Coordina el parser y evaluador para crear un sistema completo de reglas musicales.
"""
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import json

from .rule_parser import RuleParser, RuleParseError
from .rule_evaluator import RuleEvaluator
from .expression_ast import ExpressionAST


@dataclass
class SmartPlaylist:
    """Representa una playlist inteligente con reglas."""
    id: str
    name: str
    description: str
    rule_expression: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    color: str = "#6750A4"
    icon: str = "🎵"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rule_expression": self.rule_expression,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "color": self.color,
            "icon": self.icon
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SmartPlaylist':
        """Crea desde diccionario."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            rule_expression=data["rule_expression"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            is_active=data.get("is_active", True),
            color=data.get("color", "#6750A4"),
            icon=data.get("icon", "🎵")
        )


class RuleEngine:
    """Motor de reglas principal para Nueva Biblioteca."""
    
    def __init__(self):
        self.parser = RuleParser()
        self.evaluator = RuleEvaluator()
        self.smart_playlists: Dict[str, SmartPlaylist] = {}
        self._field_definitions = self._setup_field_definitions()
        
    def _setup_field_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Define los campos disponibles y sus características."""
        return {
            "title": {
                "type": "string",
                "description": "Título de la canción",
                "searchable": True,
                "operators": ["=", "!=", "CONTAINS", "STARTS_WITH", "ENDS_WITH"]
            },
            "artist": {
                "type": "string", 
                "description": "Artista principal",
                "searchable": True,
                "operators": ["=", "!=", "CONTAINS", "STARTS_WITH", "ENDS_WITH"]
            },
            "album": {
                "type": "string",
                "description": "Álbum",
                "searchable": True,
                "operators": ["=", "!=", "CONTAINS", "STARTS_WITH", "ENDS_WITH"]
            },
            "genre": {
                "type": "string",
                "description": "Género musical",
                "searchable": True,
                "operators": ["=", "!=", "IN", "CONTAINS"]
            },
            "bpm": {
                "type": "number",
                "description": "Beats por minuto",
                "searchable": False,
                "operators": ["=", "!=", ">", ">=", "<", "<=", "BETWEEN"],
                "min": 60,
                "max": 200
            },
            "key": {
                "type": "string",
                "description": "Clave musical (notación Camelot)",
                "searchable": False,
                "operators": ["=", "!=", "IN", "COMPATIBLE_WITH"],
                "values": [f"{i}{letter}" for i in range(1, 13) for letter in ["A", "B"]]
            },
            "energy": {
                "type": "number",
                "description": "Nivel de energía (0.0 - 1.0)",
                "searchable": False,
                "operators": ["=", "!=", ">", ">=", "<", "<=", "BETWEEN"],
                "min": 0.0,
                "max": 1.0
            },
            "valence": {
                "type": "number",
                "description": "Valencia emocional (0.0 - 1.0)",
                "searchable": False,
                "operators": ["=", "!=", ">", ">=", "<", "<=", "BETWEEN"],
                "min": 0.0,
                "max": 1.0
            },
            "danceability": {
                "type": "number",
                "description": "Bailabilidad (0.0 - 1.0)",
                "searchable": False,
                "operators": ["=", "!=", ">", ">=", "<", "<=", "BETWEEN"],
                "min": 0.0,
                "max": 1.0
            },
            "year": {
                "type": "number",
                "description": "Año de lanzamiento",
                "searchable": False,
                "operators": ["=", "!=", ">", ">=", "<", "<=", "BETWEEN"],
                "min": 1900,
                "max": datetime.now().year + 1
            },
            "duration": {
                "type": "number",
                "description": "Duración en segundos",
                "searchable": False,
                "operators": ["=", "!=", ">", ">=", "<", "<=", "BETWEEN"],
                "min": 30,
                "max": 3600
            },
            "rating": {
                "type": "number",
                "description": "Calificación (1-5 estrellas)",
                "searchable": False,
                "operators": ["=", "!=", ">", ">=", "<", "<=", "BETWEEN"],
                "min": 1,
                "max": 5
            },
            "play_count": {
                "type": "number",
                "description": "Número de reproducciones",
                "searchable": False,
                "operators": ["=", "!=", ">", ">=", "<", "<=", "BETWEEN"],
                "min": 0
            },
            "last_played": {
                "type": "date",
                "description": "Última reproducción",
                "searchable": False,
                "operators": ["=", "!=", ">", ">=", "<", "<=", "BETWEEN"]
            }
        }
    
    def get_available_fields(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene la definición de campos disponibles."""
        return self._field_definitions.copy()
    
    def get_field_operators(self, field_name: str) -> List[str]:
        """Obtiene los operadores válidos para un campo."""
        field_def = self._field_definitions.get(field_name, {})
        return field_def.get("operators", [])
    
    def validate_rule(self, rule_expression: str) -> Tuple[bool, Optional[str], List[str]]:
        """Valida una regla completamente."""
        # Validar sintaxis
        syntax_valid, syntax_error = self.parser.validate_syntax(rule_expression)
        if not syntax_valid:
            return False, f"Error de sintaxis: {syntax_error}", []
        
        # Validar campos
        try:
            ast = self.parser.parse(rule_expression)
            used_fields = ast.get_fields_used()
            
            # Verificar que todos los campos existan
            available_fields = list(self._field_definitions.keys())
            invalid_fields = [field for field in used_fields if field not in available_fields]
            
            if invalid_fields:
                return False, f"Campos no válidos: {', '.join(invalid_fields)}", used_fields
            
            return True, None, used_fields
            
        except Exception as e:
            return False, f"Error de validación: {str(e)}", []
    
    def create_smart_playlist(self, name: str, rule_expression: str, 
                            description: str = "", color: str = "#6750A4", 
                            icon: str = "🎵") -> Tuple[bool, str, Optional[SmartPlaylist]]:
        """Crea una nueva playlist inteligente."""
        # Validar regla
        is_valid, error, used_fields = self.validate_rule(rule_expression)
        if not is_valid:
            return False, error, None
        
        # Generar ID único
        import uuid
        playlist_id = str(uuid.uuid4())
        
        # Crear playlist
        now = datetime.now()
        playlist = SmartPlaylist(
            id=playlist_id,
            name=name,
            description=description,
            rule_expression=rule_expression,
            created_at=now,
            updated_at=now,
            color=color,
            icon=icon
        )
        
        self.smart_playlists[playlist_id] = playlist
        return True, f"Playlist '{name}' creada exitosamente", playlist
    
    def update_smart_playlist(self, playlist_id: str, **kwargs) -> Tuple[bool, str]:
        """Actualiza una playlist inteligente."""
        if playlist_id not in self.smart_playlists:
            return False, "Playlist no encontrada"
        
        playlist = self.smart_playlists[playlist_id]
        
        # Si se actualiza la regla, validarla
        if "rule_expression" in kwargs:
            is_valid, error, _ = self.validate_rule(kwargs["rule_expression"])
            if not is_valid:
                return False, error
        
        # Actualizar campos
        for field, value in kwargs.items():
            if hasattr(playlist, field):
                setattr(playlist, field, value)
        
        playlist.updated_at = datetime.now()
        return True, "Playlist actualizada exitosamente"
    
    def delete_smart_playlist(self, playlist_id: str) -> Tuple[bool, str]:
        """Elimina una playlist inteligente."""
        if playlist_id not in self.smart_playlists:
            return False, "Playlist no encontrada"
        
        playlist_name = self.smart_playlists[playlist_id].name
        del self.smart_playlists[playlist_id]
        return True, f"Playlist '{playlist_name}' eliminada"
    
    def get_smart_playlist(self, playlist_id: str) -> Optional[SmartPlaylist]:
        """Obtiene una playlist inteligente por ID."""
        return self.smart_playlists.get(playlist_id)
    
    def list_smart_playlists(self, active_only: bool = True) -> List[SmartPlaylist]:
        """Lista todas las playlists inteligentes."""
        playlists = list(self.smart_playlists.values())
        if active_only:
            playlists = [p for p in playlists if p.is_active]
        return sorted(playlists, key=lambda p: p.updated_at, reverse=True)
    
    def generate_playlist_tracks(self, playlist_id: str, 
                               tracks: List[Dict[str, Any]]) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """Genera los tracks para una playlist inteligente."""
        playlist = self.get_smart_playlist(playlist_id)
        if not playlist:
            return False, "Playlist no encontrada", []
        
        try:
            filtered_tracks = self.evaluator.filter_tracks(playlist.rule_expression, tracks)
            return True, f"Generados {len(filtered_tracks)} tracks", filtered_tracks
        except Exception as e:
            return False, f"Error al generar playlist: {str(e)}", []
    
    def analyze_playlist_rule(self, playlist_id: str, 
                            tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza el rendimiento de la regla de una playlist."""
        playlist = self.get_smart_playlist(playlist_id)
        if not playlist:
            return {"error": "Playlist no encontrada"}
        
        return self.evaluator.analyze_rule_performance(playlist.rule_expression, tracks)
    
    def suggest_rule_improvements(self, rule_expression: str) -> List[str]:
        """Sugiere mejoras para una regla."""
        return self.evaluator.suggest_optimizations(rule_expression)
    
    def create_rule_from_template(self, template_type: str, **params) -> str:
        """Crea una regla desde una plantilla predefinida."""
        templates = {
            "genre_energy": "genre = '{genre}' AND energy > {min_energy}",
            "bpm_range": "bpm BETWEEN {min_bpm} AND {max_bpm}",
            "year_genre": "year BETWEEN {start_year} AND {end_year} AND genre = '{genre}'",
            "artist_recent": "artist CONTAINS '{artist}' AND year > {min_year}",
            "high_energy": "energy > 0.7 AND danceability > 0.6 AND bpm > 120",
            "chill_vibes": "energy < 0.5 AND valence > 0.4 AND bpm < 120",
            "workout": "energy > 0.8 AND bpm BETWEEN 120 AND 140",
            "focus": "energy BETWEEN 0.3 AND 0.7 AND valence BETWEEN 0.3 AND 0.7",
            "party": "energy > 0.7 AND danceability > 0.7 AND valence > 0.6",
            "camelot_compatible": "key COMPATIBLE_WITH '{target_key}'"
        }
        
        template = templates.get(template_type, "")
        if not template:
            return ""
        
        try:
            return template.format(**params)
        except KeyError as e:
            return f"# Error: Parámetro faltante {e}"
    
    def export_playlists(self, file_path: str) -> Tuple[bool, str]:
        """Exporta todas las playlists a un archivo JSON."""
        try:
            data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "playlists": [playlist.to_dict() for playlist in self.smart_playlists.values()]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True, f"Exportadas {len(self.smart_playlists)} playlists a {file_path}"
            
        except Exception as e:
            return False, f"Error al exportar: {str(e)}"
    
    def import_playlists(self, file_path: str, overwrite: bool = False) -> Tuple[bool, str]:
        """Importa playlists desde un archivo JSON."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported_count = 0
            skipped_count = 0
            
            for playlist_data in data.get("playlists", []):
                playlist = SmartPlaylist.from_dict(playlist_data)
                
                # Validar regla
                is_valid, error, _ = self.validate_rule(playlist.rule_expression)
                if not is_valid:
                    skipped_count += 1
                    continue
                
                # Verificar si ya existe
                if playlist.id in self.smart_playlists and not overwrite:
                    skipped_count += 1
                    continue
                
                self.smart_playlists[playlist.id] = playlist
                imported_count += 1
            
            message = f"Importadas {imported_count} playlists"
            if skipped_count > 0:
                message += f", {skipped_count} omitidas"
            
            return True, message
            
        except Exception as e:
            return False, f"Error al importar: {str(e)}"
    
    def get_rule_statistics(self, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Obtiene estadísticas generales para ayudar en la creación de reglas."""
        stats = {}
        
        for field_name in self._field_definitions.keys():
            field_stats = self.evaluator.get_field_statistics(tracks, field_name)
            if field_stats["count"] > 0:
                stats[field_name] = field_stats
        
        return stats
    
    def suggest_rule_templates(self, tracks: List[Dict[str, Any]]) -> List[str]:
        """Sugiere plantillas de reglas basadas en los datos disponibles."""
        stats = self.get_rule_statistics(tracks)
        return self.evaluator.create_rule_template(stats)


# Funciones de utilidad
def create_rule_engine() -> RuleEngine:
    """Función de conveniencia para crear un motor de reglas."""
    return RuleEngine()


def quick_filter(rule: str, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Función de conveniencia para filtrado rápido."""
    engine = RuleEngine()
    return engine.evaluator.filter_tracks(rule, tracks)


# Testing y ejemplos
if __name__ == "__main__":
    print("🚀 TESTING RULE ENGINE - NUEVA BIBLIOTECA")
    print("=" * 60)
    
    # Crear motor de reglas
    engine = RuleEngine()
    
    # Datos de ejemplo
    sample_tracks = [
        {
            "title": "Strobe", "artist": "deadmau5", "genre": "Progressive House",
            "bpm": 128, "key": "8A", "energy": 0.7, "year": 2009, "duration": 636,
            "rating": 5, "play_count": 42
        },
        {
            "title": "Levels", "artist": "Avicii", "genre": "House",
            "bpm": 126, "key": "7A", "energy": 0.9, "year": 2011, "duration": 202,
            "rating": 4, "play_count": 28
        },
        {
            "title": "Adagio for Strings", "artist": "Tiësto", "genre": "Trance",
            "bpm": 136, "key": "9A", "energy": 0.8, "year": 2004, "duration": 480,
            "rating": 5, "play_count": 15
        }
    ]
    
    # Test 1: Crear playlist inteligente
    print("\n📝 Test 1: Crear playlist inteligente")
    success, message, playlist = engine.create_smart_playlist(
        name="House Energético",
        rule_expression="genre = 'House' AND energy > 0.8",
        description="House music con alta energía",
        icon="🏠"
    )
    print(f"✅ {message}")
    
    if playlist:
        # Test 2: Generar tracks para la playlist
        print(f"\n🎵 Test 2: Generar tracks para '{playlist.name}'")
        success, message, filtered_tracks = engine.generate_playlist_tracks(playlist.id, sample_tracks)
        print(f"✅ {message}")
        
        for track in filtered_tracks:
            print(f"   🎵 {track['artist']} - {track['title']} (Energy: {track['energy']})")
    
    # Test 3: Crear desde plantilla
    print(f"\n🎨 Test 3: Crear regla desde plantilla")
    workout_rule = engine.create_rule_from_template("workout")
    print(f"✅ Regla workout: {workout_rule}")
    
    # Test 4: Análisis de estadísticas
    print(f"\n📊 Test 4: Estadísticas de campos")
    stats = engine.get_rule_statistics(sample_tracks)
    for field, field_stats in stats.items():
        if "avg" in field_stats:
            print(f"   📈 {field}: promedio {field_stats['avg']:.2f}")
        elif "most_common" in field_stats:
            print(f"   📈 {field}: más común {field_stats['most_common'][0]}")
    
    print(f"\n" + "=" * 60)
    print("✅ Testing del motor de reglas completado") 
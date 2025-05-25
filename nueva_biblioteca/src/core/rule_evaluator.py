"""
Evaluador de reglas para Nueva Biblioteca.
Aplica expresiones AST a conjuntos de datos musicales.
"""
from typing import List, Dict, Any, Optional, Callable, Iterator
from .expression_ast import ExpressionAST, ASTNode
from .rule_parser import RuleParser


class RuleEvaluator:
    """Evaluador de reglas para filtrar y buscar tracks musicales."""
    
    def __init__(self):
        self.parser = RuleParser()
        self._field_processors = {}
        self._setup_default_processors()
        
    def _setup_default_processors(self):
        """Configura procesadores por defecto para campos especiales."""
        # Procesador para normalizar géneros
        self._field_processors['genre'] = lambda x: str(x).strip().title() if x else ""
        
        # Procesador para normalizar artistas
        self._field_processors['artist'] = lambda x: str(x).strip() if x else ""
        
        # Procesador para BPM (asegurar que sea numérico)
        self._field_processors['bpm'] = lambda x: float(x) if x and str(x).replace('.', '').isdigit() else 0.0
        
        # Procesador para energía (normalizar a 0-1)
        self._field_processors['energy'] = lambda x: max(0.0, min(1.0, float(x))) if x and str(x).replace('.', '').isdigit() else 0.0
        
        # Procesador para año
        self._field_processors['year'] = lambda x: int(x) if x and str(x).isdigit() else 0
        
        # Procesador para duración (en segundos)
        self._field_processors['duration'] = lambda x: int(x) if x and str(x).isdigit() else 0
        
    def add_field_processor(self, field_name: str, processor: Callable[[Any], Any]):
        """Agrega un procesador personalizado para un campo."""
        self._field_processors[field_name] = processor
        
    def _process_track_data(self, track: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa los datos de un track aplicando los procesadores de campo."""
        processed = {}
        
        for field, value in track.items():
            if field in self._field_processors:
                try:
                    processed[field] = self._field_processors[field](value)
                except (ValueError, TypeError):
                    processed[field] = value  # Usar valor original si falla el procesamiento
            else:
                processed[field] = value
                
        return processed
        
    def evaluate_rule(self, rule_expression: str, track: Dict[str, Any]) -> bool:
        """Evalúa una regla contra un track individual."""
        try:
            ast = self.parser.parse(rule_expression)
            processed_track = self._process_track_data(track)
            return ast.evaluate(processed_track)
        except Exception:
            return False  # En caso de error, no incluir el track
            
    def filter_tracks(self, rule_expression: str, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtra una lista de tracks usando una regla."""
        if not rule_expression or not rule_expression.strip():
            return tracks  # Sin regla, retornar todos los tracks
            
        try:
            ast = self.parser.parse(rule_expression)
            filtered = []
            
            for track in tracks:
                processed_track = self._process_track_data(track)
                if ast.evaluate(processed_track):
                    filtered.append(track)
                    
            return filtered
            
        except Exception:
            return []  # En caso de error, retornar lista vacía
            
    def filter_tracks_generator(self, rule_expression: str, tracks: Iterator[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """Filtra tracks usando un generador para eficiencia de memoria."""
        if not rule_expression or not rule_expression.strip():
            yield from tracks
            return
            
        try:
            ast = self.parser.parse(rule_expression)
            
            for track in tracks:
                processed_track = self._process_track_data(track)
                if ast.evaluate(processed_track):
                    yield track
                    
        except Exception:
            return  # En caso de error, no generar nada
            
    def count_matches(self, rule_expression: str, tracks: List[Dict[str, Any]]) -> int:
        """Cuenta cuántos tracks coinciden con una regla sin crear la lista filtrada."""
        if not rule_expression or not rule_expression.strip():
            return len(tracks)
            
        try:
            ast = self.parser.parse(rule_expression)
            count = 0
            
            for track in tracks:
                processed_track = self._process_track_data(track)
                if ast.evaluate(processed_track):
                    count += 1
                    
            return count
            
        except Exception:
            return 0
            
    def get_field_statistics(self, tracks: List[Dict[str, Any]], field: str) -> Dict[str, Any]:
        """Obtiene estadísticas de un campo específico."""
        values = []
        
        for track in tracks:
            processed_track = self._process_track_data(track)
            if field in processed_track and processed_track[field] is not None:
                values.append(processed_track[field])
                
        if not values:
            return {"count": 0, "unique": 0}
            
        stats = {
            "count": len(values),
            "unique": len(set(values))
        }
        
        # Estadísticas numéricas
        if all(isinstance(v, (int, float)) for v in values):
            stats.update({
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "median": sorted(values)[len(values) // 2]
            })
            
        # Estadísticas de texto
        elif all(isinstance(v, str) for v in values):
            from collections import Counter
            counter = Counter(values)
            stats.update({
                "most_common": counter.most_common(5),
                "avg_length": sum(len(v) for v in values) / len(values)
            })
            
        return stats
        
    def analyze_rule_performance(self, rule_expression: str, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza el rendimiento y efectividad de una regla."""
        import time
        
        start_time = time.time()
        
        try:
            ast = self.parser.parse(rule_expression)
            fields_used = ast.get_fields_used()
            
            matches = 0
            total = len(tracks)
            
            for track in tracks:
                processed_track = self._process_track_data(track)
                if ast.evaluate(processed_track):
                    matches += 1
                    
            end_time = time.time()
            
            return {
                "rule": rule_expression,
                "fields_used": fields_used,
                "total_tracks": total,
                "matches": matches,
                "match_percentage": (matches / total * 100) if total > 0 else 0,
                "execution_time_ms": (end_time - start_time) * 1000,
                "tracks_per_second": total / (end_time - start_time) if (end_time - start_time) > 0 else 0,
                "valid": True
            }
            
        except Exception as e:
            return {
                "rule": rule_expression,
                "error": str(e),
                "valid": False,
                "execution_time_ms": (time.time() - start_time) * 1000
            }
            
    def suggest_optimizations(self, rule_expression: str) -> List[str]:
        """Sugiere optimizaciones para una regla."""
        suggestions = []
        
        try:
            ast = self.parser.parse(rule_expression)
            fields_used = ast.get_fields_used()
            
            # Sugerir índices para campos utilizados
            if len(fields_used) > 1:
                suggestions.append(f"Considerar crear índices para: {', '.join(fields_used)}")
                
            # Sugerir reordenamiento para eficiencia
            if "bpm" in fields_used and "genre" in fields_used:
                suggestions.append("Considerar evaluar 'bpm' antes que 'genre' para mejor performance")
                
            # Sugerir simplificación de expresiones complejas
            rule_complexity = rule_expression.count("AND") + rule_expression.count("OR") + rule_expression.count("NOT")
            if rule_complexity > 5:
                suggestions.append("Regla muy compleja, considerar dividir en múltiples reglas más simples")
                
            # Sugerir uso de BETWEEN en lugar de comparaciones múltiples
            if "> " in rule_expression and "< " in rule_expression:
                suggestions.append("Considerar usar BETWEEN en lugar de comparaciones múltiples")
                
        except Exception:
            suggestions.append("Regla inválida, revisar sintaxis")
            
        return suggestions
        
    def create_rule_template(self, field_stats: Dict[str, Dict[str, Any]]) -> List[str]:
        """Crea plantillas de reglas basadas en estadísticas de campos."""
        templates = []
        
        for field, stats in field_stats.items():
            if field == "genre" and "most_common" in stats:
                common_genres = [genre for genre, _ in stats["most_common"][:3]]
                templates.append(f"genre IN ({', '.join(repr(g) for g in common_genres)})")
                
            elif field == "bpm" and "min" in stats and "max" in stats:
                min_bpm = int(stats["min"])
                max_bpm = int(stats["max"])
                mid_bpm = (min_bpm + max_bpm) // 2
                templates.append(f"bpm BETWEEN {mid_bpm - 10} AND {mid_bpm + 10}")
                
            elif field == "energy" and "avg" in stats:
                avg_energy = stats["avg"]
                templates.append(f"energy > {avg_energy:.1f}")
                
            elif field == "year" and "max" in stats:
                recent_year = int(stats["max"]) - 5
                templates.append(f"year > {recent_year}")
                
        return templates
        
    def validate_rule_fields(self, rule_expression: str, available_fields: List[str]) -> Dict[str, Any]:
        """Valida que todos los campos de una regla estén disponibles."""
        try:
            ast = self.parser.parse(rule_expression)
            used_fields = ast.get_fields_used()
            
            missing_fields = [field for field in used_fields if field not in available_fields]
            
            return {
                "valid": len(missing_fields) == 0,
                "used_fields": used_fields,
                "missing_fields": missing_fields,
                "available_fields": available_fields
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "used_fields": [],
                "missing_fields": [],
                "available_fields": available_fields
            }


# Funciones de utilidad
def evaluate_rule_on_track(rule: str, track: Dict[str, Any]) -> bool:
    """Función de conveniencia para evaluar una regla en un track."""
    evaluator = RuleEvaluator()
    return evaluator.evaluate_rule(rule, track)


def filter_music_collection(rule: str, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Función de conveniencia para filtrar una colección musical."""
    evaluator = RuleEvaluator()
    return evaluator.filter_tracks(rule, tracks)


# Testing y ejemplos
if __name__ == "__main__":
    # Datos de ejemplo para testing
    sample_tracks = [
        {
            "title": "Strobe",
            "artist": "deadmau5",
            "album": "For Lack of a Better Name",
            "genre": "Progressive House",
            "bpm": 128,
            "key": "8A",
            "energy": 0.7,
            "year": 2009,
            "duration": 636
        },
        {
            "title": "Levels",
            "artist": "Avicii",
            "album": "True",
            "genre": "House",
            "bpm": 126,
            "key": "7A",
            "energy": 0.9,
            "year": 2011,
            "duration": 202
        },
        {
            "title": "Adagio for Strings",
            "artist": "Tiësto",
            "album": "In Search of Sunrise 3",
            "genre": "Trance",
            "bpm": 136,
            "key": "9A",
            "energy": 0.8,
            "year": 2004,
            "duration": 480
        },
        {
            "title": "One More Time",
            "artist": "Daft Punk",
            "album": "Discovery",
            "genre": "House",
            "bpm": 123,
            "key": "8B",
            "energy": 0.85,
            "year": 2000,
            "duration": 320
        }
    ]
    
    print("🧪 TESTING RULE EVALUATOR - NUEVA BIBLIOTECA")
    print("=" * 60)
    
    evaluator = RuleEvaluator()
    
    # Test de reglas básicas
    test_rules = [
        "genre = 'House'",
        "bpm > 125",
        "year BETWEEN 2000 AND 2010",
        "artist CONTAINS 'deadmau5'",
        "energy > 0.8 AND bpm < 130"
    ]
    
    for rule in test_rules:
        print(f"\n📝 Regla: {rule}")
        
        # Filtrar tracks
        matches = evaluator.filter_tracks(rule, sample_tracks)
        print(f"✅ Matches: {len(matches)}/{len(sample_tracks)}")
        
        for track in matches:
            print(f"   🎵 {track['artist']} - {track['title']} ({track['genre']}, {track['bpm']} BPM)")
            
        # Análisis de performance
        analysis = evaluator.analyze_rule_performance(rule, sample_tracks)
        print(f"📊 Performance: {analysis['execution_time_ms']:.2f}ms, {analysis['match_percentage']:.1f}% matches")
    
    print(f"\n" + "=" * 60)
    print("✅ Testing del evaluador completado") 
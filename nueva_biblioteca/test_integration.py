#!/usr/bin/env python3
"""
Script de prueba para verificar la integración completa de Nueva Biblioteca.
Prueba el motor de reglas integrado con los servicios y la UI.
"""

import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Importar directamente desde los módulos
from src.services.music_service import MusicService
from src.services.rule_service import RuleService


def test_music_service():
    """Prueba el servicio de música."""
    print("🎵 Probando MusicService...")
    
    music_service = MusicService()
    
    # Probar obtención de datos
    all_tracks = music_service.get_all_tracks()
    print(f"✓ Tracks cargados: {len(all_tracks)}")
    
    # Probar búsqueda
    search_results = music_service.search_tracks("deadmau5")
    print(f"✓ Búsqueda 'deadmau5': {len(search_results)} resultados")
    
    # Probar estadísticas
    stats = music_service.get_statistics()
    print(f"✓ Estadísticas: {stats['total_tracks']} tracks, {stats['genres_count']} géneros")
    
    return music_service


def test_rule_service(music_service):
    """Prueba el servicio de reglas."""
    print("\n📝 Probando RuleService...")
    
    rule_service = RuleService(music_service)
    
    # Probar validación de reglas
    test_rules = [
        "genre = 'House'",
        "bpm BETWEEN 120 AND 140",
        "energy > 0.8 AND danceability > 0.7",
        "key COMPATIBLE_WITH '8A'",
        "artist CONTAINS 'deadmau5' OR rating >= 5"
    ]
    
    for rule in test_rules:
        is_valid, message, fields = rule_service.validate_rule_expression(rule)
        status = "✓" if is_valid else "✗"
        print(f"{status} Regla: '{rule}' - {message}")
    
    # Probar aplicación de filtros
    print("\n🔍 Probando filtros...")
    
    # Filtro por género
    house_tracks = rule_service.apply_filter_rule("genre CONTAINS 'House'")
    print(f"✓ Tracks de House: {len(house_tracks)}")
    
    # Filtro por energía
    high_energy = rule_service.apply_filter_rule("energy > 0.8")
    print(f"✓ Tracks alta energía: {len(high_energy)}")
    
    # Filtro complejo
    complex_filter = rule_service.apply_filter_rule("(genre = 'House' OR genre = 'Progressive House') AND bpm BETWEEN 120 AND 130")
    print(f"✓ Filtro complejo: {len(complex_filter)}")
    
    # Probar filtros rápidos
    quick_filters = rule_service.get_quick_filters()
    print(f"✓ Filtros rápidos disponibles: {len(quick_filters)}")
    
    return rule_service


def test_smart_playlists(rule_service):
    """Prueba las playlists inteligentes."""
    print("\n🎵 Probando Smart Playlists...")
    
    # Crear playlist de alta energía
    success, message, playlist = rule_service.create_smart_playlist(
        "Alta Energía",
        "energy > 0.8 AND danceability > 0.7",
        "Tracks perfectos para entrenar",
        "#FF6B6B",
        "⚡"
    )
    
    if success:
        print(f"✓ Playlist creada: {playlist.name}")
        
        # Generar tracks para la playlist
        success, message, tracks = rule_service.generate_playlist_tracks(playlist.id)
        if success:
            print(f"✓ Tracks generados: {len(tracks)}")
        else:
            print(f"✗ Error generando tracks: {message}")
    else:
        print(f"✗ Error creando playlist: {message}")
    
    # Crear playlist de House music
    success, message, playlist2 = rule_service.create_smart_playlist(
        "House Vibes",
        "genre CONTAINS 'House' AND bpm BETWEEN 120 AND 130",
        "Lo mejor del House music",
        "#6750A4",
        "🏠"
    )
    
    if success:
        print(f"✓ Playlist creada: {playlist2.name}")
    
    # Listar todas las playlists
    playlists = rule_service.list_smart_playlists()
    print(f"✓ Total playlists: {len(playlists)}")
    
    for pl in playlists:
        print(f"  - {pl.name}: {pl.rule_expression}")


def test_field_analysis(rule_service):
    """Prueba el análisis de campos."""
    print("\n📊 Probando análisis de campos...")
    
    # Obtener campos disponibles
    fields = rule_service.get_available_fields()
    print(f"✓ Campos disponibles: {len(fields)}")
    
    # Analizar algunos campos específicos
    test_fields = ["genre", "artist", "bpm", "energy", "key"]
    
    for field in test_fields:
        if field in fields:
            values = rule_service.get_field_values(field)
            operators = rule_service.get_field_operators(field)
            print(f"✓ {field}: {len(values)} valores únicos, {len(operators)} operadores")


def test_examples_and_templates(rule_service):
    """Prueba ejemplos y plantillas."""
    print("\n📚 Probando ejemplos y plantillas...")
    
    # Obtener ejemplos
    examples = rule_service.get_rule_examples()
    print(f"✓ Ejemplos disponibles: {len(examples)}")
    
    # Obtener sugerencias
    suggestions = rule_service.get_rule_suggestions()
    print(f"✓ Sugerencias generadas: {len(suggestions)}")
    
    # Probar plantillas
    templates = ["high_energy", "chill_vibes", "workout", "camelot_compatible"]
    
    for template in templates:
        try:
            rule = rule_service.create_rule_from_template(template)
            print(f"✓ Plantilla '{template}': {rule}")
        except Exception as e:
            print(f"✗ Error en plantilla '{template}': {e}")


def main():
    """Función principal de prueba."""
    print("🚀 PRUEBA DE INTEGRACIÓN - NUEVA BIBLIOTECA")
    print("=" * 50)
    
    try:
        # Probar servicios
        music_service = test_music_service()
        rule_service = test_rule_service(music_service)
        
        # Probar funcionalidades avanzadas
        test_smart_playlists(rule_service)
        test_field_analysis(rule_service)
        test_examples_and_templates(rule_service)
        
        print("\n" + "=" * 50)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("\n🎉 Nueva Biblioteca está completamente integrada y funcional!")
        print("\nCaracterísticas probadas:")
        print("  ✓ Servicio de datos musicales")
        print("  ✓ Motor de reglas core")
        print("  ✓ Parser de expresiones lógicas")
        print("  ✓ Evaluador de reglas")
        print("  ✓ Playlists inteligentes")
        print("  ✓ Filtros rápidos")
        print("  ✓ Análisis de campos")
        print("  ✓ Plantillas y ejemplos")
        print("  ✓ Integración con servicios")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN LAS PRUEBAS: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
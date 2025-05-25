#!/usr/bin/env python3
"""
🎵 DEMOSTRACIÓN PRÁCTICA - NUEVA BIBLIOTECA
==========================================
Script para mostrar las capacidades de la aplicación
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services.music_service import MusicService
from src.services.rule_service import RuleService

def main():
    print('🎵 DEMOSTRACIÓN PRÁCTICA - NUEVA BIBLIOTECA')
    print('=' * 50)

    # Inicializar servicios
    music_service = MusicService()
    rule_service = RuleService(music_service)

    print('📊 BIBLIOTECA MUSICAL:')
    stats = music_service.get_statistics()
    print(f'  • Total tracks: {stats["total_tracks"]}')
    print(f'  • Géneros: {stats["genres_count"]}')
    print(f'  • Artistas: {stats["artists_count"]}')
    print(f'  • Duración total: {stats["total_duration_formatted"]}')
    print(f'  • Rating promedio: {stats["average_rating"]}')

    print('\n🎯 EJEMPLOS DE REGLAS INTELIGENTES:')
    ejemplos = [
        ('🏠 House Music', 'genre CONTAINS "House"'),
        ('⚡ Alta Energía', 'energy > 0.8'),
        ('🎹 Compatible 8A', 'key COMPATIBLE_WITH "8A"'),
        ('💪 Workout', 'energy > 0.8 AND bpm BETWEEN 120 AND 140'),
        ('😌 Chill Vibes', 'energy < 0.5 AND valence > 0.4'),
        ('🎖️ Clásicos', 'year < 2010 AND rating >= 4'),
        ('🔥 Populares', 'play_count > 30'),
        ('🆕 Recientes', 'year > 2015')
    ]

    for nombre, regla in ejemplos:
        tracks = rule_service.apply_filter_rule(regla)
        print(f'  {nombre}: {len(tracks)} tracks')
        if tracks:
            ejemplo = tracks[0]
            print(f'    └─ Ejemplo: {ejemplo["artist"]} - {ejemplo["title"]}')

    print('\n🎨 GÉNEROS DISPONIBLES:')
    generos = music_service.get_genres()
    print(f'  • {", ".join(generos)}')

    print('\n🎹 CLAVES CAMELOT DISPONIBLES:')
    claves = music_service.get_keys()
    print(f'  • {", ".join(claves)}')

    print('\n🚀 PLAYLISTS INTELIGENTES CREADAS:')
    playlists = rule_service.list_smart_playlists()
    for playlist in playlists:
        success, message, tracks = rule_service.generate_playlist_tracks(playlist.id)
        if success:
            print(f'  • {playlist.name}: {len(tracks)} tracks')
            print(f'    └─ Regla: {playlist.rule_expression}')

    print('\n' + '=' * 50)
    print('🎵 ¡Nueva Biblioteca está completamente funcional!')
    print('✨ Interfaz Material 3 Expressive ejecutándose')
    print('🚀 Lista para gestionar tu música de forma inteligente')

if __name__ == "__main__":
    main() 
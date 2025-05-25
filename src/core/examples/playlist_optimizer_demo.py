#!/usr/bin/env python3
"""
Demostración del sistema de optimización de playlists.
Muestra diferentes estrategias de reorganización y análisis.
"""

import logging
from typing import Dict, Any, List
from ..playlist_optimizer import PlaylistOptimizer, OptimizationStrategy

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_demo_tracks() -> List[Dict[str, Any]]:
    """
    Crea una lista de tracks de ejemplo con diferentes características.
    
    Returns:
        Lista de tracks para demostración
    """
    return [
        {
            'title': 'Track 1',
            'key': 'G maj',      # 8A
            'bpm': 126,
            'energy': 0.7,
            'danceability': 0.8
        },
        {
            'title': 'Track 2',
            'key': 'D min',      # 7B
            'bpm': 124,
            'energy': 0.6,
            'danceability': 0.7
        },
        {
            'title': 'Track 3',
            'key': 'A maj',      # 11A
            'bpm': 128,
            'energy': 0.9,
            'danceability': 0.8
        },
        {
            'title': 'Track 4',
            'key': 'F min',      # 4B
            'bpm': 122,
            'energy': 0.5,
            'danceability': 0.6
        },
        {
            'title': 'Track 5',
            'key': 'C maj',      # 8B
            'bpm': 130,
            'energy': 0.8,
            'danceability': 0.9
        }
    ]

def print_playlist(tracks: List[Dict[str, Any]], title: str = None):
    """
    Muestra información de una playlist.
    
    Args:
        tracks: Lista de tracks a mostrar
        title: Título opcional para la playlist
    """
    if title:
        print(f"\n{title}")
        print("=" * len(title))
        
    for i, track in enumerate(tracks, 1):
        print(
            f"\n{i}. {track['title']}\n"
            f"   Key: {track['key']:<10} BPM: {track['bpm']}\n"
            f"   Energy: {track['energy']:.2f}  Dance: {track['danceability']:.2f}"
        )

def print_analysis(analysis: Dict[str, Any]):
    """
    Muestra análisis de transiciones.
    
    Args:
        analysis: Dict con información de análisis
    """
    print("\nAnálisis de Transiciones")
    print("=====================")
    print(f"Score promedio: {analysis['average_score']:.2f}\n")
    
    for transition in analysis['transitions']:
        print(
            f"{transition['from']} -> {transition['to']}\n"
            f"Score: {transition['score']:.2f}"
        )
        
    if analysis['problem_areas']:
        print("\nÁreas Problemáticas")
        print("==================")
        for problem in analysis['problem_areas']:
            print(
                f"\nPosición {problem['position']}:\n"
                f"Score: {problem['score']:.2f}\n"
                f"Sugerencia: {problem['suggestion']}"
            )

def demo_key_progression():
    """Demuestra optimización por progresión de claves."""
    logger.info("Demostrando optimización por progresión de claves...")
    
    # Crear datos de prueba
    tracks = create_demo_tracks()
    print_playlist(tracks, "Playlist Original")
    
    # Optimizar
    optimizer = PlaylistOptimizer()
    result = optimizer.optimize(
        tracks,
        strategy=OptimizationStrategy.KEY_PROGRESSION
    )
    
    if result.success:
        print_playlist(result.tracks, "\nPlaylist Optimizada (Claves)")
        print(f"\nScore final: {result.score:.2f}")
        
        if result.warnings:
            print("\nAdvertencias:")
            for warning in result.warnings:
                print(f"- {warning}")
    else:
        print("\nError optimizando playlist")
        
def demo_energy_flow():
    """Demuestra optimización por flujo de energía."""
    logger.info("Demostrando optimización por energía...")
    
    # Crear datos de prueba
    tracks = create_demo_tracks()
    
    # Optimizar
    optimizer = PlaylistOptimizer()
    result = optimizer.optimize(
        tracks,
        strategy=OptimizationStrategy.ENERGY_FLOW
    )
    
    if result.success:
        print_playlist(result.tracks, "\nPlaylist Optimizada (Energía)")
        print(f"\nScore final: {result.score:.2f}")
        
        # Mostrar curva de energía
        print("\nCurva de Energía")
        print("===============")
        for track in result.tracks:
            print(
                f"[{'#' * int(track['energy'] * 20):<20}] "
                f"{track['energy']:.2f} - {track['title']}"
            )
    else:
        print("\nError optimizando playlist")
        
def demo_hybrid():
    """Demuestra optimización híbrida (claves + energía)."""
    logger.info("Demostrando optimización híbrida...")
    
    # Crear datos de prueba
    tracks = create_demo_tracks()
    
    # Optimizar
    optimizer = PlaylistOptimizer()
    result = optimizer.optimize(
        tracks,
        strategy=OptimizationStrategy.HYBRID
    )
    
    if result.success:
        print_playlist(result.tracks, "\nPlaylist Optimizada (Híbrida)")
        print(f"\nScore final: {result.score:.2f}")
        
        # Analizar transiciones
        analysis = optimizer.analyze_transitions(
            result.tracks,
            strategy=OptimizationStrategy.HYBRID
        )
        print_analysis(analysis)
    else:
        print("\nError optimizando playlist")
        
def main():
    """Punto de entrada principal de la demo."""
    try:
        # Demostrar diferentes estrategias
        demo_key_progression()
        demo_energy_flow()
        demo_hybrid()
        
    except Exception as e:
        logger.error(f"Error en la demo: {str(e)}")
        return 1
        
    return 0

if __name__ == '__main__':
    exit(main())

import unittest
from typing import List, Dict, Any
from src.core.playlist_optimizer import (
    PlaylistOptimizer, OptimizationStrategy, OptimizationResult,
    KeyProgressionStrategy, EnergyFlowStrategy, HybridStrategy
)

class TestPlaylistOptimizer(unittest.TestCase):
    """
    Pruebas para el sistema de optimización de playlists.
    """
    
    def setUp(self):
        """Configura el ambiente de prueba."""
        self.optimizer = PlaylistOptimizer()
        
        # Playlist de prueba
        self.test_tracks = [
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
            }
        ]
        
    def test_empty_playlist(self):
        """Prueba optimización de playlist vacía."""
        result = self.optimizer.optimize([])
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.tracks), 0)
        self.assertEqual(result.score, 1.0)
        self.assertEqual(len(result.warnings), 0)
        
    def test_key_progression_strategy(self):
        """Prueba optimización por progresión de claves."""
        result = self.optimizer.optimize(
            self.test_tracks,
            strategy=OptimizationStrategy.KEY_PROGRESSION
        )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.tracks), len(self.test_tracks))
        
        # Verificar que las claves son compatibles
        for i in range(len(result.tracks) - 1):
            track1 = result.tracks[i]
            track2 = result.tracks[i + 1]
            
            # Usar estrategia directamente para verificar compatibilidad
            strategy = KeyProgressionStrategy()
            score = strategy.get_transition_score(track1, track2)
            
            self.assertGreater(score, 0.0)
            
    def test_energy_flow_strategy(self):
        """Prueba optimización por flujo de energía."""
        result = self.optimizer.optimize(
            self.test_tracks,
            strategy=OptimizationStrategy.ENERGY_FLOW
        )
        
        self.assertTrue(result.success)
        
        # Verificar que no hay cambios bruscos de energía
        for i in range(len(result.tracks) - 1):
            track1 = result.tracks[i]
            track2 = result.tracks[i + 1]
            
            energy_diff = abs(track1['energy'] - track2['energy'])
            self.assertLess(energy_diff, 0.3)  # Umbral razonable
            
    def test_hybrid_strategy(self):
        """Prueba optimización híbrida."""
        result = self.optimizer.optimize(
            self.test_tracks,
            strategy=OptimizationStrategy.HYBRID
        )
        
        self.assertTrue(result.success)
        self.assertGreater(result.score, 0.0)
        
        # Verificar que hay un balance entre clave y energía
        key_strategy = KeyProgressionStrategy()
        energy_strategy = EnergyFlowStrategy()
        
        for i in range(len(result.tracks) - 1):
            track1 = result.tracks[i]
            track2 = result.tracks[i + 1]
            
            key_score = key_strategy.get_transition_score(track1, track2)
            energy_score = energy_strategy.get_transition_score(track1, track2)
            
            # Al menos uno debe ser bueno
            self.assertTrue(key_score > 0.5 or energy_score > 0.5)
            
    def test_custom_strategy(self):
        """Prueba uso de estrategia personalizada."""
        # Crear estrategia que invierte el orden
        class ReverseStrategy(KeyProgressionStrategy):
            def reorder(self, tracks: List[Dict[str, Any]]) -> OptimizationResult:
                return OptimizationResult(
                    success=True,
                    tracks=list(reversed(tracks)),
                    stats={},
                    score=1.0,
                    warnings=[]
                )
                
        # Probar estrategia
        result = self.optimizer.optimize(
            self.test_tracks,
            strategy=OptimizationStrategy.CUSTOM,
            custom_strategy=ReverseStrategy()
        )
        
        self.assertTrue(result.success)
        self.assertEqual(
            [t['title'] for t in result.tracks],
            [t['title'] for t in reversed(self.test_tracks)]
        )
        
    def test_transition_analysis(self):
        """Prueba análisis de transiciones."""
        analysis = self.optimizer.analyze_transitions(
            self.test_tracks,
            strategy=OptimizationStrategy.HYBRID
        )
        
        # Verificar estructura del análisis
        self.assertIn('transitions', analysis)
        self.assertIn('average_score', analysis)
        self.assertIn('problem_areas', analysis)
        
        # Verificar transiciones
        self.assertEqual(
            len(analysis['transitions']),
            len(self.test_tracks) - 1
        )
        
        for transition in analysis['transitions']:
            self.assertIn('from', transition)
            self.assertIn('to', transition)
            self.assertIn('score', transition)
            self.assertGreaterEqual(transition['score'], 0.0)
            self.assertLessEqual(transition['score'], 1.0)
            
    def test_invalid_tracks(self):
        """Prueba optimización con tracks inválidos."""
        # Track sin clave
        invalid_tracks = [
            {'title': 'Track 1', 'energy': 0.5},
            {'title': 'Track 2', 'key': 'C maj'}
        ]
        
        result = self.optimizer.optimize(
            invalid_tracks,
            strategy=OptimizationStrategy.KEY_PROGRESSION
        )
        
        self.assertTrue(result.success)  # No debe fallar
        self.assertTrue(len(result.warnings) > 0)  # Debe advertir
        
    def test_strategy_registration(self):
        """Prueba registro de estrategias personalizadas."""
        # Crear y registrar estrategia
        class TestStrategy(KeyProgressionStrategy):
            pass
            
        self.optimizer.add_custom_strategy('test', TestStrategy())
        
        # Verificar registro
        strategies = self.optimizer.get_available_strategies()
        self.assertIn('test', strategies)
        
        # Verificar error con estrategia inválida
        with self.assertRaises(ValueError):
            self.optimizer.add_custom_strategy('invalid', object())

if __name__ == '__main__':
    unittest.main()

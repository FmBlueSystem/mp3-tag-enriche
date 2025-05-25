"""
Sistema de optimización y reorganización de playlists.
Implementa diferentes estrategias para ordenar tracks de forma óptima.
"""

from typing import List, Dict, Any, Optional, Type
from abc import ABC, abstractmethod
import logging
from dataclasses import dataclass
from enum import Enum, auto

from .camelot import CamelotWheel, CompatibilityMode

class OptimizationStrategy(Enum):
    """Estrategias disponibles de optimización."""
    KEY_PROGRESSION = auto()  # Progresión de claves musicales
    ENERGY_FLOW = auto()      # Flujo de energía
    HYBRID = auto()          # Combinación de clave y energía
    CUSTOM = auto()          # Estrategia personalizada

@dataclass
class OptimizationResult:
    """Resultado de una optimización."""
    success: bool
    tracks: List[Dict[str, Any]]
    stats: Dict[str, Any]
    score: float
    warnings: List[str]

class ReorderStrategy(ABC):
    """Clase base para estrategias de reordenamiento."""
    
    @abstractmethod
    def reorder(self, tracks: List[Dict[str, Any]]) -> OptimizationResult:
        """
        Reordena una lista de tracks según la estrategia.
        
        Args:
            tracks: Lista de tracks a reordenar
            
        Returns:
            OptimizationResult con el resultado
        """
        pass
        
    @abstractmethod
    def get_transition_score(self, track1: Dict[str, Any], track2: Dict[str, Any]) -> float:
        """
        Calcula un puntaje para la transición entre dos tracks.
        
        Args:
            track1: Primer track
            track2: Segundo track
            
        Returns:
            float: Puntaje entre 0 y 1 (mayor es mejor)
        """
        pass

class KeyProgressionStrategy(ReorderStrategy):
    """
    Estrategia que optimiza la progresión de claves musicales.
    Usa la rueda Camelot para crear transiciones armónicas suaves.
    """
    
    def __init__(self):
        self.wheel = CamelotWheel()
        self._logger = logging.getLogger(__name__)
        
    def reorder(self, tracks: List[Dict[str, Any]]) -> OptimizationResult:
        try:
            if not tracks:
                return OptimizationResult(
                    success=True,
                    tracks=[],
                    stats={},
                    score=1.0,
                    warnings=[]
                )
                
            # Obtener claves musicales
            track_keys = []
            warnings = []
            
            for track in tracks:
                key = track.get('key')
                if not key:
                    warnings.append(
                        f"Track sin clave: {track.get('title', 'Unknown')}"
                    )
                    track_keys.append(None)
                else:
                    track_keys.append(key)
                    
            # Crear matriz de compatibilidad
            size = len(tracks)
            compatibility = [[0.0] * size for _ in range(size)]
            
            for i in range(size):
                for j in range(size):
                    if i != j:
                        compatibility[i][j] = self.get_transition_score(
                            tracks[i], tracks[j]
                        )
                        
            # Encontrar mejor orden usando el algoritmo del viajante
            ordered_indices = self._solve_tsp(compatibility)
            
            # Reordenar tracks
            result = [tracks[i] for i in ordered_indices]
            
            # Calcular estadísticas
            stats = self._calculate_stats(result, compatibility, ordered_indices)
            
            return OptimizationResult(
                success=True,
                tracks=result,
                stats=stats,
                score=stats['average_transition_score'],
                warnings=warnings
            )
            
        except Exception as e:
            self._logger.error(f"Error optimizando playlist: {str(e)}")
            return OptimizationResult(
                success=False,
                tracks=tracks,
                stats={},
                score=0.0,
                warnings=[str(e)]
            )
            
    def get_transition_score(self, track1: Dict[str, Any], track2: Dict[str, Any]) -> float:
        """
        Calcula el puntaje de transición entre dos tracks basado en sus claves.
        
        Args:
            track1: Primer track
            track2: Segundo track
            
        Returns:
            float: Puntaje entre 0 y 1
        """
        key1 = track1.get('key')
        key2 = track2.get('key')
        
        if not key1 or not key2:
            return 0.0
            
        return self._get_key_compatibility(key1, key2)
        
    def _get_key_compatibility(self, key1: Optional[str], key2: Optional[str]) -> float:
        """
        Calcula compatibilidad entre dos claves musicales.
        
        Args:
            key1: Primera clave
            key2: Segunda clave
            
        Returns:
            float: Puntaje entre 0 y 1
        """
        if not key1 or not key2:
            return 0.0
            
        # Puntajes por tipo de compatibilidad
        scores = {
            CompatibilityMode.PERFECT: 1.0,    # Misma clave
            CompatibilityMode.ENERGY_UP: 0.8,  # +1 en la rueda
            CompatibilityMode.ENERGY_DOWN: 0.8,# -1 en la rueda
            CompatibilityMode.HARMONIC: 0.6    # Clave relativa
        }
        
        # Verificar cada tipo de compatibilidad
        max_score = 0.0
        
        for mode, score in scores.items():
            compatible = self.wheel.get_compatible_keys(key1, mode)
            if key2 in compatible:
                max_score = max(max_score, score)
                
        return max_score
        
    def _solve_tsp(self, compatibility: List[List[float]]) -> List[int]:
        """
        Resuelve el problema del viajante para encontrar el mejor orden.
        Usa una implementación simple y aproximada para playlists pequeñas.
        
        Args:
            compatibility: Matriz de compatibilidad entre tracks
            
        Returns:
            Lista de índices en el orden óptimo
        """
        size = len(compatibility)
        if size <= 1:
            return list(range(size))
            
        # Algoritmo greedy con múltiples puntos de inicio
        best_path = None
        best_score = -1
        
        for start in range(size):
            # Inicializar con un nodo
            current_path = [start]
            used = {start}
            current_score = 0
            
            # Agregar nodos greedily
            while len(current_path) < size:
                last = current_path[-1]
                best_next = None
                best_next_score = -1
                
                # Encontrar el mejor siguiente nodo
                for next_node in range(size):
                    if next_node not in used:
                        score = compatibility[last][next_node]
                        if score > best_next_score:
                            best_next = next_node
                            best_next_score = score
                            
                current_path.append(best_next)
                used.add(best_next)
                current_score += best_next_score
                
            # Actualizar mejor solución
            if current_score > best_score:
                best_path = current_path
                best_score = current_score
                
        return best_path
        
    def _calculate_stats(
        self,
        tracks: List[Dict[str, Any]],
        compatibility: List[List[float]],
        order: List[int]
    ) -> Dict[str, Any]:
        """
        Calcula estadísticas de la optimización.
        
        Args:
            tracks: Lista de tracks ordenada
            compatibility: Matriz de compatibilidad
            order: Orden final de los tracks
            
        Returns:
            Dict con estadísticas
        """
        size = len(tracks)
        if size <= 1:
            return {
                'transitions': [],
                'average_transition_score': 1.0,
                'worst_transition_score': 1.0,
                'best_transition_score': 1.0
            }
            
        # Calcular puntajes de transiciones
        transitions = []
        scores = []
        
        for i in range(size - 1):
            current_idx = order[i]
            next_idx = order[i + 1]
            score = compatibility[current_idx][next_idx]
            
            transitions.append({
                'from': tracks[current_idx].get('title', 'Unknown'),
                'to': tracks[next_idx].get('title', 'Unknown'),
                'score': score
            })
            
            scores.append(score)
            
        return {
            'transitions': transitions,
            'average_transition_score': sum(scores) / len(scores),
            'worst_transition_score': min(scores),
            'best_transition_score': max(scores)
        }

class EnergyFlowStrategy(ReorderStrategy):
    """
    Estrategia que optimiza el flujo de energía.
    Considera BPM, energy y danceability para crear una curva dinámica.
    """
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        
        # Pesos para diferentes atributos
        self.weights = {
            'bpm': 0.4,
            'energy': 0.3,
            'danceability': 0.3
        }
        
    def reorder(self, tracks: List[Dict[str, Any]]) -> OptimizationResult:
        try:
            if not tracks:
                return OptimizationResult(
                    success=True,
                    tracks=[],
                    stats={},
                    score=1.0,
                    warnings=[]
                )
                
            # Calcular matriz de compatibilidad
            size = len(tracks)
            compatibility = [[0.0] * size for _ in range(size)]
            
            for i in range(size):
                for j in range(size):
                    if i != j:
                        compatibility[i][j] = self.get_transition_score(
                            tracks[i], tracks[j]
                        )
                        
            # Encontrar mejor orden para curva energética
            ordered_indices = self._find_best_energy_curve(tracks, compatibility)
            
            # Reordenar tracks
            result = [tracks[i] for i in ordered_indices]
            
            # Calcular estadísticas
            score = 0.0
            transitions = []
            
            for i in range(len(result) - 1):
                trans_score = self.get_transition_score(
                    result[i], result[i + 1]
                )
                score += trans_score
                
                transitions.append({
                    'from': result[i].get('title', 'Unknown'),
                    'to': result[i + 1].get('title', 'Unknown'),
                    'score': trans_score,
                    'energy_diff': abs(
                        result[i].get('energy', 0) -
                        result[i + 1].get('energy', 0)
                    )
                })
                
            avg_score = score / (len(result) - 1) if len(result) > 1 else 1.0
            
            return OptimizationResult(
                success=True,
                tracks=result,
                stats={
                    'transitions': transitions,
                    'average_score': avg_score,
                    'energy_curve': [
                        {
                            'position': i,
                            'energy': t.get('energy', 0),
                            'bpm': t.get('bpm', 0),
                            'dance': t.get('danceability', 0)
                        }
                        for i, t in enumerate(result)
                    ]
                },
                score=avg_score,
                warnings=[]
            )
            
        except Exception as e:
            self._logger.error(f"Error optimizando por energía: {str(e)}")
            return OptimizationResult(
                success=False,
                tracks=tracks,
                stats={},
                score=0.0,
                warnings=[str(e)]
            )
            
    def get_transition_score(self, track1: Dict[str, Any], track2: Dict[str, Any]) -> float:
        """
        Calcula el puntaje de transición entre dos tracks basado en energía.
        
        Args:
            track1: Primer track
            track2: Segundo track
            
        Returns:
            float: Puntaje entre 0 y 1
        """
        # Recopilar atributos
        attrs = {}
        for attr, weight in self.weights.items():
            val1 = track1.get(attr)
            val2 = track2.get(attr)
            
            # Si falta algún valor, asignar peso 0
            if val1 is None or val2 is None:
                attrs[attr] = 0.0
                continue
                
            # Normalizar BPM a rango 0-1
            if attr == 'bpm':
                val1 = val1 / 200.0  # Asumiendo max BPM = 200
                val2 = val2 / 200.0
                
            # Calcular diferencia normalizada
            diff = abs(val2 - val1)
            
            # Convertir diferencia a score (menor diferencia = mayor score)
            attrs[attr] = 1.0 - min(diff, 1.0)
            
        # Calcular score ponderado
        score = sum(
            score * weight
            for (attr, score), weight in zip(attrs.items(), self.weights.values())
        )
        
        return score
        
    def _find_best_energy_curve(
        self,
        tracks: List[Dict[str, Any]],
        compatibility: List[List[float]]
    ) -> List[int]:
        """
        Encuentra el mejor orden para crear una curva de energía dinámica.
        Usa un algoritmo que intenta maximizar el flujo mientras mantiene
        transiciones suaves.
        
        Args:
            tracks: Lista de tracks
            compatibility: Matriz de compatibilidad
            
        Returns:
            Lista de índices en el orden óptimo
        """
        size = len(tracks)
        if size <= 1:
            return list(range(size))
            
        # Calcular energía promedio de cada track
        energies = []
        for track in tracks:
            energy = 0.0
            count = 0
            
            for attr, weight in self.weights.items():
                val = track.get(attr)
                if val is not None:
                    # Normalizar BPM
                    if attr == 'bpm':
                        val = val / 200.0
                    energy += val * weight
                    count += weight
                    
            energies.append(energy / count if count > 0 else 0)
            
        # Ordenar por energía pero preservar índices
        energy_indices = list(enumerate(energies))
        energy_indices.sort(key=lambda x: x[1])
        
        # Crear curva dinámica
        result = []
        used = set()
        
        # Comenzar con energía media-baja
        start_idx = len(energy_indices) // 3
        current = energy_indices[start_idx][0]
        result.append(current)
        used.add(current)
        
        # Alternar entre subidas y bajadas de energía
        rising = True  # Comenzar subiendo
        
        while len(result) < size:
            best_next = None
            best_score = -1
            
            # Buscar mejor siguiente track
            for i in range(size):
                if i in used:
                    continue
                    
                # Calcular score combinado de energía y compatibilidad
                energy_score = energies[i]
                if not rising:
                    energy_score = 1.0 - energy_score
                    
                compat_score = compatibility[current][i]
                
                # Ponderar scores
                combined_score = (energy_score * 0.7) + (compat_score * 0.3)
                
                if combined_score > best_score:
                    best_next = i
                    best_score = combined_score
                    
            result.append(best_next)
            used.add(best_next)
            current = best_next
            
            # Cambiar dirección en puntos estratégicos
            if len(result) == size // 2:  # Punto medio
                rising = False
                
        return result

class HybridStrategy(ReorderStrategy):
    """
    Estrategia que combina progresión de claves con flujo de energía.
    Balancea ambos aspectos para crear transiciones óptimas.
    """
    
    def __init__(self):
        self.key_strategy = KeyProgressionStrategy()
        self.energy_strategy = EnergyFlowStrategy()
        
        # Pesos para cada estrategia
        self.weights = {
            'key': 0.6,
            'energy': 0.4
        }
        
        self._logger = logging.getLogger(__name__)
        
    def reorder(self, tracks: List[Dict[str, Any]]) -> OptimizationResult:
        try:
            # Obtener resultados de ambas estrategias
            key_result = self.key_strategy.reorder(tracks)
            energy_result = self.energy_strategy.reorder(tracks)
            
            # Combinar scores y estadísticas
            warnings = key_result.warnings + energy_result.warnings
            
            # Crear matriz de compatibilidad híbrida
            size = len(tracks)
            compatibility = [[0.0] * size for _ in range(size)]
            
            for i in range(size):
                for j in range(size):
                    if i != j:
                        compatibility[i][j] = self.get_transition_score(
                            tracks[i], tracks[j]
                        )
                        
            # Usar orden basado en scores combinados
            ordered_indices = self._find_optimal_order(tracks, compatibility)
            result = [tracks[i] for i in ordered_indices]
            
            # Calcular estadísticas combinadas
            transitions = []
            score = 0.0
            
            for i in range(len(result) - 1):
                trans_score = self.get_transition_score(
                    result[i], result[i + 1]
                )
                score += trans_score
                
                key_score = self.key_strategy.get_transition_score(
                    result[i], result[i + 1]
                )
                energy_score = self.energy_strategy.get_transition_score(
                    result[i], result[i + 1]
                )
                
                transitions.append({
                    'from': result[i].get('title', 'Unknown'),
                    'to': result[i + 1].get('title', 'Unknown'),
                    'score': trans_score,
                    'key_score': key_score,
                    'energy_score': energy_score
                })
                
            avg_score = score / (len(result) - 1) if len(result) > 1 else 1.0
            
            return OptimizationResult(
                success=True,
                tracks=result,
                stats={
                    'transitions': transitions,
                    'average_score': avg_score,
                    'key_score': key_result.score,
                    'energy_score': energy_result.score,
                    'key_stats': key_result.stats,
                    'energy_stats': energy_result.stats
                },
                score=avg_score,
                warnings=warnings
            )
            
        except Exception as e:
            self._logger.error(f"Error optimizando con estrategia híbrida: {str(e)}")
            return OptimizationResult(
                success=False,
                tracks=tracks,
                stats={},
                score=0.0,
                warnings=[str(e)]
            )
            
    def get_transition_score(self, track1: Dict[str, Any], track2: Dict[str, Any]) -> float:
        key_score = self.key_strategy.get_transition_score(track1, track2)
        energy_score = self.energy_strategy.get_transition_score(track1, track2)
        
        return (
            key_score * self.weights['key'] +
            energy_score * self.weights['energy']
        )
        
    def _find_optimal_order(
        self,
        tracks: List[Dict[str, Any]],
        compatibility: List[List[float]]
    ) -> List[int]:
        """
        Encuentra el mejor orden considerando ambos aspectos.
        
        Args:
            tracks: Lista de tracks
            compatibility: Matriz de compatibilidad
            
        Returns:
            Lista de índices en el orden óptimo
        """
        size = len(tracks)
        if size <= 1:
            return list(range(size))
            
        # Comenzar con el track que tiene mejor balance
        start_idx = 0
        best_score = -1
        
        for i in range(size):
            key_compat = 0.0
            energy_compat = 0.0
            
            for j in range(size):
                if i != j:
                    key_compat += self.key_strategy.get_transition_score(
                        tracks[i], tracks[j]
                    )
                    energy_compat += self.energy_strategy.get_transition_score(
                        tracks[i], tracks[j]
                    )
                    
            score = (
                key_compat * self.weights['key'] +
                energy_compat * self.weights['energy']
            )
            
            if score > best_score:
                start_idx = i
                best_score = score
                
        # Construir orden óptimo
        result = [start_idx]
        used = {start_idx}
        current = start_idx
        
        while len(result) < size:
            best_next = None
            best_score = -1
            
            for i in range(size):
                if i not in used:
                    score = compatibility[current][i]
                    if score > best_score:
                        best_next = i
                        best_score = score
                        
            result.append(best_next)
            used.add(best_next)
            current = best_next
            
        return result

class PlaylistOptimizer:
    """
    Optimizador de playlists que aplica diferentes estrategias
    de reorganización según las necesidades.
    """
    
    def __init__(self):
        self._strategies = {
            OptimizationStrategy.KEY_PROGRESSION: KeyProgressionStrategy(),
            OptimizationStrategy.ENERGY_FLOW: EnergyFlowStrategy(),
            OptimizationStrategy.HYBRID: HybridStrategy()
        }
        
        self._logger = logging.getLogger(__name__)
        
    def optimize(
        self,
        tracks: List[Dict[str, Any]],
        strategy: OptimizationStrategy = OptimizationStrategy.HYBRID,
        custom_strategy: Optional[ReorderStrategy] = None
    ) -> OptimizationResult:
        """
        Optimiza el orden de una playlist.
        
        Args:
            tracks: Lista de tracks a optimizar
            strategy: Estrategia a utilizar
            custom_strategy: Estrategia personalizada opcional
            
        Returns:
            OptimizationResult con el resultado
            
        Raises:
            ValueError: Si la estrategia no es válida
        """
        try:
            # Validar entrada
            if not tracks:
                return OptimizationResult(
                    success=True,
                    tracks=[],
                    stats={},
                    score=1.0,
                    warnings=[]
                )
                
            # Obtener estrategia
            if strategy == OptimizationStrategy.CUSTOM:
                if not custom_strategy:
                    raise ValueError("Se requiere custom_strategy")
                reorder_strategy = custom_strategy
            else:
                reorder_strategy = self._strategies[strategy]
                
            # Aplicar optimización
            return reorder_strategy.reorder(tracks)
            
        except Exception as e:
            self._logger.error(f"Error optimizando playlist: {str(e)}")
            return OptimizationResult(
                success=False,
                tracks=tracks,
                stats={},
                score=0.0,
                warnings=[str(e)]
            )
            
    def add_custom_strategy(self, name: str, strategy: ReorderStrategy):
        """
        Agrega una estrategia personalizada.
        
        Args:
            name: Nombre de la estrategia
            strategy: Implementación de la estrategia
        """
        if not isinstance(strategy, ReorderStrategy):
            raise ValueError("La estrategia debe heredar de ReorderStrategy")
            
        self._strategies[name] = strategy
        
    def get_available_strategies(self) -> List[str]:
        """
        Retorna las estrategias disponibles.
        
        Returns:
            Lista de nombres de estrategias
        """
        return list(self._strategies.keys())
        
    def analyze_transitions(
        self,
        tracks: List[Dict[str, Any]],
        strategy: OptimizationStrategy = OptimizationStrategy.HYBRID
    ) -> Dict[str, Any]:
        """
        Analiza las transiciones en una playlist.
        
        Args:
            tracks: Lista de tracks a analizar
            strategy: Estrategia para evaluar transiciones
            
        Returns:
            Dict con análisis de transiciones
        """
        try:
            reorder_strategy = self._strategies[strategy]
            size = len(tracks)
            
            if size <= 1:
                return {
                    'transitions': [],
                    'average_score': 1.0,
                    'problem_areas': []
                }
                
            # Analizar cada transición
            transitions = []
            problem_areas = []
            
            for i in range(size - 1):
                score = reorder_strategy.get_transition_score(
                    tracks[i], tracks[i + 1]
                )
                
                transition = {
                    'from': tracks[i].get('title', 'Unknown'),
                    'to': tracks[i + 1].get('title', 'Unknown'),
                    'score': score
                }
                
                transitions.append(transition)
                
                # Identificar problemas
                if score < 0.5:
                    problem_areas.append({
                        'position': i,
                        'tracks': [tracks[i], tracks[i + 1]],
                        'score': score,
                        'suggestion': self._get_transition_suggestion(
                            tracks[i], tracks[i + 1], strategy
                        )
                    })
                    
            return {
                'transitions': transitions,
                'average_score': sum(t['score'] for t in transitions) / len(transitions),
                'problem_areas': problem_areas
            }
            
        except Exception as e:
            self._logger.error(f"Error analizando transiciones: {str(e)}")
            return {
                'transitions': [],
                'average_score': 0.0,
                'problem_areas': [],
                'error': str(e)
            }
            
    def _get_transition_suggestion(
        self,
        track1: Dict[str, Any],
        track2: Dict[str, Any],
        strategy: OptimizationStrategy
    ) -> str:
        """
        Genera una sugerencia para mejorar una transición.
        
        Args:
            track1: Primer track
            track2: Segundo track
            strategy: Estrategia actual
            
        Returns:
            str con sugerencia
        """
        if strategy == OptimizationStrategy.KEY_PROGRESSION:
            return self._get_key_suggestion(track1, track2)
        elif strategy == OptimizationStrategy.ENERGY_FLOW:
            return self._get_energy_suggestion(track1, track2)
        else:
            return "Considere reordenar estos tracks o agregar una transición intermedia"
            
    def _get_key_suggestion(self, track1: Dict[str, Any], track2: Dict[str, Any]) -> str:
        """Genera sugerencia para mejorar transición de claves."""
        key1 = track1.get('key')
        key2 = track2.get('key')
        
        if not key1 or not key2:
            return "Falta información de clave musical"
            
        wheel = CamelotWheel()
        
        # Encontrar claves compatibles
        compatible = wheel.get_compatible_keys(key1)
        if key2 not in compatible:
            return (
                f"Las claves {key1} y {key2} no son compatibles. "
                f"Considere usar una de: {', '.join(sorted(compatible))}"
            )
            
        return "Transición de claves subóptima"
        
    def _get_energy_suggestion(self, track1: Dict[str, Any], track2: Dict[str, Any]) -> str:
        """Genera sugerencia para mejorar transición de energía."""
        # Calcular diferencias
        attr_diffs = []
        
        for attr in ['bpm', 'energy', 'danceability']:
            val1 = track1.get(attr)
            val2 = track2.get(attr)
            
            if val1 is not None and val2 is not None:
                diff = abs(val2 - val1)
                if diff > 0.2:  # Umbral de diferencia significativa
                    attr_diffs.append(f"{attr} ({diff:.2f})")
                    
        if attr_diffs:
            return (
                f"Cambio brusco en: {', '.join(attr_diffs)}. "
                "Considere una transición más gradual"
            )
            
        return "Transición de energía subóptima"

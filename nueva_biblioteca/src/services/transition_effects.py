"""Provee efectos de transición entre pistas de audio."""

import numpy as np
from typing import Dict, List, Optional, Tuple
class TransitionEffect:
    """Efecto base para transiciones entre pistas."""
    """Efecto base para transiciones entre pistas."""
    
    def __init__(self, duration: float = 2.0):
        """
        Inicializa el efecto de transición.
        
        Args:
            duration: Duración del efecto en segundos
        """
        self.duration = duration
    
    def apply(self, audio1: np.ndarray, audio2: np.ndarray, 
             sr: int) -> np.ndarray:
        """
        Aplica el efecto de transición entre dos segmentos de audio.
        
        Args:
            audio1: Array numpy del audio saliente 
            audio2: Array numpy del audio entrante
            sr: Sample rate del audio
            
        Returns:
            Array numpy con la transición aplicada
        """
        raise NotImplementedError
        
    @property
    def name(self) -> str:
        """Retorna el nombre del efecto."""
        return self.__class__.__name__
        
class CrossFadeEffect(TransitionEffect):
    """Efecto de crossfade lineal entre pistas."""
    
    def apply(self, audio1: np.ndarray, audio2: np.ndarray, 
             sr: int) -> np.ndarray:
        """Aplica un crossfade lineal entre los audios."""
        # Convertir duración a muestras
        n_samples = int(self.duration * sr)
        
        # Asegurar que tenemos suficientes muestras
        if len(audio1) < n_samples or len(audio2) < n_samples:
            raise ValueError("Los segmentos de audio son muy cortos para la duración del fade")
            
        # Crear rampas de volumen
        fade_out = np.linspace(1.0, 0.0, n_samples)
        fade_in = np.linspace(0.0, 1.0, n_samples)
        
        # Aplicar fades
        audio1_fade = audio1[-n_samples:] * fade_out
        audio2_fade = audio2[:n_samples] * fade_in
        
        # Mezclar
        transition = audio1_fade + audio2_fade
        
        return transition

class EQTransitionEffect(TransitionEffect):
    """Transición usando ecualización (versión simplificada para demo)."""
    
    def __init__(self, duration: float = 2.0, 
                 bands: List[float] = [60, 250, 1000, 4000]):
        super().__init__(duration)
        self.bands = bands
        
    def apply(self, audio1: np.ndarray, audio2: np.ndarray, 
             sr: int) -> np.ndarray:
        """Versión simplificada para demo sin librosa."""
        n_samples = int(self.duration * sr)
        
        # Crear fade out/in por bandas simuladas
        fade_out = np.linspace(1.0, 0.0, n_samples)
        fade_in = np.linspace(0.0, 1.0, n_samples)
        
        # Simular transición por bandas
        transition = audio1[-n_samples:] * fade_out + audio2[:n_samples] * fade_in
        
        return transition

class TransitionEffectManager:
    """Gestiona los efectos de transición disponibles."""
    
    def __init__(self):
        """Inicializa el gestor de efectos."""
        self._effects: Dict[str, TransitionEffect] = {}
        self._register_defaults()
        
    def _register_defaults(self):
        """Registra los efectos por defecto."""
        self.register_effect("crossfade", CrossFadeEffect())
        self.register_effect("eq_transition", EQTransitionEffect())
        
    def register_effect(self, name: str, effect: TransitionEffect):
        """
        Registra un nuevo efecto.
        
        Args:
            name: Nombre para identificar el efecto
            effect: Instancia del efecto a registrar
        """
        self._effects[name] = effect
        
    def get_effect(self, name: str) -> Optional[TransitionEffect]:
        """
        Obtiene un efecto por nombre.
        
        Args:
            name: Nombre del efecto
            
        Returns:
            El efecto si existe, None si no
        """
        return self._effects.get(name)
        
    def get_effects(self) -> Dict[str, TransitionEffect]:
        """
        Retorna todos los efectos registrados.
        
        Returns:
            Diccionario de nombres a efectos
        """
        return self._effects.copy()

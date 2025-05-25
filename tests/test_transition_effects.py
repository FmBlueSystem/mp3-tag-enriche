"""Pruebas para los efectos de transición."""

import pytest
import numpy as np
from nueva_biblioteca.src.services.transition_effects import (
    TransitionEffect, CrossFadeEffect, EQTransitionEffect, 
    TransitionEffectManager
)

@pytest.fixture
def audio_segments():
    """Fixture que provee segmentos de audio de prueba."""
    # Crear dos segmentos de audio sintéticos
    sr = 44100  # Sample rate estándar
    duration = 3.0  # 3 segundos
    t = np.linspace(0, duration, int(sr * duration))
    
    # Audio 1: Tono de 440 Hz (La4)
    audio1 = np.sin(2 * np.pi * 440 * t)
    
    # Audio 2: Tono de 880 Hz (La5)
    audio2 = np.sin(2 * np.pi * 880 * t)
    
    return audio1, audio2, sr

@pytest.fixture
def effect_manager():
    """Fixture que provee una instancia de TransitionEffectManager."""
    return TransitionEffectManager()

def test_crossfade_effect(audio_segments):
    """Prueba el efecto de crossfade."""
    audio1, audio2, sr = audio_segments
    effect = CrossFadeEffect(duration=1.0)
    
    # Aplicar crossfade
    transition = effect.apply(audio1, audio2, sr)
    
    # Verificar dimensiones
    expected_samples = int(1.0 * sr)  # 1 segundo
    assert len(transition) == expected_samples
    
    # Verificar que la transición comienza con audio1 y termina con audio2
    assert np.allclose(transition[0], audio1[-expected_samples], atol=1e-7)
    assert np.allclose(transition[-1], audio2[expected_samples-1], atol=1e-7)

def test_eq_transition_effect(audio_segments):
    """Prueba el efecto de transición EQ."""
    audio1, audio2, sr = audio_segments
    
    # Crear efecto con bandas personalizadas
    bands = [100, 500, 2000, 8000]
    effect = EQTransitionEffect(duration=1.0, bands=bands)
    
    # Aplicar transición
    transition = effect.apply(audio1, audio2, sr)
    
    # Verificar dimensiones
    expected_samples = int(1.0 * sr)
    assert len(transition) == expected_samples
    
    # Verificar que las bandas se configuraron correctamente
    assert effect.bands == bands

def test_effect_manager_defaults(effect_manager):
    """Prueba la configuración por defecto del gestor de efectos."""
    # Verificar efectos registrados por defecto
    effects = effect_manager.get_effects()
    assert "crossfade" in effects
    assert "eq_transition" in effects
    
    # Verificar tipos de efectos
    assert isinstance(effects["crossfade"], CrossFadeEffect)
    assert isinstance(effects["eq_transition"], EQTransitionEffect)

def test_effect_manager_registration(effect_manager):
    """Prueba el registro de efectos personalizados."""
    # Crear efecto personalizado
    class CustomEffect(TransitionEffect):
        def apply(self, audio1, audio2, sr):
            return audio1  # Solo para pruebas
            
    # Registrar efecto
    custom = CustomEffect()
    effect_manager.register_effect("custom", custom)
    
    # Verificar registro
    effects = effect_manager.get_effects()
    assert "custom" in effects
    assert effects["custom"] is custom

def test_invalid_duration():
    """Prueba el manejo de duraciones inválidas."""
    effect = CrossFadeEffect(duration=0.1)
    
    # Crear audio muy corto
    sr = 44100
    audio = np.zeros(int(0.05 * sr))  # 50ms
    
    # Verificar que se lanza error por audio muy corto
    with pytest.raises(ValueError):
        effect.apply(audio, audio, sr)

def test_effect_duration_update():
    """Prueba la actualización de duración del efecto."""
    effect = CrossFadeEffect(duration=1.0)
    assert effect.duration == 1.0
    
    # Actualizar duración
    effect.duration = 2.0
    assert effect.duration == 2.0

def test_effect_name():
    """Prueba la propiedad name de los efectos."""
    crossfade = CrossFadeEffect()
    eq_transition = EQTransitionEffect()
    
    assert crossfade.name == "CrossFadeEffect"
    assert eq_transition.name == "EQTransitionEffect"

def test_get_nonexistent_effect(effect_manager):
    """Prueba obtener un efecto que no existe."""
    assert effect_manager.get_effect("nonexistent") is None

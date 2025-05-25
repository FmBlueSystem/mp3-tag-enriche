#!/usr/bin/env python3
"""
Motor de DJ - Funcionalidades para mezcla profesional
Incluye sincronización de BPM, cálculos de pitch y análisis de compatibilidad.
"""

import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

class TransitionQuality(Enum):
    """Calidad de transición entre dos tracks."""
    PERFECT = "Perfecta"
    EXCELLENT = "Excelente" 
    GOOD = "Buena"
    FAIR = "Aceptable"
    POOR = "Pobre"

@dataclass
class TrackInfo:
    """Información de un track para análisis de DJ."""
    track_id: int
    title: str
    artist: str
    bpm: float
    key: str
    camelot_key: str
    energy: int
    rating: float
    duration: int  # en segundos

@dataclass
class TransitionAnalysis:
    """Análisis de transición entre dos tracks."""
    track_a: TrackInfo
    track_b: TrackInfo
    bpm_difference: float
    pitch_adjustment: float  # Porcentaje de ajuste necesario
    harmonic_compatibility: bool
    camelot_technique: str
    energy_flow: str  # "up", "down", "stable"
    transition_quality: TransitionQuality
    compatibility_score: float  # 0-100

class DJEngine:
    """Motor principal para funcionalidades de DJ."""
    
    # Límites recomendados para transiciones
    MAX_BPM_DIFFERENCE = 6.0  # BPM máximo de diferencia sin pitch
    MAX_PITCH_ADJUSTMENT = 8.0  # Porcentaje máximo de pitch recomendado
    
    def __init__(self):
        """Inicializa el motor de DJ."""
        # Mapeo de técnicas Camelot (importado de camelot_wheel.py)
        self.camelot_techniques = {
            'adjacent': 'Mezcla Adyacente',
            'same_number': 'Mismo Número',
            'diagonal': 'Diagonal',
            'relative_mix': 'Relativa Alternativa',
            'energy_boost': 'Salto Energético',
            'dominant': 'Dominante/Subdominante',
            'camelot_inverse': 'Camelot Inverso',
            'harmonic_cadence': 'Cadencia Armónica'
        }
    
    def calculate_pitch_adjustment(self, bpm_from: float, bpm_to: float) -> float:
        """
        Calcula el ajuste de pitch necesario para sincronizar BPMs.
        
        Args:
            bpm_from: BPM del track origen
            bpm_to: BPM del track destino
            
        Returns:
            Porcentaje de ajuste de pitch (positivo = más rápido, negativo = más lento)
        """
        if bpm_from <= 0 or bpm_to <= 0:
            return 0.0
        
        # Fórmula: ((BPM_destino / BPM_origen) - 1) * 100
        pitch_ratio = bpm_to / bpm_from
        pitch_adjustment = (pitch_ratio - 1) * 100
        
        return round(pitch_adjustment, 2)
    
    def calculate_synced_bpm(self, original_bpm: float, pitch_adjustment: float) -> float:
        """
        Calcula el BPM resultante después de aplicar un ajuste de pitch.
        
        Args:
            original_bpm: BPM original del track
            pitch_adjustment: Porcentaje de ajuste de pitch
            
        Returns:
            BPM sincronizado
        """
        if original_bpm <= 0:
            return 0.0
        
        # Aplicar el ajuste: BPM_nuevo = BPM_original * (1 + ajuste/100)
        synced_bpm = original_bpm * (1 + pitch_adjustment / 100)
        return round(synced_bpm, 1)
    
    def analyze_bpm_compatibility(self, bpm_a: float, bpm_b: float) -> Dict[str, Any]:
        """
        Analiza la compatibilidad de BPM entre dos tracks.
        
        Args:
            bpm_a: BPM del primer track
            bpm_b: BPM del segundo track
            
        Returns:
            Diccionario con análisis de compatibilidad
        """
        bpm_diff = abs(bpm_b - bpm_a)
        pitch_needed = self.calculate_pitch_adjustment(bpm_a, bpm_b)
        
        # Determinar compatibilidad
        if bpm_diff <= 2.0:
            compatibility = "Perfecta"
            score = 100
        elif bpm_diff <= 4.0:
            compatibility = "Excelente"
            score = 85
        elif bpm_diff <= self.MAX_BPM_DIFFERENCE:
            compatibility = "Buena"
            score = 70
        elif abs(pitch_needed) <= self.MAX_PITCH_ADJUSTMENT:
            compatibility = "Aceptable con pitch"
            score = 55
        else:
            compatibility = "Difícil"
            score = 30
        
        return {
            'bpm_difference': round(bpm_diff, 1),
            'pitch_adjustment': pitch_needed,
            'compatibility': compatibility,
            'score': score,
            'needs_pitch': abs(pitch_needed) > 2.0,
            'recommended': bpm_diff <= self.MAX_BPM_DIFFERENCE or abs(pitch_needed) <= self.MAX_PITCH_ADJUSTMENT
        }
    
    def get_harmonic_compatibility(self, key_a: str, key_b: str) -> Dict[str, Any]:
        """
        Analiza la compatibilidad armónica entre dos tonalidades.
        
        Args:
            key_a: Tonalidad del primer track (formato Camelot)
            key_b: Tonalidad del segundo track (formato Camelot)
            
        Returns:
            Diccionario con análisis armónico
        """
        # Esta función se integraría con CamelotKey de camelot_wheel.py
        # Por ahora, implementación básica
        
        if not key_a or not key_b:
            return {
                'compatible': False,
                'technique': 'Desconocida',
                'score': 0,
                'description': 'Tonalidad no disponible'
            }
        
        # Análisis básico - en implementación real se usaría CamelotKey
        if key_a == key_b:
            return {
                'compatible': True,
                'technique': 'Misma tonalidad',
                'score': 100,
                'description': 'Compatibilidad perfecta'
            }
        
        # Simulación de compatibilidad (se reemplazaría con lógica real de Camelot)
        return {
            'compatible': True,
            'technique': 'Técnica estándar',
            'score': 75,
            'description': 'Compatible según rueda Camelot'
        }
    
    def analyze_energy_flow(self, energy_a: int, energy_b: int) -> Dict[str, Any]:
        """
        Analiza el flujo de energía entre dos tracks.
        
        Args:
            energy_a: Nivel de energía del primer track (1-10)
            energy_b: Nivel de energía del segundo track (1-10)
            
        Returns:
            Diccionario con análisis de flujo energético
        """
        energy_diff = energy_b - energy_a
        
        if energy_diff > 1:
            flow_type = "Ascendente"
            description = f"Incrementa energía (+{energy_diff})"
            score = 85 if energy_diff <= 3 else 60
        elif energy_diff < -1:
            flow_type = "Descendente"
            description = f"Reduce energía ({energy_diff})"
            score = 70 if energy_diff >= -2 else 50
        else:
            flow_type = "Estable"
            description = "Mantiene nivel energético"
            score = 90
        
        return {
            'flow_type': flow_type,
            'energy_difference': energy_diff,
            'description': description,
            'score': score,
            'recommended': abs(energy_diff) <= 3
        }
    
    def analyze_transition(self, track_a: TrackInfo, track_b: TrackInfo) -> TransitionAnalysis:
        """
        Realiza un análisis completo de transición entre dos tracks.
        
        Args:
            track_a: Información del primer track
            track_b: Información del segundo track
            
        Returns:
            Análisis completo de la transición
        """
        # Análisis de BPM
        bpm_analysis = self.analyze_bpm_compatibility(track_a.bpm, track_b.bpm)
        
        # Análisis armónico
        harmonic_analysis = self.get_harmonic_compatibility(track_a.camelot_key, track_b.camelot_key)
        
        # Análisis de energía
        energy_analysis = self.analyze_energy_flow(track_a.energy, track_b.energy)
        
        # Calcular score de compatibilidad total
        bpm_weight = 0.4
        harmonic_weight = 0.4
        energy_weight = 0.2
        
        total_score = (
            bpm_analysis['score'] * bpm_weight +
            harmonic_analysis['score'] * harmonic_weight +
            energy_analysis['score'] * energy_weight
        )
        
        # Determinar calidad de transición
        if total_score >= 90:
            quality = TransitionQuality.PERFECT
        elif total_score >= 80:
            quality = TransitionQuality.EXCELLENT
        elif total_score >= 70:
            quality = TransitionQuality.GOOD
        elif total_score >= 60:
            quality = TransitionQuality.FAIR
        else:
            quality = TransitionQuality.POOR
        
        return TransitionAnalysis(
            track_a=track_a,
            track_b=track_b,
            bpm_difference=bpm_analysis['bpm_difference'],
            pitch_adjustment=bpm_analysis['pitch_adjustment'],
            harmonic_compatibility=harmonic_analysis['compatible'],
            camelot_technique=harmonic_analysis['technique'],
            energy_flow=energy_analysis['flow_type'],
            transition_quality=quality,
            compatibility_score=round(total_score, 1)
        )
    
    def suggest_transitions(self, current_track: TrackInfo, available_tracks: List[TrackInfo], 
                          max_suggestions: int = 5) -> List[TransitionAnalysis]:
        """
        Sugiere las mejores transiciones para un track actual.
        
        Args:
            current_track: Track actual
            available_tracks: Lista de tracks disponibles
            max_suggestions: Número máximo de sugerencias
            
        Returns:
            Lista de análisis de transición ordenados por compatibilidad
        """
        transitions = []
        
        for track in available_tracks:
            if track.track_id != current_track.track_id:  # No sugerir el mismo track
                analysis = self.analyze_transition(current_track, track)
                transitions.append(analysis)
        
        # Ordenar por score de compatibilidad (descendente)
        transitions.sort(key=lambda x: x.compatibility_score, reverse=True)
        
        return transitions[:max_suggestions]
    
    def calculate_crossfader_mix(self, position: float) -> Tuple[float, float]:
        """
        Calcula los niveles de volumen para crossfader.
        
        Args:
            position: Posición del crossfader (-1.0 a 1.0)
                     -1.0 = solo track A, 0.0 = 50/50, 1.0 = solo track B
                     
        Returns:
            Tupla con (volumen_A, volumen_B) de 0.0 a 1.0
        """
        # Normalizar posición a 0-1
        normalized_pos = (position + 1.0) / 2.0
        
        # Curva de crossfade (puede ser lineal o logarítmica)
        # Implementación lineal por simplicidad
        volume_a = 1.0 - normalized_pos
        volume_b = normalized_pos
        
        return (volume_a, volume_b)
    
    def get_beat_grid_info(self, bpm: float, duration_seconds: int) -> Dict[str, Any]:
        """
        Calcula información de grilla de beats para un track.
        
        Args:
            bpm: BPM del track
            duration_seconds: Duración en segundos
            
        Returns:
            Información de grilla de beats
        """
        if bpm <= 0:
            return {'total_beats': 0, 'beat_interval': 0, 'bars': 0}
        
        # Calcular intervalo entre beats (en segundos)
        beat_interval = 60.0 / bpm
        
        # Calcular total de beats
        total_beats = int(duration_seconds / beat_interval)
        
        # Calcular número de compases (asumiendo 4/4)
        bars = total_beats // 4
        
        return {
            'total_beats': total_beats,
            'beat_interval': round(beat_interval, 3),
            'bars': bars,
            'beats_per_bar': 4,
            'time_signature': '4/4'
        }

# Funciones de utilidad
def format_bpm_difference(bpm_diff: float) -> str:
    """Formatea la diferencia de BPM para mostrar en UI."""
    if bpm_diff == 0:
        return "Idéntico"
    elif bpm_diff < 1:
        return f"{bpm_diff:.1f} BPM"
    else:
        return f"{bpm_diff:.0f} BPM"

def format_pitch_adjustment(pitch: float) -> str:
    """Formatea el ajuste de pitch para mostrar en UI."""
    if pitch == 0:
        return "Sin ajuste"
    elif pitch > 0:
        return f"+{pitch:.1f}%"
    else:
        return f"{pitch:.1f}%"

def get_transition_color(quality: TransitionQuality) -> str:
    """Devuelve un color para representar la calidad de transición."""
    color_map = {
        TransitionQuality.PERFECT: "#00FF00",    # Verde
        TransitionQuality.EXCELLENT: "#7FFF00", # Verde lima
        TransitionQuality.GOOD: "#FFFF00",      # Amarillo
        TransitionQuality.FAIR: "#FFA500",      # Naranja
        TransitionQuality.POOR: "#FF0000"       # Rojo
    }
    return color_map.get(quality, "#808080")  # Gris por defecto

# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del motor
    dj_engine = DJEngine()
    
    # Tracks de ejemplo
    track_a = TrackInfo(
        track_id=1,
        title="Song A",
        artist="Artist 1", 
        bpm=128.0,
        key="Am",
        camelot_key="8A",
        energy=7,
        rating=4.5,
        duration=240
    )
    
    track_b = TrackInfo(
        track_id=2,
        title="Song B",
        artist="Artist 2",
        bpm=132.0,
        key="Em", 
        camelot_key="9A",
        energy=8,
        rating=4.0,
        duration=210
    )
    
    # Analizar transición
    analysis = dj_engine.analyze_transition(track_a, track_b)
    
    print(f"Análisis de transición:")
    print(f"De: {track_a.title} ({track_a.bpm} BPM, {track_a.camelot_key})")
    print(f"A: {track_b.title} ({track_b.bpm} BPM, {track_b.camelot_key})")
    print(f"Diferencia BPM: {analysis.bpm_difference}")
    print(f"Ajuste de pitch: {analysis.pitch_adjustment}%")
    print(f"Calidad: {analysis.transition_quality.value}")
    print(f"Score: {analysis.compatibility_score}/100") 
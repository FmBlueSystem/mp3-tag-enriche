"""
Servicio de análisis de audio.
Permite analizar archivos de audio y obtener características en tiempo real.
"""
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import numpy as np
import librosa

class AudioAnalyzer:
    """Analizador de audio para extraer características."""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.current_audio = None
        self.sample_rate = None
        
    def load_file(self, file_path: str) -> bool:
        """
        Carga un archivo de audio para análisis.
        
        Args:
            file_path: Ruta al archivo de audio
            
        Returns:
            True si se cargó exitosamente
        """
        try:
            # Cargar audio con librosa
            self.current_audio, self.sample_rate = librosa.load(
                file_path,
                sr=None  # Mantener sample rate original
            )
            return True
        except Exception as e:
            self._logger.error(f"Error cargando audio {file_path}: {str(e)}")
            self.current_audio = None
            self.sample_rate = None
            return False
            
    def analyze_segment(self, start_time: float, end_time: float) -> Dict[str, Any]:
        """
        Analiza un segmento del audio cargado.
        
        Args:
            start_time: Tiempo inicial en segundos
            end_time: Tiempo final en segundos
            
        Returns:
            Diccionario con características del segmento
        """
        try:
            if self.current_audio is None:
                raise RuntimeError("No hay audio cargado")
                
            # Convertir tiempos a samples
            start_sample = int(start_time * self.sample_rate)
            end_sample = int(end_time * self.sample_rate)
            
            # Extraer segmento
            segment = self.current_audio[start_sample:end_sample]
            
            # Extraer características
            return {
                'bpm': self._extract_bpm(segment),
                'key': self._extract_key(segment),
                'energy': self._extract_energy(segment),
                'spectrum': self._extract_spectrum(segment),
                'volume': self._extract_volume(segment)
            }
            
        except Exception as e:
            self._logger.error(f"Error analizando segmento: {str(e)}")
            return {}
            
    def get_waveform(self, width: int = 800, height: int = 200) -> Optional[List[float]]:
        """
        Genera datos de forma de onda para visualización.
        
        Args:
            width: Ancho deseado de la visualización
            height: Alto deseado de la visualización
            
        Returns:
            Lista de valores normalizados para dibujar la forma de onda
        """
        try:
            if self.current_audio is None:
                return None
                
            # Reducir muestras al ancho deseado
            samples_per_pixel = len(self.current_audio) // width
            max_samples = np.array_split(
                abs(self.current_audio),
                width
            )
            waveform = [float(max(chunk)) for chunk in max_samples]
            
            # Normalizar a la altura deseada
            max_val = max(waveform)
            if max_val > 0:
                waveform = [
                    (val / max_val) * (height / 2)
                    for val in waveform
                ]
                
            return waveform
            
        except Exception as e:
            self._logger.error(f"Error generando forma de onda: {str(e)}")
            return None
            
    def _extract_bpm(self, audio: np.ndarray) -> Optional[float]:
        """
        Extrae el BPM del segmento de audio.
        
        Args:
            audio: Segmento de audio como numpy array
            
        Returns:
            BPM como float o None si no se pudo detectar
        """
        try:
            tempo, _ = librosa.beat.beat_track(
                y=audio,
                sr=self.sample_rate
            )
            return float(tempo)
        except Exception as e:
            self._logger.error(f"Error extrayendo BPM: {str(e)}")
            return None
            
    def _extract_key(self, audio: np.ndarray) -> Optional[str]:
        """
        Extrae la tonalidad del segmento de audio.
        
        Args:
            audio: Segmento de audio como numpy array
            
        Returns:
            Tonalidad como string o None si no se pudo detectar
        """
        try:
            # Extraer cromagrama
            chroma = librosa.feature.chroma_cqt(
                y=audio,
                sr=self.sample_rate
            )
            
            # Obtener tonalidad más probable
            key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            key_features = np.mean(chroma, axis=1)
            key_index = np.argmax(key_features)
            
            return key_names[key_index]
            
        except Exception as e:
            self._logger.error(f"Error extrayendo tonalidad: {str(e)}")
            return None
            
    def _extract_energy(self, audio: np.ndarray) -> Optional[float]:
        """
        Extrae la energía del segmento de audio.
        
        Args:
            audio: Segmento de audio como numpy array
            
        Returns:
            Energía como float o None si no se pudo calcular
        """
        try:
            # Calcular RMS (Root Mean Square) como medida de energía
            energy = float(np.sqrt(np.mean(np.square(audio))))
            
            # Normalizar entre 0 y 1
            return min(1.0, energy * 10)  # Multiplicar por 10 para mejor rango
            
        except Exception as e:
            self._logger.error(f"Error extrayendo energía: {str(e)}")
            return None
            
    def _extract_spectrum(self, audio: np.ndarray) -> Optional[List[float]]:
        """
        Extrae el espectro de frecuencias del segmento.
        
        Args:
            audio: Segmento de audio como numpy array
            
        Returns:
            Lista de magnitudes de frecuencia o None si hubo error
        """
        try:
            # Calcular espectrograma
            D = librosa.stft(audio)
            magnitudes = librosa.amplitude_to_db(np.abs(D), ref=np.max)
            
            # Reducir a 128 bandas de frecuencia
            return [float(x) for x in np.mean(magnitudes, axis=1)[:128]]
            
        except Exception as e:
            self._logger.error(f"Error extrayendo espectro: {str(e)}")
            return None
            
    def _extract_volume(self, audio: np.ndarray) -> Optional[float]:
        """
        Extrae el volumen del segmento de audio.
        
        Args:
            audio: Segmento de audio como numpy array
            
        Returns:
            Volumen como float entre 0 y 1, o None si hubo error
        """
        try:
            # Calcular RMS y normalizar
            rms = librosa.feature.rms(y=audio)[0]
            volume = float(np.mean(rms))
            
            # Convertir a escala logarítmica y normalizar
            volume = np.log10(max(volume, 1e-10))
            volume = (volume + 10) / 10  # Normalizar aproximadamente entre 0 y 1
            
            return min(1.0, max(0.0, volume))
            
        except Exception as e:
            self._logger.error(f"Error extrayendo volumen: {str(e)}")
            return None

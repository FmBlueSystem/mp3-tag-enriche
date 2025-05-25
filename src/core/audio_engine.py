#!/usr/bin/env python3
"""
Motor de Audio - v3.0
Sistema de reproducción de audio para aplicaciones de DJ usando pygame.
"""

import pygame
import threading
import time
import os
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

class PlaybackState(Enum):
    """Estados de reproducción."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"

@dataclass
class AudioInfo:
    """Información de un archivo de audio."""
    file_path: str
    duration: float = 0.0
    sample_rate: int = 44100
    channels: int = 2
    format_name: str = "unknown"
    file_size: int = 0

class AudioEngine:
    """Motor de audio principal para reproducción de archivos."""
    
    def __init__(self, buffer_size: int = 1024):
        """
        Inicializa el motor de audio.
        
        Args:
            buffer_size: Tamaño del buffer de audio
        """
        self.buffer_size = buffer_size
        self.is_initialized = False
        self.current_file: Optional[str] = None
        self.current_sound: Optional[pygame.mixer.Sound] = None
        self.current_channel: Optional[pygame.mixer.Channel] = None
        self.state = PlaybackState.STOPPED
        self.position = 0.0  # Posición actual en segundos
        self.volume = 1.0
        self.audio_info: Optional[AudioInfo] = None
        
        # Callbacks para eventos
        self.on_position_changed: Optional[Callable[[float], None]] = None
        self.on_state_changed: Optional[Callable[[PlaybackState], None]] = None
        self.on_track_finished: Optional[Callable[[], None]] = None
        
        # Thread para monitoreo de posición
        self._position_thread: Optional[threading.Thread] = None
        self._stop_monitoring = False
        
        self._initialize_pygame()
    
    def _initialize_pygame(self) -> bool:
        """Inicializa pygame mixer."""
        try:
            pygame.mixer.pre_init(
                frequency=44100,
                size=-16,
                channels=2,
                buffer=self.buffer_size
            )
            pygame.mixer.init()
            self.is_initialized = True
            print("🎵 Motor de audio inicializado correctamente")
            return True
        except Exception as e:
            print(f"❌ Error inicializando motor de audio: {e}")
            self.is_initialized = False
            return False
    
    def load_file(self, file_path: str) -> bool:
        """
        Carga un archivo de audio.
        
        Args:
            file_path: Ruta al archivo de audio
            
        Returns:
            True si se cargó correctamente
        """
        if not self.is_initialized:
            print("❌ Motor de audio no inicializado")
            return False
        
        if not os.path.exists(file_path):
            print(f"❌ Archivo no encontrado: {file_path}")
            return False
        
        try:
            self._set_state(PlaybackState.LOADING)
            
            # Detener reproducción actual si existe
            self.stop()
            
            # Cargar nuevo archivo
            self.current_sound = pygame.mixer.Sound(file_path)
            self.current_file = file_path
            self.position = 0.0
            
            # Obtener información del archivo
            self.audio_info = self._get_audio_info(file_path)
            
            self._set_state(PlaybackState.STOPPED)
            print(f"✅ Archivo cargado: {os.path.basename(file_path)}")
            return True
            
        except Exception as e:
            print(f"❌ Error cargando archivo {file_path}: {e}")
            self.current_sound = None
            self.current_file = None
            self.audio_info = None
            self._set_state(PlaybackState.STOPPED)
            return False
    
    def play(self) -> bool:
        """Inicia la reproducción."""
        if not self.current_sound:
            print("❌ No hay archivo cargado")
            return False
        
        try:
            if self.state == PlaybackState.PAUSED:
                # Reanudar reproducción pausada
                pygame.mixer.unpause()
            else:
                # Iniciar nueva reproducción
                self.current_channel = self.current_sound.play()
                if self.current_channel:
                    self.current_channel.set_volume(self.volume)
                    self._start_position_monitoring()
            
            self._set_state(PlaybackState.PLAYING)
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando reproducción: {e}")
            return False
    
    def pause(self) -> bool:
        """Pausa la reproducción."""
        if self.state != PlaybackState.PLAYING:
            return False
        
        try:
            pygame.mixer.pause()
            self._set_state(PlaybackState.PAUSED)
            return True
        except Exception as e:
            print(f"❌ Error pausando reproducción: {e}")
            return False
    
    def stop(self) -> bool:
        """Detiene la reproducción."""
        try:
            pygame.mixer.stop()
            self.position = 0.0
            self.current_channel = None
            self._stop_position_monitoring()
            self._set_state(PlaybackState.STOPPED)
            return True
        except Exception as e:
            print(f"❌ Error deteniendo reproducción: {e}")
            return False
    
    def set_volume(self, volume: float) -> bool:
        """
        Establece el volumen.
        
        Args:
            volume: Volumen entre 0.0 y 1.0
        """
        volume = max(0.0, min(1.0, volume))
        self.volume = volume
        
        if self.current_channel:
            self.current_channel.set_volume(volume)
        
        return True
    
    def seek(self, position: float) -> bool:
        """
        Busca una posición específica en el audio.
        
        Args:
            position: Posición en segundos
            
        Note:
            pygame no soporta seek nativo, esta es una implementación limitada
        """
        if not self.audio_info:
            return False
        
        # Limitar posición al rango válido
        position = max(0.0, min(position, self.audio_info.duration))
        
        # Para pygame, necesitamos reiniciar desde el principio
        # Esta es una limitación conocida de pygame
        was_playing = self.state == PlaybackState.PLAYING
        
        self.stop()
        self.position = position
        
        if was_playing and position < self.audio_info.duration:
            # Nota: Esta implementación es limitada
            # Para seek real necesitaríamos una librería más avanzada
            print(f"⚠️ Seek limitado a posición {position:.1f}s")
            self.play()
        
        return True
    
    def get_position(self) -> float:
        """Obtiene la posición actual en segundos."""
        return self.position
    
    def get_duration(self) -> float:
        """Obtiene la duración total en segundos."""
        return self.audio_info.duration if self.audio_info else 0.0
    
    def get_state(self) -> PlaybackState:
        """Obtiene el estado actual de reproducción."""
        return self.state
    
    def is_playing(self) -> bool:
        """Verifica si está reproduciendo."""
        return self.state == PlaybackState.PLAYING
    
    def _get_audio_info(self, file_path: str) -> AudioInfo:
        """Obtiene información básica del archivo de audio."""
        try:
            file_size = os.path.getsize(file_path)
            
            # Para pygame, la información es limitada
            # Estimamos duración basada en el tamaño del archivo
            # Esta es una aproximación muy básica
            estimated_duration = file_size / (44100 * 2 * 2)  # Estimación básica
            
            return AudioInfo(
                file_path=file_path,
                duration=max(1.0, estimated_duration),  # Mínimo 1 segundo
                sample_rate=44100,
                channels=2,
                format_name=os.path.splitext(file_path)[1].lower(),
                file_size=file_size
            )
        except Exception as e:
            print(f"⚠️ Error obteniendo info de audio: {e}")
            return AudioInfo(
                file_path=file_path,
                duration=60.0,  # Duración por defecto
                sample_rate=44100,
                channels=2,
                format_name="unknown",
                file_size=0
            )
    
    def _set_state(self, new_state: PlaybackState):
        """Cambia el estado y notifica a los callbacks."""
        if self.state != new_state:
            self.state = new_state
            if self.on_state_changed:
                self.on_state_changed(new_state)
    
    def _start_position_monitoring(self):
        """Inicia el monitoreo de posición en un thread separado."""
        self._stop_monitoring = False
        if self._position_thread and self._position_thread.is_alive():
            return
        
        self._position_thread = threading.Thread(
            target=self._position_monitor_loop,
            daemon=True
        )
        self._position_thread.start()
    
    def _stop_position_monitoring(self):
        """Detiene el monitoreo de posición."""
        self._stop_monitoring = True
    
    def _position_monitor_loop(self):
        """Loop de monitoreo de posición."""
        start_time = time.time()
        
        while not self._stop_monitoring and self.state == PlaybackState.PLAYING:
            # Actualizar posición basada en tiempo transcurrido
            elapsed = time.time() - start_time
            self.position = min(elapsed, self.get_duration())
            
            # Notificar cambio de posición
            if self.on_position_changed:
                self.on_position_changed(self.position)
            
            # Verificar si terminó la reproducción
            if self.current_channel and not self.current_channel.get_busy():
                self._set_state(PlaybackState.STOPPED)
                self.position = 0.0
                if self.on_track_finished:
                    self.on_track_finished()
                break
            
            # Verificar si llegamos al final
            if self.position >= self.get_duration():
                self.stop()
                if self.on_track_finished:
                    self.on_track_finished()
                break
            
            time.sleep(0.1)  # Actualizar cada 100ms
    
    def cleanup(self):
        """Limpia recursos del motor de audio."""
        self.stop()
        self._stop_monitoring = True
        
        if self._position_thread and self._position_thread.is_alive():
            self._position_thread.join(timeout=1.0)
        
        if self.is_initialized:
            pygame.mixer.quit()
            self.is_initialized = False
        
        print("🔄 Motor de audio limpiado")

# Funciones de utilidad para formatos de audio soportados
SUPPORTED_FORMATS = {'.wav', '.ogg', '.mp3'}

def is_audio_file(file_path: str) -> bool:
    """Verifica si un archivo es de audio soportado."""
    return os.path.splitext(file_path.lower())[1] in SUPPORTED_FORMATS

def get_supported_formats() -> list:
    """Obtiene lista de formatos soportados."""
    return list(SUPPORTED_FORMATS)

def format_time(seconds: float) -> str:
    """Formatea tiempo en formato MM:SS."""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}" 
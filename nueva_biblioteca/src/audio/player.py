"""
Reproductor de audio integrado para Nueva Biblioteca.
"""

import pygame
import threading
import time
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue
import logging

class PlayerState(Enum):
    """Estados del reproductor."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"

@dataclass
class Track:
    """Información básica de un track para reproducción."""
    id: int
    file_path: str
    title: str
    artist: str
    duration: Optional[float] = None
    
@dataclass
class PlaybackStatus:
    """Estado actual de reproducción."""
    state: PlayerState = PlayerState.STOPPED
    current_track: Optional[Track] = None
    position: float = 0.0  # Posición en segundos
    duration: float = 0.0  # Duración total en segundos
    volume: float = 0.7    # Volumen 0.0 - 1.0
    is_muted: bool = False
    playlist_position: int = -1
    playlist_length: int = 0

class AudioPlayer:
    """
    Reproductor de audio básico usando pygame.
    Soporta reproducción, pausa, búsqueda y gestión de playlist.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Estado del reproductor
        self._status = PlaybackStatus()
        self._playlist: List[Track] = []
        
        # Control de hilos
        self._position_thread: Optional[threading.Thread] = None
        self._stop_position_thread = threading.Event()
        
        # Callbacks
        self._status_callbacks: List[Callable[[PlaybackStatus], None]] = []
        self._track_end_callbacks: List[Callable[[Track], None]] = []
        self._error_callbacks: List[Callable[[str], None]] = []
        
        # Queue para comandos thread-safe
        self._command_queue: Queue = Queue()
        
        # Inicializar pygame mixer
        self._initialize_pygame()
        
        # Hilo para procesar comandos
        self._command_thread = threading.Thread(target=self._process_commands, daemon=True)
        self._command_thread.start()
    
    def _initialize_pygame(self):
        """Inicializa pygame mixer."""
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
            pygame.mixer.init()
            self.logger.info("Pygame mixer inicializado correctamente")
        except Exception as e:
            self.logger.error(f"Error inicializando pygame mixer: {e}")
            self._status.state = PlayerState.ERROR
            self._notify_error(f"Error inicializando audio: {e}")
    
    def _process_commands(self):
        """Procesa comandos del reproductor en un hilo separado."""
        while True:
            try:
                command, args, kwargs = self._command_queue.get()
                if command == "stop_thread":
                    break
                
                method = getattr(self, f"_cmd_{command}", None)
                if method:
                    method(*args, **kwargs)
                
                self._command_queue.task_done()
            except Exception as e:
                self.logger.error(f"Error procesando comando: {e}")
    
    def _send_command(self, command: str, *args, **kwargs):
        """Envía un comando al hilo de procesamiento."""
        self._command_queue.put((command, args, kwargs))
    
    # Callbacks
    def add_status_callback(self, callback: Callable[[PlaybackStatus], None]):
        """Añade un callback para cambios de estado."""
        self._status_callbacks.append(callback)
    
    def add_track_end_callback(self, callback: Callable[[Track], None]):
        """Añade un callback para cuando termina un track."""
        self._track_end_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str], None]):
        """Añade un callback para errores."""
        self._error_callbacks.append(callback)
    
    def _notify_status_change(self):
        """Notifica cambios de estado a los callbacks."""
        for callback in self._status_callbacks:
            try:
                callback(self._status)
            except Exception as e:
                self.logger.error(f"Error en callback de estado: {e}")
    
    def _notify_track_end(self, track: Track):
        """Notifica fin de track a los callbacks."""
        for callback in self._track_end_callbacks:
            try:
                callback(track)
            except Exception as e:
                self.logger.error(f"Error en callback de fin de track: {e}")
    
    def _notify_error(self, error_message: str):
        """Notifica errores a los callbacks."""
        for callback in self._error_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                self.logger.error(f"Error en callback de error: {e}")
    
    # Comandos del reproductor
    def _cmd_load_track(self, track: Track):
        """Comando para cargar un track."""
        try:
            self._status.state = PlayerState.LOADING
            self._notify_status_change()
            
            file_path = Path(track.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {track.file_path}")
            
            # Detener reproducción actual
            pygame.mixer.music.stop()
            
            # Cargar nuevo archivo
            pygame.mixer.music.load(str(file_path))
            
            # Actualizar estado
            self._status.current_track = track
            self._status.position = 0.0
            self._status.duration = track.duration or 0.0
            self._status.state = PlayerState.STOPPED
            
            self.logger.info(f"Track cargado: {track.title}")
            self._notify_status_change()
            
        except Exception as e:
            self.logger.error(f"Error cargando track: {e}")
            self._status.state = PlayerState.ERROR
            self._notify_error(f"Error cargando track: {e}")
            self._notify_status_change()
    
    def _cmd_play(self):
        """Comando para iniciar reproducción."""
        try:
            if self._status.state == PlayerState.PAUSED:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.play()
                self._start_position_tracking()
            
            self._status.state = PlayerState.PLAYING
            self.logger.info("Reproducción iniciada")
            self._notify_status_change()
            
        except Exception as e:
            self.logger.error(f"Error iniciando reproducción: {e}")
            self._status.state = PlayerState.ERROR
            self._notify_error(f"Error iniciando reproducción: {e}")
            self._notify_status_change()
    
    def _cmd_pause(self):
        """Comando para pausar reproducción."""
        try:
            pygame.mixer.music.pause()
            self._status.state = PlayerState.PAUSED
            self._stop_position_tracking()
            
            self.logger.info("Reproducción pausada")
            self._notify_status_change()
            
        except Exception as e:
            self.logger.error(f"Error pausando reproducción: {e}")
    
    def _cmd_stop(self):
        """Comando para detener reproducción."""
        try:
            pygame.mixer.music.stop()
            self._status.state = PlayerState.STOPPED
            self._status.position = 0.0
            self._stop_position_tracking()
            
            self.logger.info("Reproducción detenida")
            self._notify_status_change()
            
        except Exception as e:
            self.logger.error(f"Error deteniendo reproducción: {e}")
    
    def _cmd_set_volume(self, volume: float):
        """Comando para cambiar volumen."""
        try:
            volume = max(0.0, min(1.0, volume))  # Limitar entre 0 y 1
            pygame.mixer.music.set_volume(volume)
            self._status.volume = volume
            self._status.is_muted = False
            
            self.logger.debug(f"Volumen cambiado a: {volume}")
            self._notify_status_change()
            
        except Exception as e:
            self.logger.error(f"Error cambiando volumen: {e}")
    
    def _cmd_toggle_mute(self):
        """Comando para silenciar/activar audio."""
        try:
            if self._status.is_muted:
                pygame.mixer.music.set_volume(self._status.volume)
                self._status.is_muted = False
            else:
                pygame.mixer.music.set_volume(0.0)
                self._status.is_muted = True
            
            self.logger.debug(f"Mute toggled: {self._status.is_muted}")
            self._notify_status_change()
            
        except Exception as e:
            self.logger.error(f"Error en toggle mute: {e}")
    
    def _cmd_seek(self, position: float):
        """Comando para buscar posición (limitado en pygame)."""
        # Nota: pygame no soporta seek nativo, esto es una implementación limitada
        try:
            if self._status.current_track and 0 <= position <= self._status.duration:
                # Con pygame, tendríamos que recargar el archivo y avanzar
                # Esta es una limitación conocida de pygame
                self._status.position = position
                self.logger.warning("Seek limitado en pygame - posición actualizada solo en UI")
                self._notify_status_change()
            
        except Exception as e:
            self.logger.error(f"Error en seek: {e}")
    
    # Métodos públicos del reproductor
    def load_track(self, track: Track):
        """Carga un track para reproducción."""
        self._send_command("load_track", track)
    
    def play(self):
        """Inicia o resume la reproducción."""
        self._send_command("play")
    
    def pause(self):
        """Pausa la reproducción."""
        self._send_command("pause")
    
    def stop(self):
        """Detiene la reproducción."""
        self._send_command("stop")
    
    def toggle_play_pause(self):
        """Alterna entre play y pausa."""
        if self._status.state == PlayerState.PLAYING:
            self.pause()
        elif self._status.state in [PlayerState.PAUSED, PlayerState.STOPPED]:
            self.play()
    
    def set_volume(self, volume: float):
        """Establece el volumen (0.0 - 1.0)."""
        self._send_command("set_volume", volume)
    
    def toggle_mute(self):
        """Alterna silencio."""
        self._send_command("toggle_mute")
    
    def seek(self, position: float):
        """Busca una posición específica en segundos."""
        self._send_command("seek", position)
    
    def seek_relative(self, delta: float):
        """Busca una posición relativa en segundos."""
        new_position = max(0, min(self._status.duration, self._status.position + delta))
        self.seek(new_position)
    
    # Gestión de playlist
    def set_playlist(self, tracks: List[Track], start_index: int = 0):
        """Establece una nueva playlist."""
        self._playlist = tracks.copy()
        self._status.playlist_length = len(tracks)
        
        if tracks and 0 <= start_index < len(tracks):
            self._status.playlist_position = start_index
            self.load_track(tracks[start_index])
        
        self._notify_status_change()
    
    def next_track(self):
        """Avanza al siguiente track en la playlist."""
        if not self._playlist:
            return
        
        next_index = self._status.playlist_position + 1
        if next_index < len(self._playlist):
            self._status.playlist_position = next_index
            self.load_track(self._playlist[next_index])
            if self._status.state == PlayerState.PLAYING:
                self.play()
    
    def previous_track(self):
        """Retrocede al track anterior en la playlist."""
        if not self._playlist:
            return
        
        prev_index = self._status.playlist_position - 1
        if prev_index >= 0:
            self._status.playlist_position = prev_index
            self.load_track(self._playlist[prev_index])
            if self._status.state == PlayerState.PLAYING:
                self.play()
    
    def play_track_at_index(self, index: int):
        """Reproduce un track específico de la playlist."""
        if self._playlist and 0 <= index < len(self._playlist):
            self._status.playlist_position = index
            self.load_track(self._playlist[index])
            self.play()
    
    # Tracking de posición
    def _start_position_tracking(self):
        """Inicia el seguimiento de posición."""
        self._stop_position_tracking()
        self._stop_position_thread.clear()
        self._position_thread = threading.Thread(target=self._track_position, daemon=True)
        self._position_thread.start()
    
    def _stop_position_tracking(self):
        """Detiene el seguimiento de posición."""
        self._stop_position_thread.set()
        if self._position_thread and self._position_thread.is_alive():
            self._position_thread.join(timeout=0.5)
    
    def _track_position(self):
        """Rastrea la posición de reproducción."""
        start_time = time.time()
        initial_position = self._status.position
        
        while not self._stop_position_thread.is_set():
            if self._status.state == PlayerState.PLAYING:
                # Calcular posición basada en tiempo transcurrido
                elapsed = time.time() - start_time
                self._status.position = initial_position + elapsed
                
                # Verificar si el track terminó
                if (self._status.duration > 0 and 
                    self._status.position >= self._status.duration):
                    
                    self._on_track_end()
                    break
                
                # Verificar si pygame sigue reproduciendo
                if not pygame.mixer.music.get_busy():
                    self._on_track_end()
                    break
                
                self._notify_status_change()
            
            time.sleep(0.1)  # Actualizar cada 100ms
    
    def _on_track_end(self):
        """Maneja el fin de un track."""
        if self._status.current_track:
            self._notify_track_end(self._status.current_track)
        
        # Auto-avanzar al siguiente track si hay playlist
        if self._playlist and self._status.playlist_position < len(self._playlist) - 1:
            self.next_track()
        else:
            self._status.state = PlayerState.STOPPED
            self._status.position = 0.0
            self._notify_status_change()
    
    # Estado y propiedades
    @property
    def status(self) -> PlaybackStatus:
        """Retorna el estado actual del reproductor."""
        return self._status
    
    @property
    def is_playing(self) -> bool:
        """Retorna True si está reproduciendo."""
        return self._status.state == PlayerState.PLAYING
    
    @property
    def is_paused(self) -> bool:
        """Retorna True si está pausado."""
        return self._status.state == PlayerState.PAUSED
    
    @property
    def is_stopped(self) -> bool:
        """Retorna True si está detenido."""
        return self._status.state == PlayerState.STOPPED
    
    @property
    def current_track(self) -> Optional[Track]:
        """Retorna el track actual."""
        return self._status.current_track
    
    @property
    def playlist(self) -> List[Track]:
        """Retorna la playlist actual."""
        return self._playlist.copy()
    
    def get_position_formatted(self) -> str:
        """Retorna la posición formateada como MM:SS."""
        minutes = int(self._status.position // 60)
        seconds = int(self._status.position % 60)
        return f"{minutes}:{seconds:02d}"
    
    def get_duration_formatted(self) -> str:
        """Retorna la duración formateada como MM:SS."""
        minutes = int(self._status.duration // 60)
        seconds = int(self._status.duration % 60)
        return f"{minutes}:{seconds:02d}"
    
    def get_progress_percentage(self) -> float:
        """Retorna el progreso como porcentaje (0.0 - 1.0)."""
        if self._status.duration > 0:
            return min(1.0, self._status.position / self._status.duration)
        return 0.0
    
    # Cleanup
    def cleanup(self):
        """Limpia recursos del reproductor."""
        self.stop()
        self._stop_position_tracking()
        
        # Detener el hilo de comandos
        self._send_command("stop_thread")
        if self._command_thread.is_alive():
            self._command_thread.join(timeout=1.0)
        
        try:
            pygame.mixer.quit()
        except:
            pass
        
        self.logger.info("Reproductor limpiado")
    
    def __del__(self):
        """Destructor para cleanup automático."""
        try:
            self.cleanup()
        except:
            pass
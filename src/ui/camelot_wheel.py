"""
Widget de Rueda Camelot Interactiva para Nueva Biblioteca Musical.

La Rueda Camelot es un sistema que organiza las tonalidades musicales en un círculo,
facilitando las transiciones armónicas entre canciones para DJs.
"""

import sys
import math
from typing import List, Set, Optional, Tuple
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QCheckBox, QGroupBox, QApplication)
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPolygon, QMouseEvent


class CamelotKey:
    """Representa una tonalidad en el sistema Camelot."""
    
    # Mapeo de tonalidades musicales a códigos Camelot
    CAMELOT_MAP = {
        # Tonalidades menores (A)
        'Am': '8A', 'Em': '9A', 'Bm': '10A', 'F#m': '11A', 'C#m': '12A', 'G#m': '1A',
        'D#m': '2A', 'A#m': '3A', 'Fm': '4A', 'Cm': '5A', 'Gm': '6A', 'Dm': '7A',
        
        # Tonalidades mayores (B)
        'C': '8B', 'G': '9B', 'D': '10B', 'A': '11B', 'E': '12B', 'B': '1B',
        'F#': '2B', 'C#': '3B', 'G#': '4B', 'D#': '5B', 'A#': '6B', 'F': '7B'
    }
    
    # Mapeo inverso
    REVERSE_MAP = {v: k for k, v in CAMELOT_MAP.items()}
    
    # Posiciones en la rueda (ángulos en grados)
    POSITIONS = {
        '12A': 0, '12B': 0,    # 12 o'clock
        '1A': 30, '1B': 30,    # 1 o'clock
        '2A': 60, '2B': 60,    # 2 o'clock
        '3A': 90, '3B': 90,    # 3 o'clock
        '4A': 120, '4B': 120,  # 4 o'clock
        '5A': 150, '5B': 150,  # 5 o'clock
        '6A': 180, '6B': 180,  # 6 o'clock
        '7A': 210, '7B': 210,  # 7 o'clock
        '8A': 240, '8B': 240,  # 8 o'clock
        '9A': 270, '9B': 270,  # 9 o'clock
        '10A': 300, '10B': 300, # 10 o'clock
        '11A': 330, '11B': 330  # 11 o'clock
    }
    
    @classmethod
    def from_musical_key(cls, musical_key: str) -> Optional[str]:
        """Convierte una tonalidad musical a código Camelot."""
        return cls.CAMELOT_MAP.get(musical_key)
    
    @classmethod
    def to_musical_key(cls, camelot_code: str) -> Optional[str]:
        """Convierte un código Camelot a tonalidad musical."""
        return cls.REVERSE_MAP.get(camelot_code)
    
    @classmethod
    def get_compatible_keys(cls, camelot_code: str) -> List[str]:
        """
        Obtiene las tonalidades compatibles para transiciones armónicas.
        Este método ahora sirve como un alias para obtener las 'standard' compatibles.
        """
        return cls.get_standard_compatible_keys(camelot_code)

    @classmethod
    def _calculate_camelot_num(cls, current_num: int, offset: int) -> int:
        """Calcula un nuevo número Camelot (1-12) aplicando un offset."""
        # Asegura que current_num está en el rango 1-12
        if not 1 <= current_num <= 12:
            raise ValueError("El número Camelot debe estar entre 1 y 12.")
        
        new_num_zero_based = (current_num - 1 + offset) % 12
        return new_num_zero_based + 1

    @classmethod
    def get_standard_compatible_keys(cls, camelot_code: str) -> List[str]:
        """Reglas de compatibilidad estándar."""
        if not camelot_code or camelot_code not in cls.POSITIONS:
            return []
        
        number = int(camelot_code[:-1])
        mode = camelot_code[-1]
        opposite_mode = 'B' if mode == 'A' else 'A'
        
        compatible = []

        # 1. Misma Clave (implícito, es la clave seleccionada)
        # compatible.append(camelot_code) # No se suele añadir la misma clave a 'compatibles'

        # 2. Cambio de Modo (Ej: 8A → 8B)
        compatible.append(f"{number}{opposite_mode}")
        
        # 3. Claves Adyacentes (Ej: 8A → 7A o 9A)
        prev_num = cls._calculate_camelot_num(number, -1)
        next_num = cls._calculate_camelot_num(number, +1)
        compatible.extend([f"{prev_num}{mode}", f"{next_num}{mode}"])
        
        # Adicionalmente, las 'mezclas diagonales' o 'modulación a adyacente'
        # (Ej: 8A → 7B o 9B), que son adyacentes con cambio de modo.
        compatible.extend([f"{prev_num}{opposite_mode}", f"{next_num}{opposite_mode}"])
        
        return list(set(compatible)) # Eliminar duplicados

    @classmethod
    def get_relative_mix_keys(cls, camelot_code: str) -> List[str]:
        """Mezcla con la 'Relativa Alternativa' (Ej: 8A → 5B)"""
        if not camelot_code or camelot_code not in cls.POSITIONS:
            return []
        number = int(camelot_code[:-1])
        mode = camelot_code[-1]
        
        if mode == 'A': # From Minor XA to (X-3)B
            target_num = cls._calculate_camelot_num(number, -3)
            return [f"{target_num}B"]
        else: # From Major XB to (X+3)A
            target_num = cls._calculate_camelot_num(number, +3)
            return [f"{target_num}A"]

    @classmethod
    def get_energy_boost_keys(cls, camelot_code: str, boost_amount: int = 2) -> List[str]:
        """Saltos Energéticos (Ej: 8A → 10A, salto de +2)"""
        if not camelot_code or camelot_code not in cls.POSITIONS:
            return []
        number = int(camelot_code[:-1])
        mode = camelot_code[-1]
        
        target_num = cls._calculate_camelot_num(number, boost_amount)
        return [f"{target_num}{mode}"]

    @classmethod
    def get_dominant_subdominant_keys(cls, camelot_code: str) -> List[str]:
        """Mezcla de Cuarta (+5 num) o Quinta (-5 num) (Ej: 8A → 1A o 3A)"""
        if not camelot_code or camelot_code not in cls.POSITIONS:
            return []
        number = int(camelot_code[:-1])
        mode = camelot_code[-1]
        
        # Quinta (Dominante): +7 semitonos = +1 en rueda, pero el user rule es +5 números (subdominante de la subdominante?)
        # Cuarta (Subdominante): +5 semitonos = -1 en rueda (o +11), pero el user rule es -5 números
        # Vamos a usar los saltos numéricos literales de la regla del usuario: +5 y -5 números.
        
        key_plus_5 = f"{cls._calculate_camelot_num(number, +5)}{mode}"
        key_minus_5 = f"{cls._calculate_camelot_num(number, -5)}{mode}"
        
        return list(set([key_plus_5, key_minus_5]))

    @classmethod
    def get_inverse_camelot_keys(cls, camelot_code: str) -> List[str]:
        """Camelot Inverso (Ej: 8A → 2B, salto de +6 con cambio de modo)"""
        if not camelot_code or camelot_code not in cls.POSITIONS:
            return []
        number = int(camelot_code[:-1])
        mode = camelot_code[-1]
        opposite_mode = 'B' if mode == 'A' else 'A'
        
        target_num = cls._calculate_camelot_num(number, +6)
        return [f"{target_num}{opposite_mode}"]

    @classmethod
    def get_harmonic_cadence_keys(cls, camelot_code: str) -> List[str]:
        """Cadencia Armónica: Progresiones como I-V-vi-IV (Ej: 8A → 3A → 6A → 1A)"""
        if not camelot_code or camelot_code not in cls.POSITIONS:
            return []
        number = int(camelot_code[:-1])
        mode = camelot_code[-1]
        
        # Progresión I-V-vi-IV en términos de Camelot (aproximación)
        # V = +5, vi = +3, IV = -2 (en términos de números Camelot)
        cadence_keys = []
        cadence_keys.append(f"{cls._calculate_camelot_num(number, +5)}{mode}")  # V
        cadence_keys.append(f"{cls._calculate_camelot_num(number, +3)}{mode}")  # vi
        cadence_keys.append(f"{cls._calculate_camelot_num(number, -2)}{mode}")  # IV
        
        return cadence_keys

    @classmethod
    def get_pendular_mix_keys(cls, camelot_code: str) -> List[str]:
        """Mezcla Pendular: Claves que permiten movimientos de ida y vuelta"""
        if not camelot_code or camelot_code not in cls.POSITIONS:
            return []
        number = int(camelot_code[:-1])
        mode = camelot_code[-1]
        opposite_mode = 'B' if mode == 'A' else 'A'
        
        # Claves que permiten "rebotar": adyacentes y sus cambios de modo
        pendular_keys = []
        prev_num = cls._calculate_camelot_num(number, -1)
        next_num = cls._calculate_camelot_num(number, +1)
        
        # Adyacentes en mismo modo y modo opuesto para crear "rebote"
        pendular_keys.extend([
            f"{prev_num}{mode}", f"{next_num}{mode}",
            f"{prev_num}{opposite_mode}", f"{next_num}{opposite_mode}"
        ])
        
        return pendular_keys

    @classmethod
    def get_key_overlay_keys(cls, camelot_code: str) -> List[str]:
        """Superposición de Claves: Claves que suenan bien simultáneamente"""
        if not camelot_code or camelot_code not in cls.POSITIONS:
            return []
        number = int(camelot_code[:-1])
        mode = camelot_code[-1]
        
        # Quintas perfectas y octavas (en términos de Camelot)
        overlay_keys = []
        # Quinta perfecta: +7 semitonos ≈ +1 en Camelot
        overlay_keys.append(f"{cls._calculate_camelot_num(number, +1)}{mode}")
        overlay_keys.append(f"{cls._calculate_camelot_num(number, -1)}{mode}")
        
        # Octava (misma nota): cambio de modo
        opposite_mode = 'B' if mode == 'A' else 'A'
        overlay_keys.append(f"{number}{opposite_mode}")
        
        return overlay_keys

    @classmethod
    def get_phrase_mix_keys(cls, camelot_code: str) -> List[str]:
        """Mezcla por Fraseo: Basada en estructura musical"""
        if not camelot_code or camelot_code not in cls.POSITIONS:
            return []
        number = int(camelot_code[:-1])
        mode = camelot_code[-1]
        
        # Similar a estándar pero con énfasis en transiciones suaves
        # Incluye adyacentes y saltos de tercera
        phrase_keys = []
        phrase_keys.extend([
            f"{cls._calculate_camelot_num(number, -1)}{mode}",
            f"{cls._calculate_camelot_num(number, +1)}{mode}",
            f"{cls._calculate_camelot_num(number, +3)}{mode}",
            f"{cls._calculate_camelot_num(number, -3)}{mode}"
        ])
        
        return phrase_keys

    @classmethod
    def get_hot_cues_keys(cls, camelot_code: str) -> List[str]:
        """Hot Cues y Loops: Técnica de DJ para transiciones rápidas"""
        if not camelot_code or camelot_code not in cls.POSITIONS:
            return []
        number = int(camelot_code[:-1])
        mode = camelot_code[-1]
        opposite_mode = 'B' if mode == 'A' else 'A'
        
        # Claves que permiten cortes y loops efectivos
        # Incluye misma clave, cambio de modo, y saltos de cuarta
        hot_cues_keys = []
        hot_cues_keys.extend([
            f"{number}{opposite_mode}",  # Cambio de modo para loops
            f"{cls._calculate_camelot_num(number, +4)}{mode}",  # Salto de cuarta
            f"{cls._calculate_camelot_num(number, -4)}{mode}"   # Salto de cuarta inverso
        ])
        
        return hot_cues_keys

    @classmethod
    def get_modulation_mix_keys(cls, camelot_code: str) -> List[str]:
        """Mezcla por Modulación: Transiciones graduales y modulaciones"""
        if not camelot_code or camelot_code not in cls.POSITIONS:
            return []
        number = int(camelot_code[:-1])
        mode = camelot_code[-1]
        opposite_mode = 'B' if mode == 'A' else 'A'
        
        # Modulaciones cromáticas y por tonos enteros
        modulation_keys = []
        # Modulación cromática: +/-1 semitono (aproximado en Camelot)
        modulation_keys.extend([
            f"{cls._calculate_camelot_num(number, +1)}{opposite_mode}",
            f"{cls._calculate_camelot_num(number, -1)}{opposite_mode}"
        ])
        
        # Modulación por tonos enteros: +/-2
        modulation_keys.extend([
            f"{cls._calculate_camelot_num(number, +2)}{opposite_mode}",
            f"{cls._calculate_camelot_num(number, -2)}{opposite_mode}"
        ])
        
        return modulation_keys

    @classmethod
    def get_ascending_energy_keys(cls, camelot_code: str) -> List[str]:
        """Energía Ascendente: Progresión sistemática hacia arriba"""
        if not camelot_code or camelot_code not in cls.POSITIONS:
            return []
        number = int(camelot_code[:-1])
        mode = camelot_code[-1]
        
        # Progresión ascendente: +1, +2, +3, +4
        ascending_keys = []
        for i in range(1, 5):
            ascending_keys.append(f"{cls._calculate_camelot_num(number, +i)}{mode}")
        
        return ascending_keys

    @classmethod
    def get_all_defined_compatible_keys(cls, camelot_code: str, active_techniques: List[str]) -> List[str]:
        """Retorna una lista de todas las keys compatibles según las técnicas activas."""
        if not camelot_code or not cls.CAMELOT_MAP.get(cls.to_musical_key(camelot_code)) == camelot_code:
             # Validar que camelot_code sea un código válido en nuestra lista
            return []
            
        all_keys = set()

        # Técnicas básicas (1-8)
        if "standard" in active_techniques:
            all_keys.update(cls.get_standard_compatible_keys(camelot_code))
        if "relative_mix" in active_techniques: # Rule 4: 8A -> 5B or 8B -> 11A
            all_keys.update(cls.get_relative_mix_keys(camelot_code))
        if "energy_boost_2" in active_techniques: # Rule 5: 8A -> 10A (+2)
            all_keys.update(cls.get_energy_boost_keys(camelot_code, boost_amount=2))
        if "energy_de_escalate_2" in active_techniques: # Similar a Rule 5, pero -2
            all_keys.update(cls.get_energy_boost_keys(camelot_code, boost_amount=-2))
        if "dominant_subdominant_jump" in active_techniques: # Rule 7: 8A -> 1A (+5), 8A -> 3A (-5)
            all_keys.update(cls.get_dominant_subdominant_keys(camelot_code))
        if "inverse" in active_techniques: # Rule 8: 8A -> 2B (+6 opp mode)
            all_keys.update(cls.get_inverse_camelot_keys(camelot_code))
        
        # Técnicas avanzadas (9-15)
        if "harmonic_cadence" in active_techniques: # Rule 9: Cadencia Armónica
            all_keys.update(cls.get_harmonic_cadence_keys(camelot_code))
        if "pendular_mix" in active_techniques: # Rule 10: Mezcla Pendular
            all_keys.update(cls.get_pendular_mix_keys(camelot_code))
        if "key_overlay" in active_techniques: # Rule 11: Superposición de Claves
            all_keys.update(cls.get_key_overlay_keys(camelot_code))
        if "phrase_mix" in active_techniques: # Rule 12: Mezcla por Fraseo
            all_keys.update(cls.get_phrase_mix_keys(camelot_code))
        if "hot_cues" in active_techniques: # Rule 13: Hot Cues y Loops
            all_keys.update(cls.get_hot_cues_keys(camelot_code))
        if "modulation_mix" in active_techniques: # Rule 14: Mezcla por Modulación
            all_keys.update(cls.get_modulation_mix_keys(camelot_code))
        if "ascending_energy" in active_techniques: # Rule 15: Energía Ascendente
            all_keys.update(cls.get_ascending_energy_keys(camelot_code))

        # Eliminar la propia clave seleccionada si se coló
        all_keys.discard(camelot_code)
        return sorted(list(all_keys), key=lambda k: (int(k[:-1]), k[-1]))


class CamelotWheelWidget(QWidget):
    """Widget interactivo de la Rueda Camelot."""
    
    # Señales
    key_selected = pyqtSignal(str)  # Emite el código Camelot seleccionado
    compatible_keys_changed = pyqtSignal(list)  # Emite lista de keys compatibles
    
    # Añadir un atributo para almacenar las técnicas activas que le pasará el panel
    active_techniques_for_highlight: List[str] = ["standard"] # Default a standard
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.selected_key = None
        self.highlighted_keys = set()
        self.show_compatible = True
        self.active_techniques_for_highlight = ["standard"] # Inicializar
        
        # Colores
        self.color_minor = QColor(100, 150, 255)  # Azul para menores (A)
        self.color_major = QColor(255, 150, 100)  # Naranja para mayores (B)
        self.color_selected = QColor(255, 255, 0)  # Amarillo para seleccionado
        self.color_compatible = QColor(150, 255, 150)  # Verde para compatibles
        self.color_text = QColor(0, 0, 0)
        self.color_border = QColor(50, 50, 50)
        
    def paintEvent(self, event):
        """Dibuja la rueda Camelot."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calcular dimensiones
        size = min(self.width(), self.height()) - 40
        center_x = self.width() // 2
        center_y = self.height() // 2
        outer_radius = size // 2
        inner_radius = outer_radius * 0.6
        
        # Dibujar cada segmento de la rueda
        for i in range(1, 13):
            angle_start = (i - 1) * 30 - 90  # -90 para empezar en 12 o'clock
            
            # Dibujar segmento menor (A) - anillo exterior
            self._draw_segment(painter, center_x, center_y, inner_radius, outer_radius,
                             angle_start, 30, f"{i}A")
            
            # Dibujar segmento mayor (B) - anillo interior
            self._draw_segment(painter, center_x, center_y, inner_radius * 0.4, inner_radius,
                             angle_start, 30, f"{i}B")
        
        # Dibujar centro con información
        self._draw_center_info(painter, center_x, center_y, inner_radius * 0.4)
    
    def _draw_segment(self, painter: QPainter, center_x: int, center_y: int,
                     inner_r: float, outer_r: float, start_angle: float, 
                     span_angle: float, camelot_code: str):
        """Dibuja un segmento individual de la rueda."""
        
        # Determinar color del segmento
        if camelot_code == self.selected_key:
            color = self.color_selected
        elif camelot_code in self.highlighted_keys and self.show_compatible:
            color = self.color_compatible
        elif camelot_code.endswith('A'):
            color = self.color_minor
        else:
            color = self.color_major
        
        # Crear el segmento como polígono
        polygon = QPolygon()
        
        # Convertir ángulos a radianes
        start_rad = math.radians(start_angle)
        end_rad = math.radians(start_angle + span_angle)
        
        # Puntos del arco exterior
        steps = 10
        for i in range(steps + 1):
            angle = start_rad + (end_rad - start_rad) * i / steps
            x = center_x + outer_r * math.cos(angle)
            y = center_y + outer_r * math.sin(angle)
            polygon.append(QPoint(int(x), int(y)))
        
        # Puntos del arco interior (en reversa)
        for i in range(steps, -1, -1):
            angle = start_rad + (end_rad - start_rad) * i / steps
            x = center_x + inner_r * math.cos(angle)
            y = center_y + inner_r * math.sin(angle)
            polygon.append(QPoint(int(x), int(y)))
        
        # Dibujar el segmento
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(self.color_border, 2))
        painter.drawPolygon(polygon)
        
        # Dibujar texto del código Camelot
        text_angle = start_angle + span_angle / 2
        text_radius = (inner_r + outer_r) / 2
        text_x = center_x + text_radius * math.cos(math.radians(text_angle))
        text_y = center_y + text_radius * math.sin(math.radians(text_angle))
        
        painter.setPen(QPen(self.color_text))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        # Centrar el texto
        text_rect = QRect(int(text_x - 15), int(text_y - 10), 30, 20)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, camelot_code)
        
        # Mostrar tonalidad musical si hay espacio
        musical_key = CamelotKey.to_musical_key(camelot_code)
        if musical_key and outer_r > 80:  # Solo si hay espacio suficiente
            painter.setFont(QFont("Arial", 8))
            musical_rect = QRect(int(text_x - 15), int(text_y + 5), 30, 15)
            painter.drawText(musical_rect, Qt.AlignmentFlag.AlignCenter, musical_key)
    
    def _draw_center_info(self, painter: QPainter, center_x: int, center_y: int, radius: float):
        """Dibuja información en el centro de la rueda."""
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.setPen(QPen(self.color_border, 2))
        painter.drawEllipse(QPoint(center_x, center_y), int(radius), int(radius))
        
        if self.selected_key:
            musical_key = CamelotKey.to_musical_key(self.selected_key)
            painter.setPen(QPen(self.color_text))
            painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            
            # Código Camelot
            text_rect = QRect(center_x - 30, center_y - 20, 60, 20)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.selected_key)
            
            # Tonalidad musical
            if musical_key:
                painter.setFont(QFont("Arial", 10))
                musical_rect = QRect(center_x - 30, center_y, 60, 20)
                painter.drawText(musical_rect, Qt.AlignmentFlag.AlignCenter, musical_key)
        else:
            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.setFont(QFont("Arial", 10))
            text_rect = QRect(center_x - 40, center_y - 10, 80, 20)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "Selecciona una key")
    
    def mousePressEvent(self, event: QMouseEvent):
        """Maneja clics del mouse para seleccionar tonalidades."""
        if event.button() == Qt.MouseButton.LeftButton:
            clicked_key = self._get_key_at_position(event.position().x(), event.position().y())
            if clicked_key:
                self.select_key(clicked_key)
    
    def _get_key_at_position(self, x: float, y: float) -> Optional[str]:
        """Determina qué tonalidad está en la posición dada."""
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Calcular distancia y ángulo desde el centro
        dx = x - center_x
        dy = y - center_y
        distance = math.sqrt(dx * dx + dy * dy)
        angle = math.degrees(math.atan2(dy, dx)) + 90  # +90 para ajustar a 12 o'clock
        
        if angle < 0:
            angle += 360
        
        # Determinar radio para A o B
        size = min(self.width(), self.height()) - 40
        outer_radius = size // 2
        inner_radius = outer_radius * 0.6
        center_radius = inner_radius * 0.4
        
        # Determinar si es A (exterior) o B (interior)
        if distance < center_radius:
            return None  # Centro
        elif distance < inner_radius:
            mode = 'B'
        elif distance < outer_radius:
            mode = 'A'
        else:
            return None  # Fuera de la rueda
        
        # Determinar número (1-12) basado en el ángulo
        segment = int((angle + 15) // 30) + 1  # +15 para centrar en segmentos
        if segment > 12:
            segment = 1
        
        return f"{segment}{mode}"
    
    def select_key(self, camelot_code: str):
        """Selecciona una tonalidad y actualiza las compatibles."""
        if camelot_code == self.selected_key:
            self.selected_key = None
        else:
            self.selected_key = camelot_code
        
        self._update_highlighted_keys() 
        self.update() 
        
        if self.selected_key:
            self.key_selected.emit(self.selected_key)
            self.compatible_keys_changed.emit(list(self.highlighted_keys))
        else:
            self.key_selected.emit("")
            self.compatible_keys_changed.emit([])

    def _update_highlighted_keys(self):
        """Actualiza las tonalidades resaltadas basado en la selección y técnicas activas."""
        if not self.selected_key or not self.show_compatible:
            self.highlighted_keys.clear()
        else:
            # Usar self.active_techniques_for_highlight que es configurado por el panel
            self.highlighted_keys = set(CamelotKey.get_all_defined_compatible_keys(
                self.selected_key, 
                self.active_techniques_for_highlight 
            ))
        self.update() # Asegurar redibujado si los resaltados cambian

    def set_active_techniques(self, techniques: List[str]):
        """Configura las técnicas activas para resaltar (llamado por el panel)."""
        self.active_techniques_for_highlight = techniques
        self._update_highlighted_keys() # Re-calcular y redibujar

    def set_show_compatible(self, show: bool):
        """Activa/desactiva la visualización de tonalidades compatibles."""
        self.show_compatible = show
        self._update_highlighted_keys()

    def clear_selection(self):
        """Limpia la selección actual."""
        self.selected_key = None
        self._update_highlighted_keys()
        # self.update() # _update_highlighted_keys ya llama a update()


class CamelotWheelPanel(QWidget):
    """Panel completo con la rueda Camelot y controles."""
    
    # Señales
    filter_by_key = pyqtSignal(str)  # Para filtrar playlists por tonalidad
    filter_by_compatible = pyqtSignal(list)  # Para filtrar por compatibles
    active_techniques_changed = pyqtSignal(list) # Emite lista de técnicas activas
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.technique_checkboxes = {} # Para almacenar los checkboxes de técnicas
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del panel."""
        main_layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("🎵 Rueda Camelot Interactiva")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Widget de la rueda
        self.wheel = CamelotWheelWidget()
        main_layout.addWidget(self.wheel)
        
        # --- Grupo de Controles ---
        controls_groupbox = QGroupBox("Controles y Técnicas de Mezcla")
        controls_main_layout = QVBoxLayout(controls_groupbox)

        # Checkbox general para mostrar compatibles
        self.show_compatible_cb = QCheckBox("Resaltar tonalidades compatibles")
        self.show_compatible_cb.setChecked(True)
        self.show_compatible_cb.toggled.connect(self.wheel.set_show_compatible)
        # Conectar también a _on_technique_change para que se actualicen las técnicas de la rueda si se desactiva el resaltado
        self.show_compatible_cb.toggled.connect(self._on_technique_or_show_compatible_change)
        controls_main_layout.addWidget(self.show_compatible_cb)

        # Sub-grupo para técnicas de mezcla
        techniques_groupbox = QGroupBox("Técnicas de Mezcla Armónica Activas")
        techniques_layout = QVBoxLayout(techniques_groupbox)

        self.technique_checkboxes = {
            # Técnicas básicas (1-8)
            "standard": QCheckBox("1-3,6. Estándar (Adyacentes, Mismo Número, Diagonales)"),
            "relative_mix": QCheckBox("4. Relativa Alternativa (Ej: 8A → 5B / 8B → 11A)"),
            "energy_boost_2": QCheckBox("5. Salto Energético +2 (Ej: 8A → 10A)"),
            "energy_de_escalate_2": QCheckBox("5. Salto Energético -2 (Ej: 8A → 6A)"),
            "dominant_subdominant_jump": QCheckBox("7. Salto Dom/Subdominante +/-5 (Ej: 8A → 1A/3A)"),
            "inverse": QCheckBox("8. Camelot Inverso +6 (Ej: 8A → 2B)"),
            
            # Técnicas avanzadas (9-15)
            "harmonic_cadence": QCheckBox("9. Cadencia Armónica (I-V-vi-IV)"),
            "pendular_mix": QCheckBox("10. Mezcla Pendular (Movimientos ida y vuelta)"),
            "key_overlay": QCheckBox("11. Superposición de Claves (Quintas, Octavas)"),
            "phrase_mix": QCheckBox("12. Mezcla por Fraseo (Estructura musical)"),
            "hot_cues": QCheckBox("13. Hot Cues y Loops (Transiciones rápidas)"),
            "modulation_mix": QCheckBox("14. Mezcla por Modulación (Cromática, tonos enteros)"),
            "ascending_energy": QCheckBox("15. Energía Ascendente (Progresión +1,+2,+3,+4)")
        }
        
        self.technique_checkboxes["standard"].setChecked(True) # Estándar por defecto

        for tech_name, checkbox in self.technique_checkboxes.items():
            checkbox.toggled.connect(self._on_technique_or_show_compatible_change)
            techniques_layout.addWidget(checkbox)
        
        controls_main_layout.addWidget(techniques_groupbox)
        
        # Botones de acción
        action_buttons_layout = QHBoxLayout()
        
        self.filter_btn = QPushButton("Filtrar por Tonalidad Seleccionada")
        self.filter_btn.setEnabled(False)
        self.filter_btn.clicked.connect(self._filter_by_selected)
        action_buttons_layout.addWidget(self.filter_btn)
        
        self.filter_compatible_btn = QPushButton("Filtrar por Todas las Compatibles Resaltadas")
        self.filter_compatible_btn.setEnabled(False)
        self.filter_compatible_btn.clicked.connect(self._filter_by_all_compatible)
        action_buttons_layout.addWidget(self.filter_compatible_btn)
        
        self.clear_btn = QPushButton("Limpiar Selección")
        self.clear_btn.clicked.connect(self._clear_selection)
        action_buttons_layout.addWidget(self.clear_btn)
        
        controls_main_layout.addLayout(action_buttons_layout)
        
        # Información de la selección
        self.info_label = QLabel("Selecciona una tonalidad en la rueda para ver información.")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc; min-height: 60px;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        controls_main_layout.addWidget(self.info_label)
        
        main_layout.addWidget(controls_groupbox)
        
        # Conectar señales de la rueda al panel
        self.wheel.key_selected.connect(self._on_key_selected_on_wheel)
        self.wheel.compatible_keys_changed.connect(self._on_compatible_keys_changed_on_wheel)
        
        self._update_wheel_active_techniques() # Configuración inicial de técnicas en la rueda

    def get_active_techniques(self) -> List[str]:
        """Obtiene la lista de nombres de técnicas activas desde los checkboxes."""
        return [tech_name for tech_name, checkbox in self.technique_checkboxes.items() if checkbox.isChecked()]

    def _update_wheel_active_techniques(self):
        """Pasa la lista actual de técnicas activas al widget de la rueda."""
        active_techs = self.get_active_techniques()
        self.wheel.set_active_techniques(active_techs)
        self.active_techniques_changed.emit(active_techs) # Emitir para observadores externos

    def _on_technique_or_show_compatible_change(self):
        """Se llama cuando cambia cualquier checkbox de técnica o el de mostrar compatibles."""
        self._update_wheel_active_techniques()
        # Si hay una clave seleccionada, forzar la actualización de la info label
        if self.wheel.selected_key:
            self._on_key_selected_on_wheel(self.wheel.selected_key)
        else: # Asegurar que los botones se deshabiliten si no hay selección
            self._on_key_selected_on_wheel("")

    def _on_key_selected_on_wheel(self, camelot_code: str):
        """Maneja la selección de una tonalidad en el widget de la rueda."""
        if camelot_code:
            musical_key = CamelotKey.to_musical_key(camelot_code)
            # Las compatibles ya están calculadas por la rueda con las técnicas activas
            # y se obtienen de self.wheel.highlighted_keys
            highlighted_compatible_codes = sorted(list(self.wheel.highlighted_keys),
                                                 key=lambda k: (int(k[:-1]), k[-1]))
            
            highlighted_musical_keys = [CamelotKey.to_musical_key(k) for k in highlighted_compatible_codes]
            highlighted_musical_keys_str = \
                f" ({', '.join(filter(None, highlighted_musical_keys))})" if any(highlighted_musical_keys) else ""

            info_text = f"""
<b>Tonalidad Seleccionada:</b> {camelot_code} ({musical_key})<br>
<b>Compatibles Resaltadas ({len(highlighted_compatible_codes)}):</b> {', '.join(highlighted_compatible_codes)}
{highlighted_musical_keys_str}
            """.strip()
            
            self.info_label.setText(info_text)
            self.filter_btn.setEnabled(True)
            self.filter_compatible_btn.setEnabled(len(highlighted_compatible_codes) > 0)
        else:
            self.info_label.setText("Selecciona una tonalidad en la rueda para ver información.")
            self.filter_btn.setEnabled(False)
            self.filter_compatible_btn.setEnabled(False)
    
    def _on_compatible_keys_changed_on_wheel(self, compatible_keys: List[str]):
        """Maneja cambios en las tonalidades compatibles resaltadas por la rueda."""
        # Esta señal de la rueda ahora es más un reflejo de que sus highlighted_keys cambiaron.
        # El estado del botón y la info label se manejan mejor en _on_key_selected_on_wheel
        # y _on_technique_or_show_compatible_change para asegurar consistencia.
        # No obstante, podríamos querer actualizar algo específico aquí si fuera necesario.
        pass # Dejar vacío por ahora, ya que la lógica principal está en otros métodos.

    def _filter_by_selected(self):
        """Filtra por la tonalidad seleccionada actualmente en la rueda."""
        if self.wheel.selected_key:
            musical_key = CamelotKey.to_musical_key(self.wheel.selected_key)
            if musical_key:
                self.filter_by_key.emit(musical_key) # Emitir tonalidad musical
    
    def _filter_by_all_compatible(self):
        """Filtra por TODAS las tonalidades compatibles actualmente resaltadas en la rueda."""
        if self.wheel.selected_key and self.wheel.highlighted_keys:
            musical_keys = [CamelotKey.to_musical_key(k) for k in self.wheel.highlighted_keys]
            musical_keys = [k for k in musical_keys if k]  # Filtrar None
            if musical_keys:
                self.filter_by_compatible.emit(musical_keys) # Emitir lista de tonalidades musicales
    
    def _clear_selection(self):
        """Limpia la selección en la rueda y actualiza la UI del panel."""
        self.wheel.clear_selection()
        # _on_key_selected_on_wheel se llamará con "" y actualizará la UI.


# Ejemplo de uso y prueba
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Crear ventana de prueba
    window = QWidget()
    window.setWindowTitle("Rueda Camelot - Prueba")
    window.setGeometry(100, 100, 600, 700)
    
    layout = QVBoxLayout(window)
    
    # Añadir panel de Camelot
    camelot_panel = CamelotWheelPanel()
    layout.addWidget(camelot_panel)
    
    # Conectar señales para prueba
    def on_filter_key(key):
        print(f"Filtrar por tonalidad: {key}")
    
    def on_filter_compatible(keys):
        print(f"Filtrar por compatibles: {keys}")
    
    camelot_panel.filter_by_key.connect(on_filter_key)
    camelot_panel.filter_by_compatible.connect(on_filter_compatible)
    
    window.show()
    sys.exit(app.exec()) 
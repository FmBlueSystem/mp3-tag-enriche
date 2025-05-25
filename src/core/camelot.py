"""
Sistema de notación musical Camelot y reglas de compatibilidad armónica.
"""

from typing import Dict, List, Set, Optional, Tuple
from enum import Enum

class CompatibilityMode(Enum):
    """Modos de compatibilidad entre claves musicales."""
    PERFECT = "perfect"       # Misma clave
    ENERGY_UP = "energy_up"   # Siguiente clave (+1)
    ENERGY_DOWN = "energy_down" # Clave anterior (-1)
    HARMONIC = "harmonic"     # Clave relativa (+7)
    CUSTOM = "custom"         # Personalizado

class CamelotWheel:
    """
    Implementación de la rueda Camelot para notación musical
    y análisis de compatibilidad armónica.
    """
    
    def __init__(self):
        # Mapa de notación Camelot a notación musical tradicional
        self.camelot_map: Dict[str, str] = {
            # Claves mayores (A)
            "1A": "G♭ maj",  "2A": "D♭ maj",  "3A": "A♭ maj",  "4A": "E♭ maj",
            "5A": "B♭ maj",  "6A": "F maj",   "7A": "C maj",   "8A": "G maj",
            "9A": "D maj",   "10A": "A maj",  "11A": "E maj",  "12A": "B maj",
            
            # Claves menores (B)
            "1B": "E♭ min",  "2B": "B♭ min",  "3B": "F min",   "4B": "C min",
            "5B": "G min",   "6B": "D min",   "7B": "A min",   "8B": "E min",
            "9B": "B min",   "10B": "F♯ min", "11B": "C♯ min", "12B": "G♯ min"
        }
        
        # Mapa inverso: notación musical a Camelot
        self.reverse_map = {v: k for k, v in self.camelot_map.items()}
        
        # Reglas de compatibilidad por defecto
        self.compatibility_rules = {
            CompatibilityMode.PERFECT: [0],      # Misma clave
            CompatibilityMode.ENERGY_UP: [1],    # Siguiente clave
            CompatibilityMode.ENERGY_DOWN: [-1], # Clave anterior
            CompatibilityMode.HARMONIC: [7]     # Clave relativa
        }
        
        # Cache de compatibilidad
        self._compatibility_cache: Dict[str, Dict[CompatibilityMode, Set[str]]] = {}
        
    def get_camelot_key(self, musical_key: str) -> Optional[str]:
        """
        Convierte una clave musical a notación Camelot.
        
        Args:
            musical_key: Clave en notación musical (ej: "C maj", "Am")
            
        Returns:
            Clave en notación Camelot o None si no es válida
        """
        # Normalizar notación
        key = self._normalize_key(musical_key)
        return self.reverse_map.get(key)
        
    def get_musical_key(self, camelot_key: str) -> Optional[str]:
        """
        Convierte una clave Camelot a notación musical.
        
        Args:
            camelot_key: Clave en notación Camelot (ej: "8A", "8B")
            
        Returns:
            Clave en notación musical o None si no es válida
        """
        return self.camelot_map.get(camelot_key)
        
    def get_compatible_keys(
        self,
        key: str,
        mode: CompatibilityMode = CompatibilityMode.PERFECT
    ) -> Set[str]:
        """
        Retorna las claves compatibles según el modo especificado.
        
        Args:
            key: Clave en notación Camelot o musical
            mode: Modo de compatibilidad a usar
            
        Returns:
            Set de claves compatibles en la misma notación que la entrada
        """
        # Verificar cache
        cache_key = f"{key}:{mode.value}"
        if cache_key in self._compatibility_cache:
            return self._compatibility_cache[cache_key]
            
        # Convertir a Camelot si es necesario
        camelot_key = key if key in self.camelot_map else self.get_camelot_key(key)
        if not camelot_key:
            return set()
            
        # Obtener número y modo (A/B)
        number = int(camelot_key[:-1])
        letter = camelot_key[-1]
        
        # Calcular claves compatibles
        compatible = set()
        rules = self.compatibility_rules[mode]
        
        for offset in rules:
            # Calcular nueva posición (1-12)
            new_number = ((number + offset - 1) % 12) + 1
            new_key = f"{new_number}{letter}"
            
            # Agregar clave compatible
            if new_key in self.camelot_map:
                # Convertir al mismo formato que la entrada
                if key in self.camelot_map:
                    compatible.add(new_key)
                else:
                    musical_key = self.get_musical_key(new_key)
                    if musical_key:
                        compatible.add(musical_key)
                        
        # Guardar en cache
        self._compatibility_cache[cache_key] = compatible
        return compatible
        
    def get_key_info(self, key: str) -> Dict[str, str]:
        """
        Retorna información detallada sobre una clave.
        
        Args:
            key: Clave en notación Camelot o musical
            
        Returns:
            Dict con información de la clave
        """
        # Obtener ambas notaciones
        camelot_key = key if key in self.camelot_map else self.get_camelot_key(key)
        musical_key = key if key in self.reverse_map else self.get_musical_key(key)
        
        if not (camelot_key and musical_key):
            return {}
            
        # Analizar clave
        number = int(camelot_key[:-1])
        letter = camelot_key[-1]
        is_major = letter == 'A'
        
        # Obtener claves compatibles
        compatible = {
            mode.value: self.get_compatible_keys(camelot_key, mode)
            for mode in CompatibilityMode
            if mode != CompatibilityMode.CUSTOM
        }
        
        return {
            "camelot_key": camelot_key,
            "musical_key": musical_key,
            "number": number,
            "is_major": is_major,
            "mode": "Major" if is_major else "Minor",
            "compatible_keys": compatible
        }
        
    def add_custom_rule(self, offsets: List[int]):
        """
        Agrega una regla de compatibilidad personalizada.
        
        Args:
            offsets: Lista de desplazamientos para encontrar claves compatibles
        """
        self.compatibility_rules[CompatibilityMode.CUSTOM] = offsets
        self._compatibility_cache.clear()  # Invalidar cache
        
    @staticmethod
    def _normalize_key(key: str) -> str:
        """
        Normaliza la notación de una clave musical.
        
        Args:
            key: Clave a normalizar
            
        Returns:
            Clave normalizada
        """
        # Reemplazar notación alternativa
        replacements = {
            "maj": " maj", "min": " min",
            "M": " maj", "m": " min",
            "Major": " maj", "Minor": " min"
        }
        
        result = key
        for old, new in replacements.items():
            result = result.replace(old, new)
            
        return result.strip()
        
    def __str__(self) -> str:
        """Representación string de la rueda Camelot."""
        wheel = []
        for i in range(1, 13):
            major = self.camelot_map.get(f"{i}A", "")
            minor = self.camelot_map.get(f"{i}B", "")
            wheel.append(f"{i}A: {major:<8} {i}B: {minor:<8}")
        return "\n".join(wheel)

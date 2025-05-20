"""Internationalization support for the GUI."""
from pathlib import Path
from typing import Dict, Any, Optional, Union
import json
import os
import re
from functools import reduce

class PluralRules:
    """Reglas de pluralización por idioma."""
    
    @staticmethod
    def get_plural_form(lang_code: str, count: int) -> str:
        """Determina la forma plural correcta según el idioma y cantidad."""
        if lang_code == "es":
            return "plural" if count != 1 else "singular"
        # Por defecto usar reglas del inglés
        return "plural" if count != 1 else "singular"

class TranslationManager:
    """Gestor de traducciones para la aplicación."""
    
    def __init__(self):
        self.current_language = "en"  # Default to English
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.fallback_language = "en"
        self._load_translations()
    
    def _load_translations(self):
        """Carga todos los archivos de traducción."""
        translation_dir = Path(__file__).parent / "translations"
        if not translation_dir.exists():
            os.makedirs(translation_dir)
            
        for lang_file in translation_dir.glob("*.json"):
            lang_code = lang_file.stem
            with open(lang_file, "r", encoding="utf-8") as f:
                self.translations[lang_code] = json.load(f)

    def set_language(self, lang_code: str):
        """Establece el idioma actual."""
        if lang_code in self.translations:
            self.current_language = lang_code
        else:
            raise ValueError(f"Idioma {lang_code} no soportado")

    def _get_nested_value(self, data: Dict[str, Any], key_path: str) -> Optional[Any]:
        """Obtiene un valor anidado usando notación de puntos."""
        try:
            return reduce(lambda d, k: d[k], key_path.split("."), data)
        except (KeyError, TypeError):
            return None

    def _interpolate(self, text: str, params: Dict[str, Any]) -> str:
        """Realiza interpolación de texto con parámetros nombrados."""
        if not params:
            return text
            
        # Soporte para el formato antiguo {0}, {1}, etc
        if re.search(r'\{[0-9]+\}', text):
            try:
                return text.format(*params)
            except (IndexError, KeyError):
                return text
                
        # Soporte para el nuevo formato con nombres {name}, {count}, etc
        for key, value in params.items():
            pattern = "{" + key + "}"
            text = text.replace(pattern, str(value))
        return text

    def get_text(self, key: str, params: Optional[Union[Dict[str, Any], tuple]] = None) -> str:
        """
        Obtiene el texto traducido para una clave con soporte para parámetros.
        
        Args:
            key: Clave de traducción usando notación de puntos (ej: "ui.buttons.save")
            params: Diccionario de parámetros para interpolación o tupla para formato antiguo
            
        Returns:
            Texto traducido con parámetros interpolados
        """
        # Convertir tupla a diccionario si es necesario (compatibilidad)
        if isinstance(params, tuple):
            params = {str(i): v for i, v in enumerate(params)}
        elif params is None:
            params = {}

        # Intentar obtener traducción en el idioma actual
        value = self._get_nested_value(self.translations.get(self.current_language, {}), key)
        
        # Si no se encuentra, intentar en el idioma de fallback
        if value is None and self.current_language != self.fallback_language:
            value = self._get_nested_value(self.translations.get(self.fallback_language, {}), key)
        
        # Si aún no se encuentra, usar la clave como fallback
        if value is None:
            return key
            
        # Si el valor es un diccionario (ej: para plurales), usar la forma apropiada
        if isinstance(value, dict) and "singular" in value and "plural" in value:
            count = params.get("count", 0)
            plural_form = PluralRules.get_plural_form(self.current_language, count)
            value = value.get(plural_form, value.get("singular", key))
            
        return self._interpolate(str(value), params)

    def get_raw(self, key: str) -> Any:
        """
        Obtiene el valor sin procesar de una clave de traducción.
        Útil para obtener estructuras completas como diccionarios.
        """
        return self._get_nested_value(self.translations.get(self.current_language, {}), key)

# Instancia global del gestor de traducciones
_manager = TranslationManager()

def tr(key: str, params: Optional[Union[Dict[str, Any], tuple]] = None) -> str:
    """
    Obtiene el texto traducido para una clave.
    
    Args:
        key: Clave de traducción usando notación de puntos
        params: Parámetros para interpolación (dict o tuple)
        
    Returns:
        Texto traducido
    """
    return _manager.get_text(key, params)

def get_raw(key: str) -> Any:
    """Obtiene el valor sin procesar de una clave de traducción."""
    return _manager.get_raw(key)

def set_language(lang_code: str):
    """Establece el idioma actual."""
    _manager.set_language(lang_code)
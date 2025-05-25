"""
Configuración global para Nueva Biblioteca.
"""
import os
from pathlib import Path

# Información de la aplicación
APP_NAME = "Nueva Biblioteca"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Sistema Inteligente de Gestión de Bibliotecas Musicales"
APP_AUTHOR = "Nueva Biblioteca Team"
APP_DOMAIN = "nuevabiblioteca.app"

# Rutas de la aplicación
APP_DIR = Path(__file__).parent
SRC_DIR = APP_DIR / "src"
UI_DIR = SRC_DIR / "ui"

# Configuración de Material 3 Expressive
MATERIAL_THEME = {
    'theme': 'dark_purple.xml',
    'primary_color': '#6750A4',
    'secondary_color': '#625B71',
    'surface_color': '#1C1B1F',
    'background_color': '#141218',
    'error_color': '#F2B8B5',
    'warning_color': '#F9C74F',
    'success_color': '#90E0EF',
    'info_color': '#CAF0F8',
    'font_family': 'SF Pro Display, Roboto',  # Optimizado para macOS
    'font_size': '13px',                      # Aumentado para Retina
    'font_size_small': '11px',
    'font_size_large': '15px',
    'icon_size': '24px',                      # 48px efectivo en Retina
    'border_radius': '8px',
    'spacing': '8px',
    'high_dpi': True
}

# Configuración de la ventana principal
WINDOW_CONFIG = {
    'title': f"{APP_NAME} - Gestión Musical Inteligente",
    'min_width': 1280,         # 50% del ancho de la pantalla
    'min_height': 800,         # 50% del alto de la pantalla
    'default_width': 1920,     # 75% del ancho de la pantalla
    'default_height': 1200,    # 75% del alto de la pantalla
    'max_width': 2560,         # Ancho máximo (full resolution)
    'max_height': 1600,        # Alto máximo (full resolution)
    'scale_factor': 2.0,       # Factor de escala para Retina
    'padding': 8,             # Padding base para elementos UI
    'margin': 8               # Margen base para elementos UI
}

# Configuración de la splash screen
SPLASH_CONFIG = {
    'width': 800,              # 400 * 2 para Retina
    'height': 600,             # 300 * 2 para Retina
    'duration': 2000,          # milisegundos
    'scale_factor': 2.0,       # Factor de escala para Retina
    'border_radius': 16,       # Radio de bordes
    'font_size': '28px',       # Tamaño de fuente para Retina
    'background_opacity': 0.95, # Opacidad del fondo
    'messages': [
        "Inicializando componentes...",
        "Cargando bibliotecas...",
        "Aplicando tema Material 3...",
        "Configurando interfaz..."
    ]
}

# Formatos de audio soportados
SUPPORTED_FORMATS = {
    'audio': ['.mp3', '.flac', '.wav', '.ogg', '.m4a', '.wma', '.aac'],
    'playlist': ['.m3u', '.m3u8', '.pls', '.xspf']
}

# Configuración por defecto de la aplicación
DEFAULT_SETTINGS = {
    'general': {
        'auto_scan': True,
        'remember_window': True,
        'minimize_to_tray': False,
        'auto_update': True,
        'update_frequency': 'Semanal'
    },
    'library': {
        'main_path': str(Path.home() / "Music"),
        'auto_import': True,
        'watch_folders': False,
        'scan_interval': 5
    },
    'playback': {
        'output_device': 'Dispositivo por defecto',
        'buffer_size': 1,  # 0=Pequeño, 1=Medio, 2=Grande
        'crossfade': False,
        'crossfade_duration': 3,
        'gapless': True,
        'resume_playback': False,
        'volume_normalization': False,
        'replay_gain': False
    },
    'interface': {
        'theme': 0,  # 0=Material 3 Expressive (Oscuro)
        'accent_color': 0,  # 0=Púrpura
        'font_family': 0,  # 0=SF Pro Display
        'font_size': 13,   # Tamaño base para Retina
        'animations': True,
        'transparency': True,
        'blur_effects': True,  # Habilitado para macOS
        'high_dpi': True,     # Soporte para Retina
        'responsive_layout': True
    }
}

# Configuración de logging
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}',
    'file': APP_DIR / 'logs' / 'nueva_biblioteca.log'
}

# Configuración de base de datos (para futuras implementaciones)
DATABASE_CONFIG = {
    'type': 'sqlite',
    'path': APP_DIR / 'data' / 'biblioteca.db',
    'backup_interval': 24  # horas
}

# URLs y recursos
RESOURCES = {
    'icons': {
        'app': ':/icons/app_icon.png',
        'library': ':/icons/library_music.png',
        'playlist': ':/icons/queue_music.png',
        'search': ':/icons/search.png',
        'settings': ':/icons/settings.png'
    },
    'help_url': 'https://nuevabiblioteca.app/help',
    'update_url': 'https://api.nuevabiblioteca.app/updates',
    'feedback_url': 'https://nuevabiblioteca.app/feedback'
}

# Configuración de rendimiento
PERFORMANCE_CONFIG = {
    'max_search_results': 1000,
    'thumbnail_cache_size': 100,  # MB
    'metadata_cache_timeout': 3600,  # segundos
    'ui_update_interval': 100  # milisegundos
}

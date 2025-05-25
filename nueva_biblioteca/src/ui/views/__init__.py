"""
Vistas principales para Nueva Biblioteca.
"""

# Placeholder imports para vistas que crearemos
try:
    from .library_view import LibraryView
except ImportError:
    LibraryView = None

try:
    from .playlist_view import PlaylistView
except ImportError:
    PlaylistView = None

try:
    from .settings_view import SettingsView
except ImportError:
    SettingsView = None

__all__ = [
    'LibraryView',
    'PlaylistView', 
    'SettingsView'
]

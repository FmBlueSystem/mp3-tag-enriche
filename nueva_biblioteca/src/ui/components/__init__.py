"""
Componentes de UI para Nueva Biblioteca.
"""

from .search_bar import SearchBar
from .library_panel import LibraryPanel

# Placeholder imports para componentes que crearemos
try:
    from .playlist_panel import PlaylistPanel
except ImportError:
    PlaylistPanel = None

try:
    from .player_controls import PlayerControls
except ImportError:
    PlayerControls = None

try:
    from .filter_panel import FilterPanel
except ImportError:
    FilterPanel = None

__all__ = [
    'SearchBar',
    'LibraryPanel',
    'PlaylistPanel',
    'PlayerControls',
    'FilterPanel'
]

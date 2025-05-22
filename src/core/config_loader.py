"""API Configuration Loader."""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration file paths
CONFIG_PATHS = [
    "config/api_keys.json",
    os.path.expanduser("~/.genredetector/api_keys.json"),
    "/etc/genredetector/api_keys.json"
]

def load_api_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load API configuration from the specified path or predefined paths.
    
    Args:
        config_path: Path to the configuration file (optional)
        
    Returns:
        Dictionary containing the API configuration
    """
    # Check explicit path first
    if config_path and os.path.exists(config_path):
        return _load_config_file(config_path)
    
    # Try predefined paths
    for path in CONFIG_PATHS:
        if os.path.exists(path):
            return _load_config_file(path)
    
    # No configuration found, return empty dictionary
    return {
        "spotify": {},
        "lastfm": {},
        "discogs": {},
        "musicbrainz": {}
    }

def _load_config_file(path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file.
    
    Args:
        path: Path to the configuration file
        
    Returns:
        Dictionary containing the configuration
    """
    try:
        with open(path, 'r') as f:
            config = json.load(f)
        return config
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading configuration from {path}: {e}")
        return {
            "spotify": {},
            "lastfm": {},
            "discogs": {},
            "musicbrainz": {}
        }

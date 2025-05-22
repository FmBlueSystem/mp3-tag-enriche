#!/usr/bin/env python3
"""
Spotify Integration Demo for MP3 Genre Detection
=============================================

This script demonstrates how to properly use the Spotify API 
for genre detection and metadata enrichment.

Usage:
  python spotify_demo.py [--track "Artist - Track Title"]
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import Spotify API and configuration
try:
    from src.core.spotify_api import SpotifyAPI
    from src.core.config_loader import load_api_config
    from src.core.file_handler import Mp3FileHandler
    IMPORTS_OK = True
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    IMPORTS_OK = False

def load_spotify_credentials() -> Dict[str, str]:
    """Load Spotify API credentials from config file or environment variables."""
    credentials = {
        "client_id": os.environ.get("SPOTIPY_CLIENT_ID", ""),
        "client_secret": os.environ.get("SPOTIPY_CLIENT_SECRET", "")
    }
    
    # Try loading from config file if environment variables not set
    if not (credentials["client_id"] and credentials["client_secret"]):
        try:
            config = load_api_config("config/api_keys.json")
            spotify_config = config.get("spotify", {})
            
            if spotify_config.get("client_id"):
                credentials["client_id"] = spotify_config["client_id"]
            
            if spotify_config.get("client_secret"):
                credentials["client_secret"] = spotify_config["client_secret"]
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")
    
    return credentials

def search_track(api: SpotifyAPI, artist: str, title: str) -> Dict[str, Any]:
    """Search for track information using Spotify API."""
    print(f"\nSearching Spotify for: {artist} - {title}")
    
    result = api.get_track_info(artist, title)
    
    print("\nResults:")
    if result.get("genres"):
        print(f"Genres: {', '.join(result['genres'])}")
    else:
        print("Genres: No genres found")
    
    if result.get("year"):
        print(f"Year: {result['year']}")
    else:
        print("Year: Not found")
    
    if result.get("album"):
        print(f"Album: {result['album']}")
    else:
        print("Album: Not found")
    
    return result

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Spotify API integration demo")
    
    parser.add_argument(
        "--track",
        default="Queen - Bohemian Rhapsody",
        help="Track to search for in 'Artist - Title' format"
    )
    
    parser.add_argument(
        "--client-id",
        help="Spotify API client ID (overrides config file)"
    )
    
    parser.add_argument(
        "--client-secret",
        help="Spotify API client secret (overrides config file)"
    )
    
    return parser.parse_args()

def main():
    """Main entry point."""
    if not IMPORTS_OK:
        print("Error: Required modules could not be imported.")
        return 1
    
    args = parse_args()
    
    # Get credentials
    credentials = load_spotify_credentials()
    
    # Override with command line args if provided
    if args.client_id:
        credentials["client_id"] = args.client_id
    
    if args.client_secret:
        credentials["client_secret"] = args.client_secret
    
    # Validate credentials
    if not credentials["client_id"] or not credentials["client_secret"]:
        print("Error: Spotify API credentials not found.")
        print("Please set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables")
        print("or update the config/api_keys.json file with valid credentials.")
        return 1
    
    # Mask credentials for display
    masked_id = f"{credentials['client_id'][:4]}...{credentials['client_id'][-4:]}"
    masked_secret = f"****...{credentials['client_secret'][-4:]}"
    print(f"Using Spotify credentials - Client ID: {masked_id}, Secret: {masked_secret}")
    
    # Initialize Spotify API
    try:
        spotify_api = SpotifyAPI(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"]
        )
        
        if not spotify_api.sp:
            print("Error: Failed to initialize Spotify API client.")
            return 1
        
        # Parse artist and title from input
        if " - " in args.track:
            artist, title = args.track.split(" - ", 1)
        else:
            print("Error: Track must be in 'Artist - Title' format.")
            return 1
        
        # Search track
        search_track(spotify_api, artist, title)
        
    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Unexpected error")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

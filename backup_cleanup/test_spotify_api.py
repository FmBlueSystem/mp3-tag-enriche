#!/usr/bin/env python3
"""Test Spotify API connection."""
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    # Import Spotify libraries
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    from src.core.config_loader import load_api_config
    from src.core.spotify_api import SpotifyAPI
    
    # Load configuration
    config = load_api_config("config/api_keys.json")
    spotify_config = config.get("spotify", {})
    client_id = spotify_config.get("client_id")
    client_secret = spotify_config.get("client_secret")
    
    print(f"Client ID: {client_id[:4]}...{client_id[-4:] if client_id else 'None'}")
    print(f"Client Secret: {'*' * 8}{client_secret[-4:] if client_secret else 'None'}")
    
    if not client_id or not client_secret:
        print("Missing Spotify API credentials in config file.")
        sys.exit(1)
    
    # Try using the SpotifyAPI class
    print("\nTesting with SpotifyAPI class:")
    try:
        spotify_api = SpotifyAPI(client_id=client_id, client_secret=client_secret)
        print("SpotifyAPI initialization successful")
        
        # Test getting track info
        artist = "Queen"
        track = "Bohemian Rhapsody"
        print(f"\nTesting track info for: {artist} - {track}")
        result = spotify_api.get_track_info(artist, track)
        
        print("\nTrack Info Results:")
        print(f"Genres: {result.get('genres', [])}")
        print(f"Year: {result.get('year')}")
        print(f"Album: {result.get('album')}")
        
    except Exception as e:
        print(f"Error with SpotifyAPI class: {e}")
    
    # Try using the Spotipy library directly
    print("\nTesting with Spotipy library directly:")
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # Test search
        search_results = sp.search(q="artist:Queen track:Bohemian Rhapsody", type='track', limit=1)
        
        if search_results and search_results.get('tracks', {}).get('items'):
            track_data = search_results['tracks']['items'][0]
            print("\nDirect Search Results:")
            print(f"Track: {track_data.get('name')}")
            print(f"Artist: {track_data['artists'][0]['name'] if track_data.get('artists') else 'Unknown'}")
            print(f"Album: {track_data['album']['name'] if track_data.get('album') else 'Unknown'}")
            print(f"Release Date: {track_data['album']['release_date'] if track_data.get('album') else 'Unknown'}")
        else:
            print("No search results found")
            
    except Exception as e:
        print(f"Error with direct Spotipy usage: {e}")
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure spotipy is installed: pip install spotipy")
except Exception as e:
    print(f"Unexpected error: {e}")

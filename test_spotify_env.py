#!/usr/bin/env python3
"""Test Spotify API connection using environment variables."""
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

# Set Spotify API credentials as environment variables
# These are test credentials for demonstration only - not real credentials
os.environ["SPOTIPY_CLIENT_ID"] = "YOUR_CLIENT_ID_HERE"
os.environ["SPOTIPY_CLIENT_SECRET"] = "YOUR_CLIENT_SECRET_HERE"
# If you have a redirect URI set up for your app
os.environ["SPOTIPY_REDIRECT_URI"] = "http://localhost:8888/callback"

# Add the project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    # Import Spotify libraries
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    
    print(f"SPOTIPY_CLIENT_ID: {os.environ.get('SPOTIPY_CLIENT_ID')[:4]}...{os.environ.get('SPOTIPY_CLIENT_ID')[-4:] if os.environ.get('SPOTIPY_CLIENT_ID') else 'None'}")
    print(f"SPOTIPY_CLIENT_SECRET: {'*' * 8}{os.environ.get('SPOTIPY_CLIENT_SECRET')[-4:] if os.environ.get('SPOTIPY_CLIENT_SECRET') else 'None'}")
    
    # Try using the Spotipy library directly with environment variables
    print("\nTesting with Spotipy library using environment variables:")
    
    try:
        # The spotipy library will automatically use the environment variables
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
        
        # Test search
        search_results = sp.search(q="artist:Queen track:Bohemian Rhapsody", type='track', limit=1)
        
        if search_results and search_results.get('tracks', {}).get('items'):
            track_data = search_results['tracks']['items'][0]
            print("\nSearch Results:")
            print(f"Track: {track_data.get('name')}")
            print(f"Artist: {track_data['artists'][0]['name'] if track_data.get('artists') else 'Unknown'}")
            print(f"Album: {track_data['album']['name'] if track_data.get('album') else 'Unknown'}")
            print(f"Release Date: {track_data['album']['release_date'] if track_data.get('album') else 'Unknown'}")
            
            # Get artist info
            if track_data.get('artists') and len(track_data['artists']) > 0:
                artist_id = track_data['artists'][0]['id']
                artist_data = sp.artist(artist_id)
                
                print("\nArtist Info:")
                print(f"Name: {artist_data.get('name')}")
                print(f"Genres: {artist_data.get('genres')}")
                print(f"Popularity: {artist_data.get('popularity')}")
        else:
            print("No search results found")
            
    except Exception as e:
        print(f"Error with Spotipy usage: {e}")
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure spotipy is installed: pip install spotipy")
except Exception as e:
    print(f"Unexpected error: {e}")

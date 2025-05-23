#!/usr/bin/env python3
"""Test genre and year detection functionality."""
import sys
import os
from src.core.genre_detector import GenreDetector
from src.core.music_apis import MusicBrainzAPI, LastFmAPI, DiscogsAPI
from pathlib import Path

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def main():
    # Sample artists and tracks for testing
    test_tracks = [
        {"artist": "Michael Jackson", "title": "Billie Jean"},
        {"artist": "Madonna", "title": "Like a Prayer"},
        {"artist": "Queen", "title": "Bohemian Rhapsody"},
        {"artist": "ABBA", "title": "Dancing Queen"},
        {"artist": "Prince", "title": "Purple Rain"}
    ]
    
    # Initialize APIs
    apis = [
        MusicBrainzAPI(email="user@example.com"),
        LastFmAPI(),
        DiscogsAPI()
    ]
    
    # Initialize detector
    genre_detector = GenreDetector(apis=apis)
    
    print("\n===== Testing Direct API Calls =====")
    # Test direct API calls to verify each API is working
    for api in apis:
        for track in test_tracks[:2]:  # Test with just 2 tracks for quicker execution
            artist, title = track["artist"], track["title"]
            print(f"\nTesting {api.__class__.__name__} with {artist} - {title}")
            
            try:
                track_info = api.get_track_info(artist, title)
                print(f"  Genres: {track_info.get('genres', [])}")
                print(f"  Year: {track_info.get('year')}")
                print(f"  Album: {track_info.get('album')}")
                
                genre_scores = api.get_genres(artist, title)
                print(f"  Normalized genres with scores: {genre_scores}")
            except Exception as e:
                print(f"  Error: {e}")
    
    print("\n===== Testing Genre Detector =====")
    # Test the integration through GenreDetector
    for track in test_tracks:
        artist, title = track["artist"], track["title"]
        print(f"\nTesting GenreDetector with {artist} - {title}")
        
        # Create a mock MP3 info dictionary to test GenreDetector workflow
        mock_file_info = {
            "artist": artist,
            "title": title,
            "album": "",
            "current_genre": ""
        }
        
        # Mock the file handler
        class MockFileHandler:
            def get_file_info(self, file_path, chunk_size=8192):
                return mock_file_info
        
        genre_detector.file_handler = MockFileHandler()
        
        try:
            # Using a dummy file path since we're mocking the file handler
            result = genre_detector.analyze_file("dummy_path.mp3")
            print(f"  Detected genres: {result.get('detected_genres', {}).keys()}")
            print(f"  Year: {result.get('year')}")
            
            # Check API results to see if any API returned year information
            for api_name, api_result in result.get('api_results', {}).items():
                print(f"  {api_name} year: {api_result.get('year')}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    main()

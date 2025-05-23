#!/usr/bin/env python3
"""Test script to verify proper handling of different metadata scenarios."""
import logging
from src.core.music_apis import MusicBrainzAPI, LastFmAPI, DiscogsAPI
from src.core.genre_detector import GenreDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def test_with_metadata(apis, artist, title, description="Normal case"):
    """Test genre detection with specific metadata values."""
    print(f"\n===== Testing {description}: '{artist}' - '{title}' =====")
    
    # Create mock metadata
    metadata = {
        'artist': artist,
        'title': title,
        'album': ""
    }
    
    # Create a mock file handler that returns our test metadata
    class MockFileHandler:
        def get_file_info(self, file_path, chunk_size=8192):
            return {
                "artist": metadata['artist'],
                "title": metadata['title'],
                "album": metadata['album'],
                "current_genre": ""
            }
    
    # Initialize detector with mock file handler
    detector = GenreDetector(apis=apis)
    detector.file_handler = MockFileHandler()
    
    # Run the test
    result = detector.analyze_file("dummy_path.mp3")
    
    # Print results
    print(f"Detected genres: {result.get('detected_genres', {}).keys()}")
    print(f"Year: {result.get('year')}")
    print(f"Metadata used: {result.get('metadata')}")
    print(f"API results received: {len(result.get('api_results', {}))}")
    
    for api_name, api_result in result.get('api_results', {}).items():
        print(f"  {api_name} year: {api_result.get('year')}")
        print(f"  {api_name} genres: {api_result.get('genres')}")
        
    # Return the result to allow assertions if needed
    return result

def main():
    """Run metadata handling tests."""
    # Initialize APIs
    apis = [
        MusicBrainzAPI(email="user@example.com"),
        LastFmAPI(),
        DiscogsAPI()
    ]
    
    # Test case 1: Normal metadata
    test_with_metadata(apis, "Madonna", "Like a Prayer", "Normal case")
    
    # Test case 2: None values
    test_with_metadata(apis, None, None, "None values")
    
    # Test case 3: String 'None' values
    test_with_metadata(apis, "None", "None", "String 'None' values")
    
    # Test case 4: Empty strings
    test_with_metadata(apis, "", "", "Empty strings")
    
    # Test case 5: Mixed valid/invalid
    test_with_metadata(apis, "Madonna", None, "Valid artist, None title")
    
    # Test case 6: Test with actual string that shouldn't match anything
    test_with_metadata(apis, "NonExistentArtist12345", "NonExistentTrack67890", "Nonexistent artist/track")

if __name__ == "__main__":
    main()

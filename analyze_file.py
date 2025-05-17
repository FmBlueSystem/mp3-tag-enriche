"""Direct file analysis script."""
import os
import sys
from pathlib import Path
import glob
from src.core.music_apis import MusicBrainzAPI
from src.core.genre_detector import GenreDetector

def analyze_file(filepath: str):
    print(f"\nTrying to analyze file: {filepath}")
    print(f"Path type: {type(filepath)}")
    print(f"Path encoding (if string): {filepath.encode()}")
    
    # Try different path representations
    path_obj = Path(filepath)
    print(f"\nPath object: {path_obj}")
    print(f"Absolute path: {path_obj.absolute()}")
    print(f"Resolved path: {path_obj.resolve()}")
    
    if not os.path.exists(filepath):
        print(f"Direct path check: File does not exist!")
    else:
        print(f"Direct path check: File exists!")
        
    if not path_obj.exists():
        print(f"Path object check: File does not exist!")
    else:
        print(f"Path object check: File exists!")
        
    # Try glob pattern matching
    print("\nTrying glob pattern matching:")
    base_dir = "/Volumes/My Passport/Dj compilation 2025/DMS/Mayo25/X-Mix Club Classics/X-Mix Club Classics 021"
    pattern = os.path.join(base_dir, "*.mp3")
    print(f"Looking for MP3 files in: {base_dir}")
    
    for found_file in glob.glob(pattern):
        print(f"Found file: {found_file}")
        if "Bryan Adams" in found_file:
            print(f"\nFound matching file: {found_file}")
            if os.path.exists(found_file):
                print(f"Size: {os.path.getsize(found_file)} bytes")
                filepath = found_file
                break

    if os.path.exists(filepath):
        print("\nProceeding with analysis...")
        detector = GenreDetector(apis=[MusicBrainzAPI()], verbose=True)
        results = detector.analyze_file(filepath)
        print("\nAnalysis results:")
        print(results)

if __name__ == "__main__":
    filepath = "/Volumes/My Passport/Dj compilation 2025/DMS/Mayo25/X-Mix Club Classics/X-Mix Club Classics 021/Bryan Adams - Summer Of '69.mp3"
    analyze_file(filepath)

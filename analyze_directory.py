"""Analyze all MP3 files in the directory."""
import os
import sys
import json
from pathlib import Path
import glob
from src.core.music_apis import MusicBrainzAPI
from src.core.genre_detector import GenreDetector

def analyze_directory(directory: str):
    print(f"\nAnalyzing directory: {directory}")
    
    # Initialize detector
    detector = GenreDetector(apis=[MusicBrainzAPI()], verbose=True)
    results = {}
    
    # Find all MP3 files
    pattern = os.path.join(directory, "*.mp3")
    print(f"\nLooking for MP3 files with pattern: {pattern}")
    
    for filepath in glob.glob(pattern):
        print(f"\nAnalyzing: {os.path.basename(filepath)}")
        if os.path.exists(filepath):
            try:
                result = detector.analyze_file(filepath)
                results[filepath] = result
            except Exception as e:
                print(f"Error analyzing {filepath}: {e}")
                results[filepath] = {"error": str(e)}
                
    # Save results
    output_file = "analysis_results.json"
    print(f"\nSaving results to {output_file}")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nAnalysis complete!")
    return results

if __name__ == "__main__":
    directory = "/Volumes/My Passport/Dj compilation 2025/DMS/Mayo25/X-Mix Club Classics/X-Mix Club Classics 021"
    results = analyze_directory(directory)
    print("\nSummary:")
    for filepath, result in results.items():
        filename = os.path.basename(filepath)
        current = result.get('current_genres', [])
        detected = result.get('detected_genres', {})
        print(f"\n{filename}:")
        print(f"Current genres: {current}")
        print(f"Detected genres: {detected}")

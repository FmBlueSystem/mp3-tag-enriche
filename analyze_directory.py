"""Analyze all MP3 files in the directory."""
import os
import sys
import json
from pathlib import Path
import glob
import logging
from src.core.music_apis import MusicBrainzAPI
from src.core.genre_detector import GenreDetector

logger = logging.getLogger(__name__)

def analyze_directory(directory: str):
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger.info(f"\nAnalyzing directory: {directory}")
    
    # Initialize detector
    detector = GenreDetector(apis=[MusicBrainzAPI()], verbose=True)
    results = {}
    
    # Find all MP3 files
    pattern = os.path.join(directory, "*.mp3")
    logger.info(f"\nLooking for MP3 files with pattern: {pattern}")
    
    for filepath in glob.glob(pattern):
        logger.info(f"\nAnalyzing: {os.path.basename(filepath)}")
        if os.path.exists(filepath):
            try:
                result = detector.analyze_file(filepath)
                results[filepath] = result
            except Exception as e:
                logger.error(f"Error analyzing {filepath}: {e}")
                results[filepath] = {"error": str(e)}
                
    # Save results
    output_file = "analysis_results.json"
    logger.info(f"\nSaving results to {output_file}")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("\nAnalysis complete!")
    return results

if __name__ == '__main__':
    if len(sys.argv) > 1:
        analyze_directory(sys.argv[1])
    else:
        logger.error("Please provide a directory path.")

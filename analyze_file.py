"""Direct file analysis script."""
import os
import sys
from pathlib import Path
import glob
import logging
from src.core.music_apis import MusicBrainzAPI
from src.core.genre_detector import GenreDetector

logger = logging.getLogger(__name__)

def analyze_file(filepath: str):
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger.info(f"\nTrying to analyze file: {filepath}")
    logger.info(f"Path type: {type(filepath)}")
    if isinstance(filepath, str):
        logger.info(f"Path encoding (if string): {filepath.encode()}")

    # Try different path representations
    path_obj = Path(filepath)
    logger.info(f"\nPath object: {path_obj}")
    logger.info(f"Absolute path: {path_obj.absolute()}")
    logger.info(f"Resolved path: {path_obj.resolve()}")
    
    if not os.path.exists(filepath):
        logger.warning(f"Direct path check: File does not exist!")
    else:
        logger.info(f"Direct path check: File exists!")
        
    if not path_obj.exists():
        logger.warning(f"Path object check: File does not exist!")
    else:
        logger.info(f"Path object check: File exists!")
        
    # Try glob pattern matching (esto parece más para un ejemplo, no para el análisis de UN archivo)
    # logger.info("\nTrying glob pattern matching:")
    # base_dir = "/Volumes/My Passport/Dj compilation 2025/DMS/Mayo25/X-Mix Club Classics/X-Mix Club Classics 021"
    # pattern = os.path.join(base_dir, "*.mp3")
    # logger.info(f"Looking for MP3 files in: {base_dir}")
    
    # for found_file in glob.glob(pattern):
    #     logger.info(f"Found file: {found_file}")
    #     if "Bryan Adams" in found_file: # Ejemplo específico
    #         logger.info(f"\nFound matching file: {found_file}")
    #         if os.path.exists(found_file):
    #             logger.info(f"Size: {os.path.getsize(found_file)} bytes")
    #             filepath = found_file
    #             break

    if os.path.exists(filepath):
        logger.info("\nProceeding with analysis...")
        detector = GenreDetector(apis=[MusicBrainzAPI()], verbose=True)
        results = detector.analyze_file(filepath)
        logger.info("\nAnalysis results:")
        logger.info(results)
    else:
        logger.error(f"File not found after all checks: {filepath}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        analyze_file(sys.argv[1])
    else:
        logger.error("Please provide a file path to analyze.")

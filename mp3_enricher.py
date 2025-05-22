#!/usr/bin/env python3
"""Enhanced MP3 Enricher CLI with Spotify integration."""
import os
import sys
import time
import json
import glob
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to the path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.core.genre_detector import GenreDetector
from src.core.file_handler import Mp3FileHandler
from src.core.music_apis import MusicBrainzAPI, LastFmAPI, DiscogsAPI
try:
    from src.core.spotify_api import SpotifyAPI
    SPOTIFY_AVAILABLE = True
except ImportError:
    SPOTIFY_AVAILABLE = False
from src.core.config_loader import load_api_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mp3_enricher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Enrich MP3 files with genre metadata from multiple sources")
    
    parser.add_argument(
        "directory",
        nargs="?",
        help="Directory containing MP3 files to process"
    )
    
    parser.add_argument(
        "--config",
        help="Path to API configuration file"
    )
    
    parser.add_argument(
        "--backup-dir",
        help="Directory for MP3 backups before modification"
    )
    
    parser.add_argument(
        "--rename",
        action="store_true",
        help="Rename files based on metadata"
    )
    
    parser.add_argument(
        "--include-genres",
        action="store_true",
        help="Include detected genres in filenames when renaming"
    )
    
    parser.add_argument(
        "--write-genres",
        action="store_true",
        help="Write detected genres to MP3 tags"
    )
    
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.5,
        help="Minimum genre confidence threshold (0.0-1.0)"
    )
    
    parser.add_argument(
        "--max-genres",
        type=int,
        default=3,
        help="Maximum number of genres to write"
    )
    
    parser.add_argument(
        "--output",
        help="Output JSON file for analysis results"
    )
    
    parser.add_argument(
        "--use-spotify",
        action="store_true",
        help="Use Spotify as a data source (requires API credentials)"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode, prompting for each file"
    )
    
    return parser.parse_args()

def configure_apis(config: Dict[str, Any], use_spotify: bool) -> List[Any]:
    """Configure and initialize API clients.
    
    Args:
        config: API configuration dictionary
        use_spotify: Whether to use Spotify API
    
    Returns:
        List of initialized API clients
    """
    apis = []
    
    # Initialize MusicBrainz API
    mb_config = config.get("musicbrainz", {})
    mb_api = MusicBrainzAPI(
        app_name=mb_config.get("app_name", "GenreDetector"),
        version=mb_config.get("version", "0.2.0"),
        email=mb_config.get("email", "")
    )
    apis.append(mb_api)
    
    # Initialize Last.fm API
    lastfm_config = config.get("lastfm", {})
    lastfm_api = LastFmAPI(
        api_key=lastfm_config.get("api_key"),
        api_secret=lastfm_config.get("api_secret")
    )
    apis.append(lastfm_api)
    
    # Initialize Discogs API
    discogs_config = config.get("discogs", {})
    discogs_api = DiscogsAPI(
        api_token=discogs_config.get("api_token")
    )
    apis.append(discogs_api)
    
        # Initialize Spotify API if requested and available
        if use_spotify and SPOTIFY_AVAILABLE:
            try:
                spotify_config = config.get("spotify", {})
                client_id = spotify_config.get("client_id")
                client_secret = spotify_config.get("client_secret")
                
                # Check environment variables as fallback
                if not client_id or not client_secret:
                    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
                    client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")
                
                if client_id and client_secret:
                    spotify_api = SpotifyAPI(client_id=client_id, client_secret=client_secret)
                    if spotify_api.sp:  # Only add if successfully initialized
                        apis.append(spotify_api)
                        logger.info("Spotify API enabled")
                    else:
                        logger.warning("Spotify API client initialization failed, continuing without Spotify")
                else:
                    logger.warning("Spotify API credentials missing, continuing without Spotify")
            except Exception as e:
                logger.error(f"Error initializing Spotify API: {e}")
                logger.info("Continuing without Spotify API integration")
    
    return apis

def process_files(
    genre_detector: GenreDetector,
    file_paths: List[str],
    write_genres: bool = False,
    rename_files: bool = False,
    include_genres: bool = False,
    confidence_threshold: float = 0.5,
    max_genres: int = 3,
    interactive: bool = False
) -> Dict[str, Dict]:
    """Process MP3 files to detect genres and optionally write tags.
    
    Args:
        genre_detector: Initialized GenreDetector instance
        file_paths: List of MP3 file paths to process
        write_genres: Whether to write detected genres to MP3 tags
        rename_files: Whether to rename files based on metadata
        include_genres: Whether to include genres in filenames when renaming
        confidence_threshold: Minimum genre confidence threshold
        max_genres: Maximum number of genres to write
        interactive: Whether to prompt for each file
        
    Returns:
        Dictionary of analysis results
    """
    results = {}
    total = len(file_paths)
    
    for idx, file_path in enumerate(file_paths, 1):
        try:
            logger.info(f"[{idx}/{total}] Processing: {file_path}")
            result = genre_detector.analyze_file(file_path)
            
            # Skip files with missing metadata only if we couldn't get artist or title from either tags or filename
            if not result.get('metadata', {}).get('artist') or not result.get('metadata', {}).get('title'):
                print(f"[SKIP] {os.path.basename(file_path)} | Missing both artist and title")
                logger.warning(f"Skipping file with completely missing metadata: {file_path}")
                continue
                
            artist = result['metadata']['artist']
            title = result['metadata']['title']
            
            # Print detected genres and their confidence scores
            detected_genres = result.get('detected_genres', {})
            filtered_genres = {k: v for k, v in detected_genres.items() if v >= confidence_threshold}
            
            def to_str(g):
                if isinstance(g, str):
                    return g
                if isinstance(g, tuple) and len(g) > 0:
                    return g[0]
                return str(g)
            
            print(f"\n{artist} - {title}")
            
            if filtered_genres:
                print("Detected genres:")
                for genre, score in sorted(filtered_genres.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {to_str(genre)}: {score:.2f}")
            else:
                print("No genres detected with sufficient confidence")
            
            # Print year if available
            if result.get('year'):
                print(f"Year: {result['year']}")
            
            # Interactive mode - ask user what to do
            proceed = True
            if interactive:
                response = input("\nApply these changes? [Y/n/s(skip)]: ").lower()
                if response in ['n', 'no']:
                    proceed = False
                elif response in ['s', 'skip']:
                    print("Skipping this file")
                    continue
            
            if proceed:
                # Get top genres to write
                top_genres = sorted(filtered_genres.items(), key=lambda x: x[1], reverse=True)
                genres_to_write = [to_str(g[0]) for g in top_genres[:max_genres]]
                
                # Perform requested operations
                if write_genres and genres_to_write:
                    print(f"Writing genres: {', '.join(genres_to_write)}")
                    genre_detector.file_handler.write_genre(file_path, genres_to_write)
                
                if rename_files:
                    rename_result = genre_detector.file_handler.rename_file_by_genre(
                        file_path,
                        genres_to_write if write_genres else None,
                        perform_os_rename_action=True,
                        include_genre_in_filename=include_genres,
                        max_genres_in_filename=2
                    )
                    
                    if rename_result.get('success'):
                        print(f"File renamed: {os.path.basename(rename_result.get('new_path', ''))}")
                    else:
                        print(f"Rename error: {rename_result.get('error', 'Unknown error')}")
                
                if not write_genres and not rename_files:
                    print("Analysis complete (no changes made)")
            
            results[file_path] = result
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}", exc_info=True)
            print(f"Error processing {os.path.basename(file_path)}: {e}")
            results[file_path] = {"error": str(e)}
    
    return results

def main():
    """Main entry point."""
    args = parse_args()
    
    # Load API configuration
    config = load_api_config(args.config)
    
    # Configure APIs based on config
    apis = configure_apis(config, args.use_spotify)
    
    # Initialize file handler with backup directory if specified
    file_handler = Mp3FileHandler(backup_dir=args.backup_dir)
    
    # Initialize genre detector
    genre_detector = GenreDetector(apis=apis, file_handler=file_handler)
    genre_detector.confidence_threshold = args.confidence
    genre_detector.max_genres = args.max_genres
    
    # Get directory to process
    directory = args.directory
    if not directory:
        directory = input("Enter directory path to process: ").strip()
        if not directory:
            print("No directory specified. Exiting.")
            return 1
    
    # Expand directory path
    directory = os.path.expanduser(directory)
    if not os.path.isdir(directory):
        print(f"Directory not found: {directory}")
        return 1
    
    # Find MP3 files
    mp3_pattern = os.path.join(directory, "**", "*.mp3")
    file_paths = glob.glob(mp3_pattern, recursive=True)
    
    if not file_paths:
        print(f"No MP3 files found in {directory}")
        return 1
    
    print(f"Found {len(file_paths)} MP3 files to process")
    
    # Process files
    start_time = time.time()
    results = process_files(
        genre_detector=genre_detector,
        file_paths=file_paths,
        write_genres=args.write_genres,
        rename_files=args.rename,
        include_genres=args.include_genres,
        confidence_threshold=args.confidence,
        max_genres=args.max_genres,
        interactive=args.interactive
    )
    
    # Write results to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results written to {args.output}")
    
    elapsed = time.time() - start_time
    print(f"\nProcessed {len(results)} files in {elapsed:.2f} seconds")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

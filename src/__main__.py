"""Command line interface for MP3 genre detection."""
import argparse
import os
import json
import sys
from typing import Dict, List
from .core.music_apis import MusicBrainzAPI, LastFmAPI, DiscogsAPI
from .core.genre_detector import GenreDetector
import logging

# Try to import Spotify API
try:
    from .core.spotify_api import SpotifyAPI
    SPOTIFY_AVAILABLE = True
except ImportError:
    SPOTIFY_AVAILABLE = False

# Try to import config loader
try:
    from .core.config_loader import load_api_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)

def verify_path(path: str) -> bool:
    """Verify that a path exists and is accessible.
    
    Args:
        path: Path to verify
        
    Returns:
        True if path exists and is accessible
    """
    print(f"Verifying path: {path}")
    if os.path.exists(path):
        print(f"Path exists: {path}")
        return True
    print(f"Path does not exist: {path}")
    return False

def create_detector(lastfm_api_key: str = None, 
                   lastfm_api_secret: str = None,
                   backup_dir: str = None,
                   use_spotify: bool = True,
                   config_path: str = None,
                   verbose: bool = True) -> GenreDetector:
    """Create and configure the genre detector.
    
    Args:
        lastfm_api_key: Last.fm API key
        lastfm_api_secret: Last.fm API secret
        backup_dir: Directory for file backups
        use_spotify: Whether to use Spotify API
        config_path: Path to API configuration file
        verbose: Enable verbose output
        
    Returns:
        Configured GenreDetector instance
    """
    logger.info("Creating detector...")
    apis = [MusicBrainzAPI()]
    
    # Add Last.fm API if credentials provided
    if lastfm_api_key and lastfm_api_secret:
        logger.info("Adding Last.fm API")
        apis.append(LastFmAPI(lastfm_api_key, lastfm_api_secret))
    
    # Add Discogs API
    apis.append(DiscogsAPI())
    
    # Add Spotify API if available and requested
    if use_spotify and SPOTIFY_AVAILABLE and CONFIG_AVAILABLE:
        try:
            # Load configuration
            config = load_api_config(config_path)
            spotify_config = config.get("spotify", {})
            client_id = spotify_config.get("client_id")
            client_secret = spotify_config.get("client_secret")
            
            if client_id and client_secret:
                logger.info("Adding Spotify API")
                spotify_api = SpotifyAPI(client_id=client_id, client_secret=client_secret)
                apis.append(spotify_api)
            else:
                logger.warning("Spotify API credentials missing, continuing without Spotify")
        except Exception as e:
            logger.error(f"Error initializing Spotify API: {e}")
    
    detector = GenreDetector(apis=apis)
    if backup_dir:
        logger.info(f"Setting backup directory for file handler: {backup_dir}")
        detector.file_handler.backup_dir = backup_dir
        
    logger.info(f"Created detector with {len(apis)} APIs")
    return detector

def process_files(detector: GenreDetector,
                 paths: List[str],
                 recursive: bool = False,
                 analyze_only: bool = False,
                 **kwargs) -> Dict[str, any]:
    """Process files and directories.
    
    Args:
        detector: GenreDetector instance
        paths: List of file/directory paths
        recursive: Process directories recursively
        analyze_only: Only analyze without modifying
        **kwargs: Additional arguments for processing
        
    Returns:
        Dictionary with results
    """
    results = {}
    
    for path in paths:
        if not verify_path(path):
            logger.warning(f"Skipping inaccessible path: {path}")
            continue
            
        logger.info(f"\nProcessing path: {path}")
        if os.path.isfile(path):
            if analyze_only:
                logger.info("Analyzing file...")
                results[path] = detector.analyze_file(path)
            else:
                logger.info("Processing file...")
                results[path] = detector.process_file(path, **kwargs)
        elif os.path.isdir(path):
            if analyze_only:
                logger.info("Analyzing directory...")
                # Analyze each file individually
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith('.mp3'):
                            file_path = os.path.join(root, file)
                            logger.info(f"\nAnalyzing: {file_path}")
                            results[file_path] = detector.analyze_file(file_path)
                    if not recursive:
                        break
            else:
                logger.info("Processing directory...")
                results.update(detector.process_directory(
                    path,
                    recursive=recursive,
                    **kwargs
                ))
                
    return results

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Detect and normalize music genres in MP3 files"
    )
    
    parser.add_argument(
        'paths',
        nargs='+',
        help='Paths to MP3 files or directories'
    )
    
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Process directories recursively'
    )
    
    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze files without modifying'
    )
    
    parser.add_argument(
        '--backup-dir',
        default="/Volumes/My Passport/Dj compilation 2025/Respados mp3",
        help='Directory for file backups (default: /Volumes/My Passport/Dj compilation 2025/Respados mp3)'
    )
    
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.3,
        help='Minimum confidence threshold (default: 0.3)'
    )
    
    parser.add_argument(
        '--max-genres',
        type=int,
        default=3,
        help='Maximum number of genres to write (default: 3)'
    )
    
    parser.add_argument(
        '--lastfm-key',
        help='Last.fm API key'
    )
    
    parser.add_argument(
        '--lastfm-secret',
        help='Last.fm API secret'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output JSON file for results'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Disable verbose output'
    )
    
    parser.add_argument(
        '--no-spotify',
        action='store_true',
        help='Disable Spotify API integration'
    )
    
    parser.add_argument(
        '--config',
        help='Path to API configuration file'
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        logger.info("Starting genre detection...")
        logger.info(f"Paths to process: {args.paths}")
        logger.info(f"Analyze only: {args.analyze_only}")
        logger.info(f"Recursive: {args.recursive}")
    else:
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

    try:
        # Create detector
        detector = create_detector(
            lastfm_api_key=args.lastfm_key,
            lastfm_api_secret=args.lastfm_secret,
            backup_dir=args.backup_dir,
            use_spotify=not args.no_spotify,
            config_path=args.config
        )
        
        # Process files
        results = process_files(
            detector,
            args.paths,
            recursive=args.recursive,
            analyze_only=args.analyze_only,
            confidence_threshold=args.confidence,
            max_genres=args.max_genres
        )
        
        # Output results
        output_data = json.dumps(results, indent=2)
        if args.output:
            print(f"Writing results to {args.output}")
            with open(args.output, 'w') as f:
                f.write(output_data)
        else:
            print("\nResults:")
            print(output_data)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
        
    return 0

if __name__ == '__main__':
    sys.exit(main())

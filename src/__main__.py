"""Command line interface for MP3 genre detection."""
import argparse
import os
import json
import sys
from typing import Dict, List
from .core.music_apis import MusicBrainzAPI, LastFmAPI
from .core.genre_detector import GenreDetector

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
                   verbose: bool = True) -> GenreDetector:
    """Create and configure the genre detector.
    
    Args:
        lastfm_api_key: Last.fm API key
        lastfm_api_secret: Last.fm API secret
        backup_dir: Directory for file backups
        verbose: Enable verbose output
        
    Returns:
        Configured GenreDetector instance
    """
    print("Creating detector...")
    apis = [MusicBrainzAPI()]
    
    if lastfm_api_key and lastfm_api_secret:
        print("Adding Last.fm API")
        apis.append(LastFmAPI(lastfm_api_key, lastfm_api_secret))
    
    detector = GenreDetector(apis=apis, backup_dir=backup_dir, verbose=verbose)
    print(f"Created detector with {len(apis)} APIs")
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
            print(f"Skipping inaccessible path: {path}")
            continue
            
        print(f"\nProcessing path: {path}")
        if os.path.isfile(path):
            if analyze_only:
                print("Analyzing file...")
                results[path] = detector.analyze_file(path)
            else:
                print("Processing file...")
                results[path] = detector.process_file(path, **kwargs)
        elif os.path.isdir(path):
            if analyze_only:
                print("Analyzing directory...")
                # Analyze each file individually
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith('.mp3'):
                            file_path = os.path.join(root, file)
                            print(f"\nAnalyzing: {file_path}")
                            results[file_path] = detector.analyze_file(file_path)
                    if not recursive:
                        break
            else:
                print("Processing directory...")
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
        help='Directory for file backups'
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
    
    args = parser.parse_args()
    
    # Enable more verbose logging
    if not args.quiet:
        print("Starting genre detection...")
        print(f"Paths to process: {args.paths}")
        print(f"Analyze only: {args.analyze_only}")
        print(f"Recursive: {args.recursive}")
    
    try:
        # Create detector
        detector = create_detector(
            lastfm_api_key=args.lastfm_key,
            lastfm_api_secret=args.lastfm_secret,
            backup_dir=args.backup_dir,
            verbose=not args.quiet
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

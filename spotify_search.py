#!/usr/bin/env python3
"""Spotify search utility for music metadata."""
import os
import sys
import argparse
import logging
from typing import Dict, List, Optional

# Add the project root to the path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.core.spotify_api import SpotifyAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("spotify_search.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Search Spotify by year and genre")
    
    parser.add_argument(
        "--client-id",
        default=os.environ.get("SPOTIFY_CLIENT_ID"),
        help="Spotify API client ID (can also use SPOTIFY_CLIENT_ID env var)"
    )
    
    parser.add_argument(
        "--client-secret",
        default=os.environ.get("SPOTIFY_CLIENT_SECRET"),
        help="Spotify API client secret (can also use SPOTIFY_CLIENT_SECRET env var)"
    )
    
    parser.add_argument(
        "--year",
        help="Release year to search for"
    )
    
    parser.add_argument(
        "--genre",
        help="Genre to search for"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode with prompts"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results to return (default: 10)"
    )
    
    return parser.parse_args()

def interactive_search(spotify_api: SpotifyAPI):
    """Run an interactive search session."""
    print("\n🎵 Spotify Search Tool 🎵")
    print("=======================")
    
    while True:
        query = input("\n¿Qué querés buscar? (formato: year:1985 genre:funk)\n(Escribe 'salir' para terminar): ")
        
        if query.lower() in ['salir', 'exit', 'quit', 'q']:
            print("¡Hasta luego!")
            break
        
        # Parse query for year and genre
        year = None
        genre = None
        
        year_match = re.search(r'year:(\d{4})', query)
        if year_match:
            year = year_match.group(1)
        
        genre_match = re.search(r'genre:(\w+)', query)
        if genre_match:
            genre = genre_match.group(1)
        
        # If no structured format, try to interpret the query
        if not year and not genre:
            parts = query.split()
            for part in parts:
                if part.isdigit() and len(part) == 4 and 1900 <= int(part) <= 2030:
                    year = part
                elif len(part) > 3:
                    genre = part
        
        # Execute search
        results = spotify_api.search_by_year_and_genre(year, genre, limit=10)
        
        if not results:
            print("No se encontraron resultados. Intenta con otra búsqueda.")
            continue
        
        print(f"\n🎧 Se encontraron {len(results)} resultados:\n")
        for idx, track in enumerate(results, 1):
            print(f"{idx}. {track['name']} - {track['artist']} ({track['release_date'][:4]})")
            print(f"   Álbum: {track['album']}")
            print(f"   Popularidad: {track['popularity']}/100")
            if track['preview_url']:
                print(f"   Preview: {track['preview_url']}")
            print(f"   Link: {track['external_url']}")
            print()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Validate credentials
    if not args.client_id or not args.client_secret:
        logger.error(
            "Spotify API credentials missing. Please provide --client-id and --client-secret "
            "or set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables."
        )
        return 1
    
    # Initialize Spotify API
    spotify_api = SpotifyAPI(args.client_id, args.client_secret)
    
    if not spotify_api.sp:
        logger.error("Failed to initialize Spotify API client")
        return 1
    
    if args.interactive:
        import re  # Import here for interactive mode only
        interactive_search(spotify_api)
        return 0
    
    # Execute search with command line parameters
    if not args.year and not args.genre:
        logger.error("Please specify at least one search parameter (--year or --genre)")
        return 1
    
    results = spotify_api.search_by_year_and_genre(args.year, args.genre, limit=args.limit)
    
    if not results:
        print("No se encontraron resultados.")
        return 0
    
    print(f"\n🎧 Se encontraron {len(results)} resultados:\n")
    for idx, track in enumerate(results, 1):
        print(f"{idx}. {track['name']} - {track['artist']} ({track['release_date'][:4]})")
        print(f"   Álbum: {track['album']}")
        print(f"   Popularidad: {track['popularity']}/100")
        if idx < len(results):
            print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

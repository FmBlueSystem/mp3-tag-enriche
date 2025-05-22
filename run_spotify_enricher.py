#!/usr/bin/env python3
"""MP3 Enricher with Spotify API Environment Variables"""
import os
import sys
import argparse
from pathlib import Path

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run MP3 Enricher with Spotify API")
    
    parser.add_argument(
        "--client-id",
        default=os.environ.get("SPOTIFY_CLIENT_ID"),
        help="Spotify API client ID"
    )
    
    parser.add_argument(
        "--client-secret",
        default=os.environ.get("SPOTIFY_CLIENT_SECRET"),
        help="Spotify API client secret"
    )
    
    parser.add_argument(
        "--directory", "-d",
        default="./mp3_backups",
        help="Directory containing MP3 files"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Validate arguments
    if not args.client_id or not args.client_secret:
        print("Error: Spotify API credentials are required.")
        print("Provide them as arguments or set environment variables:")
        print("  SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
        return 1
    
    # Set environment variables for spotipy
    os.environ["SPOTIPY_CLIENT_ID"] = args.client_id
    os.environ["SPOTIPY_CLIENT_SECRET"] = args.client_secret
    
    print(f"Using Spotify client ID: {args.client_id[:4]}...{args.client_id[-4:]}")
    print(f"Using directory: {args.directory}")
    
    # Build command for mp3_enricher.py
    cmd_args = [
        "python", "mp3_enricher.py",
        args.directory,
        "--use-spotify"
    ]
    
    if args.interactive:
        cmd_args.append("--interactive")
    
    # Run the enricher
    cmd = " ".join(cmd_args)
    print(f"\nRunning: {cmd}")
    return os.system(cmd)

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Spotify API Test - Configure valid credentials here before running

1. Get client ID and client secret from your Spotify Developer Dashboard
   https://developer.spotify.com/dashboard/
2. Set them below and run this script
"""
import os
import subprocess

# ======== SET YOUR SPOTIFY API CREDENTIALS HERE ========
# These should be from your Spotify Developer account
CLIENT_ID = "your_spotify_client_id"
CLIENT_SECRET = "your_spotify_client_secret"
# ======================================================

def main():
    # Set environment variables
    os.environ["SPOTIPY_CLIENT_ID"] = CLIENT_ID
    os.environ["SPOTIPY_CLIENT_SECRET"] = CLIENT_SECRET
    
    # Check if credentials have been updated
    if CLIENT_ID == "your_spotify_client_id" or CLIENT_SECRET == "your_spotify_client_secret":
        print("Error: You need to update the script with your actual Spotify API credentials.")
        print("Please edit this file and replace the placeholders with your real credentials.")
        return 1
    
    # Run the MP3 enricher with Spotify enabled
    print("Running MP3 enricher with Spotify API...")
    cmd = ["python", "mp3_enricher.py", "./mp3_backups", "--use-spotify"]
    result = subprocess.run(cmd, env=os.environ)
    
    return result.returncode

if __name__ == "__main__":
    main()

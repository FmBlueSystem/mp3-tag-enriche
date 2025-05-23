"""Verify genre updates in MP3 files."""
import os
from src.core.file_handler import Mp3FileHandler

def verify_genres(directory: str):
    """Print current genres for all MP3 files in directory."""
    handler = Mp3FileHandler()
    
    print("\nVerifying genre updates:")
    for filename in sorted(os.listdir(directory)):
        if filename.lower().endswith('.mp3'):
            filepath = os.path.join(directory, filename)
            info = handler.get_file_info(filepath)
            print(f"\n{filename}")
            print(f"Current genre: {info.get('current_genre')}")

if __name__ == "__main__":
    directory = "/Volumes/My Passport/Dj compilation 2025/DMS/Mayo25/X-Mix Club Classics/X-Mix Club Classics 021"
    verify_genres(directory)

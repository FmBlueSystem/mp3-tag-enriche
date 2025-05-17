"""Fix genre case formatting."""
import os
from src.core.file_handler import Mp3FileHandler

def fix_genre_cases(directory: str):
    """Update genre cases to proper CamelCase format."""
    handler = Mp3FileHandler()
    case_map = {
        'pop': 'Pop',
        'rock': 'Rock',
        'r&b': 'RAndB',
        'hip hop': 'HipHop',
        'r&b, rock, pop': 'RAndB, Rock, Pop'
    }
    
    for filename in os.listdir(directory):
        if not filename.lower().endswith('.mp3'):
            continue
            
        filepath = os.path.join(directory, filename)
        info = handler.get_file_info(filepath)
        current_genre = info.get('current_genre', '')
        
        if current_genre.lower() in case_map:
            print(f"\nFixing genre case for: {filename}")
            print(f"Current: {current_genre}")
            new_genre = case_map[current_genre.lower()]
            print(f"New: {new_genre}")
            handler.write_genre(filepath, [new_genre])

if __name__ == "__main__":
    directory = "/Volumes/My Passport/Dj compilation 2025/DMS/Mayo25/X-Mix Club Classics/X-Mix Club Classics 021"
    fix_genre_cases(directory)

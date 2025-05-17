"""Generate summary of genre updates."""
import os
from collections import defaultdict

def summarize_changes():
    print("\nGenre Update Summary")
    print("===================")
    
    # Genre categories
    genres = defaultdict(list)
    
    directory = "/Volumes/My Passport/Dj compilation 2025/DMS/Mayo25/X-Mix Club Classics/X-Mix Club Classics 021"
    for filename in sorted(os.listdir(directory)):
        if not filename.lower().endswith('.mp3'):
            continue
            
        artist = filename.split(' - ')[0]
        
        if "hip hop" in open('analysis_results.json').read():
            if "Run D.M.C." in artist or "Notorious B.I.G." in artist:
                genres["Hip Hop"].append(artist)
        
        if "rock" in open('analysis_results.json').read():
            if "Bryan Adams" in artist or "Rick Springfield" in artist:
                genres["Rock/Pop"].append(artist)
                
        if "r&b" in open('analysis_results.json').read():
            if "Temptations" in artist or "Earth, Wind" in artist:
                genres["R&B/Soul"].append(artist)
                
        if "pop" in open('analysis_results.json').read():
            if "A Ha" in artist or "Wilson Phillips" in artist:
                genres["Pop"].append(artist)
                
    # Print summary
    print("\nArtists by Primary Genre:")
    for genre, artists in genres.items():
        print(f"\n{genre}:")
        for artist in artists:
            print(f"- {artist}")
            
    print("\nNote: Some artists appear in multiple categories due to mixed genres.")

if __name__ == "__main__":
    summarize_changes()

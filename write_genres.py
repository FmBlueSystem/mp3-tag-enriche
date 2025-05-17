"""Write detected genres back to MP3 files."""
import os
import json
from pathlib import Path
from src.core.file_handler import Mp3FileHandler

def write_genres(analysis_file: str, confidence_threshold: float = 0.3, max_genres: int = 3):
    """Write detected genres to MP3 files.
    
    Args:
        analysis_file: Path to JSON analysis results
        confidence_threshold: Minimum confidence to include genre
        max_genres: Maximum number of genres to write
    """
    print(f"\nLoading analysis from: {analysis_file}")
    with open(analysis_file) as f:
        results = json.load(f)
        
    # Create file handler with backup directory
    backup_dir = "/Volumes/My Passport/Dj compilation 2025/Respados mp3"
    handler = Mp3FileHandler(backup_dir)
    
    print(f"\nProcessing {len(results)} files...")
    print(f"Using confidence threshold: {confidence_threshold}")
    print(f"Maximum genres per file: {max_genres}")
    
    for filepath, analysis in results.items():
        print(f"\nProcessing: {os.path.basename(filepath)}")
        
        # Get detected genres sorted by confidence
        genres = analysis.get("detected_genres", {})
        selected_genres = []
        
        for genre, confidence in sorted(
            genres.items(), 
            key=lambda x: x[1], 
            reverse=True
        ):
            if confidence >= confidence_threshold:
                selected_genres.append(genre)
                if len(selected_genres) >= max_genres:
                    break
                    
        if not selected_genres:
            print("No genres met confidence threshold")
            continue
            
        print(f"Writing genres: {selected_genres}")
        success = handler.write_genre(filepath, selected_genres)
        
        if success:
            print("Successfully updated file")
        else:
            print("Failed to update file")
            
    print("\nFinished processing files")

if __name__ == "__main__":
    write_genres(
        "analysis_results.json",
        confidence_threshold=0.3,
        max_genres=3
    )

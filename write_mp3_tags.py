#!/usr/bin/env python3
"""Write ID3 tags to an MP3 file."""
import os
import sys
import shutil
import argparse
from mutagen.id3 import ID3, TXXX
from mutagen.easyid3 import EasyID3, error as EasyID3Error

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Write ID3 tags to an MP3 file")
    
    parser.add_argument(
        "file_path",
        help="Path to the MP3 file to modify"
    )
    
    parser.add_argument(
        "--artist",
        help="Set the artist tag"
    )
    
    parser.add_argument(
        "--title",
        help="Set the title tag"
    )
    
    parser.add_argument(
        "--album",
        help="Set the album tag"
    )
    
    parser.add_argument(
        "--date",
        help="Set the date tag (YYYY or YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--year",
        help="Set the year tag (YYYY)"
    )
    
    parser.add_argument(
        "--genre",
        help="Set the genre tag (comma-separated for multiple genres)"
    )
    
    parser.add_argument(
        "--composer",
        help="Set the composer tag"
    )
    
    parser.add_argument(
        "--performer",
        help="Set the performer tag"
    )
    
    parser.add_argument(
        "--album-artist",
        help="Set the album artist tag"
    )
    
    parser.add_argument(
        "--track-number",
        help="Set the track number (e.g., '1' or '1/10')"
    )
    
    parser.add_argument(
        "--disc-number",
        help="Set the disc number (e.g., '1' or '1/2')"
    )
    
    parser.add_argument(
        "--comment",
        help="Set a comment"
    )
    
    parser.add_argument(
        "--custom",
        action="append",
        help="Set a custom tag (format: 'key=value'). Can be used multiple times."
    )
    
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create a backup of the original file"
    )
    
    parser.add_argument(
        "--remove-all",
        action="store_true",
        help="Remove all existing tags before adding new ones"
    )
    
    return parser.parse_args()

def create_backup(file_path):
    """Create a backup of the file.
    
    Args:
        file_path: Path to the file to back up
        
    Returns:
        Path to the backup file
    """
    backup_path = f"{file_path}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"Backup created: {backup_path}")
    return backup_path

def write_tags(file_path, tags_dict, remove_all=False):
    """Write tags to an MP3 file.
    
    Args:
        file_path: Path to the MP3 file
        tags_dict: Dictionary of tags to write
        remove_all: Whether to remove all existing tags before writing
    """
    try:
        # Initialize EasyID3
        try:
            if remove_all:
                # Delete existing ID3 tag completely
                id3 = ID3(file_path)
                id3.delete()
                print("Removed all existing tags")
            
            # Create/load the tags
            audio = EasyID3(file_path)
        except EasyID3Error:
            # If no existing tags, create them
            audio = EasyID3()
            audio.save(file_path)
        
        # Write standard tags
        for key, value in tags_dict.items():
            if value and key in audio.valid_keys.keys():
                if isinstance(value, list):
                    audio[key] = value
                else:
                    audio[key] = [value]
        
        # Save changes
        audio.save(file_path)
        
        # Handle custom tags which EasyID3 doesn't support
        custom_tags = {k: v for k, v in tags_dict.items() if k.startswith('custom:')}
        if custom_tags:
            id3 = ID3(file_path)
            for key, value in custom_tags.items():
                desc = key.split(':', 1)[1]
                txxx = TXXX(encoding=3, desc=desc, text=value)
                id3.add(txxx)
            id3.save(file_path)
        
        print("Tags updated successfully")
    
    except Exception as e:
        print(f"Error writing tags: {e}")
        return False
    
    return True

def main():
    """Main entry point."""
    args = parse_args()
    
    # Validate file
    if not os.path.exists(args.file_path):
        print(f"Error: File not found: {args.file_path}")
        return 1
    
    # Create backup if requested
    if args.backup:
        create_backup(args.file_path)
    
    # Parse custom tags
    custom_tags = {}
    if args.custom:
        for custom in args.custom:
            if '=' in custom:
                key, value = custom.split('=', 1)
                custom_tags[f"custom:{key}"] = value
            else:
                print(f"Warning: Ignoring malformed custom tag: {custom}")
    
    # Prepare tags dictionary
    tags = {
        'artist': args.artist,
        'title': args.title,
        'album': args.album,
        'date': args.date,
        'genre': args.genre.split(',') if args.genre else None,
        'composer': args.composer,
        'performer': args.performer,
        'albumartist': args.album_artist,
        'tracknumber': args.track_number,
        'discnumber': args.disc_number,
        'comment': args.comment
    }
    
    # Add year if specifically provided (some players prefer 'date', others 'year')
    if args.year:
        tags['year'] = args.year
    
    # Add custom tags
    tags.update(custom_tags)
    
    # Filter out None values
    tags = {k: v for k, v in tags.items() if v is not None}
    
    if not tags:
        print("Error: No tags specified")
        return 1
    
    # Write tags
    if write_tags(args.file_path, tags, args.remove_all):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())

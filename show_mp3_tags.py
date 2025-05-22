#!/usr/bin/env python3
"""Display all ID3 tags from an MP3 file."""
import os
import sys
import argparse
from mutagen.id3 import ID3
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Display all ID3 tags from an MP3 file")
    
    parser.add_argument(
        "file_path",
        help="Path to the MP3 file to analyze"
    )
    
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Show raw ID3 frames instead of friendly names"
    )
    
    return parser.parse_args()

def read_id3_tags(file_path: str, use_raw: bool = False):
    """Read ID3 tags from an MP3 file.
    
    Args:
        file_path: Path to the MP3 file
        use_raw: Whether to use raw ID3 frames instead of friendly names
    
    Returns:
        Dictionary of tags and their values
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return {}
    
    tags = {}
    
    try:
        # First try with EasyID3 for common tags
        if not use_raw:
            try:
                audio = EasyID3(file_path)
                if audio:
                    for key in audio:
                        tags[key.upper()] = audio[key]
            except Exception as e:
                print(f"EasyID3 warning: {e}")
        
        # Then try with full ID3 for all tags
        try:
            audio = ID3(file_path)
            if audio:
                # Process raw frame data
                for key in audio:
                    if use_raw:
                        # Use raw frame IDs for keys
                        frame_key = key
                        frame_value = str(audio[key])
                    else:
                        # Use friendly names for keys
                        frame_type = key.split(':', 1)[0]
                        if frame_type == 'TXXX':
                            # Handle user-defined text frames
                            desc = getattr(audio[key], 'desc', '')
                            frame_key = f"{frame_type}: {desc}"
                        else:
                            frame_key = frame_type
                        
                        # Try to get text or direct value
                        if hasattr(audio[key], 'text'):
                            frame_value = audio[key].text
                        else:
                            frame_value = str(audio[key])
                    
                    if frame_key not in tags:
                        tags[frame_key] = frame_value
        except Exception as e:
            print(f"ID3 warning: {e}")
        
        # Get MP3 technical info
        try:
            mp3_info = MP3(file_path).info
            tags['__BITRATE__'] = f"{mp3_info.bitrate // 1000} kbps"
            tags['__SAMPLERATE__'] = f"{mp3_info.sample_rate} Hz"
            tags['__LENGTH__'] = f"{int(mp3_info.length // 60)}:{int(mp3_info.length % 60):02d}"
            tags['__MODE__'] = mp3_info.mode
        except Exception as e:
            print(f"MP3 info warning: {e}")
        
    except Exception as e:
        print(f"Error reading tags: {e}")
    
    return tags

def main():
    """Main entry point."""
    args = parse_args()
    
    # Read tags
    tags = read_id3_tags(args.file_path, args.raw)
    
    # Print file info
    print(f"\nFile: {os.path.basename(args.file_path)}")
    print(f"Size: {os.path.getsize(args.file_path) // 1024} KB")
    
    # Print tags
    if tags:
        print("\nID3 Tags:")
        print("-" * 50)
        
        # Print technical info first
        tech_keys = [k for k in tags.keys() if k.startswith('__')]
        for key in sorted(tech_keys):
            print(f"{key.strip('_'):15}: {tags[key]}")
        
        # Print content tags
        content_keys = [k for k in tags.keys() if not k.startswith('__')]
        for key in sorted(content_keys):
            print(f"{key:15}: {tags[key]}")
    else:
        print("\nNo ID3 tags found")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

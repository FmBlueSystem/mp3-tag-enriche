"""Test utilities and helper functions."""
import os
import base64

def get_minimal_mp3_data():
    """Get a minimal valid MP3 file data for testing.
    
    This is a base64-encoded minimal MP3 file with:
    - Valid ID3v2 header
    - Valid MPEG frame header
    - Minimal audio data
    """
    # This is a base64 encoded minimal valid MP3 file (44.1kHz, 128kbps, stereo)
    minimal_mp3 = """
    SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAA
    AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
    """
    return base64.b64decode(minimal_mp3.strip())

def create_minimal_mp3(path):
    """Create a minimal valid MP3 file at the given path.
    
    Args:
        path: Path where to create the MP3 file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(path, 'wb') as f:
            f.write(get_minimal_mp3_data())
        return True
    except Exception as e:
        print(f"Error creating minimal MP3: {e}")
        return False

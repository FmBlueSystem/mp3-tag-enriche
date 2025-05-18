"""Create a test MP3 file with valid headers and ID3 tags."""
import os
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TCON, TALB

def create_empty_mp3(path):
    """Create a minimal valid MP3 file."""
    # MPEG 1 Layer III frame header (stereo, 44.1kHz, 128kbps)
    header_data = (
        # ID3v2 header
        b'ID3\x03\x00\x00\x00\x00\x00\x00' +
        # MPEG sync (0xFFF)
        b'\xFF\xFB' +
        # MPEG 1 Layer 3, Not protected
        b'\x90' +
        # Bitrate (128kbps), Frequency (44.1kHz), Padding bit
        b'\x64' +
        # Private bit, Stereo
        b'\x00' +
        # Frame payload (zeros)
        bytes([0] * 417) +  # 417 bytes = 128kbps frame at 44.1kHz
        # Add a second frame to make it more realistic
        b'\xFF\xFB\x90\x64\x00' + bytes([0] * 417)
    )
    
    with open(path, 'wb') as f:
        f.write(header_data)

def add_id3_tags(path):
    """Add ID3 tags to an MP3 file."""
    try:
        # Create new ID3 tag
        tags = ID3()
        
        # Add the tags
        tags.add(TIT2(encoding=3, text="Test Song"))
        tags.add(TPE1(encoding=3, text="Test Artist"))
        tags.add(TCON(encoding=3, text="Rock"))
        tags.add(TALB(encoding=3, text="Test Album"))
        
        # Save tags at the start of the file
        with open(path, 'rb') as f:
            audio_data = f.read()[10:]  # Skip ID3 header
        
        tags.save(path, v2_version=3)
        
        # Append audio data after tags
        with open(path, 'ab') as f:
            f.write(audio_data)
            
        return True
    except Exception as e:
        print(f"Error adding ID3 tags: {e}")
        return False

def create_test_mp3(output_dir="tests/resources"):
    """Create a test MP3 file with ID3 tags."""
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(output_dir, "sample.mp3")
    
    try:
        # Create MP3 file
        create_empty_mp3(output_path)
        
        # Add ID3 tags
        if not add_id3_tags(output_path):
            raise Exception("Failed to add ID3 tags")
            
        # Verify the file is readable
        MP3(output_path)
        return output_path
        
    except Exception as e:
        print(f"Error creating test MP3: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None

if __name__ == "__main__":
    result = create_test_mp3()
    if result:
        print(f"Successfully created test MP3: {result}")
    else:
        print("Failed to create test MP3")

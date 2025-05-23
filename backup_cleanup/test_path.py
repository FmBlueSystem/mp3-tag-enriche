import os
import glob

path = "/Volumes/My Passport/Dj compilation 2025/DMS/Mayo25/X-Mix Club Classics/X-Mix Club Classics 021"
print("Files in directory:")
for filepath in glob.glob(os.path.join(path, "*.mp3")):
    print(f"Found: {filepath}")
    if os.path.exists(filepath):
        print(f"File exists and is accessible")
        print(f"Size: {os.path.getsize(filepath)} bytes")
    else:
        print(f"File does not exist or is not accessible")

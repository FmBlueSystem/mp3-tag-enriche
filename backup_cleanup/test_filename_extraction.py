from src.core.file_handler import Mp3FileHandler

file_path = '/Volumes/My Passport/Dj compilation 2025/DMS/DMS 80s/Joan Jett - I Love Rock Roll Quantized - Super Short Edit.mp3'

# Create handler and get file info
handler = Mp3FileHandler()
file_info = handler.get_file_info(file_path)

# Print the results
print("File info:")
for key, value in file_info.items():
    print(f"  {key}: {value}")

print("\nExtracting from filename:")
filename = "Joan Jett - I Love Rock Roll Quantized - Super Short Edit"
artist, title = handler.extract_artist_title_from_filename(filename)
print(f"  Artist: {artist}")
print(f"  Title: {title}")

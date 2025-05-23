from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

file_path = '/Volumes/My Passport/Dj compilation 2025/DMS/DMS 80s/Joan Jett - I Love Rock Roll Quantized - Super Short Edit.mp3'

print('EasyID3 Tags:')
try:
    tags = EasyID3(file_path)
    print(dict(tags))
except Exception as e:
    print(f'EasyID3 Error: {e}')

print('\nMP3 Info:')
try:
    info = MP3(file_path)
    print(info.info)
    print(info.tags)
except Exception as e:
    print(f'MP3 Error: {e}')

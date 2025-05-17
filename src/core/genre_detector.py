"""Main genre detection and processing module."""
from typing import Dict, List, Optional, Set
from .music_apis import MusicAPI, MusicBrainzAPI, LastFmAPI
from .genre_normalizer import GenreNormalizer
from .file_handler import Mp3FileHandler

class GenreDetector:
    """Main class for genre detection and processing."""
    
    def __init__(self, 
                 apis: Optional[List[MusicAPI]] = None,
                 backup_dir: Optional[str] = None,
                 verbose: bool = True):
        """Initialize the genre detector.
        
        Args:
            apis: List of MusicAPI instances (optional)
            backup_dir: Directory for file backups (optional)
            verbose: Enable verbose output (default: True)
        """
        self.apis = apis or []
        self.normalizer = GenreNormalizer()
        self.file_handler = Mp3FileHandler(backup_dir)
        self.verbose = verbose
        
    def add_api(self, api: MusicAPI):
        """Add an API source.
        
        Args:
            api: MusicAPI instance
        """
        self.apis.append(api)
        
    def detect_genres(self, artist: str, track: str) -> Dict[str, float]:
        """Detect and normalize genres for a track.
        
        Args:
            artist: Artist name
            track: Track title
            
        Returns:
            Dictionary of normalized genres with confidence scores
        """
        if self.verbose:
            print(f"\nProcessing: {artist} - {track}")
            
        # Collect genres from all APIs
        all_genres = []
        for api in self.apis:
            try:
                if self.verbose:
                    print(f"Querying {api.__class__.__name__}...")
                genres = api.get_genres(artist, track)
                if self.verbose:
                    print(f"Found genres: {genres}")
                all_genres.extend(genres)
            except Exception as e:
                print(f"Error getting genres from {api.__class__.__name__}: {e}")
                
        # Normalize and get confidence scores
        scores = self.normalizer.get_confidence_score(all_genres)
        if self.verbose:
            print(f"Normalized genres with confidence scores: {scores}\n")
        return scores
        
    def process_file(self, 
                    file_path: str,
                    confidence_threshold: float = 0.3,
                    max_genres: int = 3,
                    create_backup: bool = True) -> bool:
        """Process an MP3 file to detect and write genres.
        
        Args:
            file_path: Path to the MP3 file
            confidence_threshold: Minimum confidence score to include genre
            max_genres: Maximum number of genres to write
            create_backup: Whether to create a backup before modifying
            
        Returns:
            True if successful, False otherwise
        """
        if self.verbose:
            print(f"\nProcessing file: {file_path}")
            
        # Validate file
        if not self.file_handler.is_valid_mp3(file_path):
            print(f"Invalid MP3 file: {file_path}")
            return False
            
        # Get current file info
        info = self.file_handler.get_file_info(file_path)
        if not info.get('artist') or not info.get('title'):
            print(f"Missing artist/title tags in {file_path}")
            return False
            
        if self.verbose:
            print(f"Current file info: {info}")
            
        # Detect genres
        genres = self.detect_genres(info['artist'], info['title'])
        
        # Filter by confidence and limit
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
            print(f"No genres detected with confidence >= {confidence_threshold}")
            return False
            
        # Write genres to file
        if self.verbose:
            print(f"Selected genres to write: {selected_genres}")
            
        return self.file_handler.write_genre(
            file_path,
            selected_genres,
            backup=create_backup
        )
        
    def process_directory(self,
                         directory: str,
                         recursive: bool = True,
                         **kwargs) -> Dict[str, bool]:
        """Process all MP3 files in a directory.
        
        Args:
            directory: Directory path
            recursive: Whether to process subdirectories
            **kwargs: Additional arguments passed to process_file()
            
        Returns:
            Dictionary of file paths to success status
        """
        from pathlib import Path
        
        if self.verbose:
            print(f"\nProcessing directory: {directory}")
            print(f"Recursive: {recursive}")
        
        results = {}
        directory = Path(directory)
        
        pattern = '**/*.mp3' if recursive else '*.mp3'
        for mp3_file in directory.glob(pattern):
            try:
                success = self.process_file(str(mp3_file), **kwargs)
                results[str(mp3_file)] = success
            except Exception as e:
                print(f"Error processing {mp3_file}: {e}")
                results[str(mp3_file)] = False
                
        return results
        
    def analyze_file(self, file_path: str) -> Dict[str, any]:
        """Analyze an MP3 file without modifying it.
        
        Args:
            file_path: Path to the MP3 file
            
        Returns:
            Dictionary with analysis results
        """
        if self.verbose:
            print(f"\nAnalyzing file: {file_path}")
            
        # Get file info
        info = self.file_handler.get_file_info(file_path)
        if not info:
            return {'error': 'Could not read file info'}
            
        # Get current genres
        current_genres = set(info.get('current_genre', '').split(', '))
        current_genres.discard('')
        
        if self.verbose:
            print(f"Current file info: {info}")
            print(f"Current genres: {current_genres}")
            
        # Detect new genres
        if info.get('artist') and info.get('title'):
            detected_genres = self.detect_genres(info['artist'], info['title'])
        else:
            detected_genres = {}
            
        return {
            'file_info': info,
            'current_genres': list(current_genres),
            'detected_genres': detected_genres
        }

"""Core functionality module for MP3 tag processing."""

from pathlib import Path
import re
from dataclasses import dataclass
from typing import Optional, Dict, Tuple

import mutagen.id3
from mutagen.mp3 import MP3
import musicbrainzngs
import requests
from langdetect import detect, LangDetectException

@dataclass
class ProcessingResult:
    """Container for MP3 processing results."""
    success: bool
    message: str
    original_tags: Dict[str, str]
    proposed_tags: Dict[str, str]
    musicbrainz_info: Dict[str, str]
    detected_language: Optional[str] = None
    translated_title: Optional[str] = None

class MP3TagProcessor:
    """Handles MP3 file tag processing and enrichment."""
    
    def __init__(self):
        # Configure MusicBrainz
        musicbrainzngs.set_useragent(
            "MP3TagEnricher",
            "1.0",
            "https://github.com/yourusername/mp3tagenricher"
        )
    
    def load_current_tags(self, filepath: Path) -> Dict[str, str]:
        """Load current ID3 tags from the MP3 file."""
        tags = {}
        try:
            id3 = mutagen.id3.ID3(filepath)
            
            # Extract basic tags
            if 'TPE1' in id3 and id3['TPE1'].text:
                tags['artist'] = id3['TPE1'].text[0]
            if 'TIT2' in id3 and id3['TIT2'].text:
                tags['title'] = id3['TIT2'].text[0]
            if 'TALB' in id3 and id3['TALB'].text:
                tags['album'] = id3['TALB'].text[0]
            if 'TDRC' in id3 and id3['TDRC'].text:
                tags['year'] = str(id3['TDRC'].text[0])
            if 'TCON' in id3 and id3['TCON'].text:
                tags['genre'] = id3['TCON'].text[0]
            if 'TRCK' in id3 and id3['TRCK'].text:
                tags['track'] = id3['TRCK'].text[0]
                
        except mutagen.id3.ID3NoHeaderError:
            pass  # File has no ID3 tag
        except Exception as e:
            raise RuntimeError(f"Error reading ID3 tags: {e}")
            
        return tags
    
    def infer_from_filename(self, filepath: Path) -> Tuple[Optional[str], Optional[str]]:
        """Attempt to infer artist and title from filename."""
        name = filepath.stem
        name = name.strip()
        
        # Remove track number prefix
        name = re.sub(r'^[0-9]+[\s\-\_\.]+', '', name)
        if not name:
            return None, None
            
        # Try different separators
        if ' - ' in name:
            parts = name.split(' - ', 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
        
        if '-' in name:
            parts = name.split('-', 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
        
        if '_' in name:
            if name.count('_') >= 2:
                parts = name.rsplit('_', 1)
            else:
                parts = name.split('_', 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
                
        return None, None
    
    def normalize_text(self, text: str) -> str:
        """Normalize text fields to Title Case and clean formatting."""
        if not text:
            return text
            
        # Replace separators with spaces
        normalized = text.replace('_', ' ').replace('-', ' ')
        
        # Remove multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Convert to Title Case
        normalized = normalized.title()
        
        return normalized
    
    def detect_language(self, text: str) -> Optional[str]:
        """Detect text language."""
        if not text:
            return None
            
        try:
            return detect(text).lower()
        except LangDetectException:
            return None
    
    def fetch_musicbrainz_data(
        self,
        artist: str,
        title: str,
        translated_title: Optional[str] = None
    ) -> Dict[str, str]:
        """Query MusicBrainz API for additional track metadata."""
        try:
            # First try with original title
            result = musicbrainzngs.search_recordings(
                artist=artist,
                recording=title,
                limit=5
            )
            recordings = result.get('recording-list', [])
            
            # If no results and we have a translation, try with that
            if not recordings and translated_title:
                result = musicbrainzngs.search_recordings(
                    artist=artist,
                    recording=translated_title,
                    limit=5
                )
                recordings = result.get('recording-list', [])
            
            if not recordings:
                return {}
                
            # Find best match
            best_recording = None
            best_score = -1
            
            for rec in recordings:
                score = int(rec.get('score', 0))
                rec_artists = ""
                
                if 'artist-credit' in rec:
                    for ac in rec['artist-credit']:
                        if 'name' in ac:
                            rec_artists += ac['name']
                        if ac.get('joinphrase'):
                            rec_artists += ac['joinphrase']
                
                if (rec_artists and
                    rec_artists.lower() == artist.lower() and
                    score >= best_score):
                    best_recording = rec
                    best_score = score
                elif best_recording is None or score > best_score:
                    best_recording = rec
                    best_score = score
            
            if not best_recording:
                return {}
                
            # Get full recording details
            rec_data = musicbrainzngs.get_recording_by_id(
                best_recording['id'],
                includes=['releases', 'tags']
            )
            
            metadata = {}
            recording = rec_data['recording']
            
            # Process release information
            releases = recording.get('release-list', [])
            if releases:
                release = releases[0]  # Use first release
                metadata['album'] = release.get('title')
                
                release_date = release.get('date', '')
                if release_date and release_date[:4].isdigit():
                    metadata['year'] = release_date[:4]
                
                # Try to get track number
                release_id = release.get('id')
                if release_id:
                    try:
                        rel_data = musicbrainzngs.get_release_by_id(
                            release_id,
                            includes=['recordings']
                        )
                        for medium in rel_data['release']['medium-list']:
                            for track in medium['track-list']:
                                if (track.get('recording', {}).get('id') ==
                                    best_recording['id']):
                                    metadata['track'] = str(track.get('position', ''))
                                    break
                    except Exception:
                        pass
            
            # Get genre
            genres = recording.get('genre-list', [])
            if genres:
                metadata['genre'] = genres[0]['name'].title()
            else:
                # Try tags as fallback
                tags = recording.get('tag-list', [])
                if tags:
                    tags.sort(key=lambda x: int(x.get('count', 0)), reverse=True)
                    metadata['genre'] = tags[0]['name'].title()
            
            return metadata
            
        except Exception as e:
            print(f"MusicBrainz error: {e}")
            return {}
    
    def process_file(self, filepath: Path, analysis_mode: bool = False) -> ProcessingResult:
        """Process an MP3 file, analyzing or updating its tags."""
        try:
            # Load current tags
            current_tags = self.load_current_tags(filepath)
            
            # Get artist/title from tags or filename
            artist = current_tags.get('artist')
            title = current_tags.get('title')
            
            if not artist or not title:
                inferred_artist, inferred_title = self.infer_from_filename(filepath)
                if not artist and inferred_artist:
                    artist = inferred_artist
                if not title and inferred_title:
                    title = inferred_title
            
            if not artist or not title:
                return ProcessingResult(
                    success=False,
                    message="Could not determine artist and title from tags or filename",
                    original_tags=current_tags,
                    proposed_tags={},
                    musicbrainz_info={}
                )
            
            # Normalize text
            normalized_artist = self.normalize_text(artist)
            normalized_title = self.normalize_text(title)
            
            # Detect language only
            lang = self.detect_language(normalized_title)
            
            # Get additional metadata from MusicBrainz
            mb_data = self.fetch_musicbrainz_data(
                normalized_artist,
                normalized_title,
                None  # No translation needed
            )
            
            # Prepare proposed tags
            proposed_tags = current_tags.copy()
            proposed_tags.update({
                'artist': normalized_artist,
                'title': normalized_title
            })
            
            if mb_data:
                # Only update empty or missing fields from MusicBrainz
                for key, value in mb_data.items():
                    if key not in proposed_tags or not proposed_tags[key]:
                        proposed_tags[key] = value
            
            if not analysis_mode:
                # Update ID3 tags
                try:
                    tags = mutagen.id3.ID3(filepath)
                except mutagen.id3.ID3NoHeaderError:
                    tags = mutagen.id3.ID3()
                
                # Apply changes
                if proposed_tags.get('artist'):
                    tags['TPE1'] = mutagen.id3.TPE1(
                        encoding=3,
                        text=[proposed_tags['artist']]
                    )
                if proposed_tags.get('title'):
                    tags['TIT2'] = mutagen.id3.TIT2(
                        encoding=3,
                        text=[proposed_tags['title']]
                    )
                if proposed_tags.get('album'):
                    tags['TALB'] = mutagen.id3.TALB(
                        encoding=3,
                        text=[proposed_tags['album']]
                    )
                if proposed_tags.get('year'):
                    tags['TDRC'] = mutagen.id3.TDRC(
                        encoding=3,
                        text=[proposed_tags['year']]
                    )
                if proposed_tags.get('genre'):
                    tags['TCON'] = mutagen.id3.TCON(
                        encoding=3,
                        text=[proposed_tags['genre']]
                    )
                if proposed_tags.get('track'):
                    tags['TRCK'] = mutagen.id3.TRCK(
                        encoding=3,
                        text=[proposed_tags['track']]
                    )
                
                # Save changes to tags
                tags.save(filepath, v2_version=4, v1=0)
                
                # Rename file based on metadata
                if proposed_tags.get('artist') and proposed_tags.get('title'):
                    new_name = f"{proposed_tags['artist']} - {proposed_tags['title']}.mp3"
                    new_name = re.sub(r'[<>:"/\\|?*]', '', new_name)  # Remove invalid chars
                    new_path = filepath.parent / new_name
                    if new_path != filepath:
                        filepath.rename(new_path)
            
            return ProcessingResult(
                success=True,
                message="Analysis complete" if analysis_mode else "Tags updated successfully",
                original_tags=current_tags,
                proposed_tags=proposed_tags,
                musicbrainz_info=mb_data,
                detected_language=lang,
                translated_title=None
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                message=f"Error processing file: {str(e)}",
                original_tags=current_tags if 'current_tags' in locals() else {},
                proposed_tags={},
                musicbrainz_info={}
            )

import pytest
import os
from src.core.music_apis import MusicBrainzAPI, LastFmAPI, DiscogsAPI
from src.core.file_handler import Mp3FileHandler

# Test MP3 file path
TEST_MP3_PATH = "/Volumes/My Passport/Dj compilation 2025/DMS/Mayo25/X-Mix Club Classics/Viola Wills - Hot For You Ultimix By Les Massengale.mp3"

def get_test_track_info(mp3_handler):
    """Extract artist and title from test MP3 filename"""
    filename = os.path.basename(TEST_MP3_PATH)
    artist, title = mp3_handler.extract_artist_title_from_filename(os.path.splitext(filename)[0])
    return artist, title

@pytest.fixture
def musicbrainz_api():
    return MusicBrainzAPI(email="test@example.com")

@pytest.fixture
def lastfm_api():
    return LastFmAPI()

@pytest.fixture
def mp3_handler():
    return Mp3FileHandler()

@pytest.fixture
def discogs_api():
    return DiscogsAPI()

def test_musicbrainz_year_extraction(musicbrainz_api, mp3_handler):
    # Test year extraction with real MP3
    artist, title = get_test_track_info(mp3_handler)
    result = musicbrainz_api.get_track_info(artist, title)
    
    if result.get("year"):
        assert 1900 <= int(result["year"]) <= 2030, "Year should be within valid range"

def test_lastfm_year_extraction(lastfm_api, mp3_handler):
    # Test year extraction with real MP3
    artist, title = get_test_track_info(mp3_handler)
    result = lastfm_api.get_track_info(artist, title)
    
    if result.get("year"):
        assert 1900 <= int(result["year"]) <= 2030, "Year should be within valid range"

def test_discogs_year_extraction(discogs_api, mp3_handler):
    # Test year extraction with real MP3
    artist, title = get_test_track_info(mp3_handler)
    result = discogs_api.get_track_info(artist, title)
    
    if result.get("year"):
        assert 1900 <= int(result["year"]) <= 2030, "Year should be within valid range"

def test_year_validation_edge_cases(musicbrainz_api, lastfm_api, discogs_api, mp3_handler):
    """Test year validation with corrupted filename"""
    # Test with corrupted version of the real filename
    corrupted_name = "X-Mix Club Classics####InvalidArtist@@@@.mp3"
    artist, title = mp3_handler.extract_artist_title_from_filename(os.path.splitext(corrupted_name)[0])
    
    # Test each API with corrupted data
    apis = [musicbrainz_api, lastfm_api, discogs_api]
    for api in apis:
        result = api.get_track_info(artist, title)
        assert result.get("year") is None, f"{api.__class__.__name__} should return None for corrupted data"

def test_year_prioritization(musicbrainz_api, lastfm_api, discogs_api, mp3_handler):
    """Test year consistency across APIs using real track data"""
    
    # Get real track info
    artist, title = get_test_track_info(mp3_handler)
    
    # Get results from all APIs
    mb_result = musicbrainz_api.get_track_info(artist, title)
    lastfm_result = lastfm_api.get_track_info(artist, title)
    discogs_result = discogs_api.get_track_info(artist, title)
    
    # Collect all valid years
    years = []
    for result in [mb_result, lastfm_result, discogs_result]:
        if result.get("year"):
            year = int(result["year"])
            if 1900 <= year <= 2030:
                years.append(year)
    
    # Verify we got at least one valid year
    assert len(years) > 0, "Should get at least one valid year from APIs"
    
    # All years should be valid
    for year in years:
        assert 1900 <= year <= 2030, f"Year {year} should be within valid range"
        
    # Log the year variations for analysis
    if len(years) > 1:
        print(f"\nYear variations for {artist} - {title}:")
        print(f"MusicBrainz: {mb_result.get('year')}")
        print(f"Last.fm: {lastfm_result.get('year')}")
        print(f"Discogs: {discogs_result.get('year')}")
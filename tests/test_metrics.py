"""Tests for API metrics tracking."""
import pytest
import time
from pathlib import Path
import tempfile
import json
from typing import Dict, Any

from src.core.music_apis import MusicBrainzAPI, LastFmAPI, DiscogsAPI
from src.core.api_metrics import MetricsTracker

@pytest.fixture
def metrics_file():
    """Create temporary metrics file."""
    with tempfile.NamedTemporaryFile(suffix='.json') as f:
        yield f.name

@pytest.fixture
def tracker(metrics_file):
    """Create metrics tracker instance."""
    return MetricsTracker(metrics_file)

@pytest.fixture
def apis(mocker):
    """Create API instances with mocked external calls."""
    # Mock MusicBrainz
    mocker.patch('musicbrainzngs.search_recordings', return_value={"recording-list": []})
    mb_api = MusicBrainzAPI()
    
    # Mock Last.fm
    mocker.patch('pylast.LastFMNetwork')
    lastfm_api = LastFmAPI()
    
    # Mock Discogs
    mocker.patch('requests.get')
    discogs_api = DiscogsAPI()
    
    return {"musicbrainz": mb_api, "lastfm": lastfm_api, "discogs": discogs_api}

def test_metrics_recording(apis, tracker):
    """Test recording of API call metrics."""
    # Make API calls and verify metrics
    mb_api = apis["musicbrainz"]
    
    # Successful call
    mb_api.get_track_info("Artist", "Track")
    metrics = mb_api.get_metrics()
    
    assert metrics["total_calls"] == 1
    assert metrics["success_rate"] == 1.0
    assert 0 <= metrics["avg_latency"] <= 1.0  # Should be very quick for mocked calls
    assert metrics["rate_limit_ratio"] == 0.0

def test_metrics_persistence(apis, metrics_file):
    """Test that metrics persist between tracker instances."""
    mb_api = apis["musicbrainz"]
    
    # Make some API calls
    mb_api.get_track_info("Artist 1", "Track 1")
    mb_api.get_track_info("Artist 2", "Track 2")
    
    # Create new tracker and verify metrics loaded
    new_tracker = MetricsTracker(metrics_file)
    metrics = new_tracker.get_metrics("MusicBrainzAPI")
    
    assert metrics["total_calls"] == 2
    assert metrics["success_rate"] == 1.0

def test_rate_limit_tracking(apis, tracker, mocker):
    """Test tracking of rate limit hits."""
    mb_api = apis["musicbrainz"]
    
    # Mock rate limit exceeded
    mocker.patch('src.core.rate_limiter.RateLimiter.acquire', return_value=False)
    
    # This should hit rate limit
    with pytest.raises(RuntimeError):
        mb_api.get_track_info("Artist", "Track")
    
    metrics = mb_api.get_metrics()
    assert metrics["rate_limit_ratio"] > 0
    assert metrics["success_rate"] < 1.0

def test_error_tracking(apis, tracker, mocker):
    """Test tracking of API errors."""
    lastfm_api = apis["lastfm"]
    
    # Mock API error
    mock_network = mocker.MagicMock()
    mock_network.get_track.side_effect = Exception("API Error")
    lastfm_api.network = mock_network
    
    # Make failing call
    lastfm_api.get_track_info("Artist", "Track")
    
    metrics = lastfm_api.get_metrics()
    assert metrics["success_rate"] < 1.0
    assert metrics["total_calls"] == 1
    assert metrics["rate_limit_ratio"] == 0.0  # No rate limit hit

def test_latency_tracking(apis, tracker):
    """Test tracking of API call latencies."""
    discogs_api = apis["discogs"]
    
    # Make API call with artificial delay
    time.sleep(0.1)  # Add 100ms delay
    discogs_api.get_track_info("Artist", "Track")
    
    metrics = discogs_api.get_metrics()
    assert metrics["avg_latency"] >= 0.1  # Should include our delay

def test_multi_api_tracking(apis, tracker):
    """Test tracking metrics for multiple APIs."""
    # Make calls to different APIs
    apis["musicbrainz"].get_track_info("Artist", "Track")
    apis["lastfm"].get_track_info("Artist", "Track")
    apis["discogs"].get_track_info("Artist", "Track")
    
    # Verify separate metrics for each
    mb_metrics = apis["musicbrainz"].get_metrics()
    lastfm_metrics = apis["lastfm"].get_metrics()
    discogs_metrics = apis["discogs"].get_metrics()
    
    assert mb_metrics["total_calls"] == 1
    assert lastfm_metrics["total_calls"] == 1
    assert discogs_metrics["total_calls"] == 1
    
    # Each should have independent success rates
    assert mb_metrics["success_rate"] != lastfm_metrics["success_rate"] or \
           mb_metrics["success_rate"] != discogs_metrics["success_rate"] or \
           lastfm_metrics["success_rate"] != discogs_metrics["success_rate"]
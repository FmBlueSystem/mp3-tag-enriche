"""Tests for API metrics tracking."""
import pytest
import time
import tempfile
from pathlib import Path
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

def test_basic_metrics_recording(tracker):
    """Test recording basic API call metrics."""
    # Record successful call
    tracker.record_api_call("TestAPI", success=True, latency=0.1)
    
    metrics = tracker.get_metrics("TestAPI")
    assert metrics["total_calls"] == 1
    assert metrics["success_rate"] == 1.0
    assert metrics["avg_latency"] == 0.1
    assert metrics["rate_limit_ratio"] == 0.0
    
    # Record failed call
    tracker.record_api_call("TestAPI", success=False, latency=0.2)
    
    metrics = tracker.get_metrics("TestAPI")
    assert metrics["total_calls"] == 2
    assert metrics["success_rate"] == 0.5
    assert metrics["avg_latency"] == 0.15  # (0.1 + 0.2) / 2
    assert metrics["rate_limit_ratio"] == 0.0

def test_rate_limit_tracking(tracker):
    """Test tracking rate limit hits."""
    # Record normal call
    tracker.record_api_call("TestAPI", success=True, latency=0.1)
    
    # Record rate limited call
    tracker.record_api_call("TestAPI", success=False, latency=0.1, rate_limited=True)
    
    metrics = tracker.get_metrics("TestAPI")
    assert metrics["total_calls"] == 2
    assert metrics["success_rate"] == 0.5
    assert metrics["rate_limit_ratio"] == 0.5

def test_multiple_apis(tracker):
    """Test tracking metrics for multiple APIs."""
    # Record calls for API1
    tracker.record_api_call("API1", success=True, latency=0.1)
    tracker.record_api_call("API1", success=True, latency=0.2)
    
    # Record calls for API2
    tracker.record_api_call("API2", success=False, latency=0.3)
    
    # Check API1 metrics
    metrics1 = tracker.get_metrics("API1")
    assert metrics1["total_calls"] == 2
    assert metrics1["success_rate"] == 1.0
    assert metrics1["avg_latency"] == 0.15
    
    # Check API2 metrics
    metrics2 = tracker.get_metrics("API2")
    assert metrics2["total_calls"] == 1
    assert metrics2["success_rate"] == 0.0
    assert metrics2["avg_latency"] == 0.3

def test_metrics_persistence(metrics_file):
    """Test that metrics persist between tracker instances."""
    # Create first tracker and record calls
    tracker1 = MetricsTracker(metrics_file)
    tracker1.record_api_call("TestAPI", success=True, latency=0.1)
    tracker1.record_api_call("TestAPI", success=False, latency=0.2)
    
    # Create new tracker instance
    tracker2 = MetricsTracker(metrics_file)
    
    # Verify metrics were loaded
    metrics = tracker2.get_metrics("TestAPI")
    assert metrics["total_calls"] == 2
    assert metrics["success_rate"] == 0.5
    assert metrics["avg_latency"] == 0.15

def test_nonexistent_api(tracker):
    """Test getting metrics for nonexistent API."""
    metrics = tracker.get_metrics("NonexistentAPI")
    assert metrics["total_calls"] == 0
    assert metrics["success_rate"] == 0.0
    assert metrics["avg_latency"] == 0.0
    assert metrics["rate_limit_ratio"] == 0.0

def test_reset_metrics(tracker):
    """Test resetting metrics."""
    # Record calls for multiple APIs
    tracker.record_api_call("API1", success=True, latency=0.1)
    tracker.record_api_call("API2", success=True, latency=0.2)
    
    # Reset metrics for API1
    tracker.reset_metrics("API1")
    assert tracker.get_metrics("API1")["total_calls"] == 0
    assert tracker.get_metrics("API2")["total_calls"] == 1
    
    # Reset all metrics
    tracker.reset_metrics()
    assert tracker.get_metrics("API1")["total_calls"] == 0
    assert tracker.get_metrics("API2")["total_calls"] == 0

def test_corrupted_metrics_file(metrics_file):
    """Test handling of corrupted metrics file."""
    # Write invalid JSON to metrics file
    Path(metrics_file).write_text("invalid json")
    
    # Should handle gracefully and start with empty metrics
    tracker = MetricsTracker(metrics_file)
    assert tracker.get_metrics("TestAPI")["total_calls"] == 0
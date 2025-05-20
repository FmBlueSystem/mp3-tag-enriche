"""Tests for token bucket rate limiter with fixed-point precision."""
import pytest
import time
from src.core.rate_limiter import RateLimiter

def test_basic_rate_limiting():
    """Test basic token bucket functionality with precise checks."""
    limiter = RateLimiter()
    limiter.create_limit("test", capacity=10, fill_rate=2)  # 2 tokens/second
    
    # Initial tokens should be at capacity
    assert limiter.get_token_count("test") == pytest.approx(10, abs=1e-6)
    
    # Use 5 tokens
    assert limiter.acquire("test", tokens=5)
    assert limiter.get_token_count("test") == pytest.approx(5, abs=1e-6)
    
    # Use remaining 5 tokens
    assert limiter.acquire("test", tokens=5)
    assert limiter.get_token_count("test") == pytest.approx(0, abs=1e-6)
    
    # Should not be able to get more tokens immediately
    assert not limiter.acquire("test", tokens=1, wait=False)

def test_token_replenishment():
    """Test precise token replenishment rate."""
    limiter = RateLimiter()
    limiter.create_limit("test", capacity=10, fill_rate=2)  # 2 tokens/second
    
    # Use all tokens
    assert limiter.acquire("test", tokens=10)
    assert limiter.get_token_count("test") == pytest.approx(0, abs=1e-6)
    
    # Wait 0.5 seconds, should have 1 new token
    time.sleep(0.5)
    assert limiter.get_token_count("test") == pytest.approx(1, abs=1e-5)
    
    # Wait another 0.5 seconds, should have 2 tokens
    time.sleep(0.5)
    assert limiter.get_token_count("test") == pytest.approx(2, abs=1e-5)

def test_burst_capacity():
    """Test burst handling with maximum capacity and precise timing."""
    limiter = RateLimiter()
    limiter.create_limit("test", capacity=5, fill_rate=1)  # 1 token/second
    
    assert limiter.get_token_count("test") == pytest.approx(5, abs=1e-6)
    
    # Use 3 tokens
    assert limiter.acquire("test", tokens=3)
    assert limiter.get_token_count("test") == pytest.approx(2, abs=1e-6)
    
    # Wait 1.5 seconds, should have 3.5 tokens
    time.sleep(1.5)
    assert limiter.get_token_count("test") == pytest.approx(3.5, abs=1e-5)
    
    # Try to use 4 tokens (should fail)
    assert not limiter.acquire("test", tokens=4, wait=False)
    
    # Use 3 tokens (should succeed)
    assert limiter.acquire("test", tokens=3)
    assert limiter.get_token_count("test") == pytest.approx(0.5, abs=1e-5)

def test_multiple_buckets():
    """Test multiple rate limiters with different configurations."""
    limiter = RateLimiter()
    limiter.create_limit("fast", capacity=10, fill_rate=10)  # 10 tokens/second
    limiter.create_limit("slow", capacity=5, fill_rate=1)    # 1 token/second
    
    # Use tokens from both buckets
    assert limiter.acquire("fast", tokens=5)
    assert limiter.acquire("slow", tokens=3)
    
    # Check remaining tokens
    assert limiter.get_token_count("fast") == pytest.approx(5, abs=1e-6)
    assert limiter.get_token_count("slow") == pytest.approx(2, abs=1e-6)
    
    # Different replenishment rates
    time.sleep(0.5)
    fast_count = limiter.get_token_count("fast")
    slow_count = limiter.get_token_count("slow")
    
    assert fast_count == pytest.approx(10, abs=1e-5)  # Should be full (10 * 0.5 = 5 new tokens)
    assert slow_count == pytest.approx(2.5, abs=1e-5)  # Should have gained 0.5

def test_boundary_conditions():
    """Test boundary conditions and edge cases."""
    limiter = RateLimiter()
    limiter.create_limit("test", capacity=1.5, fill_rate=1)  # Small capacity
    
    # Verify initial state
    assert limiter.get_token_count("test") == pytest.approx(1.5, abs=1e-6)
    
    # Test fractional token acquisition
    assert limiter.acquire("test", tokens=0.3)
    assert limiter.get_token_count("test") == pytest.approx(1.2, abs=1e-6)
    
    # Test very small token request
    assert limiter.acquire("test", tokens=0.0001)
    assert limiter.get_token_count("test") == pytest.approx(1.1999, abs=1e-6)
    
    # Test exact capacity token request
    limiter.create_limit("exact", capacity=2, fill_rate=1)
    assert limiter.acquire("exact", tokens=2)
    assert limiter.get_token_count("exact") == pytest.approx(0, abs=1e-6)

def test_nonexistent_bucket():
    """Test behavior with nonexistent bucket."""
    limiter = RateLimiter()
    
    # Should return True when bucket doesn't exist
    assert limiter.acquire("nonexistent")
    assert limiter.get_token_count("nonexistent") is None

def test_high_precision_timing():
    """Test precise timing and token accumulation."""
    limiter = RateLimiter()
    limiter.create_limit("precise", capacity=10, fill_rate=0.1)  # 0.1 tokens/second
    
    # Use 1 token
    assert limiter.acquire("precise", tokens=1)
    assert limiter.get_token_count("precise") == pytest.approx(9, abs=1e-6)
    
    # Wait 0.15 seconds - should accumulate 0.015 tokens
    time.sleep(0.15)
    assert limiter.get_token_count("precise") == pytest.approx(9.015, abs=1e-5)
"""Token bucket rate limiter implementation with fixed-point arithmetic."""
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from threading import Lock
import logging

logger = logging.getLogger(__name__)

# Use integer arithmetic with fixed-point scaling
SCALE_FACTOR = 1000000  # 6 decimal places of precision

def _to_fixed(value: float) -> int:
    """Convert float to fixed-point integer."""
    return int(value * SCALE_FACTOR)

def _from_fixed(value: int) -> float:
    """Convert fixed-point integer to float."""
    return value / SCALE_FACTOR

@dataclass
class TokenBucket:
    """Token bucket for rate limiting using fixed-point arithmetic."""
    capacity: int      # Maximum number of tokens (fixed-point)
    fill_rate: int     # Tokens per second (fixed-point)
    tokens: int = 0    # Current token count (fixed-point)
    last_update: int = 0  # Last update timestamp in nanoseconds

class RateLimiter:
    """Token bucket rate limiter implementation using fixed-point arithmetic."""
    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = Lock()
        
    def create_limit(self, key: str, capacity: float, fill_rate: float) -> None:
        """Create a new rate limit bucket.
        
        Args:
            key: Unique identifier for this rate limit
            capacity: Maximum number of tokens (burst capacity)
            fill_rate: Rate of token replenishment per second
        """
        with self._lock:
            self._buckets[key] = TokenBucket(
                capacity=_to_fixed(capacity),
                fill_rate=_to_fixed(fill_rate),
                tokens=_to_fixed(capacity),  # Start full
                last_update=int(time.time_ns())
            )

    def _update_tokens(self, bucket: TokenBucket) -> None:
        """Update token count based on elapsed time using fixed-point arithmetic."""
        now_ns = time.time_ns()
        if bucket.last_update:
            # Calculate elapsed time in seconds with nanosecond precision
            elapsed_ns = now_ns - bucket.last_update
            elapsed_seconds = elapsed_ns / 1e9
            
            # Calculate new tokens using fixed-point multiplication
            new_tokens = int(elapsed_seconds * bucket.fill_rate)
            bucket.tokens = min(bucket.capacity, bucket.tokens + new_tokens)
            
        bucket.last_update = now_ns

    def acquire(self, key: str, tokens: float = 1.0, wait: bool = True) -> bool:
        """Attempt to acquire tokens from the bucket.
        
        Args:
            key: Bucket identifier
            tokens: Number of tokens to acquire
            wait: If True, wait for tokens to become available
            
        Returns:
            True if tokens were acquired, False if not available and wait=False
        """
        tokens_fixed = _to_fixed(tokens)
        
        with self._lock:
            bucket = self._buckets.get(key)
            if not bucket:
                logger.warning(f"No rate limit bucket found for key: {key}")
                return True  # Allow if no bucket exists
            
            while True:
                self._update_tokens(bucket)
                
                if bucket.tokens >= tokens_fixed:
                    bucket.tokens -= tokens_fixed
                    return True
                    
                if not wait:
                    return False
                
                # Calculate sleep time needed for enough tokens
                needed = tokens_fixed - bucket.tokens
                # Convert to float for division to maintain precision
                sleep_time = _from_fixed(needed) / _from_fixed(bucket.fill_rate)
                
                # Release lock while sleeping
                self._lock.release()
                try:
                    # Add small buffer to avoid waking up just slightly too early
                    time.sleep(sleep_time + 0.0001)
                finally:
                    self._lock.acquire()

    def get_token_count(self, key: str) -> Optional[float]:
        """Get current token count for a bucket."""
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket:
                self._update_tokens(bucket)
                return _from_fixed(bucket.tokens)
            return None
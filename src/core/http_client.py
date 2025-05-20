"""HTTP client with connection pooling, circuit breaker, and retries."""
import time
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Any, Callable
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from threading import Lock

logger = logging.getLogger(__name__)

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5  # Number of failures before opening
    reset_timeout: float = 60.0  # Seconds to wait before attempting reset
    half_open_timeout: float = 30.0  # Seconds to wait in half-open state

class CircuitBreaker:
    """Circuit breaker implementation."""
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failures = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
        self._lock = Lock()

    def record_failure(self):
        """Record a failure and possibly open the circuit."""
        with self._lock:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.config.failure_threshold:
                self.state = "open"
                logger.warning("Circuit breaker opened due to too many failures")

    def record_success(self):
        """Record a success and possibly close the circuit."""
        with self._lock:
            self.failures = 0
            if self.state == "half-open":
                self.state = "closed"
                logger.info("Circuit breaker closed after successful test request")

    def can_execute(self) -> bool:
        """Check if the request can be executed based on circuit state."""
        with self._lock:
            now = time.time()
            
            if self.state == "closed":
                return True
                
            elif self.state == "open":
                # Check if enough time has passed to try half-open
                if now - self.last_failure_time > self.config.reset_timeout:
                    self.state = "half-open"
                    logger.info("Circuit breaker entering half-open state")
                    return True
                return False
                
            elif self.state == "half-open":
                # Allow limited requests in half-open state
                return now - self.last_failure_time > self.config.half_open_timeout
                
            return True

class HTTPClient:
    """HTTP client with connection pooling, circuit breaker and retries."""
    
    def __init__(
        self,
        base_url: str,
        pool_connections: int = 10,
        pool_maxsize: int = 10,
        max_retries: int = 3,
        timeout: int = 15,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    ):
        """Initialize HTTP client.
        
        Args:
            base_url: Base URL for all requests
            pool_connections: Number of connection pools to cache
            pool_maxsize: Maximum number of connections to save in the pool
            max_retries: Maximum number of retries for failed requests
            timeout: Request timeout in seconds
            circuit_breaker_config: Circuit breaker configuration
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Configure retries with exponential backoff
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,  # Will sleep for [0.5, 1, 2, 4, ...] seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'])
        )
        
        # Configure connection pooling
        adapter = HTTPAdapter(
            pool_connections=pool_connections,  # Number of pools
            pool_maxsize=pool_maxsize,        # Connections per pool
            max_retries=retry_strategy
        )
        
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            circuit_breaker_config or CircuitBreakerConfig()
        )
        
    def request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[requests.Response]:
        """Make an HTTP request with circuit breaker protection.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (will be joined with base_url)
            headers: Request headers
            params: Query parameters
            json: JSON body data
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response object or None if request failed
            
        Raises:
            RuntimeError: If circuit breaker is open
        """
        if not self.circuit_breaker.can_execute():
            raise RuntimeError(
                f"Circuit breaker is open. Too many failures, waiting "
                f"{self.circuit_breaker.config.reset_timeout}s before retry."
            )
            
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            
            self.circuit_breaker.record_success()
            return response
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error making request to {url}: {e}")
            if e.response.status_code >= 500:
                self.circuit_breaker.record_failure()
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error making request to {url}: {e}")
            self.circuit_breaker.record_failure()
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error making request to {url}: {e}", exc_info=True)
            self.circuit_breaker.record_failure()
            return None
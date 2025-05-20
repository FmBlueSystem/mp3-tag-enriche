"""API metrics tracking."""
import time
from dataclasses import dataclass
from typing import Dict, List
import logging
from threading import Lock
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class APIMetrics:
    """API call metrics."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_latency: float = 0.0
    rate_limit_hits: int = 0

class MetricsTracker:
    """Tracks API metrics with persistence."""
    
    def __init__(self, metrics_file: str = "api_metrics.json"):
        """Initialize metrics tracker.
        
        Args:
            metrics_file: Path to save metrics (default: api_metrics.json)
        """
        self._metrics: Dict[str, APIMetrics] = {}
        self._lock = Lock()
        self._metrics_file = Path(metrics_file)
        self._load_metrics()
    
    def _load_metrics(self) -> None:
        """Load saved metrics from disk."""
        if not self._metrics_file.exists():
            return
            
        try:
            data = json.loads(self._metrics_file.read_text())
            with self._lock:
                self._metrics = {
                    api: APIMetrics(**metrics)
                    for api, metrics in data.items()
                }
        except Exception as e:
            logger.error(f"Failed to load metrics from {self._metrics_file}: {e}")
    
    def _save_metrics(self) -> None:
        """Save metrics to disk."""
        try:
            data = {
                api: {
                    "total_calls": m.total_calls,
                    "successful_calls": m.successful_calls,
                    "failed_calls": m.failed_calls,
                    "total_latency": m.total_latency,
                    "rate_limit_hits": m.rate_limit_hits
                }
                for api, m in self._metrics.items()
            }
            self._metrics_file.write_text(json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to save metrics to {self._metrics_file}: {e}")
    
    def record_api_call(self, api: str, success: bool, latency: float, rate_limited: bool = False) -> None:
        """Record metrics for an API call.
        
        Args:
            api: Name of the API
            success: Whether the call succeeded
            latency: Call latency in seconds
            rate_limited: Whether call was rate limited
        """
        with self._lock:
            if api not in self._metrics:
                self._metrics[api] = APIMetrics()
            
            metrics = self._metrics[api]
            metrics.total_calls += 1
            metrics.total_latency += latency
            
            if success:
                metrics.successful_calls += 1
            else:
                metrics.failed_calls += 1
                
            if rate_limited:
                metrics.rate_limit_hits += 1
            
            self._save_metrics()
    
    def get_metrics(self, api: str) -> Dict[str, float]:
        """Get current metrics for an API.
        
        Args:
            api: Name of the API
            
        Returns:
            Dict containing metrics and calculated values
        """
        with self._lock:
            if api not in self._metrics:
                return {
                    "total_calls": 0,
                    "success_rate": 0.0,
                    "avg_latency": 0.0,
                    "rate_limit_ratio": 0.0
                }
            
            m = self._metrics[api]
            total = max(m.total_calls, 1)  # Avoid division by zero
            
            return {
                "total_calls": m.total_calls,
                "success_rate": m.successful_calls / total,
                "avg_latency": m.total_latency / total,
                "rate_limit_ratio": m.rate_limit_hits / total
            }
    
    def reset_metrics(self, api: str = None) -> None:
        """Reset metrics for specified API or all APIs.
        
        Args:
            api: API to reset, or None to reset all
        """
        with self._lock:
            if api:
                self._metrics.pop(api, None)
            else:
                self._metrics.clear()
            self._save_metrics()
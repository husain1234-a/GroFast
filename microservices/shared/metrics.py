import time
from typing import Dict, Optional
from collections import defaultdict, deque
import threading
import json

class MetricsCollector:
    """Simple metrics collector for microservices"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._lock = threading.Lock()
        
        # Counters
        self.counters: Dict[str, int] = defaultdict(int)
        
        # Gauges
        self.gauges: Dict[str, float] = {}
        
        # Histograms (response times, etc.)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        
        # Request tracking
        self.active_requests = 0
        self.total_requests = 0
        self.request_errors = 0
    
    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        with self._lock:
            key = self._make_key(name, labels)
            self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        with self._lock:
            key = self._make_key(name, labels)
            self.gauges[key] = value
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a value in a histogram"""
        with self._lock:
            key = self._make_key(name, labels)
            self.histograms[key].append(value)
    
    def start_request(self):
        """Track request start"""
        with self._lock:
            self.active_requests += 1
            self.total_requests += 1
    
    def end_request(self, success: bool = True):
        """Track request end"""
        with self._lock:
            self.active_requests = max(0, self.active_requests - 1)
            if not success:
                self.request_errors += 1
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create metric key with labels"""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics(self) -> Dict:
        """Get all metrics as dictionary"""
        with self._lock:
            metrics = {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "active_requests": self.active_requests,
                "total_requests": self.total_requests,
                "request_errors": self.request_errors,
                "error_rate": self.request_errors / max(1, self.total_requests),
                "histograms": {}
            }
            
            # Calculate histogram statistics
            for name, values in self.histograms.items():
                if values:
                    sorted_values = sorted(values)
                    count = len(sorted_values)
                    metrics["histograms"][name] = {
                        "count": count,
                        "min": min(sorted_values),
                        "max": max(sorted_values),
                        "avg": sum(sorted_values) / count,
                        "p50": sorted_values[int(count * 0.5)],
                        "p95": sorted_values[int(count * 0.95)],
                        "p99": sorted_values[int(count * 0.99)]
                    }
            
            return metrics
    
    def get_prometheus_format(self) -> str:
        """Get metrics in Prometheus format"""
        lines = []
        
        # Counters
        for name, value in self.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        
        # Gauges
        for name, value in self.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        # System metrics
        lines.append("# TYPE http_requests_total counter")
        lines.append(f"http_requests_total {self.total_requests}")
        
        lines.append("# TYPE http_requests_active gauge")
        lines.append(f"http_requests_active {self.active_requests}")
        
        lines.append("# TYPE http_request_errors_total counter")
        lines.append(f"http_request_errors_total {self.request_errors}")
        
        return "\n".join(lines)

# Global metrics instance
metrics = MetricsCollector()

class MetricsMiddleware:
    """FastAPI middleware for automatic metrics collection"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        metrics.start_request()
        
        # Track response
        status_code = 500  # Default to error
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
            success = 200 <= status_code < 400
        except Exception as e:
            success = False
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            metrics.end_request(success)
            metrics.record_histogram("http_request_duration_seconds", duration)
            metrics.increment_counter("http_requests_total", labels={
                "method": scope["method"],
                "status": str(status_code)
            })
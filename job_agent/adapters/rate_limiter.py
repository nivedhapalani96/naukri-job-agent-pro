import time
from typing import Optional

class RateLimiter:
    """Simple rate limiter to avoid overwhelming servers."""
    
    def __init__(self, min_interval_seconds: float = 1.0):
        self.min_interval = min_interval_seconds
        self.last_request_time: Optional[float] = None
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limit."""
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()


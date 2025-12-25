import requests
from typing import Optional
from job_agent.models.config import RequestCfg
from job_agent.adapters.rate_limiter import RateLimiter

class NaukriHTTPClient:
    """HTTP client for Naukri.com with rate limiting."""
    
    def __init__(self, cfg: RequestCfg, rate_limiter: Optional[RateLimiter] = None):
        self.cfg = cfg
        self.rate_limiter = rate_limiter or RateLimiter()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": cfg.user_agent,
        })
    
    def get(self, url: str) -> requests.Response:
        """Fetch a URL with rate limiting."""
        self.rate_limiter.wait_if_needed()
        response = self.session.get(url, timeout=self.cfg.timeout_seconds)
        response.raise_for_status()
        return response


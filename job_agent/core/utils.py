import hashlib
from urllib.parse import urlparse, urlunparse

def stable_job_key(url: str) -> str:
    """
    Generate a stable job key by normalizing the URL and hashing it.
    This ensures idempotency across polling cycles.
    """
    try:
        u = urlparse(url)
        url = urlunparse((u.scheme, u.netloc, u.path, u.params, u.query, ""))
    except Exception:
        pass

    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]

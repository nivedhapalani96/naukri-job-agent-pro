from datetime import datetime
import pytz

class Clock:
    """Provides timezone-aware datetime operations."""
    
    def __init__(self, timezone: str = "UTC"):
        self.tz = pytz.timezone(timezone)
    
    def now_utc(self) -> datetime:
        """Return current UTC datetime."""
        return datetime.now(pytz.UTC)
    
    def now_local(self) -> datetime:
        """Return current local datetime in configured timezone."""
        return datetime.now(self.tz)


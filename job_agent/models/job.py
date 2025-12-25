from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class JobPosting:
    source: str
    title: str
    company: str
    location: str
    url: str
    posted_text: str = ""
    description: str = ""

@dataclass(frozen=True)
class ObservedJob:
    job: JobPosting
    job_key: str
    first_seen_at: datetime

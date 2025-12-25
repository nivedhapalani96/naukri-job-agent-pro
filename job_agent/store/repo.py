from typing import Optional, List
from sqlalchemy.orm import Session
from job_agent.store.models import JobRecord
from job_agent.models.job import ObservedJob
from job_agent.models.score import ScoreResult
from datetime import datetime, timedelta
import pytz
import json

class JobRepository:
    """Repository for job records."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def exists(self, job_key: str) -> bool:
        """Check if a job with the given key exists."""
        return self.session.query(JobRecord).filter_by(job_key=job_key).first() is not None
    
    def insert(self, observed: ObservedJob, score_result: ScoreResult):
        """Insert a new job record."""
        now = datetime.now(pytz.UTC)
        record = JobRecord(
            job_key=observed.job_key,
            source=observed.job.source,
            title=observed.job.title,
            company=observed.job.company,
            location=observed.job.location,
            url=observed.job.url,
            posted_text=observed.job.posted_text,
            description=observed.job.description,
            first_seen_at=observed.first_seen_at,
            score=score_result.score,
            score_reasons=json.dumps(score_result.reasons),
            action=score_result.action,
            status="NEW",
        )
        self.session.add(record)
        self.session.commit()
    
    def mark_emailed(self, job_key: str):
        """Mark a job as emailed."""
        record = self.session.query(JobRecord).filter_by(job_key=job_key).first()
        if record:
            record.emailed_at = datetime.now(pytz.UTC)
            self.session.commit()
    
    def mark_status(self, job_key: str, status: str):
        """Mark a job with a status (APPLIED, SKIPPED, MANUAL)."""
        record = self.session.query(JobRecord).filter_by(job_key=job_key).first()
        if record:
            record.status = status
            self.session.commit()
    
    def list_digest(self) -> List[JobRecord]:
        """List jobs for digest email (recent jobs that were emailed)."""
        # Return jobs that were emailed in the last 24 hours
        cutoff = datetime.now(pytz.UTC) - timedelta(days=1)
        
        return self.session.query(JobRecord).filter(
            JobRecord.emailed_at.isnot(None),
            JobRecord.emailed_at >= cutoff
        ).order_by(JobRecord.emailed_at.desc()).all()


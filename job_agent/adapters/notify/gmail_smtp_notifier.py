from typing import List, Optional
from job_agent.models.job import ObservedJob
from job_agent.models.score import ScoreResult
from job_agent.models.config import EmailCfg
from job_agent.store.models import JobRecord
from job_agent.adapters.notify.gmail_smtp import GmailSMTPClient
from job_agent.adapters.notify.render import EmailRenderer

class GmailNotifier:
    """Notifier that sends emails via Gmail SMTP."""
    
    def __init__(self, cfg: EmailCfg):
        self.cfg = cfg
        self.enabled = cfg.enabled and cfg.gmail_smtp.enabled
        if self.enabled:
            self.smtp = GmailSMTPClient(cfg.gmail_smtp)
            self.renderer = EmailRenderer()
        else:
            self.smtp = None
            self.renderer = None
    
    def send_job(self, job: ObservedJob, score: ScoreResult, notes: str = ""):
        """Send notification for a new job."""
        if not self.enabled or not self.smtp or not self.renderer:
            return
        
        subject = f"{self.cfg.subject_prefix} {job.job.title} at {job.job.company}"
        html_body = self.renderer.render_new_job(job, score, notes)
        
        self.smtp.send_email(
            from_email=self.cfg.from_email,
            to_emails=self.cfg.to_emails,
            subject=subject,
            html_body=html_body,
        )
    
    def send_digest(self, jobs: List[JobRecord]):
        """Send daily digest email."""
        if not self.enabled or not self.smtp or not self.renderer:
            return
        
        subject = f"{self.cfg.subject_prefix} Daily Digest - {len(jobs)} jobs"
        html_body = self.renderer.render_digest(jobs)
        
        self.smtp.send_email(
            from_email=self.cfg.from_email,
            to_emails=self.cfg.to_emails,
            subject=subject,
            html_body=html_body,
        )


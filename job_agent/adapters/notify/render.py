from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from job_agent.models.job import ObservedJob
from job_agent.models.score import ScoreResult
from job_agent.store.models import JobRecord
from typing import List

class EmailRenderer:
    """Renders email templates using Jinja2."""
    
    def __init__(self):
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    def render_new_job(self, job: ObservedJob, score: ScoreResult, notes: str = "") -> str:
        """Render HTML for a new job email."""
        template = self.env.get_template("new_job_email.html.j2")
        return template.render(
            job=job.job,
            score=score.score,
            reasons=score.reasons,
            action=score.action,
            notes=notes,
            job_url=job.job.url,
        )
    
    def render_digest(self, jobs: List[JobRecord]) -> str:
        """Render HTML for a digest email."""
        template = self.env.get_template("digest_email.html.j2")
        return template.render(jobs=jobs)


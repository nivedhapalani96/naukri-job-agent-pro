import logging
from job_agent.core.utils import stable_job_key
from job_agent.core.scoring import score
from job_agent.models.job import ObservedJob
from job_agent.models.profile import Profile

log = logging.getLogger("job_agent.services")

class PollingService:
    def __init__(self, ctx, profile: Profile):
        self.ctx = ctx
        self.profile = profile

    def run_once(self, send_email: bool = True):
        source = self.ctx.naukri_source
        repo = self.ctx.job_repo()
        notifier = self.ctx.notifier if send_email else None
        clock = self.ctx.clock

        if not source:
            log.warning("No enabled job sources.")
            return

        jobs = source.search()[: self.ctx.cfg.polling.max_jobs_per_run]
        new_count = 0

        for job in jobs:
            key = stable_job_key(job.url)
            if repo.exists(key):
                continue

            observed = ObservedJob(job, key, clock.now_utc())
            score_result = score(job, self.profile, self.ctx.cfg.scoring)

            repo.insert(observed, score_result)
            new_count += 1

            if notifier and score_result.action == "EMAIL":
                notifier.send_job(observed, score_result, self._notes())
                repo.mark_emailed(key)

        log.info("Polling completed. New jobs: %s", new_count)

    def _notes(self) -> str:
        lines = []
        if self.profile.resume_summary:
            lines.append(self.profile.resume_summary)
        if self.profile.achievements:
            lines.append("\nKey achievements:")
            for a in self.profile.achievements[:5]:
                lines.append(f"- {a}")
        return "\n".join(lines)

class DigestService:
    def __init__(self, ctx, profile: Profile):
        self.ctx = ctx
        self.profile = profile

    def run_daily(self):
        notifier = self.ctx.notifier
        if not notifier:
            return
        rows = self.ctx.job_repo().list_digest()
        notifier.send_digest(rows)

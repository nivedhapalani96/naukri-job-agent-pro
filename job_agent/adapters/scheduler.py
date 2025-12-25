import random
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from job_agent.core.services import PollingService, DigestService
from job_agent.models.config import PollingCfg, DigestCfg

log = logging.getLogger("job_agent.scheduler")

class Scheduler:
    """Scheduler for polling and digest jobs."""
    
    def __init__(self, polling_cfg: PollingCfg, digest_cfg: DigestCfg):
        self.polling_cfg = polling_cfg
        self.digest_cfg = digest_cfg
        self.scheduler = BlockingScheduler()
    
    def run(self, polling_service: PollingService, digest_service: DigestService):
        """Start the scheduler with polling and digest jobs."""
        # Schedule polling job with jitter
        interval_seconds = self.polling_cfg.interval_seconds
        jitter = random.randint(0, self.polling_cfg.jitter_seconds)
        first_run_delay = interval_seconds + jitter
        
        self.scheduler.add_job(
            polling_service.run_once,
            trigger=IntervalTrigger(seconds=interval_seconds),
            id="polling",
            max_instances=1,
            replace_existing=True,
        )
        
        log.info(f"Scheduled polling job (interval: {interval_seconds}s, jitter: {jitter}s)")
        
        # Schedule digest job if enabled
        if self.digest_cfg.enabled:
            self.scheduler.add_job(
                digest_service.run_daily,
                trigger=CronTrigger(hour=self.digest_cfg.hour, minute=self.digest_cfg.minute),
                id="digest",
                max_instances=1,
                replace_existing=True,
            )
            log.info(f"Scheduled digest job (daily at {self.digest_cfg.hour:02d}:{self.digest_cfg.minute:02d})")
        
        try:
            log.info("Starting scheduler...")
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            log.info("Stopping scheduler...")
            self.scheduler.shutdown()


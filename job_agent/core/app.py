from typing import Optional
from job_agent.models.config import RootCfg
from job_agent.adapters.clock import Clock
from job_agent.adapters.scheduler import Scheduler
from job_agent.adapters.naukri.source import NaukriSource
from job_agent.adapters.notify.gmail_smtp_notifier import GmailNotifier
from job_agent.store.db import create_engine_from_url, create_session_factory, init_db
from job_agent.store.repo import JobRepository
from job_agent.core.logging import setup_logging

class AppContext:
    """Application context containing all services and adapters."""
    
    def __init__(
        self,
        cfg: RootCfg,
        clock: Clock,
        naukri_source: Optional[NaukriSource],
        notifier: Optional[GmailNotifier],
        session_factory,
    ):
        self.cfg = cfg
        self.clock = clock
        self.naukri_source = naukri_source
        self.notifier = notifier
        self._session_factory = session_factory
    
    @classmethod
    def from_config(cls, cfg: RootCfg) -> "AppContext":
        """Create AppContext from configuration."""
        # Setup logging
        setup_logging(cfg.app.log_level)
        
        # Initialize database
        engine = create_engine_from_url(cfg.app.db_url)
        init_db(engine)
        session_factory = create_session_factory(engine)
        
        # Create clock
        clock = Clock(cfg.app.user_timezone)
        
        # Create job sources
        naukri_source = None
        if cfg.sources.naukri.enabled:
            naukri_source = NaukriSource(cfg.sources.naukri)
        
        # Create notifier
        notifier = None
        if cfg.email.enabled:
            notifier = GmailNotifier(cfg.email)
        
        return cls(
            cfg=cfg,
            clock=clock,
            naukri_source=naukri_source,
            notifier=notifier,
            session_factory=session_factory,
        )
    
    def job_repo(self) -> JobRepository:
        """Get a job repository instance."""
        return JobRepository(self._session_factory())
    
    def scheduler(self) -> Scheduler:
        """Get a scheduler instance."""
        return Scheduler(self.cfg.polling, self.cfg.email.digest)


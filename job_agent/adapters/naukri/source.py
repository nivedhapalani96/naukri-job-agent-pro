from typing import List, Optional
from job_agent.models.job import JobPosting
from job_agent.models.config import NaukriCfg
from job_agent.adapters.naukri.http import NaukriHTTPClient
from job_agent.adapters.naukri.parser import NaukriParser

class NaukriSource:
    """Job source for Naukri.com."""
    
    def __init__(self, cfg: NaukriCfg):
        self.cfg = cfg
        if cfg.enabled:
            self.http = NaukriHTTPClient(cfg.request)
            self.parser = NaukriParser(cfg.parsing)
        else:
            self.http = None
            self.parser = None
    
    def search(self) -> List[JobPosting]:
        """Search for jobs across all configured URLs."""
        if not self.cfg.enabled or not self.http or not self.parser:
            return []
        
        all_jobs = []
        for url in self.cfg.search_urls:
            try:
                response = self.http.get(url)
                jobs = self.parser.parse_jobs(response.text, url)
                all_jobs.extend(jobs)
            except Exception as e:
                import logging
                log = logging.getLogger("job_agent.naukri")
                log.error(f"Error fetching jobs from {url}: {e}")
        
        return all_jobs


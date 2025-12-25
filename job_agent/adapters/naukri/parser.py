from bs4 import BeautifulSoup
from typing import List, Optional
from job_agent.models.job import JobPosting
from job_agent.models.config import ParsingCfg

class NaukriParser:
    """Parser for Naukri.com HTML pages."""
    
    def __init__(self, cfg: ParsingCfg):
        self.cfg = cfg
    
    def parse_jobs(self, html: str, base_url: str = "") -> List[JobPosting]:
        """Parse job listings from HTML."""
        soup = BeautifulSoup(html, "lxml")
        jobs = []
        
        # Find all job cards
        cards = []
        for selector in self.cfg.card_selectors:
            cards.extend(soup.select(selector))
            if cards:
                break
        
        for card in cards:
            job = self._parse_job_card(card, base_url)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _parse_job_card(self, card, base_url: str) -> Optional[JobPosting]:
        """Parse a single job card element."""
        title = self._extract_text(card, self.cfg.title_selectors)
        company = self._extract_text(card, self.cfg.company_selectors)
        location = self._extract_text(card, self.cfg.location_selectors)
        posted_text = self._extract_text(card, self.cfg.posted_selectors)
        url = self._extract_url(card, self.cfg.url_selectors, base_url)
        
        if not title or not url:
            return None
        
        return JobPosting(
            source="naukri",
            title=title,
            company=company or "Unknown",
            location=location or "",
            url=url,
            posted_text=posted_text or "",
            description="",  # Description would need separate fetch
        )
    
    def _extract_text(self, element, selectors: List[str]) -> str:
        """Extract text using the first matching selector."""
        for selector in selectors:
            found = element.select_one(selector)
            if found:
                text = found.get_text(strip=True)
                if text:
                    return text
        return ""
    
    def _extract_url(self, element, selectors: List[str], base_url: str) -> str:
        """Extract URL using the first matching selector."""
        for selector in selectors:
            found = element.select_one(selector)
            if found:
                href = found.get("href", "")
                if href:
                    if href.startswith("http"):
                        return href
                    elif base_url:
                        # Relative URL
                        from urllib.parse import urljoin
                        return urljoin(base_url, href)
                    else:
                        return href
        return ""


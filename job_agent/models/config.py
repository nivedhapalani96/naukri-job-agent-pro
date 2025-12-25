from pydantic import BaseModel
from typing import List

class AppCfg(BaseModel):
    db_url: str
    user_timezone: str
    log_level: str

class PollingCfg(BaseModel):
    interval_seconds: int
    jitter_seconds: int
    max_jobs_per_run: int

class RequestCfg(BaseModel):
    timeout_seconds: int
    user_agent: str

class ParsingCfg(BaseModel):
    card_selectors: List[str]
    title_selectors: List[str]
    company_selectors: List[str]
    location_selectors: List[str]
    posted_selectors: List[str]
    url_selectors: List[str]

class NaukriCfg(BaseModel):
    enabled: bool
    search_urls: List[str]
    request: RequestCfg
    parsing: ParsingCfg

class SourcesCfg(BaseModel):
    naukri: NaukriCfg

class FreshnessBoostCfg(BaseModel):
    just_now: int
    today: int
    last_3_days: int

class WeightsCfg(BaseModel):
    title_match: int
    skill_match: int
    seniority_match: int
    location_match: int
    company_pref: int

class HardFiltersCfg(BaseModel):
    reject_title_keywords: List[str]
    reject_desc_keywords: List[str]

class ScoringCfg(BaseModel):
    min_score_to_email: int
    freshness_boost: FreshnessBoostCfg
    weights: WeightsCfg
    hard_filters: HardFiltersCfg

class GmailCfg(BaseModel):
    enabled: bool
    username: str
    gmail_app_password: str

class DigestCfg(BaseModel):
    enabled: bool
    hour: int
    minute: int

class EmailCfg(BaseModel):
    enabled: bool
    from_email: str
    to_emails: List[str]
    subject_prefix: str
    gmail_smtp: GmailCfg
    digest: DigestCfg

class RootCfg(BaseModel):
    app: AppCfg
    polling: PollingCfg
    sources: SourcesCfg
    scoring: ScoringCfg
    email: EmailCfg
    profile_path: str

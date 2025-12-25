import re
from job_agent.models.score import ScoreResult
from job_agent.models.job import JobPosting
from job_agent.models.profile import Profile
from job_agent.models.config import ScoringCfg

def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()

def _contains(text: str, keywords: list[str]) -> bool:
    t = _norm(text)
    return any(_norm(k) in t for k in keywords if k)

def _count(text: str, keywords: list[str]) -> int:
    t = _norm(text)
    return sum(1 for k in keywords if k and _norm(k) in t)

def _freshness_boost(posted_text: str, cfg: ScoringCfg) -> int:
    t = _norm(posted_text)
    if not t:
        return 0
    if "just" in t or "minute" in t:
        return cfg.freshness_boost.just_now
    if "today" in t or "hour" in t:
        return cfg.freshness_boost.today
    if "day" in t:
        m = re.search(r"(\d+)", t)
        if m and int(m.group(1)) <= 3:
            return cfg.freshness_boost.last_3_days
    return 0

def score(job: JobPosting, profile: Profile, cfg: ScoringCfg) -> ScoreResult:
    title = job.title or ""
    text = f"{job.title} {job.description}"

    # hard filters
    if _contains(title, cfg.hard_filters.reject_title_keywords):
        return ScoreResult(0, ["Rejected by title filter"], "SKIP")

    if _contains(text, cfg.hard_filters.reject_desc_keywords):
        return ScoreResult(0, ["Rejected by description filter"], "SKIP")

    score_val = 0
    reasons: list[str] = []

    title_hits = _count(title, profile.target_titles)
    if title_hits:
        inc = min(cfg.weights.title_match, 10 * title_hits + 10)
        score_val += inc
        reasons.append(f"Title match (+{inc})")

    skill_hits = _count(
        text,
        profile.must_have_skills
        + profile.nice_to_have_skills
        + profile.domain_keywords,
    )
    if skill_hits:
        inc = min(cfg.weights.skill_match, 6 * skill_hits + 15)
        score_val += inc
        reasons.append(f"Skill/domain match (+{inc})")

    if re.search(r"\bsenior\b|\blead\b|\bprincipal\b|\bstaff\b", _norm(title)):
        score_val += cfg.weights.seniority_match
        reasons.append(f"Seniority signal (+{cfg.weights.seniority_match})")

    if profile.preferred_locations and _contains(job.location, profile.preferred_locations):
        score_val += cfg.weights.location_match
        reasons.append(f"Location match (+{cfg.weights.location_match})")

    if profile.company_preferences.preferred and _contains(job.company, profile.company_preferences.preferred):
        score_val += cfg.weights.company_pref
        reasons.append(f"Preferred company (+{cfg.weights.company_pref})")

    if profile.company_preferences.avoided and _contains(job.company, profile.company_preferences.avoided):
        score_val = max(0, score_val - 20)
        reasons.append("Avoided company (-20)")

    freshness = _freshness_boost(job.posted_text, cfg)
    if freshness:
        score_val += freshness
        reasons.append(f"Freshness (+{freshness})")

    score_val = min(100, max(0, score_val))
    action = "EMAIL" if score_val >= cfg.min_score_to_email else "QUEUE"

    return ScoreResult(score_val, reasons, action)

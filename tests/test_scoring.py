from job_agent.core.scoring import score
from job_agent.models.job import JobPosting
from job_agent.models.profile import Profile, CompanyPrefs
from job_agent.models.config import ScoringCfg, FreshnessBoostCfg, WeightsCfg, HardFiltersCfg

def test_high_match_scores_email():
    cfg = ScoringCfg(
        min_score_to_email=70,
        freshness_boost=FreshnessBoostCfg(15, 10, 6),
        weights=WeightsCfg(25, 45, 12, 8, 10),
        hard_filters=HardFiltersCfg([], []),
    )

    profile = Profile(
        name="X",
        target_titles=["Senior Backend Engineer"],
        preferred_locations=["Remote"],
        must_have_skills=["Node.js", "AWS", "PostgreSQL"],
        nice_to_have_skills=[],
        domain_keywords=[],
        company_preferences=CompanyPrefs(preferred=[], avoided=[]),
    )

    job = JobPosting(
        source="naukri",
        title="Senior Backend Engineer - Node.js AWS",
        company="Test",
        location="Remote",
        url="https://example.com",
        posted_text="Just now",
    )

    result = score(job, profile, cfg)
    assert result.action == "EMAIL"

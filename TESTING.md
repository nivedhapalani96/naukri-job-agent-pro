# Testing Guide

This guide provides comprehensive instructions for testing the Naukri Job Agent to ensure it's working correctly.

## Table of Contents

- [Quick Start Testing](#quick-start-testing)
- [Unit Tests](#unit-tests)
- [Integration Tests](#integration-tests)
- [Configuration Validation](#configuration-validation)
- [End-to-End Testing](#end-to-end-testing)
- [Manual Testing Steps](#manual-testing-steps)
- [Troubleshooting Tests](#troubleshooting-tests)

## Quick Start Testing

### 1. Verify Installation

```bash
# Check Python version (requires 3.10+)
python --version

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify package can be imported
python -c "import job_agent; print('✓ Installation successful')"
```

### 2. Run Existing Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=job_agent --cov-report=html

# Run specific test
pytest tests/test_scoring.py::test_high_match_scores_email -v
```

### 3. Validate Configuration

```bash
# Test configuration loading
python -c "
from job_agent.core.config import load_config, load_profile
cfg = load_config('config/config.example.yaml')
profile = load_profile('config/profile.example.yaml')
print('✓ Configuration valid')
"
```

### 4. Test Database Setup

```bash
# Test database initialization
python -c "
from job_agent.store.db import create_engine_from_url, init_db
from job_agent.store.models import JobRecord
engine = create_engine_from_url('sqlite:///test.db')
init_db(engine)
print('✓ Database initialized')
"
```

## Unit Tests

### Scoring Tests

The scoring engine is the core of the application. Test it thoroughly:

```bash
# Run scoring tests
pytest tests/test_scoring.py -v
```

**Test Scenarios to Verify:**

1. **High Score → EMAIL Action**
   - Job matches title, skills, location
   - Score ≥ `min_score_to_email`
   - Action should be "EMAIL"

2. **Low Score → QUEUE Action**
   - Job matches some criteria but below threshold
   - Action should be "QUEUE"

3. **Hard Filter → SKIP Action**
   - Job contains reject keywords
   - Action should be "SKIP", score = 0

4. **Freshness Boost**
   - "Just now" posts get +15 points
   - "Today" posts get +10 points
   - "Last 3 days" posts get +6 points

### Adding More Scoring Tests

Create `tests/test_scoring_comprehensive.py`:

```python
import pytest
from job_agent.core.scoring import score
from job_agent.models.job import JobPosting
from job_agent.models.profile import Profile, CompanyPrefs
from job_agent.models.config import ScoringCfg, FreshnessBoostCfg, WeightsCfg, HardFiltersCfg

@pytest.fixture
def base_cfg():
    return ScoringCfg(
        min_score_to_email=70,
        freshness_boost=FreshnessBoostCfg(15, 10, 6),
        weights=WeightsCfg(25, 45, 12, 8, 10),
        hard_filters=HardFiltersCfg([], []),
    )

@pytest.fixture
def base_profile():
    return Profile(
        name="Test User",
        target_titles=["Senior Backend Engineer"],
        preferred_locations=["Remote", "Bangalore"],
        must_have_skills=["Python", "PostgreSQL"],
        nice_to_have_skills=["Redis", "Docker"],
        domain_keywords=["e-commerce"],
        company_preferences=CompanyPrefs(
            preferred=["Stripe"],
            avoided=["Confidential"]
        ),
    )

def test_perfect_match(base_cfg, base_profile):
    """Test a job that matches all criteria"""
    job = JobPosting(
        source="naukri",
        title="Senior Backend Engineer - Python PostgreSQL",
        company="Stripe",
        location="Remote",
        url="https://example.com",
        posted_text="Just now",
        description="e-commerce platform with Redis and Docker"
    )
    result = score(job, base_profile, base_cfg)
    assert result.action == "EMAIL"
    assert result.score >= 70
    assert len(result.reasons) > 0

def test_hard_filter_rejection(base_cfg, base_profile):
    """Test that jobs with reject keywords are skipped"""
    base_cfg.hard_filters.reject_title_keywords = ["intern", "junior"]
    
    job = JobPosting(
        source="naukri",
        title="Junior Backend Engineer",
        company="Test",
        location="Remote",
        url="https://example.com",
    )
    result = score(job, base_profile, base_cfg)
    assert result.action == "SKIP"
    assert result.score == 0
    assert "Rejected" in result.reasons[0]

def test_freshness_boost(base_cfg, base_profile):
    """Test freshness boost points"""
    job = JobPosting(
        source="naukri",
        title="Senior Backend Engineer",
        company="Test",
        location="Remote",
        url="https://example.com",
        posted_text="Just now",
    )
    result = score(job, base_profile, base_cfg)
    assert "Freshness" in " ".join(result.reasons)
    assert result.score >= 15  # At least freshness boost

def test_company_preference(base_cfg, base_profile):
    """Test preferred company boost"""
    job = JobPosting(
        source="naukri",
        title="Backend Engineer",
        company="Stripe",
        location="Remote",
        url="https://example.com",
    )
    result = score(job, base_profile, base_cfg)
    assert "Preferred company" in " ".join(result.reasons)

def test_avoided_company_penalty(base_cfg, base_profile):
    """Test avoided company penalty"""
    job = JobPosting(
        source="naukri",
        title="Senior Backend Engineer",
        company="Confidential",
        location="Remote",
        url="https://example.com",
    )
    result = score(job, base_profile, base_cfg)
    assert "Avoided company" in " ".join(result.reasons)
```

## Integration Tests

### Test Configuration Loading

```bash
# Test config loading
python -c "
from job_agent.core.config import load_config, load_profile
from pathlib import Path

# Test main config
cfg = load_config('config/config.example.yaml')
assert cfg.app.db_url
assert cfg.polling.interval_seconds > 0
print('✓ Main config loaded')

# Test profile
profile_data = load_profile('config/profile.example.yaml')
assert profile_data.profile.name
assert len(profile_data.profile.target_titles) > 0
print('✓ Profile loaded')
"
```

### Test Application Context Creation

```bash
python -c "
from job_agent.core.app import AppContext
from job_agent.core.config import load_config

# Use test database
import tempfile
import os

# Create temporary config
test_config = '''
app:
  db_url: 'sqlite:///test_agent.db'
  user_timezone: 'UTC'
  log_level: 'DEBUG'
polling:
  interval_seconds: 60
  jitter_seconds: 10
  max_jobs_per_run: 10
sources:
  naukri:
    enabled: false
    search_urls: []
    request:
      timeout_seconds: 10
      user_agent: 'Test'
    parsing:
      card_selectors: []
      title_selectors: []
      company_selectors: []
      location_selectors: []
      posted_selectors: []
      url_selectors: []
scoring:
  min_score_to_email: 70
  freshness_boost:
    just_now: 15
    today: 10
    last_3_days: 6
  weights:
    title_match: 25
    skill_match: 45
    seniority_match: 12
    location_match: 8
    company_pref: 10
  hard_filters:
    reject_title_keywords: []
    reject_desc_keywords: []
email:
  enabled: false
  from_email: 'test@example.com'
  to_emails: ['test@example.com']
  subject_prefix: '[Test]'
  gmail_smtp:
    enabled: false
    username: ''
    gmail_app_password: ''
  digest:
    enabled: false
    hour: 0
    minute: 0
profile_path: 'config/profile.example.yaml'
'''

with open('test_config.yaml', 'w') as f:
    f.write(test_config)

try:
    cfg = load_config('test_config.yaml')
    ctx = AppContext.from_config(cfg)
    assert ctx.cfg is not None
    assert ctx.clock is not None
    print('✓ AppContext created successfully')
finally:
    if os.path.exists('test_config.yaml'):
        os.remove('test_config.yaml')
    if os.path.exists('test_agent.db'):
        os.remove('test_agent.db')
"
```

### Test Repository Operations

```bash
python -c "
from job_agent.store.db import create_engine_from_url, create_session_factory, init_db
from job_agent.store.repo import JobRepository
from job_agent.models.job import JobPosting, ObservedJob
from job_agent.models.score import ScoreResult
from datetime import datetime
import pytz

# Setup
engine = create_engine_from_url('sqlite:///test_repo.db')
init_db(engine)
session_factory = create_session_factory(engine)

# Test repository
repo = JobRepository(session_factory())

# Create test job
job = JobPosting(
    source='test',
    title='Test Engineer',
    company='Test Corp',
    location='Remote',
    url='https://test.com/job1',
)
observed = ObservedJob(job, 'test_key_123', datetime.now(pytz.UTC))
score_result = ScoreResult(score=85, reasons=['Test'], action='EMAIL')

# Test insert
repo.insert(observed, score_result)
print('✓ Job inserted')

# Test exists
assert repo.exists('test_key_123')
print('✓ Job exists check works')

# Test mark_emailed
repo.mark_emailed('test_key_123')
print('✓ Job marked as emailed')

# Cleanup
import os
os.remove('test_repo.db')
"
```

## Configuration Validation

### Validate Your Configuration Files

Create a validation script `scripts/validate_config.py`:

```python
#!/usr/bin/env python3
"""Validate configuration files"""

import sys
from pathlib import Path
from job_agent.core.config import load_config, load_profile

def validate_config(config_path: str):
    try:
        cfg = load_config(config_path)
        print(f"✓ Config file '{config_path}' is valid")
        
        # Validate required fields
        assert cfg.app.db_url, "db_url is required"
        assert cfg.app.user_timezone, "user_timezone is required"
        assert cfg.polling.interval_seconds > 0, "interval_seconds must be > 0"
        assert cfg.scoring.min_score_to_email >= 0, "min_score_to_email must be >= 0"
        
        if cfg.email.enabled:
            assert cfg.email.gmail_smtp.enabled, "gmail_smtp must be enabled if email is enabled"
            assert cfg.email.gmail_smtp.gmail_app_password, "gmail_app_password is required"
        
        if cfg.sources.naukri.enabled:
            assert len(cfg.sources.naukri.search_urls) > 0, "At least one search_url is required"
        
        print("✓ All configuration checks passed")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def validate_profile(profile_path: str):
    try:
        profile_data = load_profile(profile_path)
        profile = profile_data.profile
        
        assert profile.name, "name is required"
        assert len(profile.target_titles) > 0, "At least one target_title is required"
        
        print(f"✓ Profile file '{profile_path}' is valid")
        print(f"  Name: {profile.name}")
        print(f"  Target titles: {len(profile.target_titles)}")
        print(f"  Skills: {len(profile.must_have_skills)} must-have, {len(profile.nice_to_have_skills)} nice-to-have")
        return True
    except Exception as e:
        print(f"✗ Profile error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python validate_config.py <config.yaml> <profile.yaml>")
        sys.exit(1)
    
    config_ok = validate_config(sys.argv[1])
    profile_ok = validate_profile(sys.argv[2])
    
    sys.exit(0 if (config_ok and profile_ok) else 1)
```

Run validation:
```bash
python scripts/validate_config.py config/config.yaml config/profile.yaml
```

## End-to-End Testing

### Test Polling Without Email

This is the safest way to test the full pipeline:

```bash
# 1. Ensure you have valid config files
cp config/config.example.yaml config/config.yaml
cp config/profile.example.yaml config/profile.yaml

# 2. Edit config.yaml with your actual Naukri search URL
# 3. Disable email for testing
# Edit config.yaml: email.enabled: false

# 4. Run a single poll cycle
naukri-agent poll-once --config config/config.yaml --no-email

# 5. Check the output
# You should see:
# - "Polling completed. New jobs: X"
# - No errors

# 6. Check database
sqlite3 data/agent.db "SELECT job_key, title, company, score, action FROM jobs ORDER BY created_at DESC LIMIT 5;"
```

### Test Email Sending (Dry Run)

Before enabling email in production, test it:

```bash
# 1. Create a test config with email enabled
# 2. Use a test Gmail account
# 3. Run poll-once (this will send emails for high-scoring jobs)

naukri-agent poll-once --config config/config.yaml

# 4. Check your email inbox
# 5. Verify email format and content
```

### Test Database Persistence

```bash
# 1. Run poll-once twice
naukri-agent poll-once --config config/config.yaml --no-email
naukri-agent poll-once --config config/config.yaml --no-email

# 2. Check that no duplicate jobs were inserted
sqlite3 data/agent.db "
SELECT job_key, COUNT(*) as count 
FROM jobs 
GROUP BY job_key 
HAVING count > 1;
"
# Should return no rows (no duplicates)
```

## Manual Testing Steps

### Step-by-Step Verification

#### 1. **Environment Setup**
```bash
# Verify Python version
python --version  # Should be 3.10+

# Verify dependencies
pip list | grep -E "(pydantic|sqlalchemy|beautifulsoup4|apscheduler)"

# Verify package structure
python -c "from job_agent.core.app import AppContext; print('✓ Imports work')"
```

#### 2. **Configuration Setup**
```bash
# Copy example configs
cp config/config.example.yaml config/config.yaml
cp config/profile.example.yaml config/profile.yaml

# Edit config.yaml:
# - Set your Naukri search URL
# - Configure email settings (or disable for testing)
# - Adjust scoring thresholds

# Edit profile.yaml:
# - Add your target job titles
# - Add your skills
# - Set location preferences
```

#### 3. **Database Initialization**
```bash
# Create data directory
mkdir -p data

# Run a test command to initialize database
naukri-agent poll-once --config config/config.yaml --no-email

# Verify database was created
ls -lh data/agent.db
```

#### 4. **Test Scoring Logic**
```bash
# Run scoring tests
pytest tests/test_scoring.py -v

# Add your own test cases based on your profile
```

#### 5. **Test Job Fetching**
```bash
# Enable DEBUG logging in config.yaml
# app.log_level: "DEBUG"

# Run poll-once
naukri-agent poll-once --config config/config.yaml --no-email

# Check logs for:
# - "Polling completed. New jobs: X"
# - No parsing errors
# - Jobs found and processed
```

#### 6. **Test Email Sending**
```bash
# Ensure email is configured correctly
# Run with email enabled
naukri-agent poll-once --config config/config.yaml

# Check:
# - Email received in inbox
# - Email format is correct
# - Job details are accurate
```

#### 7. **Test Scheduler**
```bash
# For testing, reduce polling interval in config.yaml
# polling.interval_seconds: 60  # 1 minute for testing

# Run scheduler (will run continuously)
# Press Ctrl+C to stop
naukri-agent run --config config/config.yaml
```

## Troubleshooting Tests

### Common Test Failures

#### 1. **Import Errors**
```bash
# Solution: Install package in development mode
pip install -e .
```

#### 2. **Database Locked**
```bash
# Solution: Use separate test database
# In test code, use: sqlite:///test_agent.db
```

#### 3. **Configuration Not Found**
```bash
# Solution: Use absolute paths or run from project root
cd /path/to/naukri-job-agent-pro
```

#### 4. **Email Tests Failing**
```bash
# Solution: Mock email sending in tests
# Or use test Gmail account with app password
```

### Debug Mode

Enable debug logging for detailed information:

```yaml
# config.yaml
app:
  log_level: "DEBUG"
```

Then run:
```bash
naukri-agent poll-once --config config/config.yaml --no-email 2>&1 | tee test.log
```

### Test Checklist

Use this checklist to verify everything works:

- [ ] Python 3.10+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Configuration files created and valid
- [ ] Profile file created with your preferences
- [ ] Database initializes correctly
- [ ] Scoring tests pass
- [ ] Configuration validation passes
- [ ] Poll-once runs without errors
- [ ] Jobs are fetched from Naukri
- [ ] Jobs are stored in database
- [ ] No duplicate jobs inserted
- [ ] Email sending works (if enabled)
- [ ] Scheduler runs without errors
- [ ] Logs show expected information

## Automated Test Script

Create `scripts/test_all.sh`:

```bash
#!/bin/bash
set -e

echo "🧪 Running Naukri Job Agent Tests"
echo "=================================="

echo ""
echo "1. Testing imports..."
python -c "from job_agent.core.app import AppContext; print('✓ Imports OK')"

echo ""
echo "2. Running unit tests..."
pytest tests/ -v

echo ""
echo "3. Testing configuration loading..."
python -c "
from job_agent.core.config import load_config, load_profile
cfg = load_config('config/config.example.yaml')
profile = load_profile('config/profile.example.yaml')
print('✓ Config loading OK')
"

echo ""
echo "4. Testing database setup..."
python -c "
from job_agent.store.db import create_engine_from_url, init_db
import os
engine = create_engine_from_url('sqlite:///test_all.db')
init_db(engine)
os.remove('test_all.db')
print('✓ Database setup OK')
"

echo ""
echo "✅ All tests passed!"
```

Make it executable and run:
```bash
chmod +x scripts/test_all.sh
./scripts/test_all.sh
```

---

**Remember**: Always test with `--no-email` first to avoid sending test emails, then verify email functionality separately with a test account.


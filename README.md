# Naukri Job Agent

A production-ready, stability-first job discovery agent for Naukri.com that automatically monitors job listings, scores them against your profile, and sends intelligent email notifications. Built with a clean architecture emphasizing maintainability, testability, and operational reliability.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [System Design](#system-design)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Design Decisions](#design-decisions)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Overview

The Naukri Job Agent is an autonomous system that:

1. **Polls** Naukri.com search pages at configurable intervals
2. **Extracts** job postings using robust HTML parsing
3. **Scores** jobs against your profile using a weighted algorithm
4. **Stores** job data in a persistent database for deduplication
5. **Notifies** you via email for high-scoring matches
6. **Sends** daily digest summaries of recent opportunities

### Key Features

- **Intelligent Scoring**: Multi-factor scoring algorithm with configurable weights
- **Hard Filters**: Automatic rejection of jobs matching unwanted keywords
- **Freshness Boost**: Prioritizes recently posted jobs
- **State Persistence**: SQLite database prevents duplicate notifications
- **Rate Limiting**: Built-in protection against overwhelming target servers
- **Email Templates**: Professional HTML email templates with Jinja2
- **Scheduled Operations**: APScheduler for reliable polling and digest delivery
- **Timezone Support**: Proper timezone handling for scheduling

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Entry Point                       │
│                    (job_agent/cli.py)                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Context                       │
│                  (core/app.py)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Config     │  │    Clock     │  │   Database   │    │
│  │   Loader     │  │   Adapter    │  │   Session    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Services   │  │   Adapters   │  │    Store     │
│              │  │              │  │              │
│ • Polling    │  │ • Naukri     │  │ • Repository │
│ • Digest     │  │ • Notifier   │  │ • Models     │
│ • Scoring    │  │ • Scheduler  │  │ • Database   │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Layered Architecture

The system follows a **clean architecture** pattern with clear separation of concerns:

1. **Presentation Layer** (`cli.py`): Command-line interface
2. **Application Layer** (`core/`): Business logic and orchestration
3. **Domain Layer** (`models/`): Domain entities and value objects
4. **Infrastructure Layer** (`adapters/`, `store/`): External integrations and persistence

## System Design

### Component Breakdown

#### 1. Core Services (`core/services.py`)

**PollingService**
- Orchestrates the job discovery workflow
- Fetches jobs from sources, scores them, and triggers notifications
- Implements idempotency through job key deduplication

**DigestService**
- Aggregates jobs emailed in the last 24 hours
- Sends consolidated daily summary

#### 2. Scoring Engine (`core/scoring.py`)

Multi-factor scoring algorithm:

```
Score = Σ(weights × factors) + freshness_boost - penalties
```

**Scoring Factors:**
- **Title Match** (25 points): Matches against target job titles
- **Skill Match** (45 points): Must-have, nice-to-have skills, and domain keywords
- **Seniority Match** (12 points): Detects senior/lead/principal/staff roles
- **Location Match** (8 points): Preferred locations
- **Company Preference** (10 points): Preferred companies (+10) or avoided (-20)

**Freshness Boost:**
- Just posted: +15 points
- Posted today: +10 points
- Last 3 days: +6 points

**Hard Filters:**
- Automatic rejection if title/description contains reject keywords
- Returns `SKIP` action with 0 score

**Actions:**
- `EMAIL`: Score ≥ `min_score_to_email` (default: 78)
- `QUEUE`: Score < threshold but passed filters
- `SKIP`: Rejected by hard filters

#### 3. Adapters Layer

**Naukri Source** (`adapters/naukri/`)
- **HTTP Client**: Handles requests with rate limiting and error handling
- **Parser**: BeautifulSoup-based HTML parsing with fallback selectors
- **Source**: Orchestrates fetching and parsing across multiple search URLs

**Notification** (`adapters/notify/`)
- **SMTP Client**: Gmail SMTP integration with TLS
- **Renderer**: Jinja2 template engine for HTML emails
- **Notifier**: High-level interface for sending job and digest emails

**Scheduler** (`adapters/scheduler.py`)
- APScheduler-based job scheduling
- Interval-based polling with configurable jitter
- Cron-based daily digest delivery

**Clock** (`adapters/clock.py`)
- Timezone-aware datetime operations
- Abstraction for testability

#### 4. Data Persistence (`store/`)

**Models** (`store/models.py`)
- SQLAlchemy ORM models
- `JobRecord`: Complete job state including scores, status, and timestamps

**Repository** (`store/repo.py`)
- Data access layer following Repository pattern
- Methods: `exists()`, `insert()`, `mark_emailed()`, `mark_status()`, `list_digest()`

**Database** (`store/db.py`)
- Database initialization and session management
- Supports SQLite (default) and other SQLAlchemy-compatible databases

### Data Flow

#### Polling Workflow

```
1. Scheduler triggers PollingService.run_once()
   │
2. PollingService fetches jobs from NaukriSource
   │
3. For each job:
   │
   ├─► Generate stable job_key (SHA256 hash of normalized URL)
   │
   ├─► Check if job_key exists in database
   │   └─► If exists: Skip (idempotency)
   │
   ├─► Score job against profile
   │   └─► Apply hard filters → SKIP if rejected
   │   └─► Calculate weighted score
   │   └─► Determine action (EMAIL/QUEUE/SKIP)
   │
   ├─► Insert job record into database
   │
   └─► If action == EMAIL:
       ├─► Render email template
       ├─► Send via GmailNotifier
       └─► Mark job as emailed in database
```

#### Digest Workflow

```
1. Scheduler triggers DigestService.run_daily() (cron: daily at configured time)
   │
2. Query database for jobs emailed in last 24 hours
   │
3. Render digest template with job list
   │
4. Send consolidated email via GmailNotifier
```

### State Management

**Job States:**
- `NEW`: Just discovered, not yet acted upon
- `APPLIED`: Manually marked as applied
- `SKIPPED`: Manually marked as skipped
- `MANUAL`: Manually added/curated

**Email Tracking:**
- `emailed_at`: Timestamp when notification was sent
- Used for digest aggregation and preventing duplicate emails

## Technology Stack

### Core Dependencies

- **Python 3.10+**: Modern Python features and type hints
- **Pydantic 2.8+**: Configuration validation and data models
- **SQLAlchemy 2.0+**: ORM with async support (future-ready)
- **APScheduler 3.10+**: Enterprise-grade job scheduling
- **BeautifulSoup4 + lxml**: Robust HTML parsing
- **Jinja2**: Template engine for email rendering
- **PyYAML**: Configuration file parsing
- **requests**: HTTP client library
- **pytz**: Timezone support

### Design Patterns Used

1. **Repository Pattern**: Data access abstraction
2. **Adapter Pattern**: External service integration
3. **Dependency Injection**: AppContext provides dependencies
4. **Factory Pattern**: `AppContext.from_config()` creates configured instances
5. **Strategy Pattern**: Pluggable scoring, parsing, and notification strategies

## Project Structure

```
naukri-job-agent-pro/
├── job_agent/                    # Main application package
│   ├── cli.py                    # CLI entry point
│   ├── core/                     # Application core
│   │   ├── app.py               # Application context & DI
│   │   ├── config.py            # Configuration loading
│   │   ├── logging.py           # Logging setup
│   │   ├── scoring.py           # Scoring algorithm
│   │   ├── services.py          # Business logic services
│   │   └── utils.py             # Utility functions
│   ├── models/                   # Domain models
│   │   ├── config.py            # Pydantic config models
│   │   ├── job.py               # Job domain entities
│   │   ├── profile.py           # Profile domain model
│   │   └── score.py             # Scoring result model
│   ├── adapters/                 # External integrations
│   │   ├── clock.py             # Time abstraction
│   │   ├── scheduler.py         # Job scheduler
│   │   ├── rate_limiter.py      # Rate limiting
│   │   ├── naukri/              # Naukri.com integration
│   │   │   ├── http.py          # HTTP client
│   │   │   ├── parser.py        # HTML parser
│   │   │   └── source.py        # Job source
│   │   └── notify/              # Email notifications
│   │       ├── gmail_smtp.py    # SMTP client
│   │       ├── gmail_smtp_notifier.py  # Notifier
│   │       ├── render.py        # Template renderer
│   │       └── templates/       # Email templates
│   │           ├── new_job_email.html.j2
│   │           └── digest_email.html.j2
│   └── store/                    # Data persistence
│       ├── db.py                # Database setup
│       ├── models.py           # SQLAlchemy models
│       └── repo.py             # Repository implementation
├── config/                       # Configuration files
│   ├── config.example.yaml     # Main config template
│   └── profile.example.yaml     # Profile template
├── tests/                        # Test suite
│   └── test_scoring.py          # Scoring tests
├── requirements.txt              # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── pyproject.toml               # Package metadata
├── Dockerfile                   # Container definition
└── README.md                    # This file
```

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Gmail account with App Password (for email notifications)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd naukri-job-agent-pro
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install package in development mode** (optional)
   ```bash
   pip install -e .
   ```

5. **Create configuration files**
   ```bash
   cp config/config.example.yaml config/config.yaml
   cp config/profile.example.yaml config/profile.yaml
   ```

6. **Configure the application**
   - Edit `config/config.yaml` with your settings
   - Edit `config/profile.yaml` with your job preferences
   - See [Configuration](#configuration) section for details

7. **Create data directory** (for SQLite database)
   ```bash
   mkdir -p data
   ```

## Configuration

### Main Configuration (`config/config.yaml`)

#### Application Settings
```yaml
app:
  db_url: "sqlite:///data/agent.db"  # Database connection string
  user_timezone: "Asia/Kolkata"       # Timezone for scheduling
  log_level: "INFO"                   # DEBUG, INFO, WARNING, ERROR
```

#### Polling Configuration
```yaml
polling:
  interval_seconds: 420              # Poll every 7 minutes
  jitter_seconds: 30                 # Random jitter to avoid patterns
  max_jobs_per_run: 60               # Maximum jobs to process per cycle
```

#### Naukri Source Configuration
```yaml
sources:
  naukri:
    enabled: true
    search_urls:
      - "https://www.naukri.com/your-search-url"
    request:
      timeout_seconds: 20
      user_agent: "Mozilla/5.0 (compatible; NaukriJobAgent/0.2)"
    parsing:
      card_selectors: ["div.cust-job-tuple", "div.jobTuple"]
      title_selectors: ["a.title", "a[title]"]
      company_selectors: [".comp-name", ".companyName"]
      location_selectors: [".locWdth", ".location"]
      posted_selectors: [".job-post-day", ".postedDate"]
      url_selectors: ["a.title", "a[title]"]
```

**Getting Your Naukri Search URL:**
1. Go to Naukri.com and perform a job search with your filters
2. Copy the URL from the address bar
3. Paste it into `search_urls` array

#### Scoring Configuration
```yaml
scoring:
  min_score_to_email: 78            # Minimum score to trigger email
  freshness_boost:
    just_now: 15                    # Points for "just posted"
    today: 10                       # Points for "posted today"
    last_3_days: 6                  # Points for "posted X days ago"
  weights:
    title_match: 25                 # Weight for title matching
    skill_match: 45                 # Weight for skill matching
    seniority_match: 12             # Weight for seniority signals
    location_match: 8               # Weight for location match
    company_pref: 10                # Weight for company preference
  hard_filters:
    reject_title_keywords:          # Jobs with these in title are rejected
      - "intern"
      - "trainee"
      - "junior"
    reject_desc_keywords:           # Jobs with these in description are rejected
      - "telecalling"
      - "bpo"
```

#### Email Configuration
```yaml
email:
  enabled: true
  from_email: "your-email@gmail.com"
  to_emails: ["your-email@gmail.com"]
  subject_prefix: "[Naukri Agent]"
  gmail_smtp:
    enabled: true
    username: "your-email@gmail.com"
    gmail_app_password: "your-app-password"  # See Gmail App Password setup
  digest:
    enabled: true
    hour: 19                        # 7 PM
    minute: 0
```

**Gmail App Password Setup:**
1. Go to Google Account settings
2. Security → 2-Step Verification (must be enabled)
3. App passwords → Generate new app password
4. Copy the 16-character password to `gmail_app_password`

### Profile Configuration (`config/profile.yaml`)

```yaml
profile:
  name: "Your Name"
  target_titles:                    # Job titles you're targeting
    - "Senior Backend Engineer"
    - "Platform Engineer"
  preferred_locations:              # Preferred work locations
    - "Remote"
    - "Bangalore"
  must_have_skills:                 # Required skills (higher weight)
    - "Python"
    - "PostgreSQL"
  nice_to_have_skills:              # Bonus skills
    - "Redis"
    - "Docker"
  domain_keywords:                  # Industry/domain keywords
    - "marketplace"
    - "e-commerce"
  company_preferences:
    preferred:                      # Companies to prioritize
      - "Stripe"
      - "Amazon"
    avoided:                        # Companies to avoid
      - "Confidential"
  resume_summary: |                 # Summary for email templates
    Senior engineer with 10+ years experience...
  achievements:                     # Key achievements for emails
    - "Led team of 10 engineers"
    - "Scaled system to 1M+ users"
```

## Usage

### Command-Line Interface

The agent provides three main commands:

#### 1. Run Scheduler (Production Mode)
```bash
naukri-agent run --config config/config.yaml
```

Runs continuously, polling at configured intervals and sending daily digests.

#### 2. Poll Once (Testing/Debugging)
```bash
naukri-agent poll-once --config config/config.yaml
```

Runs a single polling cycle and exits. Useful for testing configuration.

```bash
naukri-agent poll-once --config config/config.yaml --no-email
```

Same as above but skips sending emails (useful for testing).

#### 3. Mark Job Status
```bash
naukri-agent mark --config config/config.yaml --job-key <job-key> --status APPLIED
```

Manually mark a job as `APPLIED`, `SKIPPED`, or `MANUAL`.

**Finding Job Keys:**
- Check the database: `sqlite3 data/agent.db "SELECT job_key, title FROM jobs;"`
- Or check email notifications (job key may be in email metadata)

### Programmatic Usage

```python
from job_agent.core.app import AppContext
from job_agent.core.config import load_config, load_profile
from job_agent.core.services import PollingService

# Load configuration
cfg = load_config("config/config.yaml")
profile = load_profile(cfg.profile_path).profile

# Create application context
ctx = AppContext.from_config(cfg)

# Run polling service
service = PollingService(ctx, profile)
service.run_once(send_email=True)
```

## Design Decisions

### Why Clean Architecture?

- **Testability**: Each layer can be tested in isolation
- **Maintainability**: Changes to one layer don't cascade
- **Flexibility**: Easy to swap implementations (e.g., different email providers)
- **Clarity**: Clear boundaries and responsibilities

### Why SQLAlchemy?

- **ORM Benefits**: Type-safe queries, migrations support
- **Database Agnostic**: Easy to switch from SQLite to PostgreSQL
- **Mature**: Battle-tested in production environments
- **Future-Ready**: SQLAlchemy 2.0 supports async operations

### Why APScheduler?

- **Reliability**: Handles job persistence, retries, and failures
- **Flexibility**: Supports interval, cron, and one-time jobs
- **Production-Ready**: Used in enterprise applications
- **Timezone Support**: Proper handling of timezone-aware scheduling

### Why Pydantic?

- **Validation**: Automatic validation of configuration
- **Type Safety**: IDE support and runtime type checking
- **Documentation**: Self-documenting models
- **Performance**: Fast validation with compiled models

### Why BeautifulSoup?

- **Robustness**: Handles malformed HTML gracefully
- **Flexibility**: Multiple parser backends (lxml, html.parser)
- **Selector Support**: CSS selectors for easy element extraction
- **Fallback Strategy**: Multiple selectors per field for resilience

### State Management Strategy

- **Idempotency**: Job keys prevent duplicate processing
- **Persistence**: All state in database (no in-memory state)
- **Auditability**: Timestamps for all state changes
- **Recovery**: System can restart without losing state

### Rate Limiting

- **Server Protection**: Prevents overwhelming Naukri.com servers
- **Configurable**: Easy to adjust based on server response
- **Simple**: Lightweight implementation without external dependencies

## Testing

### Quick Test

The fastest way to verify everything is working:

```bash
# Run the quick test script
python scripts/quick_test.py
```

This will verify:
- All imports work
- Configuration loading
- Database setup
- Scoring algorithm
- Repository operations

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=job_agent tests/

# Run comprehensive test suite
./scripts/test_all.sh
```

### Validate Configuration

Before running the agent, validate your configuration:

```bash
python scripts/validate_config.py config/config.yaml config/profile.yaml
```

### Test End-to-End (Without Email)

```bash
# 1. Ensure config files are set up
cp config/config.example.yaml config/config.yaml
cp config/profile.example.yaml config/profile.yaml

# 2. Edit config.yaml with your Naukri search URL

# 3. Run a single poll cycle (no email)
naukri-agent poll-once --config config/config.yaml --no-email

# 4. Check results
sqlite3 data/agent.db "SELECT title, company, score, action FROM jobs ORDER BY created_at DESC LIMIT 5;"
```

### Test Email Sending

```bash
# After verifying poll-once works, test email
naukri-agent poll-once --config config/config.yaml

# Check your email inbox for notifications
```

### Test Structure

- **Unit Tests**: Test individual components in isolation (`tests/test_scoring.py`)
- **Integration Tests**: Test component interactions
- **Scoring Tests**: Validate scoring algorithm correctness

### Comprehensive Testing Guide

See [TESTING.md](TESTING.md) for detailed testing instructions, including:
- Unit test examples
- Integration test scenarios
- Configuration validation
- End-to-end testing steps
- Troubleshooting guide

### Writing Tests

Example test structure:

```python
def test_scoring_title_match():
    from job_agent.core.scoring import score
    from job_agent.models.job import JobPosting
    from job_agent.models.profile import Profile
    
    job = JobPosting(
        source="naukri",
        title="Senior Backend Engineer",
        company="Tech Corp",
        location="Bangalore",
        url="https://naukri.com/job/123"
    )
    
    profile = Profile(
        name="Test",
        target_titles=["Senior Backend Engineer"],
        preferred_locations=[],
        must_have_skills=[],
        nice_to_have_skills=[],
        domain_keywords=[],
        company_preferences=CompanyPrefs()
    )
    
    result = score(job, profile, scoring_cfg)
    assert result.score > 0
    assert result.action in ["EMAIL", "QUEUE"]
```

## Deployment

### Docker Deployment

1. **Build image**
   ```bash
   docker build -t naukri-job-agent .
   ```

2. **Run container**
   ```bash
   docker run -d \
     -v $(pwd)/config:/app/config \
     -v $(pwd)/data:/app/data \
     --name naukri-agent \
     naukri-job-agent
   ```

3. **View logs**
   ```bash
   docker logs -f naukri-agent
   ```

### Systemd Service (Linux)

Create `/etc/systemd/system/naukri-agent.service`:

```ini
[Unit]
Description=Naukri Job Agent
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/naukri-job-agent-pro
ExecStart=/path/to/venv/bin/naukri-agent run --config /path/to/config/config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable naukri-agent
sudo systemctl start naukri-agent
sudo systemctl status naukri-agent
```

### Cloud Deployment

**AWS EC2 / DigitalOcean Droplet:**
- Use systemd service as above
- Ensure data directory is backed up
- Monitor logs for errors

**Kubernetes:**
- Create Deployment with persistent volume for database
- Use ConfigMap for configuration
- Use Secret for Gmail credentials

## Troubleshooting

### Common Issues

#### 1. No Jobs Found
- **Check**: Naukri search URL is correct and accessible
- **Check**: Parsing selectors match current Naukri HTML structure
- **Solution**: Update selectors in `config.yaml` if Naukri changed their HTML

#### 2. Email Not Sending
- **Check**: Gmail App Password is correct
- **Check**: 2-Step Verification is enabled on Gmail account
- **Check**: `email.enabled` and `gmail_smtp.enabled` are both `true`
- **Solution**: Regenerate Gmail App Password

#### 3. Database Locked
- **Cause**: Multiple processes accessing SQLite database
- **Solution**: Ensure only one instance is running, or switch to PostgreSQL

#### 4. Parsing Errors
- **Check**: Naukri HTML structure may have changed
- **Solution**: Update CSS selectors in `config.yaml` parsing section
- **Debug**: Enable DEBUG logging to see HTML structure

#### 5. High Memory Usage
- **Cause**: Large HTML pages or many jobs in memory
- **Solution**: Reduce `max_jobs_per_run` in configuration

### Debugging

Enable debug logging:
```yaml
app:
  log_level: "DEBUG"
```

Check database:
```bash
sqlite3 data/agent.db "SELECT * FROM jobs ORDER BY created_at DESC LIMIT 10;"
```

Test email sending:
```bash
naukri-agent poll-once --config config/config.yaml
```

## Contributing

1. Follow the existing architecture patterns
2. Add tests for new features
3. Update documentation for API changes
4. Ensure all tests pass before submitting

## License

MIT License - see LICENSE file for details

## Quick Testing Checklist

Before deploying to production, verify:

1. ✅ **Installation**: `python scripts/quick_test.py` passes
2. ✅ **Configuration**: `python scripts/validate_config.py config/config.yaml config/profile.yaml`
3. ✅ **Polling**: `naukri-agent poll-once --config config/config.yaml --no-email` works
4. ✅ **Database**: Jobs are stored correctly (check with `sqlite3 data/agent.db`)
5. ✅ **Email**: Test email sending with a test account first
6. ✅ **Scoring**: Review scores match your expectations

See [TESTING.md](TESTING.md) for comprehensive testing guide.

## Support

For issues, questions, or contributions, please open an issue on the repository.

---

**Built with attention to production reliability, maintainability, and developer experience.**


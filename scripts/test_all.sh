#!/bin/bash
set -e

echo "🧪 Running Naukri Job Agent Tests"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo ""
echo "1. Testing imports..."
if python -c "from job_agent.core.app import AppContext; print('✓ Imports OK')" 2>&1; then
    echo -e "${GREEN}✓ Imports successful${NC}"
else
    echo -e "${RED}✗ Import failed${NC}"
    exit 1
fi

echo ""
echo "2. Running unit tests..."
if pytest tests/ -v 2>&1; then
    echo -e "${GREEN}✓ Unit tests passed${NC}"
else
    echo -e "${RED}✗ Unit tests failed${NC}"
    exit 1
fi

echo ""
echo "3. Testing configuration loading..."
if python -c "
from job_agent.core.config import load_config, load_profile
cfg = load_config('config/config.example.yaml')
profile = load_profile('config/profile.example.yaml')
print('✓ Config loading OK')
" 2>&1; then
    echo -e "${GREEN}✓ Configuration loading successful${NC}"
else
    echo -e "${RED}✗ Configuration loading failed${NC}"
    exit 1
fi

echo ""
echo "4. Testing database setup..."
if python -c "
from job_agent.store.db import create_engine_from_url, init_db
import os
test_db = 'test_all.db'
engine = create_engine_from_url(f'sqlite:///{test_db}')
init_db(engine)
if os.path.exists(test_db):
    os.remove(test_db)
print('✓ Database setup OK')
" 2>&1; then
    echo -e "${GREEN}✓ Database setup successful${NC}"
else
    echo -e "${RED}✗ Database setup failed${NC}"
    exit 1
fi

echo ""
echo "5. Testing repository operations..."
if python -c "
from job_agent.store.db import create_engine_from_url, create_session_factory, init_db
from job_agent.store.repo import JobRepository
from job_agent.models.job import JobPosting, ObservedJob
from job_agent.models.score import ScoreResult
from datetime import datetime
import pytz
import os

test_db = 'test_repo.db'
engine = create_engine_from_url(f'sqlite:///{test_db}')
init_db(engine)
session_factory = create_session_factory(engine)

repo = JobRepository(session_factory())
job = JobPosting(
    source='test',
    title='Test Engineer',
    company='Test Corp',
    location='Remote',
    url='https://test.com/job1',
)
observed = ObservedJob(job, 'test_key_123', datetime.now(pytz.UTC))
score_result = ScoreResult(score=85, reasons=['Test'], action='EMAIL')

repo.insert(observed, score_result)
assert repo.exists('test_key_123')
repo.mark_emailed('test_key_123')

if os.path.exists(test_db):
    os.remove(test_db)
print('✓ Repository operations OK')
" 2>&1; then
    echo -e "${GREEN}✓ Repository operations successful${NC}"
else
    echo -e "${RED}✗ Repository operations failed${NC}"
    exit 1
fi

echo ""
echo "=================================="
echo -e "${GREEN}✅ All tests passed!${NC}"
echo ""


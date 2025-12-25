#!/usr/bin/env python3
"""
Quick test script to verify the Naukri Job Agent is working.
Run this after installation to verify everything is set up correctly.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all modules can be imported."""
    print("1. Testing imports...")
    try:
        from job_agent.core.app import AppContext
        from job_agent.core.config import load_config, load_profile
        from job_agent.core.scoring import score
        from job_agent.core.services import PollingService, DigestService
        from job_agent.store.db import create_engine_from_url, init_db
        from job_agent.store.repo import JobRepository
        from job_agent.adapters.clock import Clock
        from job_agent.adapters.scheduler import Scheduler
        print("   ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"   ✗ Import failed: {e}")
        return False

def test_config_loading():
    """Test configuration file loading."""
    print("\n2. Testing configuration loading...")
    config_path = Path("config/config.example.yaml")
    profile_path = Path("config/profile.example.yaml")
    
    if not config_path.exists():
        print(f"   ⚠ Config example not found: {config_path}")
        print("   (This is OK if you're using your own config)")
        return True
    
    try:
        from job_agent.core.config import load_config, load_profile
        cfg = load_config(str(config_path))
        profile = load_profile(str(profile_path))
        print(f"   ✓ Config loaded: {len(cfg.sources.naukri.search_urls)} search URLs")
        print(f"   ✓ Profile loaded: {profile.profile.name}")
        return True
    except Exception as e:
        print(f"   ✗ Config loading failed: {e}")
        return False

def test_database():
    """Test database initialization."""
    print("\n3. Testing database setup...")
    try:
        from job_agent.store.db import create_engine_from_url, init_db
        import os
        
        test_db = "test_quick.db"
        engine = create_engine_from_url(f"sqlite:///{test_db}")
        init_db(engine)
        
        if os.path.exists(test_db):
            os.remove(test_db)
        
        print("   ✓ Database initialization successful")
        return True
    except Exception as e:
        print(f"   ✗ Database setup failed: {e}")
        return False

def test_scoring():
    """Test scoring algorithm."""
    print("\n4. Testing scoring algorithm...")
    try:
        from job_agent.core.scoring import score
        from job_agent.models.job import JobPosting
        from job_agent.models.profile import Profile, CompanyPrefs
        from job_agent.models.config import ScoringCfg, FreshnessBoostCfg, WeightsCfg, HardFiltersCfg
        
        cfg = ScoringCfg(
            min_score_to_email=70,
            freshness_boost=FreshnessBoostCfg(15, 10, 6),
            weights=WeightsCfg(25, 45, 12, 8, 10),
            hard_filters=HardFiltersCfg([], []),
        )
        
        profile = Profile(
            name="Test",
            target_titles=["Senior Engineer"],
            preferred_locations=["Remote"],
            must_have_skills=["Python"],
            nice_to_have_skills=[],
            domain_keywords=[],
            company_preferences=CompanyPrefs(),
        )
        
        job = JobPosting(
            source="test",
            title="Senior Engineer - Python",
            company="Test Corp",
            location="Remote",
            url="https://test.com",
            posted_text="Just now",
        )
        
        result = score(job, profile, cfg)
        assert result.score > 0
        assert result.action in ["EMAIL", "QUEUE", "SKIP"]
        print(f"   ✓ Scoring works: score={result.score}, action={result.action}")
        return True
    except Exception as e:
        print(f"   ✗ Scoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_repository():
    """Test repository operations."""
    print("\n5. Testing repository operations...")
    try:
        from job_agent.store.db import create_engine_from_url, create_session_factory, init_db
        from job_agent.store.repo import JobRepository
        from job_agent.models.job import JobPosting, ObservedJob
        from job_agent.models.score import ScoreResult
        from datetime import datetime
        import pytz
        import os
        
        test_db = "test_repo_quick.db"
        engine = create_engine_from_url(f"sqlite:///{test_db}")
        init_db(engine)
        session_factory = create_session_factory(engine)
        
        repo = JobRepository(session_factory())
        
        # Test insert
        job = JobPosting(
            source="test",
            title="Test Job",
            company="Test",
            location="Remote",
            url="https://test.com",
        )
        observed = ObservedJob(job, "test_key", datetime.now(pytz.UTC))
        score_result = ScoreResult(score=80, reasons=["Test"], action="EMAIL")
        repo.insert(observed, score_result)
        
        # Test exists
        assert repo.exists("test_key")
        
        # Test mark_emailed
        repo.mark_emailed("test_key")
        
        if os.path.exists(test_db):
            os.remove(test_db)
        
        print("   ✓ Repository operations successful")
        return True
    except Exception as e:
        print(f"   ✗ Repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all quick tests."""
    print("=" * 60)
    print("Naukri Job Agent - Quick Test")
    print("=" * 60)
    print()
    
    tests = [
        test_imports,
        test_config_loading,
        test_database,
        test_scoring,
        test_repository,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ✗ Test crashed: {e}")
            results.append(False)
    
    print()
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All tests passed! ({passed}/{total})")
        print()
        print("Next steps:")
        print("1. Copy config.example.yaml to config.yaml")
        print("2. Copy profile.example.yaml to profile.yaml")
        print("3. Edit config.yaml with your settings")
        print("4. Edit profile.yaml with your preferences")
        print("5. Run: naukri-agent poll-once --config config/config.yaml --no-email")
        return 0
    else:
        print(f"❌ Some tests failed ({passed}/{total} passed)")
        print()
        print("Please check the errors above and fix any issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())


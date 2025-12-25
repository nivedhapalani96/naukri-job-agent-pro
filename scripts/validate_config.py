#!/usr/bin/env python3
"""Validate configuration files for Naukri Job Agent"""

import sys
from pathlib import Path
from job_agent.core.config import load_config, load_profile

def validate_config(config_path: str):
    """Validate the main configuration file."""
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
            # Check if placeholder URL is still there
            for url in cfg.sources.naukri.search_urls:
                if "<PASTE" in url or "example" in url.lower():
                    print(f"⚠ Warning: Search URL may contain placeholder: {url}")
        
        print("✓ All configuration checks passed")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_profile(profile_path: str):
    """Validate the profile configuration file."""
    try:
        profile_data = load_profile(profile_path)
        profile = profile_data.profile
        
        assert profile.name, "name is required"
        assert len(profile.target_titles) > 0, "At least one target_title is required"
        
        print(f"✓ Profile file '{profile_path}' is valid")
        print(f"  Name: {profile.name}")
        print(f"  Target titles: {len(profile.target_titles)}")
        print(f"  Skills: {len(profile.must_have_skills)} must-have, {len(profile.nice_to_have_skills)} nice-to-have")
        print(f"  Locations: {len(profile.preferred_locations)}")
        return True
    except Exception as e:
        print(f"✗ Profile error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python validate_config.py <config.yaml> <profile.yaml>")
        print("\nExample:")
        print("  python scripts/validate_config.py config/config.yaml config/profile.yaml")
        sys.exit(1)
    
    config_path = sys.argv[1]
    profile_path = sys.argv[2]
    
    if not Path(config_path).exists():
        print(f"✗ Config file not found: {config_path}")
        sys.exit(1)
    
    if not Path(profile_path).exists():
        print(f"✗ Profile file not found: {profile_path}")
        sys.exit(1)
    
    print("Validating Naukri Job Agent Configuration")
    print("=" * 50)
    print()
    
    config_ok = validate_config(config_path)
    print()
    profile_ok = validate_profile(profile_path)
    
    print()
    print("=" * 50)
    if config_ok and profile_ok:
        print("✅ All validations passed!")
        sys.exit(0)
    else:
        print("❌ Validation failed. Please fix the errors above.")
        sys.exit(1)


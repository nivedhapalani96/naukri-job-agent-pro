from pathlib import Path
import yaml
from job_agent.models.config import RootCfg
from job_agent.models.profile import RootProfile

def load_config(path: str) -> RootCfg:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return RootCfg(**data)

def load_profile(path: str) -> RootProfile:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return RootProfile(**data)

from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class ScoreResult:
    score: int
    reasons: List[str]
    action: str  # EMAIL / QUEUE / SKIP

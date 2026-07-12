from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DiscoveryContext:
    """Injectable runtime context for a discovery run."""
    foundation_gate_passed: bool = False
    focus_file_exists: bool = False
    focus_file_populated: bool = False
    batch_cap: int = 5
    creation_cap: int = 3


@dataclass
class DiscoveryRunResult:
    """Outcome of one bounded discovery run."""
    state: str
    created_pm_idea_numbers: List[int] = field(default_factory=list)
    deferred_count: int = 0
    dropped_count: int = 0
    halted_reason: Optional[str] = None

"""
Binance Sentinel
Research case data model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ResearchCase:
    case_id: str
    name: str

    symbol: str
    direction: str
    time_horizon: str
    thesis: str

    assumptions: List[str] = field(default_factory=list)

    materials: List[dict] = field(default_factory=list)

    evidence: List[dict] = field(default_factory=list)

    confidence: Optional[float] = None
    verdict: Optional[str] = None

    invalidation_conditions: List[str] = field(
        default_factory=list
    )

    thesis_versions: List[dict] = field(
        default_factory=list
    )

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    updated_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
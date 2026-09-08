"""
Binance Sentinel
Evidence Ledger.

Stores structured evidence supporting or challenging
a trading thesis.

The ledger does not decide whether the trade is good.
It records observations and their relationship to the thesis.
"""

from dataclasses import dataclass, field
from datetime import datetime


VALID_TYPES = {
    "FOR",
    "AGAINST",
    "INCONCLUSIVE",
    "INVALIDATION",
}


@dataclass
class Evidence:
    """
    One item in the Evidence Ledger.
    """

    evidence_id: str

    evidence_type: str

    observation: str

    timeframe: str

    source: str

    strength: str

    reasoning: str

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def __post_init__(self):
        self.evidence_type = self.evidence_type.upper()
        self.strength = self.strength.upper()

        if self.evidence_type not in VALID_TYPES:
            raise ValueError(
                f"Invalid evidence type: "
                f"{self.evidence_type}. "
                f"Expected one of: "
                f"{', '.join(sorted(VALID_TYPES))}"
            )


class EvidenceLedger:
    """
    Collection of evidence for one research session.
    """

    def __init__(self):
        self._evidence: list[Evidence] = []

    def add(
        self,
        evidence_type: str,
        observation: str,
        timeframe: str,
        source: str,
        strength: str,
        reasoning: str,
    ) -> Evidence:

        evidence = Evidence(
            evidence_id=self._generate_id(),
            evidence_type=evidence_type,
            observation=observation,
            timeframe=timeframe,
            source=source,
            strength=strength,
            reasoning=reasoning,
        )

        self._evidence.append(evidence)

        return evidence

    def all(self) -> list[Evidence]:
        return list(self._evidence)

    def by_type(
        self,
        evidence_type: str,
    ) -> list[Evidence]:

        evidence_type = evidence_type.upper()

        return [
            item
            for item in self._evidence
            if item.evidence_type == evidence_type
        ]

    def count(
        self,
        evidence_type: str,
    ) -> int:

        return len(
            self.by_type(evidence_type)
        )

    def summary(self) -> dict:
        return {
            "total": len(self._evidence),
            "FOR": self.count("FOR"),
            "AGAINST": self.count("AGAINST"),
            "INCONCLUSIVE": self.count("INCONCLUSIVE"),
            "INVALIDATION": self.count("INVALIDATION"),
        }

    @staticmethod
    def _generate_id() -> str:
        timestamp = datetime.now().strftime(
            "%Y%m%d%H%M%S%f"
        )

        return f"EVIDENCE_{timestamp}"


######### test

if __name__ == "__main__":

    ledger = EvidenceLedger()

    print("=" * 50)
    print("       EVIDENCE LEDGER TEST")
    print("=" * 50)

    print()

    # Evidence supporting the thesis
    ledger.add(
        evidence_type="FOR",
        observation=(
            "4H price increased 8% over the "
            "observed sample."
        ),
        timeframe="4H",
        source="python_market_analysis",
        strength="MEDIUM",
        reasoning=(
            "Positive price movement supports "
            "the long thesis."
        ),
    )

    # Evidence contradicting the thesis
    ledger.add(
        evidence_type="AGAINST",
        observation=(
            "Price is approaching the observed "
            "resistance level."
        ),
        timeframe="4H",
        source="python_market_analysis",
        strength="MEDIUM",
        reasoning=(
            "Resistance may limit further upside "
            "unless price breaks through it."
        ),
    )

    # Evidence that cannot yet be classified
    ledger.add(
        evidence_type="INCONCLUSIVE",
        observation=(
            "Volatility remains relatively low."
        ),
        timeframe="4H",
        source="python_market_analysis",
        strength="LOW",
        reasoning=(
            "Low volatility alone does not establish "
            "either continuation or reversal."
        ),
    )

    # Explicit thesis invalidation
    ledger.add(
        evidence_type="INVALIDATION",
        observation=(
            "A sustained break below the defined "
            "structural support would invalidate "
            "the long thesis."
        ),
        timeframe="4H",
        source="research_plan",
        strength="HIGH",
        reasoning=(
            "The long thesis depends on the current "
            "support structure remaining intact."
        ),
    )

    print()

    for evidence in ledger.all():

        print(
            f"[{evidence.evidence_type}] "
            f"{evidence.timeframe} | "
            f"{evidence.strength}"
        )

        print(
            f"  Observation: {evidence.observation}"
        )

        print(
            f"  Reasoning:   {evidence.reasoning}"
        )

        print(
            f"  Source:      {evidence.source}"
        )

        print()

    print("Ledger summary:")
    print(ledger.summary())

    print()
    print("=" * 50)
    print("EVIDENCE LEDGER TEST PASSED")
    print("=" * 50)
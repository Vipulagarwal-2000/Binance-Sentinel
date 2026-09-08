"""
Binance Sentinel
Adversarial thesis critic.

The critic attempts to find weaknesses in the current thesis.

It does not replace the Evidence Ledger.
It adds explicit challenges that can later be reviewed
by the reasoning/LLM layer.
"""

from dataclasses import dataclass, field

from analysis.evidence import EvidenceLedger
from analysis.multi_timeframe import MultiTimeframeResult


@dataclass
class Challenge:
    """
    One adversarial challenge against the thesis.
    """

    challenge_id: str

    category: str

    challenge: str

    severity: str

    timeframe: str

    evidence_ids: list[str] = field(
        default_factory=list
    )


@dataclass
class CriticResult:
    """
    Result of adversarial thesis examination.
    """

    challenges: list[Challenge]

    overall_risk: str

    summary: str


class AdversarialCritic:
    """
    Searches the existing evidence for weaknesses
    in the thesis.
    """

    def evaluate(
        self,
        ledger: EvidenceLedger,
        timeframe_result: MultiTimeframeResult,
        direction: str,
    ) -> CriticResult:

        direction = direction.upper()

        if direction not in {"LONG", "SHORT"}:
            raise ValueError(
                "Direction must be LONG or SHORT."
            )

        challenges = []

        challenges.extend(
            self._find_contradicting_evidence(
                ledger
            )
        )

        challenges.extend(
            self._find_invalidation_conditions(
                ledger
            )
        )

        challenges.extend(
            self._find_timeframe_divergence(
                timeframe_result
            )
        )

        challenges.extend(
            self._find_weak_confirmation(
                ledger
            )
        )

        overall_risk = self._determine_risk(
            challenges
        )

        summary = self._build_summary(
            challenges,
            overall_risk,
        )

        return CriticResult(
            challenges=challenges,
            overall_risk=overall_risk,
            summary=summary,
        )

    @staticmethod
    def _find_contradicting_evidence(
        ledger: EvidenceLedger,
    ) -> list[Challenge]:

        challenges = []

        for evidence in ledger.by_type(
            "AGAINST"
        ):

            severity = "MEDIUM"

            if evidence.strength == "HIGH":
                severity = "HIGH"

            challenges.append(
                Challenge(
                    challenge_id=(
                        "CHALLENGE_"
                        + evidence.evidence_id
                    ),
                    category="CONTRADICTING_EVIDENCE",
                    challenge=(
                        "The thesis faces contradictory "
                        "evidence: "
                        + evidence.observation
                    ),
                    severity=severity,
                    timeframe=evidence.timeframe,
                    evidence_ids=[
                        evidence.evidence_id
                    ],
                )
            )

        return challenges

    @staticmethod
    def _find_invalidation_conditions(
        ledger: EvidenceLedger,
    ) -> list[Challenge]:

        challenges = []

        for evidence in ledger.by_type(
            "INVALIDATION"
        ):

            challenges.append(
                Challenge(
                    challenge_id=(
                        "INVALIDATION_"
                        + evidence.evidence_id
                    ),
                    category="THESIS_INVALIDATION",
                    challenge=(
                        "The thesis has an explicit "
                        "invalidation condition: "
                        + evidence.observation
                    ),
                    severity="HIGH",
                    timeframe=evidence.timeframe,
                    evidence_ids=[
                        evidence.evidence_id
                    ],
                )
            )

        return challenges

    @staticmethod
    def _find_timeframe_divergence(
        timeframe_result: MultiTimeframeResult,
    ) -> list[Challenge]:

        if (
            timeframe_result.alignment
            != "DIVERGENT"
        ):
            return []

        return [
            Challenge(
                challenge_id=(
                    "CHALLENGE_TIMEFRAME_DIVERGENCE"
                ),
                category="TIMEFRAME_DIVERGENCE",
                challenge=(
                    "Different timeframes are not "
                    "aligned. The thesis may be supported "
                    "on higher timeframes while weaker "
                    "on shorter timeframes."
                ),
                severity="MEDIUM",
                timeframe="MULTIPLE",
            )
        ]

    @staticmethod
    def _find_weak_confirmation(
        ledger: EvidenceLedger,
    ) -> list[Challenge]:

        challenges = []

        inconclusive = ledger.by_type(
            "INCONCLUSIVE"
        )

        if len(inconclusive) >= 2:

            challenges.append(
                Challenge(
                    challenge_id=(
                        "CHALLENGE_WEAK_CONFIRMATION"
                    ),
                    category="INSUFFICIENT_CONFIRMATION",
                    challenge=(
                        "Multiple evidence items remain "
                        "inconclusive. The thesis may not "
                        "have enough confirmation."
                    ),
                    severity="MEDIUM",
                    timeframe="MULTIPLE",
                )
            )

        return challenges

    @staticmethod
    def _determine_risk(
        challenges: list[Challenge],
    ) -> str:

        if any(
            challenge.severity == "HIGH"
            for challenge in challenges
        ):
            return "HIGH"

        if any(
            challenge.severity == "MEDIUM"
            for challenge in challenges
        ):
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def _build_summary(
        challenges: list[Challenge],
        overall_risk: str,
    ) -> str:

        if not challenges:

            return (
                "No major weaknesses were identified "
                "by the current deterministic critic."
            )

        return (
            f"The adversarial critic identified "
            f"{len(challenges)} challenge(s). "
            f"Overall challenge risk: "
            f"{overall_risk}."
        )


if __name__ == "__main__":

    from analysis.evidence import EvidenceLedger
    from analysis.multi_timeframe import (
        MultiTimeframeAggregator,
    )

    ledger = EvidenceLedger()

    # Supporting evidence
    ledger.add(
        evidence_type="FOR",
        observation="1D trend is bullish.",
        timeframe="1D",
        source="python_market_analysis",
        strength="HIGH",
        reasoning=(
            "Higher timeframe structure supports "
            "the long thesis."
        ),
    )

    # Contradicting evidence
    ledger.add(
        evidence_type="AGAINST",
        observation="1H momentum is negative.",
        timeframe="1H",
        source="python_market_analysis",
        strength="MEDIUM",
        reasoning=(
            "Short-term momentum contradicts "
            "the long thesis."
        ),
    )

    # Invalidation
    ledger.add(
        evidence_type="INVALIDATION",
        observation=(
            "4H structure breaks below support."
        ),
        timeframe="4H",
        source="python_market_analysis",
        strength="HIGH",
        reasoning=(
            "A sustained support break invalidates "
            "the long thesis."
        ),
    )

    # Inconclusive evidence
    ledger.add(
        evidence_type="INCONCLUSIVE",
        observation=(
            "Order-book imbalance is unclear."
        ),
        timeframe="1H",
        source="python_market_analysis",
        strength="LOW",
        reasoning=(
            "The order book does not currently "
            "provide a clear directional signal."
        ),
    )

    ledger.add(
        evidence_type="INCONCLUSIVE",
        observation=(
            "Volatility regime is unclear."
        ),
        timeframe="4H",
        source="python_market_analysis",
        strength="LOW",
        reasoning=(
            "Volatility alone does not establish "
            "direction."
        ),
    )

    # Multi-timeframe analysis
    aggregator = MultiTimeframeAggregator()

    timeframe_result = aggregator.aggregate(
        ledger,
        "LONG",
    )

    # Critic
    critic = AdversarialCritic()

    result = critic.evaluate(
        ledger,
        timeframe_result,
        "LONG",
    )

    print("=" * 50)
    print("       ADVERSARIAL CRITIC TEST")
    print("=" * 50)
    print()

    print(
        f"Overall risk: {result.overall_risk}"
    )

    print(
        f"Challenges:   "
        f"{len(result.challenges)}"
    )

    print()

    for challenge in result.challenges:

        print(
            f"[{challenge.severity}] "
            f"{challenge.category}"
        )

        print(
            f"  {challenge.challenge}"
        )

        print(
            f"  Timeframe: "
            f"{challenge.timeframe}"
        )

        print()

    print("Summary:")
    print(result.summary)

    print()
    print("=" * 50)
    print("ADVERSARIAL CRITIC TEST PASSED")
    print("=" * 50)
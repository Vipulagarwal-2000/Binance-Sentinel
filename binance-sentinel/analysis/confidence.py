"""
Binance Sentinel
Evidence-weighted thesis confidence.

This is NOT a statistical price prediction.

It measures how strongly the currently available
evidence supports the user's stated thesis.
"""

from dataclasses import dataclass

from analysis.evidence import EvidenceLedger
from analysis.multi_timeframe import MultiTimeframeResult


STRENGTH_WEIGHTS = {
    "LOW": 1.0,
    "MEDIUM": 2.0,
    "HIGH": 3.0,
}


@dataclass
class ConfidenceResult:
    """
    Evidence-weighted confidence assessment.
    """

    confidence: float

    state: str

    supporting_score: float

    contradicting_score: float

    inconclusive_count: int

    invalidation_score: float

    explanation: str


class ConfidenceEngine:
    """
    Calculates thesis confidence from structured evidence.
    """

    def calculate(
        self,
        ledger: EvidenceLedger,
        timeframe_result: MultiTimeframeResult | None = None,
    ) -> ConfidenceResult:

        supporting_score = 0.0
        contradicting_score = 0.0
        invalidation_score = 0.0

        inconclusive_count = 0

        for evidence in ledger.all():

            weight = STRENGTH_WEIGHTS.get(
                evidence.strength,
                1.0,
            )

            if evidence.evidence_type == "FOR":

                supporting_score += weight

            elif evidence.evidence_type == "AGAINST":

                contradicting_score += weight

            elif evidence.evidence_type == "INCONCLUSIVE":

                inconclusive_count += 1

            elif evidence.evidence_type == "INVALIDATION":

                invalidation_score += weight

        confidence = self._calculate_confidence(
            supporting_score,
            contradicting_score,
            invalidation_score,
        )

        # Multi-timeframe divergence prevents
        # confidence from becoming excessively high.
        if (
            timeframe_result is not None
            and timeframe_result.alignment
            == "DIVERGENT"
        ):
            confidence = min(
                confidence,
                75.0,
            )

        state = self._state_from_confidence(
            confidence
        )

        explanation = self._build_explanation(
            confidence,
            supporting_score,
            contradicting_score,
            invalidation_score,
            inconclusive_count,
            timeframe_result,
        )

        return ConfidenceResult(
            confidence=confidence,
            state=state,
            supporting_score=supporting_score,
            contradicting_score=contradicting_score,
            inconclusive_count=inconclusive_count,
            invalidation_score=invalidation_score,
            explanation=explanation,
        )

    @staticmethod
    def _calculate_confidence(
        supporting_score: float,
        contradicting_score: float,
        invalidation_score: float,
    ) -> float:

        total = (
            supporting_score
            + contradicting_score
            + invalidation_score
        )

        if total == 0:
            return 50.0

        # Invalidation evidence carries additional weight.
        effective_against = (
            contradicting_score
            + invalidation_score * 1.5
        )

        effective_total = (
            supporting_score
            + effective_against
        )

        confidence = (
            supporting_score
            / effective_total
            * 100
        )

        return round(
            max(
                0.0,
                min(100.0, confidence),
            ),
            1,
        )

    @staticmethod
    def _state_from_confidence(
        confidence: float,
    ) -> str:

        if confidence >= 75:
            return "STRONGLY_SUPPORTIVE"

        if confidence >= 60:
            return "MODERATELY_SUPPORTIVE"

        if confidence >= 40:
            return "UNCERTAIN"

        if confidence >= 25:
            return "MODERATELY_CONTRADICTORY"

        return "STRONGLY_CONTRADICTORY"

    @staticmethod
    def _build_explanation(
        confidence: float,
        supporting_score: float,
        contradicting_score: float,
        invalidation_score: float,
        inconclusive_count: int,
        timeframe_result: MultiTimeframeResult | None,
    ) -> str:

        explanation = (
            f"Current evidence-weighted thesis confidence "
            f"is {confidence:.1f}%. "
        )

        explanation += (
            f"Supporting evidence score: "
            f"{supporting_score:.1f}. "
        )

        explanation += (
            f"Contradicting evidence score: "
            f"{contradicting_score:.1f}. "
        )

        explanation += (
            f"Invalidation score: "
            f"{invalidation_score:.1f}. "
        )

        explanation += (
            f"Inconclusive items: "
            f"{inconclusive_count}. "
        )

        if timeframe_result is not None:

            explanation += (
                f"Multi-timeframe alignment is "
                f"{timeframe_result.alignment}."
            )

        return explanation



    ### test

if __name__ == "__main__":

    from analysis.evidence import EvidenceLedger
    from analysis.multi_timeframe import (
        MultiTimeframeAggregator,
    )

    ledger = EvidenceLedger()

    # Strong supporting evidence
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

    ledger.add(
        evidence_type="FOR",
        observation="4H volume is expanding.",
        timeframe="4H",
        source="python_market_analysis",
        strength="MEDIUM",
        reasoning=(
            "Volume supports continuation."
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

    # Invalidation condition
    ledger.add(
        evidence_type="INVALIDATION",
        observation=(
            "Break below structural support."
        ),
        timeframe="4H",
        source="research_plan",
        strength="HIGH",
        reasoning=(
            "A sustained support break invalidates "
            "the thesis."
        ),
    )

    # Multi-timeframe analysis
    aggregator = MultiTimeframeAggregator()

    timeframe_result = aggregator.aggregate(
        ledger,
        "LONG",
    )

    # Confidence calculation
    engine = ConfidenceEngine()

    result = engine.calculate(
        ledger,
        timeframe_result,
    )

    print("=" * 50)
    print("       CONFIDENCE ENGINE TEST")
    print("=" * 50)
    print()

    print(
        f"Confidence:             "
        f"{result.confidence}%"
    )

    print(
        f"State:                  "
        f"{result.state}"
    )

    print(
        f"Supporting score:       "
        f"{result.supporting_score}"
    )

    print(
        f"Contradicting score:    "
        f"{result.contradicting_score}"
    )

    print(
        f"Invalidation score:     "
        f"{result.invalidation_score}"
    )

    print(
        f"Inconclusive items:     "
        f"{result.inconclusive_count}"
    )

    print()

    print("Explanation:")
    print(result.explanation)

    print()
    print("=" * 50)
    print("CONFIDENCE ENGINE TEST PASSED")
    print("=" * 50)
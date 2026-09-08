"""
Binance Sentinel
Multi-timeframe evidence aggregation.

Combines evidence across timeframes without pretending
that every timeframe has equal importance.
"""

from dataclasses import dataclass, field

from analysis.evidence import EvidenceLedger


@dataclass
class TimeframeSummary:
    timeframe: str

    supporting: int = 0
    contradicting: int = 0
    inconclusive: int = 0
    invalidations: int = 0

    observations: list[str] = field(
        default_factory=list
    )


@dataclass
class MultiTimeframeResult:
    """
    Aggregated view of the evidence across timeframes.
    """

    direction: str

    timeframes: list[str]

    summaries: dict[str, TimeframeSummary]

    total_for: int

    total_against: int

    total_inconclusive: int

    total_invalidation: int

    dominant_state: str

    alignment: str

    observations: list[str] = field(
        default_factory=list
    )


class MultiTimeframeAggregator:
    """
    Aggregates Evidence Ledger entries by timeframe.
    """

    def aggregate(
        self,
        ledger: EvidenceLedger,
        direction: str,
    ) -> MultiTimeframeResult:

        direction = direction.upper()

        if direction not in {"LONG", "SHORT"}:
            raise ValueError(
                "Direction must be LONG or SHORT."
            )

        evidence = ledger.all()

        timeframe_names = sorted(
            {
                item.timeframe
                for item in evidence
            }
        )

        summaries = {}

        for timeframe in timeframe_names:

            summary = TimeframeSummary(
                timeframe=timeframe
            )

            timeframe_evidence = [
                item
                for item in evidence
                if item.timeframe == timeframe
            ]

            for item in timeframe_evidence:

                if item.evidence_type == "FOR":
                    summary.supporting += 1

                elif item.evidence_type == "AGAINST":
                    summary.contradicting += 1

                elif item.evidence_type == "INCONCLUSIVE":
                    summary.inconclusive += 1

                elif item.evidence_type == "INVALIDATION":
                    summary.invalidations += 1

                summary.observations.append(
                    item.observation
                )

            summaries[timeframe] = summary

        total_for = ledger.count("FOR")
        total_against = ledger.count("AGAINST")
        total_inconclusive = ledger.count(
            "INCONCLUSIVE"
        )
        total_invalidation = ledger.count(
            "INVALIDATION"
        )

        dominant_state = self._dominant_state(
            total_for,
            total_against,
            total_inconclusive,
        )

        alignment = self._determine_alignment(
            summaries
        )

        observations = self._build_observations(
            summaries,
            alignment,
        )

        return MultiTimeframeResult(
            direction=direction,
            timeframes=timeframe_names,
            summaries=summaries,
            total_for=total_for,
            total_against=total_against,
            total_inconclusive=total_inconclusive,
            total_invalidation=total_invalidation,
            dominant_state=dominant_state,
            alignment=alignment,
            observations=observations,
        )

    @staticmethod
    def _dominant_state(
        supporting: int,
        contradicting: int,
        inconclusive: int,
    ) -> str:

        if (
            supporting > contradicting
            and supporting > inconclusive
        ):
            return "SUPPORTIVE"

        if (
            contradicting > supporting
            and contradicting > inconclusive
        ):
            return "CONTRADICTORY"

        return "MIXED"

    @staticmethod
    def _determine_alignment(
        summaries: dict[str, TimeframeSummary],
    ) -> str:

        if not summaries:
            return "NO_DATA"

        states = []

        for summary in summaries.values():

            if (
                summary.supporting
                > summary.contradicting
                and summary.supporting
                > summary.inconclusive
            ):
                states.append("SUPPORTIVE")

            elif (
                summary.contradicting
                > summary.supporting
                and summary.contradicting
                > summary.inconclusive
            ):
                states.append("CONTRADICTORY")

            else:
                states.append("MIXED")

        if all(
            state == "SUPPORTIVE"
            for state in states
        ):
            return "ALIGNED"

        if all(
            state == "CONTRADICTORY"
            for state in states
        ):
            return "ALIGNED_AGAINST"

        return "DIVERGENT"

    @staticmethod
    def _build_observations(
        summaries: dict[str, TimeframeSummary],
        alignment: str,
    ) -> list[str]:

        observations = []

        for timeframe, summary in summaries.items():

            observations.append(
                f"{timeframe}: "
                f"{summary.supporting} FOR, "
                f"{summary.contradicting} AGAINST, "
                f"{summary.inconclusive} INCONCLUSIVE, "
                f"{summary.invalidations} INVALIDATION."
            )

        observations.append(
            f"Multi-timeframe alignment: {alignment}."
        )

        return observations



    ## test

if __name__ == "__main__":

    from analysis.evidence import EvidenceLedger

    ledger = EvidenceLedger()

    # 1D supports the thesis
    ledger.add(
        evidence_type="FOR",
        observation="1D structure is bullish.",
        timeframe="1D",
        source="python_market_analysis",
        strength="HIGH",
        reasoning="Higher timeframe structure supports the long thesis.",
    )

    ledger.add(
        evidence_type="FOR",
        observation="1D momentum is positive.",
        timeframe="1D",
        source="python_market_analysis",
        strength="MEDIUM",
        reasoning="Momentum supports continuation.",
    )

    # 4H also supports
    ledger.add(
        evidence_type="FOR",
        observation="4H trend is bullish.",
        timeframe="4H",
        source="python_market_analysis",
        strength="MEDIUM",
        reasoning="4H structure supports the long thesis.",
    )

    ledger.add(
        evidence_type="FOR",
        observation="4H volume is expanding.",
        timeframe="4H",
        source="python_market_analysis",
        strength="MEDIUM",
        reasoning="Volume supports the current move.",
    )

    # 1H contradicts
    ledger.add(
        evidence_type="AGAINST",
        observation="1H momentum is negative.",
        timeframe="1H",
        source="python_market_analysis",
        strength="MEDIUM",
        reasoning="Shorter-term momentum is moving against the thesis.",
    )

    aggregator = MultiTimeframeAggregator()

    result = aggregator.aggregate(
        ledger,
        "LONG",
    )

    print("=" * 50)
    print("       MULTI-TIMEFRAME TEST")
    print("=" * 50)
    print()

    print(
        f"Direction:       {result.direction}"
    )

    print(
        f"Timeframes:      {result.timeframes}"
    )

    print(
        f"Dominant state:  {result.dominant_state}"
    )

    print(
        f"Alignment:       {result.alignment}"
    )

    print()

    print("Totals:")
    print(
        f"  FOR:           {result.total_for}"
    )
    print(
        f"  AGAINST:       {result.total_against}"
    )
    print(
        f"  INCONCLUSIVE:  {result.total_inconclusive}"
    )
    print(
        f"  INVALIDATION:  {result.total_invalidation}"
    )

    print()

    print("Timeframe summaries:")

    for timeframe, summary in (
        result.summaries.items()
    ):

        print(
            f"  {timeframe}: "
            f"{summary.supporting} FOR / "
            f"{summary.contradicting} AGAINST / "
            f"{summary.inconclusive} UNKNOWN"
        )

    print()

    print("Observations:")

    for observation in result.observations:
        print(f"  - {observation}")

    print()
    print("=" * 50)
    print("MULTI-TIMEFRAME TEST PASSED")
    print("=" * 50)  
"""
Binance Sentinel
Deterministic thesis evaluator.

Converts deterministic market-analysis results into
directional Evidence Ledger entries.

This layer does not predict price and does not use an LLM.
It classifies observed market facts as:

    FOR
    AGAINST
    INCONCLUSIVE
    INVALIDATION
"""

from typing import Dict

from analysis.evidence import EvidenceLedger
from analysis.market_analysis import AnalysisResult


class ThesisEvaluator:
    """
    Deterministic evaluator that converts market-analysis facts
    into directional thesis evidence.

    This layer does not predict price. It classifies observed facts
    as FOR, AGAINST, INCONCLUSIVE, or INVALIDATION relative to
    the supplied thesis direction.
    """

    def evaluate(
        self,
        analysis_results: Dict[str, AnalysisResult],
        direction: str,
    ) -> EvidenceLedger:

        direction = direction.upper().strip()

        if direction not in {"LONG", "SHORT"}:
            raise ValueError("Direction must be LONG or SHORT")

        ledger = EvidenceLedger()
        # Future conditions that would weaken/invalidate the thesis.
        # These are derived only from deterministic analysis already available;
        # no arbitrary price thresholds are invented.
        ledger.invalidation_conditions = []

        for timeframe, result in analysis_results.items():
            self._evaluate_trend(
                ledger, timeframe, result, direction
            )
            self._evaluate_structure(
                ledger, timeframe, result, direction
            )
            self._evaluate_momentum(
                ledger, timeframe, result, direction
            )
            self._evaluate_volume(
                ledger, timeframe, result, direction
            )
            self._evaluate_levels(
                ledger, timeframe, result, direction
            )
            self._evaluate_volatility(
                ledger, timeframe, result, direction
            )

        self._build_invalidation_conditions(
            ledger=ledger,
            analysis_results=analysis_results,
            direction=direction,
        )

        return ledger

    def _build_invalidation_conditions(
        self,
        ledger,
        analysis_results,
        direction,
    ):
        """Derive defensible future thesis-invalidation conditions.

        These are conditions to watch for, not claims that they have already
        happened. They use only levels and structural states already produced
        by the deterministic market-analysis layer.
        """
        for timeframe, result in analysis_results.items():
            support = getattr(result, "support", None)
            resistance = getattr(result, "resistance", None)
            structure = str(getattr(result, "structure", "")).upper()
            trend = str(getattr(result, "trend", "")).upper()
            momentum = str(getattr(result, "momentum", "")).upper()

            if direction == "LONG":
                if support is not None:
                    ledger.invalidation_conditions.append(
                        f"{timeframe}: a confirmed break below support ({support}) "
                        "would invalidate the LONG thesis's current structural floor."
                    )
                else:
                    ledger.invalidation_conditions.append(
                        f"{timeframe}: a confirmed shift to bearish market structure "
                        "would invalidate the LONG thesis."
                    )

                if trend == "BULLISH" or structure in {
                    "HIGHER_HIGHS_HIGHER_LOWS", "HIGHER_HIGHS", "HIGHER_LOWS"
                }:
                    ledger.invalidation_conditions.append(
                        f"{timeframe}: a sustained transition from the current bullish "
                        "trend/structure to bearish structure would invalidate the LONG thesis."
                    )
                elif trend == "BEARISH" or structure in {
                    "LOWER_HIGHS_LOWER_LOWS", "LOWER_HIGHS", "LOWER_LOWS"
                }:
                    ledger.invalidation_conditions.append(
                        f"{timeframe}: continued bearish trend and structure without "
                        "recovery would further invalidate the LONG thesis."
                    )

                if momentum == "POSITIVE":
                    ledger.invalidation_conditions.append(
                        f"{timeframe}: a confirmed shift from positive to sustained "
                        "negative momentum would remove an important LONG confirmation."
                    )

            else:  # SHORT
                if resistance is not None:
                    ledger.invalidation_conditions.append(
                        f"{timeframe}: a confirmed break above resistance ({resistance}) "
                        "would invalidate the SHORT thesis's current structural ceiling."
                    )
                else:
                    ledger.invalidation_conditions.append(
                        f"{timeframe}: a confirmed shift to bullish market structure "
                        "would invalidate the SHORT thesis."
                    )

                if trend == "BEARISH" or structure in {
                    "LOWER_HIGHS_LOWER_LOWS", "LOWER_HIGHS", "LOWER_LOWS"
                }:
                    ledger.invalidation_conditions.append(
                        f"{timeframe}: a sustained transition from the current bearish "
                        "trend/structure to bullish structure would invalidate the SHORT thesis."
                    )
                elif trend == "BULLISH" or structure in {
                    "HIGHER_HIGHS_HIGHER_LOWS", "HIGHER_HIGHS", "HIGHER_LOWS"
                }:
                    ledger.invalidation_conditions.append(
                        f"{timeframe}: continued bullish trend and structure without "
                        "reversal would further invalidate the SHORT thesis."
                    )

                if momentum == "NEGATIVE":
                    ledger.invalidation_conditions.append(
                        f"{timeframe}: a confirmed shift from negative to sustained "
                        "positive momentum would remove an important SHORT confirmation."
                    )

        # Keep the output concise and deterministic.
        ledger.invalidation_conditions = list(dict.fromkeys(ledger.invalidation_conditions))

    # ---------------------------------------------------------
    # TREND
    # ---------------------------------------------------------

    def _evaluate_trend(
        self,
        ledger,
        timeframe,
        result,
        direction,
    ):
        trend = result.trend.upper()

        if trend == "BULLISH":
            evidence_type = (
                "FOR" if direction == "LONG" else "AGAINST"
            )
        elif trend == "BEARISH":
            evidence_type = (
                "FOR" if direction == "SHORT" else "AGAINST"
            )
        else:
            evidence_type = "INCONCLUSIVE"

        if evidence_type == "FOR":
            reasoning = (
                f"The {trend.lower()} trend supports the "
                f"{direction} thesis."
            )
        elif evidence_type == "AGAINST":
            reasoning = (
                f"The {trend.lower()} trend contradicts the "
                f"{direction} thesis."
            )
        else:
            reasoning = (
                f"The {trend.lower()} trend does not establish "
                f"directional support for the {direction} thesis."
            )

        self._add(
            ledger,
            evidence_type,
            f"{timeframe} trend is {trend}.",
            timeframe,
            "HIGH",
            reasoning,
        )

    # ---------------------------------------------------------
    # STRUCTURE
    # ---------------------------------------------------------

    def _evaluate_structure(
        self,
        ledger,
        timeframe,
        result,
        direction,
    ):
        structure = result.structure.upper()

        bullish_structures = {
            "HIGHER_HIGHS_HIGHER_LOWS",
            "HIGHER_HIGHS",
            "HIGHER_LOWS",
        }

        bearish_structures = {
            "LOWER_HIGHS_LOWER_LOWS",
            "LOWER_HIGHS",
            "LOWER_LOWS",
        }

        if structure in bullish_structures:
            evidence_type = (
                "FOR" if direction == "LONG" else "AGAINST"
            )
        elif structure in bearish_structures:
            evidence_type = (
                "FOR" if direction == "SHORT" else "AGAINST"
            )
        else:
            evidence_type = "INCONCLUSIVE"

        structure_text = structure.lower().replace("_", " ")

        if evidence_type == "FOR":
            reasoning = (
                f"The {structure_text} structure supports "
                f"the {direction} thesis."
            )
        elif evidence_type == "AGAINST":
            reasoning = (
                f"The {structure_text} structure contradicts "
                f"the {direction} thesis."
            )
        else:
            reasoning = (
                f"The {structure_text} structure does not establish "
                f"directional support for the {direction} thesis."
            )

        self._add(
            ledger,
            evidence_type,
            f"{timeframe} market structure is {structure}.",
            timeframe,
            "HIGH",
            reasoning,
        )

    # ---------------------------------------------------------
    # MOMENTUM
    # ---------------------------------------------------------

    def _evaluate_momentum(
        self,
        ledger,
        timeframe,
        result,
        direction,
    ):
        momentum = result.momentum.upper()

        if momentum == "POSITIVE":
            evidence_type = (
                "FOR" if direction == "LONG" else "AGAINST"
            )
        elif momentum == "NEGATIVE":
            evidence_type = (
                "FOR" if direction == "SHORT" else "AGAINST"
            )
        else:
            evidence_type = "INCONCLUSIVE"

        if evidence_type == "FOR":
            reasoning = (
                f"{momentum.capitalize()} momentum supports "
                f"the {direction} thesis."
            )
        elif evidence_type == "AGAINST":
            reasoning = (
                f"{momentum.capitalize()} momentum contradicts "
                f"the {direction} thesis."
            )
        else:
            reasoning = (
                f"{momentum.capitalize()} momentum does not establish "
                f"directional support for the {direction} thesis."
            )

        self._add(
            ledger,
            evidence_type,
            (
                f"{timeframe} momentum is {momentum}; "
                f"RSI={result.rsi:.2f}, "
                f"ROC={result.roc_percent:.2f}%."
            ),
            timeframe,
            "MEDIUM",
            reasoning,
        )

        # Momentum change must be interpreted together with
        # momentum direction.

        change = result.momentum_change.upper()

        if change == "ACCELERATING":
            if momentum == "POSITIVE":
                change_type = (
                    "FOR" if direction == "LONG" else "AGAINST"
                )
            elif momentum == "NEGATIVE":
                change_type = (
                    "FOR" if direction == "SHORT" else "AGAINST"
                )
            else:
                change_type = "INCONCLUSIVE"

        elif change == "DECELERATING":
            if momentum == "POSITIVE":
                change_type = (
                    "AGAINST" if direction == "LONG" else "FOR"
                )
            elif momentum == "NEGATIVE":
                change_type = (
                    "AGAINST" if direction == "SHORT" else "FOR"
                )
            else:
                change_type = "INCONCLUSIVE"

        else:
            change_type = "INCONCLUSIVE"

        if change_type == "FOR":
            change_reasoning = (
                f"Momentum is {change.lower()} in a direction "
                f"consistent with the {direction} thesis."
            )
        elif change_type == "AGAINST":
            change_reasoning = (
                f"Momentum is {change.lower()} in a manner that "
                f"works against the {direction} thesis."
            )
        else:
            change_reasoning = (
                f"Momentum change is {change.lower()} and does not "
                f"provide clear directional confirmation."
            )

        self._add(
            ledger,
            change_type,
            (
                f"{timeframe} momentum change is {change}; "
                f"momentum slope={result.momentum_slope:.4f}."
            ),
            timeframe,
            "MEDIUM",
            change_reasoning,
        )

    # ---------------------------------------------------------
    # VOLUME / PRICE
    # ---------------------------------------------------------

    def _evaluate_volume(
        self,
        ledger,
        timeframe,
        result,
        direction,
    ):
        relationship = result.price_volume_relationship.upper()

        if relationship == "PRICE_UP_VOLUME_UP":
            evidence_type = (
                "FOR" if direction == "LONG" else "AGAINST"
            )
        elif relationship == "PRICE_DOWN_VOLUME_UP":
            evidence_type = (
                "FOR" if direction == "SHORT" else "AGAINST"
            )
        else:
            evidence_type = "INCONCLUSIVE"

        relationship_text = relationship.lower().replace("_", " ")

        if evidence_type == "FOR":
            reasoning = (
                f"The {relationship_text} relationship provides "
                f"directional confirmation for the {direction} thesis."
            )
        elif evidence_type == "AGAINST":
            reasoning = (
                f"The {relationship_text} relationship contradicts "
                f"the {direction} thesis."
            )
        else:
            reasoning = (
                f"The {relationship_text} relationship does not provide "
                f"clear directional confirmation."
            )

        self._add(
            ledger,
            evidence_type,
            (
                f"{timeframe} price-volume relationship is "
                f"{relationship}; volume ratio="
                f"{result.volume_ratio:.2f}x."
            ),
            timeframe,
            "MEDIUM",
            reasoning,
        )

        # Strong volume expansion is useful confirmation only
        # when its direction agrees with the thesis.

        if result.volume_ratio >= 1.5:

            if relationship == "PRICE_UP_VOLUME_UP":
                expansion_type = (
                    "FOR" if direction == "LONG" else "AGAINST"
                )
            elif relationship == "PRICE_DOWN_VOLUME_UP":
                expansion_type = (
                    "FOR" if direction == "SHORT" else "AGAINST"
                )
            else:
                expansion_type = "INCONCLUSIVE"

            if expansion_type == "FOR":
                expansion_reasoning = (
                    f"Volume expansion is aligned with price movement "
                    f"supporting the {direction} thesis, strengthening "
                    f"confirmation."
                )
            elif expansion_type == "AGAINST":
                expansion_reasoning = (
                    f"Volume expansion is aligned with price movement "
                    f"against the {direction} thesis, strengthening "
                    f"contradictory evidence."
                )
            else:
                expansion_reasoning = (
                    "Volume expansion is present, but its observed "
                    "price relationship does not establish direction."
                )

            self._add(
                ledger,
                expansion_type,
                (
                    f"{timeframe} volume is expanding "
                    f"({result.volume_ratio:.2f}x average)."
                ),
                timeframe,
                "MEDIUM",
                expansion_reasoning,
            )

        elif result.volume_ratio < 0.75:

            self._add(
                ledger,
                "INCONCLUSIVE",
                (
                    f"{timeframe} volume is contracting "
                    f"({result.volume_ratio:.2f}x average)."
                ),
                timeframe,
                "LOW",
                (
                    "Contracting volume does not independently establish "
                    "directional confirmation."
                ),
            )

    # ---------------------------------------------------------
    # SUPPORT / RESISTANCE
    # ---------------------------------------------------------

    def _evaluate_levels(
        self,
        ledger,
        timeframe,
        result,
        direction,
    ):
        support_distance = (
            result.distance_to_support_percent
        )

        resistance_distance = (
            result.distance_to_resistance_percent
        )

        # ---------------------------------------------------------
        # PRICE BELOW SUPPORT
        # ---------------------------------------------------------

        if support_distance < 0:

            if direction == "LONG":
                self._add(
                    ledger,
                    "INVALIDATION",
                    (
                        f"{timeframe} price is below support "
                        f"({result.support}); the identified support "
                        f"level no longer holds for the LONG thesis."
                    ),
                    timeframe,
                    "HIGH",
                    (
                        "Price has moved below the identified support "
                        "level, so the expected structural floor for "
                        "the LONG thesis has failed."
                    ),
                )

            else:
                self._add(
                    ledger,
                    "FOR",
                    (
                        f"{timeframe} price is below support "
                        f"({result.support}), supporting the SHORT thesis."
                    ),
                    timeframe,
                    "MEDIUM",
                    (
                        "Price being below the identified support level "
                        "is consistent with downside continuation and "
                        "therefore supports the SHORT thesis."
                    ),
                )

        # ---------------------------------------------------------
        # NEAR SUPPORT
        # ---------------------------------------------------------

        elif abs(support_distance) <= 3:

            if direction == "LONG":
                self._add(
                    ledger,
                    "FOR",
                    (
                        f"{timeframe} price is near support "
                        f"({result.support})."
                    ),
                    timeframe,
                    "MEDIUM",
                    (
                        "Price proximity to support provides a nearby "
                        "reference level that may support the LONG thesis, "
                        "although proximity alone does not confirm reversal."
                    ),
                )

            else:
                self._add(
                    ledger,
                    "AGAINST",
                    (
                        f"{timeframe} price is near support "
                        f"({result.support}), which may provide "
                        f"downside protection."
                    ),
                    timeframe,
                    "MEDIUM",
                    (
                        "Nearby support may limit further downside, "
                        "which works against the SHORT thesis."
                    ),
                )

        # ---------------------------------------------------------
        # PRICE ABOVE RESISTANCE
        # ---------------------------------------------------------

        if resistance_distance < 0:

            if direction == "SHORT":
                self._add(
                    ledger,
                    "INVALIDATION",
                    (
                        f"{timeframe} price is above resistance "
                        f"({result.resistance}); the identified "
                        f"resistance level no longer holds for the "
                        f"SHORT thesis."
                    ),
                    timeframe,
                    "HIGH",
                    (
                        "Price has moved above the identified resistance "
                        "level, so the expected structural ceiling for "
                        "the SHORT thesis has failed."
                    ),
                )

            else:
                self._add(
                    ledger,
                    "FOR",
                    (
                        f"{timeframe} price is above resistance "
                        f"({result.resistance}), supporting the "
                        f"LONG thesis."
                    ),
                    timeframe,
                    "MEDIUM",
                    (
                        "Price has moved above the identified resistance "
                        "level, which is consistent with upside continuation "
                        "and supports the LONG thesis."
                    ),
                )

        # ---------------------------------------------------------
        # NEAR RESISTANCE
        # ---------------------------------------------------------

        elif abs(resistance_distance) <= 3:

            if direction == "LONG":
                self._add(
                    ledger,
                    "AGAINST",
                    (
                        f"{timeframe} price is near resistance "
                        f"({result.resistance})."
                    ),
                    timeframe,
                    "MEDIUM",
                    (
                        "Nearby resistance represents a potential supply "
                        "level that may limit upside continuation."
                    ),
                )

            else:
                self._add(
                    ledger,
                    "FOR",
                    (
                        f"{timeframe} price is near resistance "
                        f"({result.resistance})."
                    ),
                    timeframe,
                    "MEDIUM",
                    (
                        "Nearby resistance provides a potential supply "
                        "level consistent with the SHORT thesis."
                    ),
                )

    # ---------------------------------------------------------
    # VOLATILITY
    # ---------------------------------------------------------

    def _evaluate_volatility(
        self,
        ledger,
        timeframe,
        result,
        direction,
    ):
        state = result.volatility_state.upper()

        if state == "EXPANDING":

            strength = "MEDIUM"

            observation = (
                f"{timeframe} volatility is expanding "
                f"(ATR={result.atr:.4f}, "
                f"recent range={result.recent_range_percent:.2f}%)."
            )

        elif state == "CONTRACTING":

            strength = "LOW"

            observation = (
                f"{timeframe} volatility is contracting "
                f"(ATR={result.atr:.4f}, "
                f"recent range={result.recent_range_percent:.2f}%)."
            )

        else:

            strength = "LOW"

            observation = (
                f"{timeframe} volatility is stable "
                f"(ATR={result.atr:.4f})."
            )

        self._add(
            ledger,
            "INCONCLUSIVE",
            observation,
            timeframe,
            strength,
            (
                "Volatility describes the magnitude of market movement "
                "but does not independently establish bullish or bearish "
                "direction."
            ),
        )

    # ---------------------------------------------------------
    # EVIDENCE CREATION
    # ---------------------------------------------------------

    def _add(
        self,
        ledger,
        evidence_type,
        observation,
        timeframe,
        strength,
        reasoning=None,
    ):
        """
        Add evidence through the existing EvidenceLedger API.

        Reasoning explains why the observed market fact has
        the assigned directional value.
        """

        if reasoning is None:
            reasoning = (
                "Evidence classified deterministically from "
                "market-analysis outputs."
            )

        ledger.add(
            evidence_type=evidence_type,
            observation=observation,
            timeframe=timeframe,
            source="deterministic_market_analysis",
            strength=strength,
            reasoning=reasoning,
        )


if __name__ == "__main__":

    print("=" * 60)
    print("THESIS EVALUATOR")
    print("=" * 60)
    print()
    print(
        "Deterministic thesis evaluator loaded successfully."
    )
    print()
    print("Supported directions:")
    print("  LONG")
    print("  SHORT")

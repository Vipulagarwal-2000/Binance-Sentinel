"""
Binance Sentinel
Research report generator.

Converts a completed ResearchPipeline result into a
judge-readable Markdown research report.
"""

from pathlib import Path
from datetime import datetime


class ResearchReportGenerator:
    """
    Generates a human-readable Markdown report from
    a completed Sentinel research pipeline result.
    """

    def generate(self, pipeline_result: dict) -> str:
        session = pipeline_result["session"]
        ledger = pipeline_result["ledger"]
        timeframe_result = pipeline_result["timeframe_result"]
        confidence = pipeline_result["confidence"]
        critic = pipeline_result["critic"]

        lines = []

        # ---------------------------------------------------------
        # HEADER
        # ---------------------------------------------------------

        lines.append("# Binance Sentinel Research Report")
        lines.append("")

        lines.append(f"**Case:** `{session.case_id}`")
        lines.append(f"**Generated:** {datetime.now().isoformat(timespec='seconds')}")
        lines.append(f"**Direction:** {session.direction}")
        lines.append(f"**Time Horizon:** {session.time_horizon}")
        lines.append("")

        # ---------------------------------------------------------
        # THESIS
        # ---------------------------------------------------------

        lines.append("## 1. Research Thesis")
        lines.append("")
        lines.append(session.thesis)
        lines.append("")

        # ---------------------------------------------------------
        # DATA
        # ---------------------------------------------------------

        lines.append("## 2. Market Data")
        lines.append("")

        market_data = session.market_data or {}

        lines.append(
            f"**Symbol:** `{market_data.get('symbol', 'N/A')}`"
        )

        candles = market_data.get("candles", {})

        if candles:
            lines.append("")
            lines.append("| Timeframe | Candles |")
            lines.append("|---|---:|")

            for timeframe, data in candles.items():
                lines.append(
                    f"| {timeframe} | {len(data)} |"
                )

        lines.append("")

        # ---------------------------------------------------------
        # MARKET ANALYSIS
        # ---------------------------------------------------------

        lines.append("## 3. Deterministic Market Analysis")
        lines.append("")

        if session.analysis:
            for timeframe, analysis in session.analysis.items():

                lines.append(f"### {timeframe}")
                lines.append("")

                self._add_analysis_row(
                    lines,
                    "Trend",
                    analysis.get("trend"),
                )

                self._add_analysis_row(
                    lines,
                    "Structure",
                    analysis.get("structure"),
                )

                self._add_analysis_row(
                    lines,
                    "Momentum",
                    analysis.get("momentum"),
                )

                self._add_analysis_row(
                    lines,
                    "RSI",
                    self._format_number(
                        analysis.get("rsi")
                    ),
                )

                self._add_analysis_row(
                    lines,
                    "ROC",
                    self._format_percent(
                        analysis.get("roc_percent")
                    ),
                )

                self._add_analysis_row(
                    lines,
                    "Momentum Change",
                    analysis.get("momentum_change"),
                )

                self._add_analysis_row(
                    lines,
                    "Price / Volume",
                    analysis.get(
                        "price_volume_relationship"
                    ),
                )

                self._add_analysis_row(
                    lines,
                    "Volume Ratio",
                    self._format_ratio(
                        analysis.get("volume_ratio")
                    ),
                )

                self._add_analysis_row(
                    lines,
                    "Support",
                    self._format_number(
                        analysis.get("support")
                    ),
                )

                self._add_analysis_row(
                    lines,
                    "Resistance",
                    self._format_number(
                        analysis.get("resistance")
                    ),
                )

                self._add_analysis_row(
                    lines,
                    "Volatility",
                    analysis.get("volatility_state"),
                )

                lines.append("")

        # ---------------------------------------------------------
        # EVIDENCE LEDGER
        # ---------------------------------------------------------

        lines.append("## 4. Evidence Ledger")
        lines.append("")

        evidence_types = [
            "FOR",
            "AGAINST",
            "INCONCLUSIVE",
            "INVALIDATION",
        ]

        for evidence_type in evidence_types:

            evidence_items = ledger.by_type(
                evidence_type
            )

            lines.append(
                f"### {evidence_type} ({len(evidence_items)})"
            )
            lines.append("")

            if not evidence_items:
                lines.append(
                    "_No evidence classified in this category._"
                )
                lines.append("")
                continue

            for index, evidence in enumerate(
                evidence_items,
                start=1,
            ):
                lines.append(
                    f"**{index}. "
                    f"[{evidence.timeframe}] "
                    f"{evidence.observation}**"
                )
                lines.append("")
                lines.append(
                    f"- Strength: {evidence.strength}"
                )
                lines.append(
                    f"- Source: {evidence.source}"
                )
                lines.append(
                    f"- Reasoning: {evidence.reasoning}"
                )
                lines.append("")

        # ---------------------------------------------------------
        # MULTI-TIMEFRAME
        # ---------------------------------------------------------

        lines.append("## 5. Multi-Timeframe Assessment")
        lines.append("")

        lines.append(
            f"**Direction:** {timeframe_result.direction}"
        )
        lines.append(
            f"**Timeframes:** "
            f"{', '.join(timeframe_result.timeframes)}"
        )
        lines.append(
            f"**Dominant State:** "
            f"{timeframe_result.dominant_state}"
        )
        lines.append(
            f"**Alignment:** "
            f"{timeframe_result.alignment}"
        )
        lines.append("")

        lines.append("| Evidence | Count |")
        lines.append("|---|---:|")
        lines.append(
            f"| FOR | {timeframe_result.total_for} |"
        )
        lines.append(
            f"| AGAINST | {timeframe_result.total_against} |"
        )
        lines.append(
            f"| INCONCLUSIVE | "
            f"{timeframe_result.total_inconclusive} |"
        )
        lines.append(
            f"| INVALIDATION | "
            f"{timeframe_result.total_invalidation} |"
        )
        lines.append("")

        # ---------------------------------------------------------
        # CONFIDENCE
        # ---------------------------------------------------------

        lines.append("## 6. Evidence-Weighted Confidence")
        lines.append("")

        lines.append(
            f"**Confidence:** "
            f"{confidence.confidence:.1f}%"
        )

        lines.append(
            f"**State:** {confidence.state}"
        )

        lines.append(
            f"**Supporting Score:** "
            f"{confidence.supporting_score:.1f}"
        )

        lines.append(
            f"**Contradicting Score:** "
            f"{confidence.contradicting_score:.1f}"
        )

        lines.append(
            f"**Invalidation Score:** "
            f"{confidence.invalidation_score:.1f}"
        )

        lines.append(
            f"**Inconclusive Items:** "
            f"{confidence.inconclusive_count}"
        )

        lines.append("")

        lines.append(
            "> Confidence is an evidence-weighted research score, "
            "not a statistical probability or price prediction."
        )
        lines.append("")

        # ---------------------------------------------------------
        # ADVERSARIAL CRITIC
        # ---------------------------------------------------------

        lines.append("## 7. Adversarial Critic")
        lines.append("")

        lines.append(
            f"**Overall Risk:** {critic.overall_risk}"
        )

        lines.append(
            f"**Challenges Identified:** "
            f"{len(critic.challenges)}"
        )

        lines.append("")

        for index, challenge in enumerate(
            critic.challenges,
            start=1,
        ):
            lines.append(
                f"### Challenge {index}"
            )
            lines.append("")

            if hasattr(challenge, "observation"):
                lines.append(
                    f"**Observation:** "
                    f"{challenge.observation}"
                )

            if hasattr(challenge, "reasoning"):
                lines.append(
                    f"**Reasoning:** "
                    f"{challenge.reasoning}"
                )

            if hasattr(challenge, "severity"):
                lines.append(
                    f"**Severity:** "
                    f"{challenge.severity}"
                )

            lines.append("")

        # ---------------------------------------------------------
        # INVALIDATION CONDITIONS
        # ---------------------------------------------------------

        lines.append("## 8. Thesis Invalidation Conditions")
        lines.append("")

        if session.invalidation_conditions:
            for condition in session.invalidation_conditions:
                lines.append(f"- {condition}")
        else:
            lines.append(
                "_No deterministic invalidation condition "
                "was triggered by the available market data._"
            )

        lines.append("")

        # ---------------------------------------------------------
        # VERDICT
        # ---------------------------------------------------------

        lines.append("## 9. Final Verdict")
        lines.append("")

        lines.append(
            f"# {session.verdict}"
        )
        lines.append("")

        lines.append(
            f"The deterministic research engine classified "
            f"the `{session.direction}` thesis as "
            f"**{session.verdict}**."
        )

        lines.append(
            f"Evidence-weighted confidence was "
            f"**{confidence.confidence:.1f}%**, while the "
            f"adversarial critic assigned an overall risk of "
            f"**{critic.overall_risk}**."
        )

        lines.append("")

        # ---------------------------------------------------------
        # LIMITATIONS
        # ---------------------------------------------------------

        lines.append("## 10. Research Limitations")
        lines.append("")

        lines.append(
            "- Analysis is based on the supplied Binance market data."
        )
        lines.append(
            "- Deterministic analysis does not predict future prices."
        )
        lines.append(
            "- Evidence-weighted confidence is not a probability."
        )
        lines.append(
            "- The system does not execute trades."
        )
        lines.append(
            "- A CAUTION or SUPPORTIVE verdict is not financial advice."
        )

        return "\n".join(lines)

    @staticmethod
    def _add_analysis_row(
        lines,
        label,
        value,
    ):
        if value is not None:
            lines.append(
                f"- **{label}:** {value}"
            )

    @staticmethod
    def _format_number(value):
        if value is None:
            return None

        return f"{value:.6f}"

    @staticmethod
    def _format_percent(value):
        if value is None:
            return None

        return f"{value:.2f}%"

    @staticmethod
    def _format_ratio(value):
        if value is None:
            return None

        return f"{value:.2f}x"


if __name__ == "__main__":
    print("=" * 60)
    print("BINANCE SENTINEL REPORT GENERATOR")
    print("=" * 60)
    print()
    print("Report generator loaded successfully.")
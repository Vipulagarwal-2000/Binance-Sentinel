"""
Binance Sentinel
Result-oriented PDF research report.

Converts a completed ResearchPipeline result into a
compact, judge-readable research brief.
"""

from pathlib import Path
from datetime import datetime
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)


class PDFResearchReport:
    """Generate a result-oriented PDF from a pipeline result."""

    def __init__(self, output_dir="output/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        styles = getSampleStyleSheet()

        self.title = ParagraphStyle(
            "SentinelTitle",
            parent=styles["Title"],
            fontSize=21,
            leading=25,
            alignment=TA_CENTER,
            spaceAfter=6,
        )

        self.subtitle = ParagraphStyle(
            "SentinelSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            spaceAfter=12,
        )

        self.heading = ParagraphStyle(
            "SentinelHeading",
            parent=styles["Heading1"],
            fontSize=14,
            leading=17,
            spaceBefore=5,
            spaceAfter=7,
        )

        self.subheading = ParagraphStyle(
            "SentinelSubheading",
            parent=styles["Heading2"],
            fontSize=10.5,
            leading=13,
            spaceBefore=5,
            spaceAfter=4,
        )

        self.body = ParagraphStyle(
            "SentinelBody",
            parent=styles["BodyText"],
            fontSize=8.8,
            leading=12,
            spaceAfter=5,
        )

        self.small = ParagraphStyle(
            "SentinelSmall",
            parent=self.body,
            fontSize=7.5,
            leading=10,
        )

        self.verdict = ParagraphStyle(
            "SentinelVerdict",
            parent=styles["Title"],
            fontSize=24,
            leading=28,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=4,
        )

        self.card_label = ParagraphStyle(
            "SentinelCardLabel",
            parent=self.small,
            fontSize=7.2,
            leading=9,
            alignment=TA_LEFT,
            spaceAfter=2,
        )

        self.card_value = ParagraphStyle(
            "SentinelCardValue",
            parent=self.body,
            fontSize=10,
            leading=12,
            alignment=TA_LEFT,
            spaceAfter=0,
        )

        self.callout = ParagraphStyle(
            "SentinelCallout",
            parent=self.body,
            fontSize=9.2,
            leading=12.5,
            spaceAfter=2,
        )

        self.condition = ParagraphStyle(
            "SentinelCondition",
            parent=self.body,
            fontSize=8.4,
            leading=11,
            leftIndent=0,
            spaceAfter=3,
        )

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------

    def generate(self, pipeline_result, filename=None):
        """
        Generate a PDF from the dictionary returned by
        ResearchPipeline.run().
        """

        session = pipeline_result["session"]
        ledger = pipeline_result["ledger"]
        timeframe_result = pipeline_result["timeframe_result"]
        confidence = pipeline_result["confidence"]
        critic = pipeline_result["critic"]

        if filename is None:
            filename = (
                f"{session.case_id}_result_brief.pdf"
            )

        output_path = self.output_dir / filename

        story = []

        self._page_one(
            story,
            session,
            ledger,
            timeframe_result,
            confidence,
            critic,
        )

        story.append(PageBreak())

        self._page_two(
            story,
            session,
            ledger,
            timeframe_result,
        )

        story.append(PageBreak())

        self._page_three(
            story,
            session,
            ledger,
            confidence,
            critic,
        )

        document = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=14 * mm,
            leftMargin=14 * mm,
            topMargin=13 * mm,
            bottomMargin=17 * mm,
            title=(
                f"Binance Sentinel - "
                f"{session.case_id}"
            ),
            author="Binance Sentinel",
        )

        document.build(
            story,
            onFirstPage=self._footer,
            onLaterPages=self._footer,
        )

        return output_path

    # ---------------------------------------------------------
    # PAGE 1
    # ---------------------------------------------------------

    def _page_one(
        self,
        story,
        session,
        ledger,
        timeframe_result,
        confidence,
        critic,
    ):
        symbol = (
            session.market_data.get("symbol", "N/A")
            if session.market_data
            else "N/A"
        )

        story.append(
            Paragraph(
                "BINANCE SENTINEL",
                self.title,
            )
        )

        story.append(
            Paragraph(
                "ADVERSARIAL MARKET RESEARCH — RESULT BRIEF",
                self.subtitle,
            )
        )

        story.append(
            Paragraph(
                f"<b>{symbol}</b> &nbsp; | &nbsp; "
                f"<b>{session.direction}</b> &nbsp; | &nbsp; "
                f"Case <b>{session.case_id}</b>",
                self.subtitle,
            )
        )

        story.append(
            Paragraph(
                "FINAL DECISION",
                self.heading,
            )
        )

        verdict_text = self._safe(session.verdict)
        confidence_text = f"{confidence.confidence:.1f}%"
        state_text = self._safe(confidence.state.replace("_", " "))
        risk_text = self._safe(critic.overall_risk)
        evidence_text = str(len(session.evidence))

        metric_rows = [
            [
                Paragraph("<b>VERDICT</b>", self.card_label),
                Paragraph("<b>CONFIDENCE</b>", self.card_label),
                Paragraph("<b>RISK</b>", self.card_label),
            ],
            [
                Paragraph(f"<b>{verdict_text}</b>", self.card_value),
                Paragraph(f"<b>{confidence_text}</b>", self.card_value),
                Paragraph(f"<b>{risk_text}</b>", self.card_value),
            ],
            [
                Paragraph("<b>EVIDENCE STATE</b>", self.card_label),
                Paragraph("<b>MULTI-TIMEFRAME</b>", self.card_label),
                Paragraph("<b>EVIDENCE ITEMS</b>", self.card_label),
            ],
            [
                Paragraph(state_text, self.card_value),
                Paragraph(
                    self._safe(timeframe_result.alignment),
                    self.card_value,
                ),
                Paragraph(evidence_text, self.card_value),
            ],
        ]

        table = Table(
            metric_rows,
            colWidths=[56.5 * mm] * 3,
        )

        table.setStyle(
            TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("BACKGROUND", (0, 2), (-1, 2), colors.whitesmoke),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )

        story.append(table)
        story.append(Spacer(1, 8))

        story.append(
            Paragraph(
                "TRADER THESIS",
                self.subheading,
            )
        )

        story.append(
            Paragraph(
                self._safe(session.thesis),
                self.body,
            )
        )

        story.append(
            Paragraph(
                "KEY FINDING",
                self.subheading,
            )
        )

        story.append(
            Paragraph(
                self._build_key_finding(
                    session,
                    timeframe_result,
                    confidence,
                    critic,
                ),
                self.body,
            )
        )

        story.append(
            Paragraph(
                "EVIDENCE SUMMARY",
                self.subheading,
            )
        )

        counts = [
            [
                "FOR",
                "AGAINST",
                "INCONCLUSIVE",
                "INVALIDATION",
            ],
            [
                str(timeframe_result.total_for),
                str(timeframe_result.total_against),
                str(timeframe_result.total_inconclusive),
                str(timeframe_result.total_invalidation),
            ],
        ]

        count_table = Table(
            counts,
            colWidths=[42.5 * mm] * 4,
        )

        count_table.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.7,
                        colors.black,
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.whitesmoke,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(count_table)

        story.append(Spacer(1, 9))

        story.append(
            Paragraph(
                "RESEARCH METHOD",
                self.subheading,
            )
        )

        story.append(
            Paragraph(
                "Binance market data was processed through deterministic "
                "market analysis, directional Evidence Ledger classification, "
                "multi-timeframe aggregation, evidence-weighted confidence, "
                "and adversarial criticism.",
                self.body,
            )
        )

    # ---------------------------------------------------------
    # PAGE 2
    # ---------------------------------------------------------

    def _page_two(
        self,
        story,
        session,
        ledger,
        timeframe_result,
    ):
        story.append(
            Paragraph(
                "EVIDENCE AND MARKET STRUCTURE",
                self.title,
            )
        )

        story.append(
            Paragraph(
                "MULTI-TIMEFRAME MARKET VIEW",
                self.heading,
            )
        )

        analysis = session.analysis or {}

        rows = [
            [
                "TF",
                "Trend",
                "Structure",
                "Momentum",
                "Price / Volume",
                "Volatility",
            ]
        ]

        for timeframe in timeframe_result.timeframes:
            item = analysis.get(timeframe, {})

            rows.append(
                [
                    timeframe,
                    self._display(
                        item.get("trend")
                    ),
                    self._display(
                        item.get("structure")
                    ),
                    self._display(
                        item.get("momentum")
                    ),
                    self._display(
                        item.get(
                            "price_volume_relationship"
                        )
                    ),
                    self._display(
                        item.get("volatility_state")
                    ),
                ]
            )

        table = Table(
            rows,
            colWidths=[
                14 * mm,
                25 * mm,
                42 * mm,
                25 * mm,
                43 * mm,
                25 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.7,
                        colors.black,
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.whitesmoke,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(table)
        story.append(Spacer(1, 8))

        supporting = ledger.by_type("FOR")
        contradicting = ledger.by_type("AGAINST")

        story.append(
            Paragraph(
                "SUPPORTING EVIDENCE",
                self.subheading,
            )
        )

        if supporting:
            story.append(self._evidence_table(supporting[:4], "FOR"))
        else:
            story.append(
                Paragraph(
                    "No supporting evidence was classified.",
                    self.body,
                )
            )

        story.append(Spacer(1, 5))

        story.append(
            Paragraph(
                "EVIDENCE CONTRADICTING THE THESIS",
                self.subheading,
            )
        )

        if contradicting:
            story.append(self._evidence_table(contradicting[:6], "AGAINST"))
        else:
            story.append(
                Paragraph(
                    "No contradictory evidence was classified.",
                    self.body,
                )
            )

        story.append(Spacer(1, 5))

        story.append(
            Paragraph(
                "MULTI-TIMEFRAME ASSESSMENT",
                self.subheading,
            )
        )

        story.append(
            Paragraph(
                f"Dominant state: "
                f"<b>{timeframe_result.dominant_state}</b>. "
                f"Alignment: "
                f"<b>{timeframe_result.alignment}</b>. "
                f"FOR={timeframe_result.total_for}, "
                f"AGAINST={timeframe_result.total_against}, "
                f"INCONCLUSIVE="
                f"{timeframe_result.total_inconclusive}.",
                self.body,
            )
        )

    # ---------------------------------------------------------
    # PAGE 3
    # ---------------------------------------------------------

    def _page_three(
        self,
        story,
        session,
        ledger,
        confidence,
        critic,
    ):
        story.append(
            Paragraph(
                "ADVERSARIAL REVIEW AND CONCLUSION",
                self.title,
            )
        )

        story.append(
            Paragraph(
                f"OVERALL RISK: <b>{critic.overall_risk}</b> "
                f"&nbsp; | &nbsp; "
                f"CHALLENGES: <b>{len(critic.challenges)}</b>",
                self.subtitle,
            )
        )

        story.append(
            Paragraph(
                "ADVERSARIAL CHALLENGES",
                self.heading,
            )
        )

        for index, challenge in enumerate(
            critic.challenges,
            start=1,
        ):
            observation = self._challenge_value(
                challenge,
                "observation",
                "challenge",
                "description",
                "message",
                "text",
                "issue",
            )

            severity = self._challenge_value(
                challenge,
                "severity",
                "risk",
                "level",
            )

            if not observation:
                observation = (
                    "Adversarial challenge recorded without "
                    "a display description."
                )

            reason = self._challenge_reason(observation)

            challenge_text = (
                f"<b>{index}.</b> "
                f"{self._safe(observation)} "
                f"<i>({self._safe(severity or 'N/A')})</i>"
                f"<br/><font size='7.5'>"
                f"<b>Why it matters:</b> "
                f"{self._safe(reason)}"
                f"</font>"
            )

            story.append(
                Paragraph(
                    challenge_text,
                    self.small,
                )
            )

        story.append(
            Paragraph(
                "WHAT WOULD INVALIDATE THIS THESIS?",
                self.heading,
            )
        )

        invalidation = list(session.invalidation_conditions or [])

        if invalidation:
            # Group repeated swing-high / swing-low conditions into one
            # conceptual condition and show the timeframe levels separately.
            level_rows = []
            primary_direction = session.direction.upper()

            if primary_direction == "SHORT":
                primary = (
                    "A sustained break above the relevant swing-high "
                    "structure would invalidate the SHORT thesis."
                )
                pattern = re.compile(
                    r"^([^:]+): a sustained break above the established "
                    r"swing high \(([^)]+)\)",
                    re.IGNORECASE,
                )
            else:
                primary = (
                    "A sustained break below the relevant swing-low "
                    "structure would invalidate the LONG thesis."
                )
                pattern = re.compile(
                    r"^([^:]+): a sustained break below the established "
                    r"swing low \(([^)]+)\)",
                    re.IGNORECASE,
                )

            remaining = []
            for condition in invalidation:
                match = pattern.search(str(condition))
                if match:
                    level_rows.append([
                        self._safe(match.group(1)),
                        self._safe(match.group(2)),
                    ])
                else:
                    remaining.append(condition)

            story.append(
                Paragraph("<b>PRIMARY CONDITION</b>", self.card_label)
            )
            story.append(Paragraph(self._safe(primary), self.callout))

            if level_rows:
                rows = [
                    [
                        Paragraph("<b>TIMEFRAME</b>", self.small),
                        Paragraph("<b>SWING LEVEL</b>", self.small),
                    ]
                ]
                for timeframe, level in level_rows:
                    rows.append([
                        Paragraph(timeframe, self.small),
                        Paragraph(f"<b>{level}</b>", self.small),
                    ])

                level_table = Table(
                    rows,
                    colWidths=[35 * mm, 45 * mm],
                    hAlign="LEFT",
                )
                level_table.setStyle(
                    TableStyle([
                        ("BOX", (0, 0), (-1, -1), 0.6, colors.black),
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ])
                )
                story.append(
                    Paragraph("<b>TIMEFRAME LEVELS</b>", self.card_label)
                )
                story.append(level_table)

            for condition in remaining:
                story.append(
                    Paragraph(
                        f"• {self._safe(condition)}",
                        self.condition,
                    )
                )
        else:
            story.append(
                Paragraph(
                    "<b>NO RELIABLE INVALIDATION LEVEL IDENTIFIED</b>",
                    self.callout,
                )
            )
            story.append(
                Paragraph(
                    "The available market data does not establish a "
                    "sufficiently defensible deterministic threshold.",
                    self.small,
                )
            )

        story.append(
            Paragraph(
                "CONFIDENCE BREAKDOWN",
                self.heading,
            )
        )

        confidence_rows = [
            [
                "Supporting score",
                f"{confidence.supporting_score:.1f}",
            ],
            [
                "Contradicting score",
                f"{confidence.contradicting_score:.1f}",
            ],
            [
                "Invalidation score",
                f"{confidence.invalidation_score:.1f}",
            ],
            [
                "Inconclusive items",
                str(confidence.inconclusive_count),
            ],
            [
                "Final confidence",
                f"{confidence.confidence:.1f}%",
            ],
        ]

        table = Table(
            confidence_rows,
            colWidths=[70 * mm, 45 * mm],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.7,
                        colors.black,
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.whitesmoke,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(table)
        story.append(Spacer(1, 7))

        story.append(
            Paragraph(
                "<b>Important:</b> Confidence is an "
                "evidence-weighted research score, not a "
                "statistical probability or price prediction.",
                self.small,
            )
        )

        story.append(
            Paragraph(
                "SENTINEL CONCLUSION",
                self.heading,
            )
        )

        story.append(
            Paragraph(
                self._build_conclusion(
                    session,
                    confidence,
                    critic,
                ),
                self.body,
            )
        )

        story.append(
            Spacer(1, 7)
        )

        story.append(
            Paragraph(
                "METHOD LIMITATIONS",
                self.subheading,
            )
        )

        limitations = [
            "Analysis uses the supplied Binance market data.",
            "Deterministic analysis does not predict future prices.",
            "Confidence is not a probability.",
            "Sentinel does not execute trades.",
        ]

        for item in limitations:
            story.append(
                Paragraph(
                    f"• {item}",
                    self.small,
                )
            )

    # ---------------------------------------------------------
    # TEXT HELPERS
    # ---------------------------------------------------------

    @staticmethod
    def _safe(value):
        if value is None:
            return "N/A"

        text = str(value)

        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    @staticmethod
    def _display(value):
        if value is None:
            return "N/A"

        return str(value).replace("_", " ")

    def _evidence_table(self, evidence_items, evidence_type):
        """Render compact evidence rows without creating a page per item."""
        rows = [[
            Paragraph("<b>TF</b>", self.small),
            Paragraph("<b>OBSERVATION</b>", self.small),
            Paragraph("<b>VALUE</b>", self.small),
            Paragraph("<b>REASON</b>", self.small),
        ]]

        for evidence in evidence_items:
            timeframe = self._value_from_object(
                evidence, "timeframe", "tf"
            ) or "N/A"
            observation = self._value_from_object(
                evidence, "observation", "description", "message"
            ) or "N/A"
            strength = self._value_from_object(
                evidence, "strength", "confidence"
            ) or "N/A"
            reasoning = self._value_from_object(
                evidence, "reasoning", "rationale", "why", "impact"
            )

            if not reasoning:
                reasoning = self._evidence_reason(
                    observation,
                    evidence_type,
                )

            rows.append([
                Paragraph(self._safe(timeframe), self.small),
                Paragraph(self._safe(observation), self.small),
                Paragraph(
                    f"<b>{self._safe(evidence_type)} — "
                    f"{self._safe(str(strength).upper())}</b>",
                    self.small,
                ),
                Paragraph(self._safe(reasoning), self.small),
            ])

        table = Table(
            rows,
            colWidths=[13 * mm, 57 * mm, 31 * mm, 69 * mm],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.black),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

        return table

    @staticmethod
    def _value_from_object(obj, *names):
        if obj is None:
            return None

        if isinstance(obj, dict):
            for name in names:
                value = obj.get(name)
                if value is not None and str(value).strip():
                    return value
            return None

        for name in names:
            value = getattr(obj, name, None)
            if value is not None and str(value).strip():
                return value

        return None

    @classmethod
    def _challenge_value(cls, challenge, *names):
        value = cls._value_from_object(challenge, *names)
        if value is not None:
            return value
        if isinstance(challenge, str):
            return challenge
        return None

    @staticmethod
    def _evidence_reason(observation, evidence_type):
        text = str(observation).lower()

        if evidence_type == "FOR":
            if "bullish" in text:
                return "Bullish directional structure supports the LONG thesis."
            if "higher_low" in text or "higher lows" in text:
                return "Higher lows indicate constructive structure for the thesis."
            if "decelerating" in text:
                return "Momentum is weakening less aggressively, which is directionally supportive."
            return "This observation provides directional support for the thesis."

        if "bearish" in text:
            return "Bearish direction conflicts with the LONG thesis."
        if "lower_high" in text or "lower highs" in text or "lower_low" in text:
            return "Lower highs/lows indicate adverse market structure for the thesis."
        if "negative" in text:
            return "Negative momentum weakens confirmation of the thesis."
        return "This observation provides contradictory evidence against the thesis."

    @staticmethod
    def _challenge_reason(observation):
        text = str(observation).lower()

        if "timeframe" in text or "aligned" in text or "diverg" in text:
            return (
                "Conflicting timeframe signals reduce confirmation and make "
                "the directional thesis less robust."
            )
        if "inconclusive" in text or "confirmation" in text:
            return (
                "Unresolved evidence means the thesis lacks enough independent "
                "confirmation to be treated as established."
            )
        if "momentum" in text:
            return (
                "Momentum is moving against the thesis, weakening the case "
                "for immediate continuation."
            )
        if "trend" in text or "structure" in text:
            return (
                "The observed market direction or structure conflicts with "
                "the thesis and raises the risk of continuation against it."
            )

        return (
            "This challenge identifies evidence or uncertainty that could "
            "reduce confidence in the thesis."
        )

    def _build_key_finding(
        self,
        session,
        timeframe_result,
        confidence,
        critic,
    ):
        direction = session.direction.upper()

        return (
            f"The <b>{direction}</b> thesis is currently "
            f"assessed as <b>{session.verdict}</b>. "
            f"Evidence-weighted confidence is "
            f"<b>{confidence.confidence:.1f}%</b>, while "
            f"the adversarial critic assigns "
            f"<b>{critic.overall_risk}</b> risk. "
            f"Multi-timeframe alignment is "
            f"<b>{timeframe_result.alignment}</b>, with "
            f"{timeframe_result.total_against} contradictory "
            f"evidence items versus "
            f"{timeframe_result.total_for} supporting items."
        )

    def _build_conclusion(
        self,
        session,
        confidence,
        critic,
    ):
        direction = session.direction.upper()
        verdict = session.verdict.upper()

        return (
            f"The evidence does not justify an unconditional "
            f"<b>{direction}</b> decision. Sentinel assigns "
            f"<b>{verdict}</b> with <b>{confidence.confidence:.1f}%</b> "
            f"evidence-weighted confidence. "
            f"{len(critic.challenges)} adversarial challenges were "
            f"identified, with <b>{critic.overall_risk}</b> overall risk."
        )

    # ---------------------------------------------------------
    # PAGE FOOTER
    # ---------------------------------------------------------

    @staticmethod
    def _footer(canvas, document):
        canvas.saveState()

        canvas.setFont(
            "Helvetica",
            7,
        )

        canvas.drawCentredString(
            A4[0] / 2,
            9 * mm,
            (
                "Binance Sentinel — Result Brief — "
                f"Page {document.page}"
            ),
        )

        canvas.restoreState()


if __name__ == "__main__":
    print("=" * 60)
    print("BINANCE SENTINEL PDF REPORT")
    print("=" * 60)
    print()
    print("PDF report generator loaded successfully.")
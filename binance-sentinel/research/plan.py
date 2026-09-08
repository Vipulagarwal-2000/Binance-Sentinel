from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ResearchPlan:
    """
    Defines what Sentinel needs to investigate a research thesis.

    The plan is deliberately pair-agnostic. The symbol comes from the
    ResearchCase and is supplied when the plan is used to build a request.
    """

    timeframes: List[str] = field(
        default_factory=lambda: ["1D", "4H", "1H"]
    )

    # Historical candle depth required for each timeframe.
    history_depth: Dict[str, int] = field(
        default_factory=lambda: {
            "1D": 60,
            "4H": 180,
            "1H": 720,
        }
    )

    market_data: List[str] = field(
        default_factory=lambda: [
            "price",
            "24h_statistics",
            "candles",
            "volume",
            "order_book",
        ]
    )

    # High-value analytical categories.
    analysis: List[str] = field(
        default_factory=lambda: [
            "trend_structure",
            "momentum",
            "volume_price",
            "support_resistance",
            "volatility",
        ]
    )

    # Questions Sentinel should answer while testing the thesis.
    reasoning: List[str] = field(
        default_factory=lambda: [
            "bull_case",
            "bear_case",
            "supporting_evidence",
            "contradictory_evidence",
            "inconclusive_evidence",
            "invalidation",
            "multi_timeframe_confirmation",
            "adversarial_challenge",
            "thesis_confidence",
        ]
    )

    material_categories: List[str] = field(
        default_factory=lambda: [
            "previous_analysis",
            "market_research",
            "technical_analysis",
            "project_information",
            "tokenomics",
            "news_events",
            "user_notes",
        ]
    )

    def add_timeframe(self, timeframe: str, history_depth: int = 60):
        timeframe = timeframe.upper()

        if timeframe not in self.timeframes:
            self.timeframes.append(timeframe)

        self.history_depth[timeframe] = history_depth

    def remove_timeframe(self, timeframe: str):
        timeframe = timeframe.upper()

        if timeframe in self.timeframes:
            self.timeframes.remove(timeframe)

        self.history_depth.pop(timeframe, None)

    def set_history_depth(self, timeframe: str, candles: int):
        timeframe = timeframe.upper()

        if timeframe not in self.timeframes:
            raise ValueError(
                f"Timeframe '{timeframe}' is not in the research plan."
            )

        if candles <= 0:
            raise ValueError("History depth must be greater than zero.")

        self.history_depth[timeframe] = candles

    def add_market_data(self, data_type: str):
        if data_type not in self.market_data:
            self.market_data.append(data_type)

    def remove_market_data(self, data_type: str):
        if data_type in self.market_data:
            self.market_data.remove(data_type)

    def add_analysis(self, analysis_type: str):
        if analysis_type not in self.analysis:
            self.analysis.append(analysis_type)

    def remove_analysis(self, analysis_type: str):
        if analysis_type in self.analysis:
            self.analysis.remove(analysis_type)

    def add_reasoning(self, reasoning_type: str):
        if reasoning_type not in self.reasoning:
            self.reasoning.append(reasoning_type)

    def remove_reasoning(self, reasoning_type: str):
        if reasoning_type in self.reasoning:
            self.reasoning.remove(reasoning_type)

    def validate(self):
        """
        Validate that the plan is internally consistent before research.
        """

        if not self.timeframes:
            raise ValueError("Research plan requires at least one timeframe.")

        for timeframe in self.timeframes:
            if timeframe not in self.history_depth:
                raise ValueError(
                    f"Missing history depth for timeframe '{timeframe}'."
                )

            if self.history_depth[timeframe] <= 0:
                raise ValueError(
                    f"Invalid history depth for timeframe '{timeframe}'."
                )

        if not self.market_data:
            raise ValueError("Research plan requires market data.")

        if not self.analysis:
            raise ValueError("Research plan requires analysis categories.")

        if not self.reasoning:
            raise ValueError("Research plan requires reasoning objectives.")

        return True

    def to_dict(self):
        self.validate()

        return {
            "timeframes": self.timeframes,
            "history_depth": self.history_depth,
            "market_data": self.market_data,
            "analysis": self.analysis,
            "reasoning": self.reasoning,
            "material_categories": self.material_categories,
        }

    @classmethod
    def from_dict(cls, data):
        plan = cls(
            timeframes=data.get(
                "timeframes",
                ["1D", "4H", "1H"],
            ),
            history_depth=data.get(
                "history_depth",
                {
                    "1D": 60,
                    "4H": 180,
                    "1H": 720,
                },
            ),
            market_data=data.get(
                "market_data",
                [
                    "price",
                    "24h_statistics",
                    "candles",
                    "volume",
                    "order_book",
                ],
            ),
            analysis=data.get(
                "analysis",
                [
                    "trend_structure",
                    "momentum",
                    "volume_price",
                    "support_resistance",
                    "volatility",
                ],
            ),
            reasoning=data.get(
                "reasoning",
                [
                    "bull_case",
                    "bear_case",
                    "supporting_evidence",
                    "contradictory_evidence",
                    "inconclusive_evidence",
                    "invalidation",
                    "multi_timeframe_confirmation",
                    "adversarial_challenge",
                    "thesis_confidence",
                ],
            ),
            material_categories=data.get(
                "material_categories",
                [
                    "previous_analysis",
                    "market_research",
                    "technical_analysis",
                    "project_information",
                    "tokenomics",
                    "news_events",
                    "user_notes",
                ],
            ),
        )

        plan.validate()
        return plan
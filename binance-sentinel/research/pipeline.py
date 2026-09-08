"""
Binance Sentinel
Research pipeline orchestrator.

Coordinates the deterministic research components
into one complete research run.
"""

from dataclasses import asdict

from research.data_quality import DataQualityChecker
from analysis.confidence import ConfidenceEngine
from analysis.critic import AdversarialCritic
from analysis.market_analysis import MarketAnalyzer
from analysis.multi_timeframe import MultiTimeframeAggregator
from analysis.thesis_evaluator import ThesisEvaluator
from binance.market_data import MarketSnapshot
from research.case_manager import CaseManager
from research.plan_manager import PlanManager
from research.session import SessionManager


class ResearchPipeline:
    """Runs a complete Sentinel research session."""

    def __init__(self):
        self.case_manager = CaseManager()
        self.plan_manager = PlanManager()
        self.session_manager = SessionManager()

        self.market_analyzer = MarketAnalyzer()
        self.data_quality_checker = DataQualityChecker()
        self.thesis_evaluator = ThesisEvaluator()
        self.timeframe_aggregator = MultiTimeframeAggregator()
        self.confidence_engine = ConfidenceEngine()
        self.critic = AdversarialCritic()

    def run(
        self,
        case_id: str,
        market_snapshot: MarketSnapshot,
    ):
        # 1. Load research case
        case = self.case_manager.load_case(case_id)

        # 2. Load current research plan
        plan = self.plan_manager.load_plan(case_id)

        # 3. Create historical session
        session = self.session_manager.create_session(
            case_id=case.case_id,
            thesis=case.thesis,
            direction=case.direction,
            time_horizon=case.time_horizon,
            research_plan=plan.to_dict(),
        )

        # 4. Save raw market data
        session.market_data = self._serialize_snapshot(market_snapshot)

        # 4.5 Data quality gate
        quality_result = self.data_quality_checker.check(
            snapshot=market_snapshot,
            plan=plan,
        )

        if not quality_result.passed:
            raise ValueError(quality_result.summary())

        # 5. Run deterministic market analysis
        analysis_results = self.market_analyzer.analyze_snapshot(
            market_snapshot
        )

        session.analysis = {
            timeframe: asdict(result)
            for timeframe, result in analysis_results.items()
        }

        # 6. Convert analysis into evidence
        ledger = self.thesis_evaluator.evaluate(
            analysis_results,
            case.direction,
        )

        # 7. Save evidence
        self.session_manager.save_evidence(
            session,
            ledger,
        )

        # 8. Multi-timeframe aggregation
        timeframe_result = self.timeframe_aggregator.aggregate(
            ledger,
            case.direction,
        )

        # 9. Calculate confidence
        confidence_result = self.confidence_engine.calculate(
            ledger,
            timeframe_result,
        )

        session.confidence = confidence_result.confidence

        # 10. Adversarial criticism
        critic_result = self.critic.evaluate(
            ledger,
            timeframe_result,
            case.direction,
        )

        session.challenges = [
            asdict(challenge)
            for challenge in critic_result.challenges
        ]

        # 11. Save current invalidation status AND future conditions
        #
        # INVALIDATION evidence means the thesis is already invalidated.
        # invalidation_conditions means what would invalidate it in the
        # future. They are deliberately kept conceptually separate.
        session.invalidation_conditions = (
            self._generate_invalidation_conditions(
                analysis_results,
                case.direction,
                ledger,
            )
        )

        # 12. Temporary verdict
        session.verdict = self._generate_verdict(
            confidence_result.confidence,
            critic_result.overall_risk,
        )

        # 13. Save complete session
        self.session_manager.save_session(session)

        return {
            "session": session,
            "ledger": ledger,
            "timeframe_result": timeframe_result,
            "confidence": confidence_result,
            "critic": critic_result,
        }

    @staticmethod
    def _generate_invalidation_conditions(
        analysis_results,
        direction: str,
        ledger,
    ) -> list[str]:
        """
        Derive future thesis-invalidation conditions from existing
        deterministic analysis.

        This method does not invent price levels. A numeric condition is
        only produced when the existing analysis contains a defensible
        swing level.

        The INVALIDATION entries already present in the ledger remain
        evidence that the thesis is currently invalidated; this method
        describes future conditions that would invalidate the thesis.
        """
        conditions = []
        direction = direction.upper()

        def add(condition: str):
            if condition and condition not in conditions:
                conditions.append(condition)

        # 1. Structure-based invalidation.
        # A LONG thesis is invalidated by loss of its established swing low.
        # A SHORT thesis is invalidated by a break above its established
        # swing high.
        for timeframe, result in analysis_results.items():
            swing_low = getattr(result, "swing_low", None)
            swing_high = getattr(result, "swing_high", None)

            if direction == "LONG" and swing_low is not None:
                add(
                    f"{timeframe}: a sustained break below the established "
                    f"swing low ({swing_low:g}) would invalidate the LONG thesis."
                )

            elif direction == "SHORT" and swing_high is not None:
                add(
                    f"{timeframe}: a sustained break above the established "
                    f"swing high ({swing_high:g}) would invalidate the SHORT thesis."
                )

        # 2. Structural deterioration.
        # These are qualitative conditions, so no unsupported price target
        # is introduced.
        bearish_timeframes = []
        bullish_timeframes = []

        for timeframe, result in analysis_results.items():
            structure = str(
                getattr(result, "structure", "")
            ).upper()

            if "BEAR" in structure:
                bearish_timeframes.append(timeframe)

            if "BULL" in structure:
                bullish_timeframes.append(timeframe)

        if direction == "LONG" and bearish_timeframes:
            frames = ", ".join(bearish_timeframes)
            add(
                f"Continued bearish market structure on {frames}, with "
                "further lower highs/lower lows, would invalidate the LONG thesis."
            )

        if direction == "SHORT" and bullish_timeframes:
            frames = ", ".join(bullish_timeframes)
            add(
                f"Continued bullish market structure on {frames}, with "
                "further higher highs/higher lows, would invalidate the SHORT thesis."
            )

        # 3. If no defensible condition was found, explicitly say so rather
        # than inventing a threshold.
        if not conditions:
            add(
                "No sufficiently reliable deterministic invalidation level "
                "was established by the available market data."
            )

        return conditions

    @staticmethod
    def _serialize_snapshot(
        snapshot: MarketSnapshot,
    ) -> dict:
        data = {
            "symbol": snapshot.symbol,
            "ticker": None,
            "candles": {},
            "order_book": None,
        }

        if snapshot.ticker is not None:
            data["ticker"] = asdict(snapshot.ticker)

        for timeframe, candles in snapshot.candles.items():
            data["candles"][timeframe] = [
                asdict(candle)
                for candle in candles
            ]

        if snapshot.order_book is not None:
            data["order_book"] = asdict(snapshot.order_book)

        return data

    @staticmethod
    def _generate_verdict(
        confidence: float,
        critic_risk: str,
    ) -> str:
        if confidence >= 75:
            return "SUPPORTIVE"

        if confidence >= 25:
            return "CAUTION"

        return "CONTRADICTED"

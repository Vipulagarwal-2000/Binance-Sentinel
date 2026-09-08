"""
Binance Sentinel
Research pipeline integration test.
"""

from analysis.market_analysis import MarketAnalyzer
from binance.market_data import (
    Candle,
    MarketSnapshot,
    Ticker,
    OrderBook,
    OrderBookLevel,
)
from research.case_manager import CaseManager
from research.pipeline import ResearchPipeline
from research.plan_manager import PlanManager


def create_test_candles():

    prices = [
        100,
        101,
        102,
        103,
        104,
        106,
        107,
        108,
    ]

    volumes = [
        1000,
        1050,
        1100,
        1200,
        1300,
        1600,
        1800,
        2000,
    ]

    candles = []

    for index, price in enumerate(prices):

        candles.append(
            Candle(
                open_time=index,
                open=price - 1,
                high=price + 1,
                low=price - 2,
                close=price,
                volume=volumes[index],
                close_time=index,
            )
        )

    return candles


def main():

    print("=" * 50)
    print("       RESEARCH PIPELINE TEST")
    print("=" * 50)
    print()

    # --------------------------------------------------
    # 1. Create case
    # --------------------------------------------------

    case_manager = CaseManager()

    case = case_manager.create_case(
        name="Pipeline Test",
        symbol="PIPEUSDT",
        direction="LONG",
        time_horizon="15 days",
        thesis=(
            "PIPEUSDT may continue higher if "
            "trend and volume remain supportive."
        ),
    )

    print("[1] Case created:")
    print(f"    {case.case_id}")
    print()

    # --------------------------------------------------
    # 2. Create research plan
    # --------------------------------------------------

    plan_manager = PlanManager()

    plan = plan_manager.load_plan(
        case.case_id
    )

    print("[2] Research plan loaded.")
    print()

    # --------------------------------------------------
    # 3. Create market snapshot
    # --------------------------------------------------

    candles = create_test_candles()

    snapshot = MarketSnapshot(
        symbol=case.symbol,

        ticker=Ticker(
            symbol=case.symbol,
            last_price=108.50,
            price_change=8.50,
            price_change_percent=8.50,
            high_price=112.00,
            low_price=98.00,
            volume=1250000,
            quote_volume=135625000,
        ),

        candles={
            "1d": [
                Candle(
                    open_time=i,
                    open=100 + i * 0.1,
                    high=105 + i * 0.1,
                    low=95 + i * 0.1,
                    close=102 + i * 0.1,
                    volume=1000 + i * 10,
                    close_time=i + 1,
                )
                for i in range(60)
            ],

            "4h": [
                Candle(
                    open_time=i,
                    open=100 + i * 0.05,
                    high=105 + i * 0.05,
                    low=95 + i * 0.05,
                    close=102 + i * 0.05,
                    volume=1000 + i * 10,
                    close_time=i + 1,
                )
                for i in range(180)
            ],

            "1h": [
                Candle(
                    open_time=i,
                    open=100 + i * 0.02,
                    high=105 + i * 0.02,
                    low=95 + i * 0.02,
                    close=102 + i * 0.02,
                    volume=1000 + i * 10,
                    close_time=i + 1,
                )
                for i in range(720)
            ],
        },

        order_book=OrderBook(
            bids=[
                OrderBookLevel(
                    price=108.40,
                    quantity=100,
                ),
                OrderBookLevel(
                    price=108.30,
                    quantity=150,
                ),
            ],
            asks=[
                OrderBookLevel(
                    price=108.60,
                    quantity=120,
                ),
                OrderBookLevel(
                    price=108.70,
                    quantity=180,
                ),
            ],
            timestamp=4000,
        ),
    )

    print("[3] Test market snapshot created.")
    print()

    # --------------------------------------------------
    # 4. Run complete pipeline
    # --------------------------------------------------

    pipeline = ResearchPipeline()

    result = pipeline.run(
        case.case_id,
        snapshot,
    )

    print("[4] Pipeline completed.")
    print()

    # --------------------------------------------------
    # 5. Display results
    # --------------------------------------------------

    print("RESULT")
    print("-" * 50)

    print(
        f"Confidence: "
        f"{result['confidence'].confidence}%"
    )

    print(
        f"Confidence state: "
        f"{result['confidence'].state}"
    )

    print(
        f"Verdict: "
        f"{result['session'].verdict}"
    )

    print(
        f"Critic risk: "
        f"{result['critic'].overall_risk}"
    )

    print(
        f"Evidence: "
        f"{result['ledger'].summary()}"
    )

    print(
        f"Challenges: "
        f"{len(result['critic'].challenges)}"
    )

    print()

    # --------------------------------------------------
    # 6. Verify persistence
    # --------------------------------------------------

    session_manager = pipeline.session_manager

    loaded_session = (
        session_manager.load_session(
            case.case_id,
            result["session"].session_id,
        )
    )

    assert loaded_session.confidence is not None

    assert loaded_session.verdict is not None

    assert len(
        loaded_session.evidence
    ) > 0

    assert len(
        loaded_session.analysis
    ) > 0

    print(
        "[5] Session persistence verified."
    )

    print()
    print("=" * 50)
    print("RESEARCH PIPELINE TEST PASSED")
    print("=" * 50)


if __name__ == "__main__":
    main()
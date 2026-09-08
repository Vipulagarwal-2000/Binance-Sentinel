from binance.market_data import Candle, MarketSnapshot
from research.data_quality import DataQualityChecker
from research.plan import ResearchPlan


def make_candle():
    return Candle(
        open_time=0,
        open=100.0,
        high=105.0,
        low=95.0,
        close=102.0,
        volume=1000.0,
        close_time=60_000,
        quote_volume=100_000.0,
        trade_count=100,
        taker_buy_volume=500.0,
    )


def make_snapshot(symbol, counts):
    candles = {}

    for timeframe, count in counts.items():
        candles[timeframe.lower()] = [
            make_candle()
            for _ in range(count)
        ]

    return MarketSnapshot(
        symbol=symbol,
        candles=candles,
        raw_data={
            "price": 102.0,
            "24h_statistics": {
                "price_change_percent": 1.0,
            },
            "order_book": {
                "bids": [[101.0, 100.0]],
                "asks": [[103.0, 100.0]],
            },
        },
    )


def test_complete_dataset():
    plan = ResearchPlan()

    snapshot = make_snapshot(
        "BTCUSDT",
        {
            "1D": 60,
            "4H": 180,
            "1H": 720,
        },
    )

    result = DataQualityChecker().check(
        snapshot=snapshot,
        plan=plan,
    )

    assert result.passed is True
    print("PASS: complete dataset accepted")


def test_insufficient_history():
    plan = ResearchPlan()

    snapshot = make_snapshot(
        "EDENUSDT",
        {
            "1D": 31,
            "4H": 180,
            "1H": 720,
        },
    )

    result = DataQualityChecker().check(
        snapshot=snapshot,
        plan=plan,
    )

    assert result.passed is False
    assert "1d" in result.insufficient_history

    print("PASS: insufficient history rejected")
    print(result.summary())


def test_missing_timeframe():
    plan = ResearchPlan()

    snapshot = make_snapshot(
        "ETHUSDT",
        {
            "1D": 60,
            "4H": 180,
        },
    )

    result = DataQualityChecker().check(
        snapshot=snapshot,
        plan=plan,
    )

    assert result.passed is False
    assert "1h" in result.missing_timeframes

    print("PASS: missing timeframe rejected")


if __name__ == "__main__":
    test_complete_dataset()
    test_insufficient_history()
    test_missing_timeframe()

    print()
    print("DATA QUALITY TEST PASSED")
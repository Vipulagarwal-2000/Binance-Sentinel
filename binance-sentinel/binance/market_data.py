"""
Binance Sentinel
Market data interface.

This module defines the market-data structure Sentinel's
analysis engine will consume.

The actual Binance MCP connection will be added later.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Candle:
    """
    One OHLCV candlestick.
    """

    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int

    quote_volume: float | None = None
    trade_count: int | None = None
    taker_buy_volume: float | None = None


@dataclass
class OrderBookLevel:
    """
    One order-book price level.
    """

    price: float
    quantity: float


@dataclass
class OrderBook:
    """
    Current order-book snapshot.
    """

    bids: list[OrderBookLevel] = field(
        default_factory=list
    )

    asks: list[OrderBookLevel] = field(
        default_factory=list
    )

    timestamp: int | None = None


@dataclass
class Ticker:
    """
    Current market ticker.
    """

    symbol: str

    last_price: float

    price_change: float | None = None
    price_change_percent: float | None = None

    high_price: float | None = None
    low_price: float | None = None

    volume: float | None = None
    quote_volume: float | None = None


@dataclass
class MarketSnapshot:
    """
    Complete market-data package used by one research session.
    """

    symbol: str

    ticker: Ticker | None = None

    candles: dict[str, list[Candle]] = field(
        default_factory=dict
    )

    order_book: OrderBook | None = None

    raw_data: dict[str, Any] = field(
        default_factory=dict
    )



def candle_from_binance(data: list | dict) -> Candle:
    """
    Convert a Binance kline into a Candle object.

    Supports both:

    1. Binance array-style klines
    2. Object-style candles returned by the MCP agent
    """

    if isinstance(data, dict):
        required_fields = [
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_volume",
            "trade_count",
            "taker_buy_volume",
        ]

        missing = [
            field
            for field in required_fields
            if field not in data
        ]

        if missing:
            raise ValueError(
                "Candle is missing required fields: "
                + ", ".join(missing)
            )

        return Candle(
            open_time=int(data["open_time"]),
            open=float(data["open"]),
            high=float(data["high"]),
            low=float(data["low"]),
            close=float(data["close"]),
            volume=float(data["volume"]),
            close_time=int(data["close_time"]),
            quote_volume=float(data["quote_volume"]),
            trade_count=int(data["trade_count"]),
            taker_buy_volume=float(
                data["taker_buy_volume"]
            ),
        )

    if isinstance(data, (list, tuple)):
        if len(data) < 10:
            raise ValueError(
                "Binance candle array must contain at least "
                "10 fields."
            )

        return Candle(
            open_time=int(data[0]),
            open=float(data[1]),
            high=float(data[2]),
            low=float(data[3]),
            close=float(data[4]),
            volume=float(data[5]),
            close_time=int(data[6]),
            quote_volume=float(data[7]),
            trade_count=int(data[8]),
            taker_buy_volume=float(data[9]),
        )

    raise TypeError(
        "Unsupported Binance candle format: "
        f"{type(data).__name__}"
    )


def candles_from_binance(
    data: list[list | dict],
) -> list[Candle]:
    """
    Convert multiple Binance/MCP candles.
    """

    return [
        candle_from_binance(candle)
        for candle in data
    ]


def order_book_from_binance(data: dict) -> OrderBook:
    bids = [
        OrderBookLevel(
            price=float(level[0]),
            quantity=float(level[1]),
        )
        for level in data.get("bids", [])
    ]

    asks = [
        OrderBookLevel(
            price=float(level[0]),
            quantity=float(level[1]),
        )
        for level in data.get("asks", [])
    ]

    timestamp = data.get("timestamp", data.get("T"))

    return OrderBook(
        bids=bids,
        asks=asks,
        timestamp=int(timestamp) if timestamp is not None else None,
    )


############################# test


if __name__ == "__main__":
    print("=" * 50)
    print("       BINANCE MARKET DATA TEST")
    print("=" * 50)

    sample_candle = [
        1757000000000,
        "0.1200",
        "0.1250",
        "0.1180",
        "0.1230",
        "1500000",
        1757003599999,
        "183000.00",
        12500,
        "760000",
        "92800.00",
        "0",
    ]

    candle = candle_from_binance(
        sample_candle
    )

    print()
    print("[1] Candle conversion:")
    print(f"    Open:   {candle.open}")
    print(f"    High:   {candle.high}")
    print(f"    Low:    {candle.low}")
    print(f"    Close:  {candle.close}")
    print(f"    Volume: {candle.volume}")

    sample_order_book = {
        "bids": [
            ["0.1229", "10000"],
            ["0.1228", "25000"],
        ],
        "asks": [
            ["0.1231", "12000"],
            ["0.1232", "18000"],
        ],
        "T": 1757003600000,
    }

    order_book = order_book_from_binance(
        sample_order_book
    )

    print()
    print("[2] Order book conversion:")
    print(
        f"    Best bid: "
        f"{order_book.bids[0].price}"
    )
    print(
        f"    Best ask: "
        f"{order_book.asks[0].price}"
    )

    print()
    print("=" * 50)
    print("MARKET DATA TEST PASSED")
    print("=" * 50)
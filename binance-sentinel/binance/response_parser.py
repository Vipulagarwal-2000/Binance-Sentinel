"""
Binance Sentinel
Binance MCP response parser.

Converts machine-readable Binance market-data responses
into Sentinel's internal MarketSnapshot structure.

This module does not connect to Binance.
It only parses retrieved data.
"""

from binance.market_data import (
    MarketSnapshot,
    Ticker,
    candles_from_binance,
    order_book_from_binance,
)


class BinanceResponseParser:
    """
    Convert MCP market-data responses into MarketSnapshot.
    """

    def parse(
        self,
        data: dict,
        symbol: str,
    ) -> MarketSnapshot:

        symbol = symbol.upper()

        snapshot = MarketSnapshot(
            symbol=symbol,
            raw_data=data,
        )

        # Sentinel expects a normalized Ticker object.
        #
        # Support both:
        # 1. Real MCP format: "price" + "24h_statistics"
        # 2. Legacy/test format: "ticker"

        ticker_data = {}

        if isinstance(data.get("ticker"), dict):
            ticker_data.update(data["ticker"])

        if isinstance(data.get("price"), dict):
            ticker_data.update(data["price"])

        if isinstance(data.get("24h_statistics"), dict):
            ticker_data.update(data["24h_statistics"])

        if ticker_data:
            snapshot.ticker = self._parse_ticker(
                ticker_data,
                symbol,
            )

        candles_data = data.get("candles", {})

        for timeframe, candles in candles_data.items():
            snapshot.candles[timeframe] = (
                candles_from_binance(candles)
            )

        if "order_book" in data:
            snapshot.order_book = (
                order_book_from_binance(
                    data["order_book"]
                )
            )

        return snapshot

    @staticmethod
    def _parse_ticker(
        data: dict,
        symbol: str,
    ) -> Ticker:

        def get_value(*keys):
            for key in keys:
                if data.get(key) is not None:
                    return data[key]
            return None

        last_price = get_value(
            "last_price",
            "lastPrice",
        )

        if last_price is None:
            raise ValueError(
                "Ticker data does not contain a last price."
            )

        price_change = get_value(
            "price_change",
            "priceChange",
        )

        price_change_percent = get_value(
            "price_change_percent",
            "priceChangePercent",
        )

        high_price = get_value(
            "high_price",
            "highPrice",
        )

        low_price = get_value(
            "low_price",
            "lowPrice",
        )

        volume = get_value(
            "volume",
        )

        quote_volume = get_value(
            "quote_volume",
            "quoteVolume",
        )

        return Ticker(
            symbol=symbol,
            last_price=float(last_price),
            price_change=(
                float(price_change)
                if price_change is not None
                else None
            ),
            price_change_percent=(
                float(price_change_percent)
                if price_change_percent is not None
                else None
            ),
            high_price=(
                float(high_price)
                if high_price is not None
                else None
            ),
            low_price=(
                float(low_price)
                if low_price is not None
                else None
            ),
            volume=(
                float(volume)
                if volume is not None
                else None
            ),
            quote_volume=(
                float(quote_volume)
                if quote_volume is not None
                else None
            ),
        )

if __name__ == "__main__":

    parser = BinanceResponseParser()

    # Simulated response representing what the
    # MCP-connected agent will eventually return.
    sample_response = {
        "ticker": {
            "last_price": "108.50",
            "price_change": "8.50",
            "price_change_percent": "8.50",
            "high_price": "112.00",
            "low_price": "98.00",
            "volume": "1250000",
            "quote_volume": "135625000",
        },
        "candles": {
            "4h": [
                [
                    1000,
                    "100",
                    "105",
                    "98",
                    "103",
                    "1000",
                    2000,
                    "103000",
                    100,
                    "520",
                    "53560",
                    "0",
                ],
                [
                    2000,
                    "103",
                    "108",
                    "101",
                    "106",
                    "1200",
                    3000,
                    "127200",
                    120,
                    "630",
                    "66780",
                    "0",
                ],
                [
                    3000,
                    "106",
                    "110",
                    "104",
                    "108",
                    "1500",
                    4000,
                    "162000",
                    150,
                    "780",
                    "84240",
                    "0",
                ],
            ],
            "1h": [
                [
                    1000,
                    "106",
                    "107",
                    "105",
                    "106.5",
                    "500",
                    2000,
                    "53250",
                    50,
                    "260",
                    "27690",
                    "0",
                ],
            ],
        },
        "order_book": {
            "bids": [
                ["108.40", "100"],
                ["108.30", "150"],
            ],
            "asks": [
                ["108.60", "120"],
                ["108.70", "180"],
            ],
            "T": 4000,
        },
    }

    snapshot = parser.parse(
        sample_response,
        "EDENUSDT",
    )

    assert snapshot.symbol == "EDENUSDT"

    assert snapshot.ticker is not None
    assert snapshot.ticker.last_price == 108.50

    assert "4h" in snapshot.candles
    assert len(snapshot.candles["4h"]) == 3

    assert "1h" in snapshot.candles
    assert len(snapshot.candles["1h"]) == 1

    assert snapshot.order_book is not None

    assert len(snapshot.order_book.bids) == 2
    assert len(snapshot.order_book.asks) == 2

    assert (
        snapshot.order_book.bids[0].price
        == 108.40
    )

    print("=" * 60)
    print("BINANCE RESPONSE PARSER TEST")
    print("=" * 60)

    print()
    print("Symbol:", snapshot.symbol)
    print(
        "Current price:",
        snapshot.ticker.last_price,
    )
    print(
        "4H candles:",
        len(snapshot.candles["4h"]),
    )
    print(
        "1H candles:",
        len(snapshot.candles["1h"]),
    )
    print(
        "Order book bids:",
        len(snapshot.order_book.bids),
    )
    print(
        "Order book asks:",
        len(snapshot.order_book.asks),
    )

    print()
    print("BINANCE RESPONSE PARSER TEST PASSED")
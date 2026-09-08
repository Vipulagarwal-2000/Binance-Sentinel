from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class MarketDataRequest:
    """
    Structured request describing exactly what market data Sentinel needs.
    """

    symbol: str
    timeframes: List[str]
    history_depth: Dict[str, int]
    market_data: List[str]

    def validate(self):
        if not self.symbol:
            raise ValueError("Market data request requires a symbol.")

        if not self.timeframes:
            raise ValueError("Market data request requires timeframes.")

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
            raise ValueError("Market data request requires data types.")

        return True

    def to_dict(self):
        self.validate()

        return {
            "symbol": self.symbol.upper(),
            "timeframes": self.timeframes,
            "history_depth": self.history_depth,
            "market_data": self.market_data,
        }

    def to_agent_prompt(
        self,
        request_id: str = "<REQUEST_ID>",
        result_path: str = "storage/mcp/results/<REQUEST_ID>.json",
    ) -> str:
        """
        Produce the complete instruction for the Binance MCP agent.

        The MCP agent should retrieve the requested Binance market data
        and return/save it in the structured format expected by Sentinel.
        """

        self.validate()

        symbol = self.symbol.upper()

        lines = [
            "BINANCE SENTINEL MARKET DATA REQUEST",
            "=" * 60,
            "",
            f"Request ID: {request_id}",
            f"Symbol: {symbol}",
            "",
            "OBJECTIVE",
            "Retrieve the Binance market data required for an",
            "adversarial technical research investigation.",
            "",
            "HISTORICAL CANDLE DATA",
            "",
            "Retrieve the following number of completed candles",
            "for each requested timeframe:",
            "",
        ]

        for timeframe in self.timeframes:
            depth = self.history_depth[timeframe]
            lines.append(
                f"- {timeframe}: {depth} completed candles"
            )

        lines.extend(
            [
                "",
                "For every candle, preserve these fields:",
                "- open_time",
                "- open",
                "- high",
                "- low",
                "- close",
                "- volume",
                "- close_time",
                "- quote_volume",
                "- trade_count",
                "- taker_buy_volume",
                "",
                "CURRENT MARKET DATA",
                "",
            ]
        )

        for data_type in self.market_data:
            if data_type == "candles":
                continue

            if data_type == "price":
                lines.append(
                    "- Current price / latest market price"
                )
            elif data_type == "24h_statistics":
                lines.append(
                    "- 24-hour market statistics"
                )
            elif data_type == "volume":
                lines.append(
                    "- Current/recent volume information"
                )
            elif data_type == "order_book":
                lines.append(
                    "- Current order book with bid and ask levels"
                )
            else:
                lines.append(
                    f"- {data_type}"
                )

        lines.extend(
            [
                "",
                "DATA REQUIREMENTS",
                "",
                "- Do not summarize the historical candle data.",
                "- Do not truncate the requested candle history.",
                "- Do not omit requested timeframes.",
                "- Do not replace data with a natural-language explanation.",
                "- Preserve numeric values accurately.",
                "- Return valid structured JSON.",
                "",
                "EXPECTED RESULT STRUCTURE",
                "",
                "{",
                '  "symbol": "SYMBOL",',
                '  "candles": {',
                '    "1D": [...],',
                '    "4H": [...],',
                '    "1H": [...]',
                "  },",
                '  "price": {...},',
                '  "24h_statistics": {...},',
                '  "volume": {...},',
                '  "order_book": {...}',
                "}",
                "",
                "FILE HANDOFF",
                "",
                "The result must correspond to this request ID:",
                f"{request_id}",
                "",
                "Save the final structured JSON result as:",
                result_path.replace(
                    "<REQUEST_ID>",
                    request_id,
                ),
                "",
                "Do not create a different request ID.",
                "Do not mix data from another research request.",
                "",
                "FINAL REQUIREMENT",
                "",
                "Return the requested Binance market data in structured JSON.",
                "The Sentinel research engine will perform all technical",
                "analysis independently.",
            ]
        )

        return "\n".join(lines)


class DataRequestBuilder:
    """
    Builds a MarketDataRequest from a ResearchPlan and symbol.
    """

    @staticmethod
    def from_plan(symbol: str, plan) -> MarketDataRequest:
        plan.validate()

        request = MarketDataRequest(
            symbol=symbol.upper(),
            timeframes=list(plan.timeframes),
            history_depth=dict(plan.history_depth),
            market_data=list(plan.market_data),
        )

        request.validate()

        return request
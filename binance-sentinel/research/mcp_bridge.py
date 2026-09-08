"""
Binance Sentinel
MCP research bridge.

Creates a precise MCP request for the Sentinel research
agent and converts the returned JSON into a MarketSnapshot.

File-based handoff:

    Sentinel
        ↓
    storage/mcp/requests/
        ↓
    VS Code Binance MCP Agent
        ↓
    storage/mcp/results/
        ↓
    Sentinel

This bridge does not establish or authenticate the MCP
connection. The MCP-connected agent is responsible for
retrieving Binance data.
"""

import json
from datetime import datetime
from pathlib import Path

from binance.market_data import MarketSnapshot
from binance.response_parser import BinanceResponseParser
from research.data_request import (
    DataRequestBuilder,
    MarketDataRequest,
)
from research.plan import ResearchPlan


class MCPResearchBridge:
    """
    Bridge between Sentinel's Python research engine and
    the MCP-connected agent.
    """

    def __init__(
        self,
        output_directory: str | Path = "storage/mcp",
    ):
        self.output_directory = Path(
            output_directory
        )

        self.requests_directory = (
            self.output_directory / "requests"
        )

        self.results_directory = (
            self.output_directory / "results"
        )

        self.requests_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.results_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.request_builder = DataRequestBuilder()

        self.response_parser = BinanceResponseParser()

    # --------------------------------------------------
    # REQUEST CREATION
    # --------------------------------------------------

    def create_request(
        self,
        symbol: str,
        plan: ResearchPlan,
    ) -> MarketDataRequest:
        """
        Convert a ResearchPlan into a structured
        market-data request.
        """

        return self.request_builder.from_plan(
            symbol=symbol,
            plan=plan,
        )

    # --------------------------------------------------
    # REQUEST FILE HANDOFF
    # --------------------------------------------------

    def save_request(
        self,
        request: MarketDataRequest,
    ) -> tuple[Path, Path]:
        """
        Save the structured request and compact MCP
        agent instruction into storage/mcp/requests/.

        Returns:
            (request_file, prompt_file)
        """

        request_id = (
    f"{request.symbol.upper()}_"
    f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
)

        request_file = (
    self.requests_directory
    / f"{request_id}.json"
)

        prompt_file = (
    self.requests_directory
    / f"{request_id}.txt"
)

        with request_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                request.to_dict(),
                file,
                indent=4,
                ensure_ascii=False,
            )

        prompt_file.write_text(
    request.to_agent_prompt(
        request_id=request_id,
        result_path=(
            "storage/mcp/results/<REQUEST_ID>.json"
        ),
    ),
    encoding="utf-8",
)

        return (
            request_file,
            prompt_file,
        )

    # --------------------------------------------------
    # RESULT FILE HANDOFF
    # --------------------------------------------------

    def load_response(
        self,
        response_file: str | Path,
    ) -> dict:
        """
        Load a JSON result produced by the
        MCP-connected agent.
        """

        response_path = Path(response_file)

        if not response_path.exists():
            raise FileNotFoundError(
                f"MCP result does not exist: "
                f"{response_path}"
            )

        with response_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(
                "MCP result must be a JSON object."
            )

        return data

    def find_result(
        self,
        request_id: str,
    ) -> Path | None:
        """
        Find the result associated with a request.

        Expected filename:

            <request_id>.json
        """

        result_file = (
            self.results_directory
            / f"{request_id}.json"
        )

        if result_file.exists():
            return result_file

        return None

    # --------------------------------------------------
    # RESULT PARSING
    # --------------------------------------------------

    def parse_response(
        self,
        response: dict,
        symbol: str,
    ) -> MarketSnapshot:
        """
        Convert an MCP result into Sentinel's
        MarketSnapshot.
        """

        return self.response_parser.parse(
            data=response,
            symbol=symbol,
        )

    def parse_response_file(
        self,
        response_file: str | Path,
        symbol: str,
    ) -> MarketSnapshot:
        """
        Load and parse an MCP result file.
        """

        response = self.load_response(
            response_file
        )

        return self.parse_response(
            response=response,
            symbol=symbol,
        )


if __name__ == "__main__":

    print("=" * 60)
    print("SENTINEL MCP BRIDGE TEST")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Create research plan
    # --------------------------------------------------

    plan = ResearchPlan()

    # --------------------------------------------------
    # 2. Create bridge
    # --------------------------------------------------

    bridge = MCPResearchBridge()

    # --------------------------------------------------
    # 3. Build request
    # --------------------------------------------------

    request = bridge.create_request(
        symbol="EDENUSDT",
        plan=plan,
    )

    # --------------------------------------------------
    # 4. Save request artifacts
    # --------------------------------------------------

    request_file, prompt_file = (
        bridge.save_request(request)
    )

    print()
    print("Request created.")
    print(
    "Request ID:",
    request_file.stem,
)

    print()
    print("Request file:")
    print(request_file)

    print()
    print("Prompt file:")
    print(prompt_file)

    # --------------------------------------------------
    # 5. Verify directories
    # --------------------------------------------------

    assert bridge.requests_directory.exists()
    assert bridge.results_directory.exists()

    # --------------------------------------------------
    # 6. Verify request files
    # --------------------------------------------------

    assert request_file.exists()
    assert prompt_file.exists()

    request_contents = json.loads(
        request_file.read_text(
            encoding="utf-8"
        )
    )

    prompt_contents = (
        prompt_file.read_text(
            encoding="utf-8"
        )
    )

    assert (
        request_contents["symbol"]
        == "EDENUSDT"
    )

    assert (
        request_contents["timeframes"]
        == ["1D", "4H", "1H"]
    )

    assert (
        request_contents["history_depth"]["1D"]
        == 60
    )

    assert (
        request_contents["history_depth"]["4H"]
        == 180
    )

    assert (
        request_contents["history_depth"]["1H"]
        == 720
    )

    assert (
        "BINANCE SENTINEL MARKET DATA REQUEST"
        in prompt_contents
    )

    assert (
        "EDENUSDT"
        in prompt_contents
    )

    assert "1D: 60 completed candles" in prompt_contents
    assert "4H: 180 completed candles" in prompt_contents
    assert "1H: 720 completed candles" in prompt_contents

    assert "open_time" in prompt_contents
    assert "open" in prompt_contents
    assert "high" in prompt_contents
    assert "low" in prompt_contents
    assert "close" in prompt_contents
    assert "volume" in prompt_contents
    assert "close_time" in prompt_contents
    assert "quote_volume" in prompt_contents
    assert "trade_count" in prompt_contents
    assert "taker_buy_volume" in prompt_contents

    assert "FILE HANDOFF" in prompt_contents
    assert request_file.stem in prompt_contents
    assert "storage/mcp/results/" in prompt_contents
    assert (
    "Return the requested Binance market data in structured JSON."
    in prompt_contents
)

    # --------------------------------------------------
    # 7. Display result
    # --------------------------------------------------

    print()
    print("Requested timeframes:")
    print(request.timeframes)

    print()
    print("Requested data:")
    print(request.market_data)

    print()
    print("Request directory:")
    print(bridge.requests_directory)

    print()
    print("Result directory:")
    print(bridge.results_directory)

    print()
    print("MCP prompt generated successfully.")

    print()
    print("SENTINEL MCP BRIDGE TEST PASSED")
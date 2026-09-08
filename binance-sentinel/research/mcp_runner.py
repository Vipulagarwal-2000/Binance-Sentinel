"""
Binance Sentinel
MCP result runner.

Consumes a completed Binance MCP result from:

    storage/mcp/results/<request_id>.json

and converts it into a MarketSnapshot for the
ResearchPipeline.

The Binance MCP connection itself is handled externally
by the VS Code MCP agent.
"""

import json
from pathlib import Path

from binance.market_data import MarketSnapshot
from binance.response_parser import BinanceResponseParser
from research.case_manager import CaseManager
from research.mcp_bridge import MCPResearchBridge
from research.pipeline import ResearchPipeline
from research.plan import ResearchPlan


class MCPResearchRunner:
    def __init__(self, output_directory: str | Path = "storage/mcp"):
        self.bridge = MCPResearchBridge(output_directory)

        self.response_parser = BinanceResponseParser()
        self.case_manager = CaseManager()
        self.pipeline = ResearchPipeline()

    def load_result(self, result_file: str | Path) -> dict:
        result_path = Path(result_file)

        if not result_path.exists():
            raise FileNotFoundError(
                f"MCP result does not exist: {result_path}"
            )

        with result_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(
                "MCP result must be a JSON object."
            )

        return data

    def result_exists(self, request_id: str) -> bool:
        return self.bridge.find_result(request_id) is not None

    def parse_result(
        self,
        result_file: str | Path,
        symbol: str,
    ) -> MarketSnapshot:
        result = self.load_result(result_file)

        return self.response_parser.parse(
            data=result,
            symbol=symbol,
        )

    def run_research(
        self,
        case_id: str,
        plan: ResearchPlan,
        result_file: str | Path,
    ):
        case = self.case_manager.load_case(case_id)

        if case is None:
            raise ValueError(
                f"Research case not found: {case_id}"
            )

        market_snapshot = self.parse_result(
            result_file=result_file,
            symbol=case.symbol,
        )

        pipeline_result = self.pipeline.run(
            case_id=case_id,
            market_snapshot=market_snapshot,
        )

        return pipeline_result


if __name__ == "__main__":
    print("=" * 60)
    print("SENTINEL MCP RUNNER TEST")
    print("=" * 60)

    runner = MCPResearchRunner()

    print()
    print("Requests directory:")
    print(runner.bridge.requests_directory)

    print()
    print("Results directory:")
    print(runner.bridge.results_directory)

    assert runner.bridge.requests_directory.exists()
    assert runner.bridge.results_directory.exists()

    print()
    print("MCP result runner initialized successfully.")
    print()
    print("SENTINEL MCP RUNNER TEST PASSED")
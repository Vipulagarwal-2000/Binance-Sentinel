"""
Binance Sentinel
Research case storage and management.
"""

import json
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from config import CASES_DIR
from thesis.model import ResearchCase


class CaseManager:
    def __init__(self, cases_dir: Path = CASES_DIR):
        self.cases_dir = cases_dir
        self.cases_dir.mkdir(parents=True, exist_ok=True)

    def _case_directory(self, case_id: str) -> Path:
        return self.cases_dir / case_id

    def _case_file(self, case_id: str) -> Path:
        return self._case_directory(case_id) / "case.json"

    def create_case(
        self,
        name: str,
        symbol: str,
        direction: str,
        time_horizon: str,
        thesis: str,
        assumptions=None,
    ) -> ResearchCase:
        symbol = symbol.upper()
        direction = direction.upper()

        case_id = self._generate_case_id(symbol)

        case = ResearchCase(
            case_id=case_id,
            name=name,
            symbol=symbol,
            direction=direction,
            time_horizon=time_horizon,
            thesis=thesis,
            assumptions=assumptions or [],
        )

        self.save_case(case)

        return case

    def save_case(self, case: ResearchCase):
        case.updated_at = datetime.now().isoformat()

        case_directory = self._case_directory(case.case_id)
        case_directory.mkdir(parents=True, exist_ok=True)

        case_file = self._case_file(case.case_id)

        with case_file.open("w", encoding="utf-8") as file:
            json.dump(
                asdict(case),
                file,
                indent=4,
                ensure_ascii=False,
            )

    def load_case(self, case_id: str) -> ResearchCase:
        case_file = self._case_file(case_id)

        if not case_file.exists():
            raise FileNotFoundError(
                f"Research case '{case_id}' does not exist."
            )

        with case_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        # Compatibility with older case files.
        # Research plans are now stored separately in
        # research_plan.json.
        data.pop("research_plan", None)

        return ResearchCase(**data)

    def list_cases(self):
        return sorted(
            directory.name
            for directory in self.cases_dir.iterdir()
            if directory.is_dir()
        )

    def _generate_case_id(self, symbol: str) -> str:
        safe_symbol = re.sub(
            r"[^A-Z0-9_-]",
            "",
            symbol.upper(),
        )

        existing_cases = self.list_cases()

        matching_numbers = []

        for case_id in existing_cases:
            prefix = f"{safe_symbol}_"

            if case_id.startswith(prefix):
                number_part = case_id[len(prefix):]

                if number_part.isdigit():
                    matching_numbers.append(
                        int(number_part)
                    )

        next_number = max(
            matching_numbers,
            default=0,
        ) + 1

        return f"{safe_symbol}_{next_number:03d}"
"""
Binance Sentinel
Research plan management.
"""

import json
from pathlib import Path

from config import CASES_DIR
from research.plan import ResearchPlan


class PlanManager:
    """
    Manages the editable research plan for a research case.
    """

    def __init__(self, cases_dir: Path = CASES_DIR):
        self.cases_dir = cases_dir

    def _plan_file(self, case_id: str) -> Path:
        """
        Return the research plan file for a case.
        """

        case_directory = self.cases_dir / case_id

        if not case_directory.exists():
            raise FileNotFoundError(
                f"Research case '{case_id}' does not exist."
            )

        return case_directory / "research_plan.json"

    def create_default_plan(self, case_id: str) -> ResearchPlan:
        """
        Create and save a default research plan.
        """

        plan = ResearchPlan()

        self.save_plan(case_id, plan)

        return plan

    def save_plan(
        self,
        case_id: str,
        plan: ResearchPlan,
    ):
        """
        Save a research plan to disk.
        """

        plan_file = self._plan_file(case_id)

        with plan_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                plan.to_dict(),
                file,
                indent=4,
                ensure_ascii=False,
            )

    def load_plan(
        self,
        case_id: str,
    ) -> ResearchPlan:
        """
        Load a research plan from disk.
        """

        plan_file = self._plan_file(case_id)

        if not plan_file.exists():
            return self.create_default_plan(case_id)

        with plan_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return ResearchPlan.from_dict(data)

    def add_timeframe(
        self,
        case_id: str,
        timeframe: str,
    ):
        """
        Add a timeframe to a case's research plan.
        """

        plan = self.load_plan(case_id)

        plan.add_timeframe(timeframe)

        self.save_plan(case_id, plan)

    def remove_timeframe(
        self,
        case_id: str,
        timeframe: str,
    ):
        """
        Remove a timeframe from a case's research plan.
        """

        plan = self.load_plan(case_id)

        plan.remove_timeframe(timeframe)

        self.save_plan(case_id, plan)

    def add_analysis(
        self,
        case_id: str,
        analysis_type: str,
    ):
        """
        Add an analysis type to a case's research plan.
        """

        plan = self.load_plan(case_id)

        plan.add_analysis(analysis_type)

        self.save_plan(case_id, plan)

    def remove_analysis(
        self,
        case_id: str,
        analysis_type: str,
    ):
        """
        Remove an analysis type from a case's research plan.
        """

        plan = self.load_plan(case_id)

        plan.remove_analysis(analysis_type)

        self.save_plan(case_id, plan)

    def add_market_data(
        self,
        case_id: str,
        data_type: str,
    ):
        """
        Add a market-data requirement.
        """

        plan = self.load_plan(case_id)

        plan.add_market_data(data_type)

        self.save_plan(case_id, plan)

    def remove_market_data(
        self,
        case_id: str,
        data_type: str,
    ):
        """
        Remove a market-data requirement.
        """

        plan = self.load_plan(case_id)

        plan.remove_market_data(data_type)

        self.save_plan(case_id, plan)

    def add_reasoning_step(
        self,
        case_id: str,
        reasoning_type: str,
    ):
        """
        Add a reasoning step.
        """

        plan = self.load_plan(case_id)

        plan.add_reasoning_step(reasoning_type)

        self.save_plan(case_id, plan)

    def remove_reasoning_step(
        self,
        case_id: str,
        reasoning_type: str,
    ):
        """
        Remove a reasoning step.
        """

        plan = self.load_plan(case_id)

        plan.remove_reasoning_step(reasoning_type)

        self.save_plan(case_id, plan)
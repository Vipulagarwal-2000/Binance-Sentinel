"""
Binance Sentinel
Research session model and storage.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from config import CASES_DIR


@dataclass
class ResearchSession:
    """
    A historical snapshot of one Sentinel research run.
    """

    session_id: str
    case_id: str

    thesis: str
    direction: str
    time_horizon: str

    research_plan: dict = field(
        default_factory=dict
    )

    market_data: dict = field(
        default_factory=dict
    )

    analysis: dict = field(
        default_factory=dict
    )

    evidence: list = field(
        default_factory=list
    )

    challenges: list = field(
        default_factory=list
    )

    confidence: float | None = None

    verdict: str | None = None

    invalidation_conditions: list = field(
        default_factory=list
    )

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )


class SessionManager:

    def __init__(
        self,
        cases_dir: Path = CASES_DIR,
    ):
        self.cases_dir = cases_dir

    def _sessions_directory(
        self,
        case_id: str,
    ) -> Path:

        directory = (
            self.cases_dir
            / case_id
            / "sessions"
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    def _session_file(
        self,
        case_id: str,
        session_id: str,
    ) -> Path:

        return (
            self._sessions_directory(case_id)
            / f"{session_id}.json"
        )

    def create_session(
        self,
        case_id: str,
        thesis: str,
        direction: str,
        time_horizon: str,
        research_plan=None,
    ) -> ResearchSession:

        session_id = self._generate_session_id()

        session = ResearchSession(
            session_id=session_id,
            case_id=case_id,
            thesis=thesis,
            direction=direction,
            time_horizon=time_horizon,
            research_plan=research_plan or {},
        )

        self.save_session(session)

        return session

    def save_session(
        self,
        session: ResearchSession,
    ):

        session_file = self._session_file(
            session.case_id,
            session.session_id,
        )

        with session_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                asdict(session),
                file,
                indent=4,
                ensure_ascii=False,
            )

    def load_session(
        self,
        case_id: str,
        session_id: str,
    ) -> ResearchSession:

        session_file = self._session_file(
            case_id,
            session_id,
        )

        if not session_file.exists():

            raise FileNotFoundError(
                f"Research session "
                f"'{session_id}' "
                f"does not exist."
            )

        with session_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return ResearchSession(**data)

    def list_sessions(
        self,
        case_id: str,
    ) -> list:

        directory = self._sessions_directory(
            case_id
        )

        return sorted(
            file.stem
            for file in directory.glob(
                "*.json"
            )
        )

    def save_evidence(
        self,
        session: ResearchSession,
        ledger,
    ):
        """
        Copy the Evidence Ledger into the session
        and persist the updated session.
        """

        session.evidence = [
            {
                "evidence_id": item.evidence_id,
                "evidence_type": item.evidence_type,
                "observation": item.observation,
                "timeframe": item.timeframe,
                "source": item.source,
                "strength": item.strength,
                "reasoning": item.reasoning,
                "created_at": item.created_at,
            }
            for item in ledger.all()
        ]

        self.save_session(session)

    @staticmethod
    def _generate_session_id() -> str:

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        return f"SESSION_{timestamp}"
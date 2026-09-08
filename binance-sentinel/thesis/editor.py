"""
Binance Sentinel
Thesis editing and version management.
"""

from copy import deepcopy
from datetime import datetime

from thesis.model import ResearchCase


def update_thesis(
    case: ResearchCase,
    *,
    name=None,
    symbol=None,
    direction=None,
    time_horizon=None,
    thesis=None,
    assumptions=None,
):
    """
    Update the editable parts of a research case.

    The current case is modified in memory.
    The caller is responsible for saving it.
    """

    if name is not None:
        case.name = name

    if symbol is not None:
        case.symbol = symbol.upper()

    if direction is not None:
        case.direction = direction.upper()

    if time_horizon is not None:
        case.time_horizon = time_horizon

    if thesis is not None:
        case.thesis = thesis

    if assumptions is not None:
        case.assumptions = assumptions

    case.updated_at = datetime.now().isoformat()

    return case


def create_thesis_version(case: ResearchCase):
    """
    Create a snapshot of the current thesis before it is changed.

    Returns a dictionary that can later be saved as a version.
    """

    return {
        "saved_at": datetime.now().isoformat(),
        "name": case.name,
        "symbol": case.symbol,
        "direction": case.direction,
        "time_horizon": case.time_horizon,
        "thesis": case.thesis,
        "assumptions": deepcopy(case.assumptions),
    }
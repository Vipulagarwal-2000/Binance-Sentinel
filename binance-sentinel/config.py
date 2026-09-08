"""
Binance Sentinel
Project configuration.
"""

from pathlib import Path


# --------------------------------------------------
# Project paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

STORAGE_DIR = BASE_DIR / "storage"
CASES_DIR = STORAGE_DIR / "cases"
SNAPSHOTS_DIR = STORAGE_DIR / "snapshots"

OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = OUTPUT_DIR / "reports"


# --------------------------------------------------
# Application settings
# --------------------------------------------------

APP_NAME = "Binance Sentinel"

DEFAULT_TIMEFRAMES = [
    "1D",
    "4H",
    "1H",
]


# --------------------------------------------------
# Research settings
# --------------------------------------------------

DEFAULT_RESEARCH_CATEGORIES = [
    "market_structure",
    "volume",
    "momentum",
    "volatility",
    "liquidity",
    "support_resistance",
]


# --------------------------------------------------
# Create required directories
# --------------------------------------------------

def initialize_directories():
    """Create Sentinel's storage directories if they don't exist."""

    directories = [
        STORAGE_DIR,
        CASES_DIR,
        SNAPSHOTS_DIR,
        OUTPUT_DIR,
        REPORTS_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
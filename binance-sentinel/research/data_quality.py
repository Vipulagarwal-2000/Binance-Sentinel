from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DataQualityResult:
    passed: bool
    missing_timeframes: List[str] = field(default_factory=list)
    insufficient_history: Dict[str, Dict[str, int]] = field(
        default_factory=dict
    )
    missing_data: List[str] = field(default_factory=list)
    invalid_timeframes: List[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.passed:
            return "DATA QUALITY: PASS"

        problems = []

        if self.missing_timeframes:
            problems.append(
                "Missing timeframes: "
                + ", ".join(self.missing_timeframes)
            )

        if self.insufficient_history:
            history_items = []

            for timeframe, values in self.insufficient_history.items():
                history_items.append(
                    f"{timeframe} "
                    f"(required {values['required']}, "
                    f"received {values['received']})"
                )

            problems.append(
                "Insufficient history: "
                + ", ".join(history_items)
            )

        if self.missing_data:
            problems.append(
                "Missing data: "
                + ", ".join(self.missing_data)
            )

        if self.invalid_timeframes:
            problems.append(
                "Invalid timeframes: "
                + ", ".join(self.invalid_timeframes)
            )

        return "DATA QUALITY: FAIL — " + "; ".join(problems)


class DataQualityChecker:
    """
    Validates whether Binance market data satisfies the ResearchPlan.

    This is a deterministic gate. Analysis should not run if the
    requested evidence is incomplete.
    """

    VALID_TIMEFRAMES = {"1M", "1W", "1D", "12H", "8H", "6H", "4H", "2H", "1H", "30M", "15M", "5M", "3M", "1M"}

    def check(self, snapshot, plan) -> DataQualityResult:
        missing_timeframes = []
        insufficient_history = {}
        missing_data = []
        invalid_timeframes = []

        # ---------------------------------------------------------
        # 1. Validate requested timeframes
        # ---------------------------------------------------------

        for timeframe in plan.timeframes:
            normalized = timeframe.upper()

            if normalized not in self.VALID_TIMEFRAMES:
                invalid_timeframes.append(normalized)

        # ---------------------------------------------------------
        # 2. Check candle availability and historical depth
        # ---------------------------------------------------------

        candles = getattr(snapshot, "candles", {}) or {}

        for timeframe in plan.timeframes:
            normalized = timeframe.lower()

            available = self._get_timeframe_candles(
                candles,
                normalized,
            )

            if available is None:
                missing_timeframes.append(normalized)
                continue

            required = plan.history_depth.get(
                timeframe.upper(),
                plan.history_depth.get(timeframe, 0),
            )

            received = len(available)

            if received < required:
                insufficient_history[normalized] = {
                    "required": required,
                    "received": received,
                }

        # ---------------------------------------------------------
        # 3. Check requested non-candle market data
        # ---------------------------------------------------------

        for data_type in plan.market_data:
            if data_type == "candles":
                continue

            if not self._has_market_data(snapshot, data_type):
                missing_data.append(data_type)

        passed = not (
            missing_timeframes
            or insufficient_history
            or missing_data
            or invalid_timeframes
        )

        return DataQualityResult(
            passed=passed,
            missing_timeframes=missing_timeframes,
            insufficient_history=insufficient_history,
            missing_data=missing_data,
            invalid_timeframes=invalid_timeframes,
        )

    @staticmethod
    def _get_timeframe_candles(candles, timeframe):
        """
        Handle either lowercase or uppercase timeframe keys.
        """

        if timeframe in candles:
            return candles[timeframe]

        upper = timeframe.upper()

        if upper in candles:
            return candles[upper]

        return None

    @staticmethod
    def _has_market_data(snapshot, data_type):
        """
        Check that the requested market-data component exists.

        MarketSnapshot stores structured market data in dedicated fields,
        while raw_data may contain the original Binance response.
        """

        if data_type == "candles":
            return bool(getattr(snapshot, "candles", {}))

        if data_type == "order_book":
            order_book = getattr(snapshot, "order_book", None)

            if order_book is not None:
                return True

            raw_data = getattr(snapshot, "raw_data", {}) or {}
            raw_order_book = raw_data.get("order_book")

            if raw_order_book is not None:
                if isinstance(raw_order_book, (list, dict, str)):
                    return len(raw_order_book) > 0

                return True

            return False

        
        if data_type in ("price", "24h_statistics"):
            ticker = getattr(snapshot, "ticker", None)

            if ticker is not None:
                return True

            raw_data = getattr(snapshot, "raw_data", {}) or {}

            if data_type in raw_data:
                value = raw_data[data_type]

                if value is not None:
                    if isinstance(value, (list, dict, str)):
                        return len(value) > 0

                    return True

            # Some Binance responses may expose ticker information
            # directly rather than under a named 24h_statistics key.
            if data_type == "price" and "ticker" in raw_data:
                return True

            if data_type == "24h_statistics" and "ticker" in raw_data:
                return True

            return False

        if data_type == "volume":
            candles = getattr(snapshot, "candles", {}) or {}
            return bool(candles)

        value = getattr(snapshot, data_type, None)

        if value is not None:
            if isinstance(value, (list, dict, str)):
                return len(value) > 0

            return True

        raw_data = getattr(snapshot, "raw_data", {}) or {}
        value = raw_data.get(data_type)

        if value is not None:
            if isinstance(value, (list, dict, str)):
                return len(value) > 0

            return True

        return False
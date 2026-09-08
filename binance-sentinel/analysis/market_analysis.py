"""
Binance Sentinel
Deterministic market analysis.

This module converts MarketSnapshot data into objective
market observations that can later become Evidence Ledger items.

No LLM reasoning happens here.
"""

from dataclasses import dataclass
from statistics import mean, stdev

from binance.market_data import Candle, MarketSnapshot


@dataclass
class AnalysisResult:
    """
    Objective analysis for one timeframe.

    The categorical fields are kept for compatibility with the
    existing thesis evaluator. The additional numerical fields
    provide auditable deterministic measurements.
    """

    timeframe: str
    current_price: float

    price_change_percent: float | None = None

    # Existing categorical outputs
    trend: str = "UNKNOWN"
    momentum: str = "UNKNOWN"
    volume_signal: str = "UNKNOWN"
    volatility: str = "UNKNOWN"

    support: float | None = None
    resistance: float | None = None

    observations: list[str] | None = None

    # ---------------------------------------------------------
    # Trend / structure
    # ---------------------------------------------------------

    short_ma: float | None = None
    long_ma: float | None = None
    ma_slope_percent: float | None = None
    price_vs_baseline_percent: float | None = None

    structure: str = "UNKNOWN"
    swing_high: float | None = None
    swing_low: float | None = None

    # ---------------------------------------------------------
    # Momentum
    # ---------------------------------------------------------

    rsi: float | None = None
    roc_percent: float | None = None
    momentum_slope: float | None = None
    momentum_change: str = "UNKNOWN"

    # ---------------------------------------------------------
    # Volume
    # ---------------------------------------------------------

    current_volume: float | None = None
    average_volume: float | None = None
    volume_ratio: float | None = None
    price_volume_relationship: str = "UNKNOWN"

    # ---------------------------------------------------------
    # Structure / levels
    # ---------------------------------------------------------

    distance_to_support_percent: float | None = None
    distance_to_resistance_percent: float | None = None

    # ---------------------------------------------------------
    # Volatility
    # ---------------------------------------------------------

    atr: float | None = None
    rolling_volatility: float | None = None
    recent_range_percent: float | None = None
    volatility_state: str = "UNKNOWN"

    def __post_init__(self):
        if self.observations is None:
            self.observations = []


class MarketAnalyzer:
    """
    Performs deterministic analysis on Sentinel market data.

    No pair is hardcoded here. The analyzer works from whatever
    MarketSnapshot/candles it receives.
    """

    SHORT_MA_PERIOD = 20
    LONG_MA_PERIOD = 50

    RSI_PERIOD = 14
    ROC_PERIOD = 10

    SWING_LOOKBACK = 2

    ATR_PERIOD = 14
    VOLATILITY_PERIOD = 20

    def analyze_timeframe(
        self,
        candles: list[Candle],
        timeframe: str,
    ) -> AnalysisResult:

        if not candles:
            raise ValueError(
                f"No candles available for {timeframe}."
            )

        if len(candles) < 5:
            raise ValueError(
                f"At least 5 candles are required for "
                f"{timeframe} analysis."
            )

        current_price = candles[-1].close

        price_change_percent = self._price_change_percent(
            candles
        )

        # -----------------------------------------------------
        # Trend / structure
        # -----------------------------------------------------

        short_ma = self._moving_average(
            candles,
            self.SHORT_MA_PERIOD,
        )

        long_ma = self._moving_average(
            candles,
            self.LONG_MA_PERIOD,
        )

        ma_slope_percent = self._ma_slope_percent(
            candles,
            self.SHORT_MA_PERIOD,
        )

        price_vs_baseline_percent = self._price_vs_baseline(
            current_price,
            long_ma,
        )

        trend = self._determine_trend(
            candles,
            short_ma,
            long_ma,
            ma_slope_percent,
        )

        structure = self._determine_structure(candles)

        swing_high = self._latest_swing_high(candles)

        swing_low = self._latest_swing_low(candles)

        # -----------------------------------------------------
        # Momentum
        # -----------------------------------------------------

        rsi = self._calculate_rsi(candles)

        roc_percent = self._calculate_roc(
            candles,
            self.ROC_PERIOD,
        )

        momentum_slope = self._momentum_slope(candles)

        momentum = self._determine_momentum(
            candles,
            rsi,
            roc_percent,
        )

        momentum_change = self._determine_momentum_change(
            candles
        )

        # -----------------------------------------------------
        # Volume
        # -----------------------------------------------------

        (
            volume_signal,
            current_volume,
            average_volume,
            volume_ratio,
        ) = self._volume_metrics(candles)

        price_volume_relationship = (
            self._price_volume_relationship(candles)
        )

        # -----------------------------------------------------
        # Support / resistance
        # -----------------------------------------------------

        support = self._support(candles)

        resistance = self._resistance(candles)

        distance_to_support_percent = (
            self._distance_percent(
                current_price,
                support,
            )
        )

        distance_to_resistance_percent = (
            self._distance_percent(
                resistance,
                current_price,
            )
        )

        # -----------------------------------------------------
        # Volatility
        # -----------------------------------------------------

        (
            volatility,
            rolling_volatility,
            atr,
            recent_range_percent,
            volatility_state,
        ) = self._volatility_metrics(candles)

        # -----------------------------------------------------
        # Human-readable deterministic observations
        # -----------------------------------------------------

        observations = []

        observations.append(
            f"{timeframe} current price: "
            f"{current_price:.8g}"
        )

        observations.append(
            f"{timeframe} price change over sample: "
            f"{price_change_percent:.2f}%"
        )

        observations.append(
            f"{timeframe} trend: {trend}"
        )

        observations.append(
            f"{timeframe} structure: {structure}"
        )

        if short_ma is not None:
            observations.append(
                f"{timeframe} short MA: "
                f"{short_ma:.8g}"
            )

        if long_ma is not None:
            observations.append(
                f"{timeframe} long MA: "
                f"{long_ma:.8g}"
            )

        if ma_slope_percent is not None:
            observations.append(
                f"{timeframe} MA slope: "
                f"{ma_slope_percent:.2f}%"
            )

        if price_vs_baseline_percent is not None:
            observations.append(
                f"{timeframe} price vs baseline: "
                f"{price_vs_baseline_percent:.2f}%"
            )

        observations.append(
            f"{timeframe} momentum: {momentum}"
        )

        if rsi is not None:
            observations.append(
                f"{timeframe} RSI: "
                f"{rsi:.2f}"
            )

        if roc_percent is not None:
            observations.append(
                f"{timeframe} ROC: "
                f"{roc_percent:.2f}%"
            )

        if momentum_slope is not None:
            observations.append(
                f"{timeframe} momentum slope: "
                f"{momentum_slope:.4f}"
            )

        observations.append(
            f"{timeframe} momentum change: "
            f"{momentum_change}"
        )

        observations.append(
            f"{timeframe} volume signal: "
            f"{volume_signal}"
        )

        if volume_ratio is not None:
            observations.append(
                f"{timeframe} volume ratio: "
                f"{volume_ratio:.2f}x"
            )

        observations.append(
            f"{timeframe} price-volume relationship: "
            f"{price_volume_relationship}"
        )

        observations.append(
            f"{timeframe} volatility: "
            f"{volatility}"
        )

        if atr is not None:
            observations.append(
                f"{timeframe} ATR: "
                f"{atr:.8g}"
            )

        if rolling_volatility is not None:
            observations.append(
                f"{timeframe} rolling volatility: "
                f"{rolling_volatility:.2f}%"
            )

        if recent_range_percent is not None:
            observations.append(
                f"{timeframe} recent range: "
                f"{recent_range_percent:.2f}%"
            )

        observations.append(
            f"{timeframe} support: "
            f"{support:.8g}"
        )

        observations.append(
            f"{timeframe} resistance: "
            f"{resistance:.8g}"
        )

        if distance_to_support_percent is not None:
            observations.append(
                f"{timeframe} distance to support: "
                f"{distance_to_support_percent:.2f}%"
            )

        if distance_to_resistance_percent is not None:
            observations.append(
                f"{timeframe} distance to resistance: "
                f"{distance_to_resistance_percent:.2f}%"
            )

        return AnalysisResult(
            timeframe=timeframe,
            current_price=current_price,
            price_change_percent=price_change_percent,
            trend=trend,
            momentum=momentum,
            volume_signal=volume_signal,
            volatility=volatility,
            support=support,
            resistance=resistance,
            observations=observations,

            short_ma=short_ma,
            long_ma=long_ma,
            ma_slope_percent=ma_slope_percent,
            price_vs_baseline_percent=price_vs_baseline_percent,

            structure=structure,
            swing_high=swing_high,
            swing_low=swing_low,

            rsi=rsi,
            roc_percent=roc_percent,
            momentum_slope=momentum_slope,
            momentum_change=momentum_change,

            current_volume=current_volume,
            average_volume=average_volume,
            volume_ratio=volume_ratio,
            price_volume_relationship=price_volume_relationship,

            distance_to_support_percent=distance_to_support_percent,
            distance_to_resistance_percent=distance_to_resistance_percent,

            atr=atr,
            rolling_volatility=rolling_volatility,
            recent_range_percent=recent_range_percent,
            volatility_state=volatility_state,
        )

    def analyze_snapshot(
        self,
        snapshot: MarketSnapshot,
    ) -> dict[str, AnalysisResult]:

        results = {}

        for timeframe, candles in snapshot.candles.items():
            results[timeframe] = self.analyze_timeframe(
                candles,
                timeframe,
            )

        return results

    # =========================================================
    # PRICE
    # =========================================================

    @staticmethod
    def _price_change_percent(
        candles: list[Candle],
    ) -> float:

        first_close = candles[0].close
        last_close = candles[-1].close

        if first_close == 0:
            return 0.0

        return (
            (last_close - first_close)
            / first_close
            * 100
        )

    # =========================================================
    # TREND
    # =========================================================

    @staticmethod
    def _moving_average(
        candles: list[Candle],
        period: int,
    ) -> float | None:

        if not candles:
            return None

        closes = [
            candle.close
            for candle in candles
        ]

        period = min(period, len(closes))

        if period <= 0:
            return None

        return mean(closes[-period:])

    @staticmethod
    def _ma_slope_percent(
        candles: list[Candle],
        period: int,
    ) -> float | None:

        if len(candles) < 2:
            return None

        closes = [
            candle.close
            for candle in candles
        ]

        period = min(period, len(closes))

        if period < 2:
            return None

        current_ma = mean(closes[-period:])

        previous_end = len(closes) - period

        if previous_end <= 0:
            return None

        previous_start = max(
            0,
            previous_end - period,
        )

        previous_values = closes[
            previous_start:previous_end
        ]

        if not previous_values:
            return None

        previous_ma = mean(previous_values)

        if previous_ma == 0:
            return None

        return (
            (current_ma - previous_ma)
            / previous_ma
            * 100
        )

    @staticmethod
    def _price_vs_baseline(
        current_price: float,
        baseline: float | None,
    ) -> float | None:

        if baseline is None or baseline == 0:
            return None

        return (
            (current_price - baseline)
            / baseline
            * 100
        )

    @staticmethod
    def _determine_trend(
        candles: list[Candle],
        short_ma: float | None = None,
        long_ma: float | None = None,
        ma_slope_percent: float | None = None,
    ) -> str:

        if short_ma is None:
            short_ma = MarketAnalyzer._moving_average(
                candles,
                MarketAnalyzer.SHORT_MA_PERIOD,
            )

        if long_ma is None:
            long_ma = MarketAnalyzer._moving_average(
                candles,
                MarketAnalyzer.LONG_MA_PERIOD,
            )

        if short_ma is None or long_ma is None:
            return "UNKNOWN"

        # Primary trend signal.
        if short_ma > long_ma * 1.01:
            base_trend = "BULLISH"

        elif short_ma < long_ma * 0.99:
            base_trend = "BEARISH"

        else:
            base_trend = "NEUTRAL"

        # MA slope strengthens the classification.
        if ma_slope_percent is not None:

            if (
                base_trend == "BULLISH"
                and ma_slope_percent < -0.5
            ):
                return "NEUTRAL"

            if (
                base_trend == "BEARISH"
                and ma_slope_percent > 0.5
            ):
                return "NEUTRAL"

        return base_trend

    # =========================================================
    # STRUCTURE
    # =========================================================

    @staticmethod
    def _determine_structure(
        candles: list[Candle],
    ) -> str:

        if len(candles) < 5:
            return "UNKNOWN"

        highs = [
            candle.high
            for candle in candles
        ]

        lows = [
            candle.low
            for candle in candles
        ]

        recent_highs = highs[-3:]
        previous_highs = highs[-6:-3]

        recent_lows = lows[-3:]
        previous_lows = lows[-6:-3]

        if not previous_highs or not previous_lows:
            return "UNKNOWN"

        higher_highs = (
            mean(recent_highs)
            > mean(previous_highs)
        )

        higher_lows = (
            mean(recent_lows)
            > mean(previous_lows)
        )

        lower_highs = (
            mean(recent_highs)
            < mean(previous_highs)
        )

        lower_lows = (
            mean(recent_lows)
            < mean(previous_lows)
        )

        if higher_highs and higher_lows:
            return "HIGHER_HIGHS_HIGHER_LOWS"

        if lower_highs and lower_lows:
            return "LOWER_HIGHS_LOWER_LOWS"

        if higher_highs:
            return "HIGHER_HIGHS"

        if higher_lows:
            return "HIGHER_LOWS"

        if lower_highs:
            return "LOWER_HIGHS"

        if lower_lows:
            return "LOWER_LOWS"

        return "MIXED"

    @staticmethod
    def _latest_swing_high(
        candles: list[Candle],
    ) -> float | None:

        lookback = MarketAnalyzer.SWING_LOOKBACK

        if len(candles) < lookback * 2 + 1:
            return None

        for index in range(
            len(candles) - lookback - 1,
            lookback - 1,
            -1,
        ):
            current = candles[index].high

            left = [
                candles[index - offset].high
                for offset in range(1, lookback + 1)
            ]

            right = [
                candles[index + offset].high
                for offset in range(1, lookback + 1)
            ]

            if current >= max(left) and current >= max(right):
                return current

        return None

    @staticmethod
    def _latest_swing_low(
        candles: list[Candle],
    ) -> float | None:

        lookback = MarketAnalyzer.SWING_LOOKBACK

        if len(candles) < lookback * 2 + 1:
            return None

        for index in range(
            len(candles) - lookback - 1,
            lookback - 1,
            -1,
        ):
            current = candles[index].low

            left = [
                candles[index - offset].low
                for offset in range(1, lookback + 1)
            ]

            right = [
                candles[index + offset].low
                for offset in range(1, lookback + 1)
            ]

            if current <= min(left) and current <= min(right):
                return current

        return None

    # =========================================================
    # MOMENTUM
    # =========================================================

    @staticmethod
    def _calculate_rsi(
        candles: list[Candle],
        period: int = 14,
    ) -> float | None:

        if len(candles) <= period:
            return None

        closes = [
            candle.close
            for candle in candles
        ]

        gains = []
        losses = []

        for previous, current in zip(
            closes[:-1],
            closes[1:],
        ):
            change = current - previous

            if change > 0:
                gains.append(change)
                losses.append(0.0)

            else:
                gains.append(0.0)
                losses.append(abs(change))

        recent_gains = gains[-period:]
        recent_losses = losses[-period:]

        average_gain = mean(recent_gains)
        average_loss = mean(recent_losses)

        if average_loss == 0:
            return 100.0

        relative_strength = (
            average_gain / average_loss
        )

        return 100 - (
            100 / (1 + relative_strength)
        )

    @staticmethod
    def _calculate_roc(
        candles: list[Candle],
        period: int,
    ) -> float | None:

        if len(candles) <= period:
            return None

        current = candles[-1].close
        previous = candles[-1 - period].close

        if previous == 0:
            return None

        return (
            (current - previous)
            / previous
            * 100
        )

    @staticmethod
    def _momentum_slope(
        candles: list[Candle],
    ) -> float | None:

        if len(candles) < 6:
            return None

        closes = [
            candle.close
            for candle in candles
        ]

        recent_changes = []

        for previous, current in zip(
            closes[-6:-1],
            closes[-5:],
        ):
            if previous == 0:
                continue

            recent_changes.append(
                (current - previous)
                / previous
                * 100
            )

        if len(recent_changes) < 2:
            return None

        first = mean(recent_changes[:2])
        last = mean(recent_changes[-2:])

        return last - first

    @staticmethod
    def _determine_momentum(
        candles: list[Candle],
        rsi: float | None = None,
        roc_percent: float | None = None,
    ) -> str:

        if roc_percent is None:
            return "UNKNOWN"

        if rsi is not None:

            if roc_percent > 2 and rsi >= 50:
                return "POSITIVE"

            if roc_percent < -2 and rsi <= 50:
                return "NEGATIVE"

        if roc_percent > 2:
            return "POSITIVE"

        if roc_percent < -2:
            return "NEGATIVE"

        return "FLAT"

    @staticmethod
    def _determine_momentum_change(
        candles: list[Candle],
    ) -> str:

        slope = MarketAnalyzer._momentum_slope(candles)

        if slope is None:
            return "UNKNOWN"

        if slope > 0.25:
            return "ACCELERATING"

        if slope < -0.25:
            return "DECELERATING"

        return "STABLE"

    # =========================================================
    # VOLUME
    # =========================================================

    @staticmethod
    def _volume_metrics(
        candles: list[Candle],
    ) -> tuple:

        volumes = [
            candle.volume
            for candle in candles
        ]

        if not volumes:
            return "UNKNOWN", None, None, None

        current_volume = volumes[-1]

        if len(volumes) < 5:
            return (
                "UNKNOWN",
                current_volume,
                None,
                None,
            )

        recent_period = min(3, len(volumes))

        recent_average = mean(
            volumes[-recent_period:]
        )

        historical_values = volumes[
            :-recent_period
        ]

        if not historical_values:
            return (
                "UNKNOWN",
                current_volume,
                None,
                None,
            )

        average_volume = mean(
            historical_values
        )

        if average_volume == 0:
            return (
                "UNKNOWN",
                current_volume,
                average_volume,
                None,
            )

        ratio = (
            recent_average
            / average_volume
        )

        if ratio >= 1.5:
            signal = "EXPANDING"

        elif ratio <= 0.7:
            signal = "CONTRACTING"

        else:
            signal = "NORMAL"

        return (
            signal,
            current_volume,
            average_volume,
            ratio,
        )

    @staticmethod
    def _price_volume_relationship(
        candles: list[Candle],
    ) -> str:

        if len(candles) < 2:
            return "UNKNOWN"

        previous = candles[-2]
        current = candles[-1]

        price_up = current.close > previous.close
        price_down = current.close < previous.close
        volume_up = current.volume > previous.volume
        volume_down = current.volume < previous.volume

        if price_up and volume_up:
            return "PRICE_UP_VOLUME_UP"

        if price_down and volume_up:
            return "PRICE_DOWN_VOLUME_UP"

        if price_up and volume_down:
            return "PRICE_UP_VOLUME_DOWN"

        if price_down and volume_down:
            return "PRICE_DOWN_VOLUME_DOWN"

        return "NEUTRAL"

    # =========================================================
    # SUPPORT / RESISTANCE
    # =========================================================

    @staticmethod
    def _support(
        candles: list[Candle],
    ) -> float:

        lows = [
            candle.low
            for candle in candles
        ]

        return min(lows)

    @staticmethod
    def _resistance(
        candles: list[Candle],
    ) -> float:

        highs = [
            candle.high
            for candle in candles
        ]

        return max(highs)

    @staticmethod
    def _distance_percent(
        level: float | None,
        price: float | None,
    ) -> float | None:

        if level is None or price is None or price == 0:
            return None

        return (
            (level - price)
            / price
            * 100
        )

    # =========================================================
    # VOLATILITY
    # =========================================================

    @staticmethod
    def _volatility_metrics(
        candles: list[Candle],
    ) -> tuple:

        returns = []

        for previous, current in zip(
            candles[:-1],
            candles[1:],
        ):
            if previous.close == 0:
                continue

            returns.append(
                (
                    current.close - previous.close
                )
                / previous.close
                * 100
            )

        if len(returns) < 2:
            return (
                "UNKNOWN",
                None,
                None,
                None,
                "UNKNOWN",
            )

        rolling_period = min(
            MarketAnalyzer.VOLATILITY_PERIOD,
            len(returns),
        )

        rolling_returns = returns[
            -rolling_period:
        ]

        rolling_volatility = stdev(
            rolling_returns
        )

        if rolling_volatility >= 5:
            volatility = "HIGH"

        elif rolling_volatility <= 1.5:
            volatility = "LOW"

        else:
            volatility = "MODERATE"

        # True Range / ATR
        true_ranges = []

        for index in range(1, len(candles)):

            current = candles[index]
            previous = candles[index - 1]

            true_range = max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close),
            )

            true_ranges.append(true_range)

        if true_ranges:
            atr_period = min(
                MarketAnalyzer.ATR_PERIOD,
                len(true_ranges),
            )

            atr = mean(
                true_ranges[-atr_period:]
            )
        else:
            atr = None

        # Recent candle range relative to price.
        recent_period = min(
            5,
            len(candles),
        )

        recent_high = max(
            candle.high
            for candle in candles[-recent_period:]
        )

        recent_low = min(
            candle.low
            for candle in candles[-recent_period:]
        )

        current_price = candles[-1].close

        if current_price != 0:
            recent_range_percent = (
                (recent_high - recent_low)
                / current_price
                * 100
            )
        else:
            recent_range_percent = None

        # Compare recent volatility with older volatility.
        if len(returns) >= 10:

            midpoint = len(returns) // 2

            older = returns[:midpoint]
            recent = returns[midpoint:]

            older_volatility = stdev(older)
            recent_volatility = stdev(recent)

            if (
                older_volatility > 0
                and recent_volatility
                > older_volatility * 1.25
            ):
                volatility_state = "EXPANDING"

            elif (
                older_volatility > 0
                and recent_volatility
                < older_volatility * 0.75
            ):
                volatility_state = "CONTRACTING"

            else:
                volatility_state = "STABLE"

        else:
            volatility_state = "UNKNOWN"

        return (
            volatility,
            rolling_volatility,
            atr,
            recent_range_percent,
            volatility_state,
        )


# =============================================================
# BASIC MODULE TEST
# =============================================================

if __name__ == "__main__":

    candles = []

    prices = [
        100,
        101,
        102,
        101,
        103,
        105,
        106,
        108,
        110,
        111,
        113,
        112,
        115,
        117,
        118,
        120,
        122,
        121,
        124,
        126,
        128,
        127,
        130,
        132,
        134,
        136,
        135,
        138,
        140,
        142,
        144,
        146,
        145,
        148,
        150,
        152,
        154,
        156,
        158,
        160,
        162,
        164,
        166,
        168,
        170,
        172,
        174,
        176,
        178,
        180,
        182,
        184,
        186,
        188,
        190,
        192,
        194,
        196,
        198,
        200,
    ]

    volumes = [
        1000 + index * 10
        for index in range(len(prices))
    ]

    for index, price in enumerate(prices):

        candles.append(
            Candle(
                open_time=index,
                open=price - 1,
                high=price + 1,
                low=price - 2,
                close=price,
                volume=volumes[index],
                close_time=index,
            )
        )

    analyzer = MarketAnalyzer()

    result = analyzer.analyze_timeframe(
        candles,
        "4H",
    )

    print("=" * 60)
    print("           MARKET ANALYSIS TEST")
    print("=" * 60)
    print()

    print(f"Timeframe:                 {result.timeframe}")
    print(f"Current price:             {result.current_price}")
    print(
        f"Price change:              "
        f"{result.price_change_percent:.2f}%"
    )

    print()
    print("TREND / STRUCTURE")
    print(f"Trend:                     {result.trend}")
    print(f"Structure:                 {result.structure}")
    print(f"Short MA:                  {result.short_ma}")
    print(f"Long MA:                   {result.long_ma}")
    print(f"MA slope:                  {result.ma_slope_percent}")
    print(
        f"Price vs baseline:        "
        f"{result.price_vs_baseline_percent}"
    )

    print()
    print("MOMENTUM")
    print(f"Momentum:                  {result.momentum}")
    print(f"RSI:                       {result.rsi}")
    print(f"ROC:                       {result.roc_percent}")
    print(f"Momentum slope:            {result.momentum_slope}")
    print(f"Momentum change:           {result.momentum_change}")

    print()
    print("VOLUME")
    print(f"Volume signal:             {result.volume_signal}")
    print(f"Current volume:            {result.current_volume}")
    print(f"Average volume:            {result.average_volume}")
    print(f"Volume ratio:              {result.volume_ratio}")
    print(
        f"Price-volume relationship:"
        f" {result.price_volume_relationship}"
    )

    print()
    print("STRUCTURE / LEVELS")
    print(f"Swing high:                {result.swing_high}")
    print(f"Swing low:                 {result.swing_low}")
    print(f"Support:                   {result.support}")
    print(f"Resistance:                {result.resistance}")
    print(
        f"Distance to support:      "
        f"{result.distance_to_support_percent}"
    )
    print(
        f"Distance to resistance:   "
        f"{result.distance_to_resistance_percent}"
    )

    print()
    print("VOLATILITY")
    print(f"Volatility:                {result.volatility}")
    print(f"ATR:                       {result.atr}")
    print(f"Rolling volatility:        {result.rolling_volatility}")
    print(f"Recent range:              {result.recent_range_percent}")
    print(f"Volatility state:          {result.volatility_state}")

    print()
    print("Observations:")

    for observation in result.observations:
        print(f"  - {observation}")

    print()
    print("=" * 60)
    print("MARKET ANALYSIS TEST PASSED")
    print("=" * 60)
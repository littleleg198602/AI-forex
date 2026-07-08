"""Example London session breakout strategy."""

from __future__ import annotations

import pandas as pd

from strategies.base import BaseStrategy


class LondonBreakoutStrategy(BaseStrategy):
    name = "london_breakout"

    def __init__(self, lookback_bars: int = 12, start_hour_utc: int = 7, end_hour_utc: int = 11) -> None:
        self.lookback_bars = lookback_bars
        self.start_hour_utc = start_hour_utc
        self.end_hour_utc = end_hour_utc

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        data["range_high"] = data["high"].rolling(self.lookback_bars).max().shift(1)
        data["range_low"] = data["low"].rolling(self.lookback_bars).min().shift(1)
        return data

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = self.prepare_data(df)
        hours = data.index.hour if isinstance(data.index, pd.DatetimeIndex) else pd.Series(0, index=data.index)
        london_window = (hours >= self.start_hour_utc) & (hours <= self.end_hour_utc)
        data["signal"] = 0
        data.loc[london_window & (data["close"] > data["range_high"]), "signal"] = 1
        data.loc[london_window & (data["close"] < data["range_low"]), "signal"] = -1
        return data

    def get_parameters(self) -> dict[str, int]:
        return {
            "lookback_bars": self.lookback_bars,
            "start_hour_utc": self.start_hour_utc,
            "end_hour_utc": self.end_hour_utc,
        }

    def describe(self) -> str:
        return "Breakout strategy that trades range breaks during the London morning window."

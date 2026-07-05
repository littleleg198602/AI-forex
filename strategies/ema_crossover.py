"""Example EMA crossover trend-following strategy."""

from __future__ import annotations

import pandas as pd

from strategies.base import BaseStrategy


class EMACrossoverStrategy(BaseStrategy):
    name = "ema_crossover"

    def __init__(self, fast_period: int = 12, slow_period: int = 26) -> None:
        if fast_period >= slow_period:
            raise ValueError("fast_period must be lower than slow_period")
        self.fast_period = fast_period
        self.slow_period = slow_period

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        data["ema_fast"] = data["close"].ewm(span=self.fast_period, adjust=False).mean()
        data["ema_slow"] = data["close"].ewm(span=self.slow_period, adjust=False).mean()
        return data

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = self.prepare_data(df)
        data["signal"] = 0
        data.loc[data["ema_fast"] > data["ema_slow"], "signal"] = 1
        data.loc[data["ema_fast"] < data["ema_slow"], "signal"] = -1
        return data

    def get_parameters(self) -> dict[str, int]:
        return {"fast_period": self.fast_period, "slow_period": self.slow_period}

    def describe(self) -> str:
        return "Trend strategy that goes long when fast EMA is above slow EMA and short in the opposite case."

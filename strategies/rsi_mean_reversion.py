"""Example RSI mean-reversion strategy."""

from __future__ import annotations

import pandas as pd

from strategies.base import BaseStrategy


class RSIMeanReversionStrategy(BaseStrategy):
    name = "rsi_mean_reversion"

    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70) -> None:
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        delta = data["close"].diff()
        gain = delta.clip(lower=0).rolling(self.period).mean()
        loss = (-delta.clip(upper=0)).rolling(self.period).mean()
        rs = gain / loss.replace(0, pd.NA)
        data["rsi"] = 100 - (100 / (1 + rs))
        return data

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = self.prepare_data(df)
        data["signal"] = 0
        data.loc[data["rsi"] < self.oversold, "signal"] = 1
        data.loc[data["rsi"] > self.overbought, "signal"] = -1
        return data

    def get_parameters(self) -> dict[str, float]:
        return {"period": self.period, "oversold": self.oversold, "overbought": self.overbought}

    def describe(self) -> str:
        return "Mean-reversion strategy that buys oversold RSI and sells overbought RSI."

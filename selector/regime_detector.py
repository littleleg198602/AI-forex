"""Basic market regime detector placeholder."""

from __future__ import annotations

import pandas as pd


def detect_regime(df: pd.DataFrame, volatility_window: int = 20) -> str:
    volatility = df["close"].pct_change().rolling(volatility_window).std().iloc[-1]
    if pd.isna(volatility):
        return "unknown"
    return "high_volatility" if volatility > 0.005 else "normal"

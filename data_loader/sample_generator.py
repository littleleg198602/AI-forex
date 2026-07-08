"""Deterministic synthetic OHLCV generation for missing data demos."""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

TIMEFRAME_FREQ = {"M5": "5min", "M15": "15min", "M30": "30min", "H1": "1h", "H4": "4h"}
DEFAULT_ROWS = {"M5": 500, "M15": 400, "M30": 350, "H1": 300, "H4": 220}


def generate_sample_ohlcv(pair: str, timeframe: str, rows: int | None = None) -> pd.DataFrame:
    """Create deterministic synthetic data labeled as sample/synthetic by callers."""
    if timeframe not in TIMEFRAME_FREQ:
        raise ValueError(f"Unsupported timeframe for sample generation: {timeframe}")
    row_count = rows or DEFAULT_ROWS[timeframe]
    seed = int(hashlib.sha256(f"{pair}-{timeframe}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    index = pd.date_range("2024-01-01", periods=row_count, freq=TIMEFRAME_FREQ[timeframe], tz="UTC")
    base_price = 145.0 if pair.endswith("JPY") else 1.10
    pip = 0.01 if pair.endswith("JPY") else 0.0001
    trend = np.linspace(0, pip * 80, row_count)
    cycle = np.sin(np.linspace(0, 18, row_count)) * pip * 35
    noise = rng.normal(0, pip * 3, row_count).cumsum()
    close = base_price + trend + cycle + noise
    open_ = np.r_[close[0], close[:-1]]
    spread = np.maximum(np.abs(close - open_), pip * 4)
    high = np.maximum(open_, close) + spread * 0.6
    low = np.minimum(open_, close) - spread * 0.6
    volume = rng.integers(500, 2500, row_count)
    return pd.DataFrame({
        "datetime": index,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })

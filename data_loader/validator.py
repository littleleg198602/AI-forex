"""OHLCV data validation for research backtests."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = ["datetime", "open", "high", "low", "close", "volume"]
OHLC_COLUMNS = ["open", "high", "low", "close"]


class DataValidationError(ValueError):
    """Raised when OHLCV data is malformed or unsafe for backtesting."""


def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize an OHLCV DataFrame.

    The returned DataFrame is indexed by UTC-like datetimes and contains numeric
    ``open/high/low/close/volume`` columns. Validation fails loudly instead of
    silently repairing data, because bad data can create false strategy results.
    """
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise DataValidationError(f"Missing required columns: {missing}")
    if df.empty:
        raise DataValidationError("OHLCV data is empty")
    if df[REQUIRED_COLUMNS].isna().any().any():
        raise DataValidationError("OHLCV data contains missing values")

    data = df[REQUIRED_COLUMNS].copy()
    data["datetime"] = pd.to_datetime(data["datetime"], utc=True, errors="coerce")
    if data["datetime"].isna().any():
        raise DataValidationError("OHLCV data contains invalid datetime values")
    if data["datetime"].duplicated().any():
        raise DataValidationError("OHLCV data contains duplicated datetime values")
    if not data["datetime"].is_monotonic_increasing:
        raise DataValidationError("OHLCV datetime values must be sorted ascending")

    for column in [*OHLC_COLUMNS, "volume"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    if data[[*OHLC_COLUMNS, "volume"]].isna().any().any():
        raise DataValidationError("OHLCV data contains non-numeric price or volume values")
    if (data[OHLC_COLUMNS] <= 0).any().any():
        raise DataValidationError("OHLC prices must be positive")
    if (data["volume"] < 0).any():
        raise DataValidationError("Volume cannot be negative")
    if (data["high"] < data["low"]).any():
        raise DataValidationError("High price cannot be lower than low price")
    if ((data["open"] > data["high"]) | (data["open"] < data["low"])).any():
        raise DataValidationError("Open price must be inside high/low range")
    if ((data["close"] > data["high"]) | (data["close"] < data["low"])).any():
        raise DataValidationError("Close price must be inside high/low range")

    return data.set_index("datetime")

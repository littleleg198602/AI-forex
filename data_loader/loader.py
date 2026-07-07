"""CSV data loading for pair/timeframe research datasets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from data_loader.sample_generator import generate_sample_ohlcv
from data_loader.validator import validate_ohlcv


@dataclass(frozen=True)
class LoadedMarketData:
    pair: str
    timeframe: str
    data: pd.DataFrame
    data_source: str
    path: Path | None = None


def csv_path(data_dir: Path, pair: str, timeframe: str) -> Path:
    return data_dir / f"{pair}_{timeframe}.csv"


def load_ohlcv_csv(path: Path) -> pd.DataFrame:
    """Load and validate one OHLCV CSV file."""
    return validate_ohlcv(pd.read_csv(path))


def load_pair_timeframe(pair: str, timeframe: str, data_dir: Path, allow_sample: bool = True) -> LoadedMarketData:
    """Load CSV data or deterministic sample data for a pair/timeframe."""
    path = csv_path(data_dir, pair, timeframe)
    if path.exists():
        return LoadedMarketData(pair=pair, timeframe=timeframe, data=load_ohlcv_csv(path), data_source="csv", path=path)
    if not allow_sample:
        raise FileNotFoundError(f"Missing OHLCV CSV: {path}")
    sample = validate_ohlcv(generate_sample_ohlcv(pair, timeframe))
    return LoadedMarketData(pair=pair, timeframe=timeframe, data=sample, data_source="synthetic_sample", path=None)

import pandas as pd
import pytest

from data_loader.loader import load_ohlcv_csv
from data_loader.validator import DataValidationError, validate_ohlcv


def valid_frame():
    return pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=3, freq="h", tz="UTC"),
        "open": [1.0, 1.1, 1.2],
        "high": [1.2, 1.3, 1.4],
        "low": [0.9, 1.0, 1.1],
        "close": [1.1, 1.2, 1.3],
        "volume": [100, 110, 120],
    })


def test_load_valid_csv(tmp_path):
    path = tmp_path / "EURUSD_M15.csv"
    valid_frame().to_csv(path, index=False)
    data = load_ohlcv_csv(path)
    assert list(data.columns) == ["open", "high", "low", "close", "volume"]
    assert data.index.is_monotonic_increasing


def test_reject_csv_without_required_columns(tmp_path):
    path = tmp_path / "bad.csv"
    valid_frame().drop(columns=["volume"]).to_csv(path, index=False)
    with pytest.raises(DataValidationError, match="Missing required columns"):
        load_ohlcv_csv(path)


def test_reject_duplicate_datetime():
    data = valid_frame()
    data.loc[1, "datetime"] = data.loc[0, "datetime"]
    with pytest.raises(DataValidationError, match="duplicated datetime"):
        validate_ohlcv(data)


def test_reject_invalid_ohlc_values():
    data = valid_frame()
    data.loc[0, "high"] = 0.5
    with pytest.raises(DataValidationError, match="High price"):
        validate_ohlcv(data)

    data = valid_frame()
    data.loc[0, "open"] = 2.0
    with pytest.raises(DataValidationError, match="Open price"):
        validate_ohlcv(data)

from pathlib import Path

import pandas as pd

from scripts.run_backtest import resolve_dataset


def write_csv(path: Path) -> None:
    pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC"),
        "open": [1.0, 1.1, 1.2, 1.3, 1.4],
        "high": [1.1, 1.2, 1.3, 1.4, 1.5],
        "low": [0.9, 1.0, 1.1, 1.2, 1.3],
        "close": [1.05, 1.15, 1.25, 1.35, 1.45],
        "volume": [100] * 5,
    }).to_csv(path, index=False)


def test_csv_only_missing_does_not_generate_synthetic(tmp_path):
    dataset, coverage = resolve_dataset("EURUSD", "M15", tmp_path, "csv-only")
    assert dataset is None
    assert coverage["data_source"] == "missing"
    assert coverage["validation_status"] == "missing"


def test_synthetic_demo_marks_synthetic(tmp_path):
    dataset, coverage = resolve_dataset("EURUSD", "M15", tmp_path, "synthetic-demo")
    assert dataset is not None
    assert dataset.data_source == "synthetic_sample"
    assert coverage["data_source"] == "synthetic_sample"


def test_mixed_uses_csv_when_available(tmp_path):
    write_csv(tmp_path / "EURUSD_M15.csv")
    dataset, coverage = resolve_dataset("EURUSD", "M15", tmp_path, "mixed")
    assert dataset is not None
    assert dataset.data_source == "csv"
    assert coverage["data_source"] == "csv"


def test_mixed_missing_uses_synthetic(tmp_path):
    dataset, coverage = resolve_dataset("EURUSD", "M15", tmp_path, "mixed")
    assert dataset is not None
    assert dataset.data_source == "synthetic_sample"
    assert coverage["data_source"] == "synthetic_sample"

import pandas as pd

from scripts.generate_report import write_data_coverage


def test_data_coverage_report_contains_missing_csv_and_synthetic_statuses(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.generate_report.REPORTS", tmp_path)
    coverage = pd.DataFrame([
        {"pair": "EURUSD", "timeframe": "M15", "csv_exists": True, "start_date": "2024-01-01", "end_date": "2024-01-02", "candles": 10, "data_source": "csv", "validation_status": "valid", "message": "ok"},
        {"pair": "GBPUSD", "timeframe": "H1", "csv_exists": False, "start_date": "", "end_date": "", "candles": 0, "data_source": "missing", "validation_status": "missing", "message": "missing"},
        {"pair": "USDJPY", "timeframe": "M5", "csv_exists": False, "start_date": "2024-01-01", "end_date": "2024-01-02", "candles": 10, "data_source": "synthetic_sample", "validation_status": "valid", "message": "demo"},
    ])
    write_data_coverage(coverage)
    text = (tmp_path / "data_coverage.md").read_text()
    assert "csv" in text
    assert "missing" in text
    assert "synthetic_sample" in text

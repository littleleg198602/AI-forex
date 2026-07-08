from argparse import Namespace
from pathlib import Path

from scripts import export_mt5_history


class FakeMT5WithLatestBars:
    TIMEFRAME_M15 = 15

    def __init__(self):
        self.shutdown_called = False

    def initialize(self):
        return True

    def shutdown(self):
        self.shutdown_called = True

    def copy_rates_range(self, symbol, timeframe, date_from, date_to):
        return []

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        return [
            {"time": 1_700_000_000, "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.05, "tick_volume": 100},
        ]

    def last_error(self):
        return (4401, "history not found")


class FakeMT5WithoutLatestBars(FakeMT5WithLatestBars):
    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        return []


def make_args(tmp_path: Path) -> Namespace:
    return Namespace(
        pairs=["EURUSD"],
        timeframes=["M15"],
        date_from="2023-01-01",
        date_to="2023-02-01",
        output=str(tmp_path),
        overwrite=True,
        validate=True,
    )


def test_no_bars_diagnostic_reports_latest_bars_available(monkeypatch, tmp_path):
    fake = FakeMT5WithLatestBars()
    monkeypatch.setattr(export_mt5_history, "load_mt5_module", lambda: fake)
    report_path = tmp_path / "mt5_export_report.md"
    monkeypatch.setattr(export_mt5_history, "REPORT_PATH", report_path)

    summary = export_mt5_history.export_history(make_args(tmp_path))

    assert fake.shutdown_called
    assert summary["invalid"]
    report = report_path.read_text()
    assert "mt5_last_error" in report
    assert "latest_bars_available" in report
    assert "True" in report
    assert "history is missing for the requested date range" in report
    assert "Open the symbol and timeframe in MT5" in report


def test_no_bars_diagnostic_reports_no_latest_data(monkeypatch, tmp_path):
    monkeypatch.setattr(export_mt5_history, "load_mt5_module", lambda: FakeMT5WithoutLatestBars())
    report_path = tmp_path / "mt5_export_report.md"
    monkeypatch.setattr(export_mt5_history, "REPORT_PATH", report_path)

    export_mt5_history.export_history(make_args(tmp_path))

    report = report_path.read_text()
    assert "False" in report
    assert "MT5 has no available bars for this symbol/timeframe" in report
    assert "Confirm the symbol is visible in Market Watch" in report

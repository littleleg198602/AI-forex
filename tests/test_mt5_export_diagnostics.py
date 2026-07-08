from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

from scripts import export_mt5_history


def rate(time_value: int, price: float = 1.0) -> dict:
    return {"time": time_value, "open": price, "high": price + 0.1, "low": price - 0.1, "close": price + 0.05, "tick_volume": 100}


class FakeMT5MixedData:
    TIMEFRAME_M15 = 15
    TIMEFRAME_H1 = 60

    def __init__(self, m15_latest=True):
        self.shutdown_called = False
        self.m15_latest = m15_latest

    def initialize(self):
        return True

    def shutdown(self):
        self.shutdown_called = True

    def version(self):
        return (5, 0, 3900)

    def terminal_info(self):
        return SimpleNamespace(path="C:/MT5/terminal64.exe", company="MetaQuotes", name="Local Test Terminal")

    def account_info(self):
        return SimpleNamespace(login=123456, server="Demo-Server")

    def copy_rates_range(self, symbol, timeframe, date_from, date_to):
        if timeframe == self.TIMEFRAME_H1:
            return [rate(1_700_000_000), rate(1_700_003_600, 1.1)]
        return []

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        if timeframe == self.TIMEFRAME_M15 and not self.m15_latest:
            return []
        return [rate(1_700_010_000 + i * 900, 1 + i * 0.01) for i in range(10)]

    def last_error(self):
        return (4401, "history not found")


def make_args(tmp_path: Path, diagnose_only: bool = False) -> Namespace:
    return Namespace(
        pairs=["GBPUSD"],
        timeframes=["M15", "H1"],
        date_from="2026-06-30",
        date_to="2026-07-08",
        output=str(tmp_path),
        overwrite=True,
        validate=True,
        diagnose_only=diagnose_only,
    )


def test_h1_data_m15_no_range_but_latest_bars(monkeypatch, tmp_path):
    fake = FakeMT5MixedData(m15_latest=True)
    monkeypatch.setattr(export_mt5_history, "load_mt5_module", lambda: fake)
    report_path = tmp_path / "mt5_export_report.md"
    monkeypatch.setattr(export_mt5_history, "REPORT_PATH", report_path)

    summary = export_mt5_history.export_history(make_args(tmp_path))

    assert fake.shutdown_called
    assert summary["exported"]
    assert summary["invalid"]
    report = report_path.read_text()
    assert "terminal_path" in report
    assert "account_login" in report
    assert "mt5_last_error" in report
    assert "Latest bars are available, but requested date range returned no bars." in report
    assert "GBPUSD_H1.csv" in summary["exported"][0]


def test_h1_data_m15_no_latest_bars(monkeypatch, tmp_path):
    monkeypatch.setattr(export_mt5_history, "load_mt5_module", lambda: FakeMT5MixedData(m15_latest=False))
    report_path = tmp_path / "mt5_export_report.md"
    monkeypatch.setattr(export_mt5_history, "REPORT_PATH", report_path)

    export_mt5_history.export_history(make_args(tmp_path))

    report = report_path.read_text()
    assert "No latest bars available for this symbol/timeframe." in report
    assert "Confirm Python is connected to the expected MT5 terminal" in report


def test_diagnose_only_writes_report_but_no_csv(monkeypatch, tmp_path):
    monkeypatch.setattr(export_mt5_history, "load_mt5_module", lambda: FakeMT5MixedData(m15_latest=True))
    report_path = tmp_path / "mt5_export_report.md"
    monkeypatch.setattr(export_mt5_history, "REPORT_PATH", report_path)

    summary = export_mt5_history.export_history(make_args(tmp_path, diagnose_only=True))

    assert summary["diagnosed"]
    assert report_path.exists()
    assert not list(tmp_path.glob("*.csv"))


def test_export_script_has_no_order_placement_call():
    text = Path("scripts/export_mt5_history.py").read_text()
    forbidden = "order" + "_" + "send"
    assert forbidden not in text

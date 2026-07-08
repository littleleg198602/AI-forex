"""Export historical OHLCV data from a local MetaTrader 5 terminal.

This is a data-only utility. It reads historical bars from an already configured
local terminal and writes CSV files for research backtests. It does not store or
request credentials and it contains no market execution functionality.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from data_loader.loader import csv_path
from data_loader.validator import DataValidationError, validate_ohlcv

TIMEFRAME_NAMES = {
    "M5": "TIMEFRAME_M5",
    "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30",
    "H1": "TIMEFRAME_H1",
    "H4": "TIMEFRAME_H4",
}
REPORT_PATH = ROOT / "reports" / "mt5_export_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export historical MT5 OHLCV bars to research CSV files.")
    parser.add_argument("--pairs", nargs="+", required=True, help="Symbols to export, e.g. EURUSD GBPUSD USDJPY")
    parser.add_argument("--timeframes", nargs="+", required=True, choices=sorted(TIMEFRAME_NAMES), help="Timeframes to export")
    parser.add_argument("--from", dest="date_from", required=True, help="Start date YYYY-MM-DD, interpreted as UTC")
    parser.add_argument("--to", dest="date_to", required=True, help="End date YYYY-MM-DD, interpreted as UTC")
    parser.add_argument("--output", default="data/raw", help="Output directory for CSV files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing CSV files")
    parser.add_argument("--validate", action="store_true", help="Validate exported CSV files with the project validator")
    parser.add_argument("--diagnose-only", action="store_true", help="Only diagnose MT5 data availability; do not write OHLCV CSV files")
    return parser.parse_args()


def load_mt5_module() -> Any:
    if importlib.util.find_spec("MetaTrader5") is None:
        raise RuntimeError(
            "Optional dependency MetaTrader5 is not installed. Install it only on a machine with a local MT5 terminal, "
            "for example: python -m pip install MetaTrader5"
        )
    return importlib.import_module("MetaTrader5")


def parse_utc_date(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def timeframe_value(mt5: Any, timeframe: str) -> int:
    return int(getattr(mt5, TIMEFRAME_NAMES[timeframe]))


def rates_to_ohlcv(rates: Any) -> pd.DataFrame:
    data = pd.DataFrame(rates)
    if data.empty:
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])
    data["datetime"] = pd.to_datetime(data["time"], unit="s", utc=True)
    data["volume"] = data.get("tick_volume", data.get("real_volume", 0))
    return data[["datetime", "open", "high", "low", "close", "volume"]]


def terminal_diagnostics(mt5: Any) -> dict[str, Any]:
    terminal = mt5.terminal_info()
    account = mt5.account_info()
    info = {
        "mt5_version": mt5.version(),
        "terminal_path": getattr(terminal, "path", "") if terminal is not None else "",
        "terminal_company": getattr(terminal, "company", "") if terminal is not None else "",
        "terminal_name": getattr(terminal, "name", "") if terminal is not None else "",
        "account_login": getattr(account, "login", "") if account is not None else "",
        "account_server": getattr(account, "server", "") if account is not None else "",
        "connected": bool(account is not None),
    }
    print("MT5 runtime diagnostics")
    for key, value in info.items():
        print(f"{key}: {value}")
    return info


def latest_probe(mt5: Any, symbol: str, timeframe_code: int) -> tuple[pd.DataFrame, Any]:
    latest_rates = mt5.copy_rates_from_pos(symbol, timeframe_code, 0, 10)
    return rates_to_ohlcv(latest_rates), mt5.last_error()


def diagnose_row(
    mt5: Any,
    clean_pair: str,
    broker_symbol: str,
    timeframe: str,
    timeframe_code: int,
    date_from: datetime,
    date_to: datetime,
    range_data: pd.DataFrame,
) -> dict[str, Any]:
    range_last_error = mt5.last_error()
    probe_data, probe_last_error = latest_probe(mt5, broker_symbol, timeframe_code)
    latest_count = len(probe_data)
    if range_data.empty and latest_count:
        diagnosis = "Latest bars are available, but requested date range returned no bars."
        suggested_action = "Try a shorter/recent date range, then open the symbol/timeframe in MT5 and download deeper history."
    elif range_data.empty:
        diagnosis = "No latest bars available for this symbol/timeframe."
        suggested_action = "Confirm Python is connected to the expected MT5 terminal, verify Market Watch symbol/suffix, then open the chart/timeframe."
    else:
        diagnosis = f"Requested range returned {len(range_data)} bars."
        suggested_action = "Data is available; export can proceed unless diagnose-only is enabled."
    return {
        "clean_pair": clean_pair,
        "broker_symbol": broker_symbol,
        "timeframe": timeframe,
        "requested_from": date_from.isoformat(),
        "requested_to": date_to.isoformat(),
        "range_bars_count": len(range_data),
        "latest_probe_bars_count": latest_count,
        "latest_probe_first_time": probe_data["datetime"].iloc[0] if latest_count else "",
        "latest_probe_last_time": probe_data["datetime"].iloc[-1] if latest_count else "",
        "mt5_last_error": range_last_error if range_data.empty else probe_last_error,
        "diagnosis": diagnosis,
        "suggested_action": suggested_action,
    }


def print_no_bars_diagnostic(row: dict[str, Any]) -> None:
    print("\nNo bars returned by MT5 historical export.")
    print(f"pair: {row['clean_pair']}")
    print(f"broker symbol: {row['broker_symbol']}")
    print(f"timeframe: {row['timeframe']}")
    print(f"from/to: {row['requested_from']} -> {row['requested_to']}")
    print(f"mt5.last_error(): {row['mt5_last_error']}")
    print(f"latest_probe_bars_count: {row['latest_probe_bars_count']}")
    print(f"diagnosis: {row['diagnosis']}")
    print(f"suggested_action: {row['suggested_action']}")


def write_export_report(rows: list[dict[str, Any]], runtime_info: dict[str, Any], report_path: Path | None = None) -> None:
    report_path = report_path or REPORT_PATH
    report_path.parent.mkdir(exist_ok=True)
    lines = ["# MT5 Export Report", "", "Data-only historical export diagnostics. No trading actions are performed.", ""]
    lines.extend(["## Runtime diagnostics", "", pd.DataFrame([runtime_info]).to_markdown(index=False), ""])
    lines.append("## Pair/timeframe diagnostics")
    lines.append("")
    if rows:
        lines.append(pd.DataFrame(rows).to_markdown(index=False))
    else:
        lines.append("No export attempts recorded.")
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def export_history(args: argparse.Namespace) -> dict[str, list[str]]:
    mt5 = load_mt5_module()
    output_dir = Path(args.output)
    if not args.diagnose_only:
        output_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, list[str]] = {"exported": [], "skipped": [], "invalid": [], "diagnosed": []}
    report_rows: list[dict[str, Any]] = []
    date_from = parse_utc_date(args.date_from)
    date_to = parse_utc_date(args.date_to)
    if date_from >= date_to:
        raise ValueError("--from must be earlier than --to")

    if not mt5.initialize():
        raise RuntimeError("Could not initialize local MetaTrader 5 terminal. Open MT5 locally and try again.")
    runtime_info: dict[str, Any] = {}
    try:
        runtime_info = terminal_diagnostics(mt5)
        for pair in args.pairs:
            for timeframe in args.timeframes:
                symbol = pair
                path = csv_path(output_dir, pair, timeframe)
                label = f"{pair}_{timeframe}"
                timeframe_code = timeframe_value(mt5, timeframe)
                if path.exists() and not args.overwrite and not args.diagnose_only:
                    summary["skipped"].append(f"{label}: exists")
                    report_rows.append({
                        "clean_pair": pair,
                        "broker_symbol": symbol,
                        "timeframe": timeframe,
                        "requested_from": date_from.isoformat(),
                        "requested_to": date_to.isoformat(),
                        "range_bars_count": "",
                        "latest_probe_bars_count": "",
                        "latest_probe_first_time": "",
                        "latest_probe_last_time": "",
                        "mt5_last_error": "",
                        "diagnosis": "Output file exists and overwrite was not requested.",
                        "suggested_action": "Use --overwrite to replace the existing file.",
                    })
                    continue
                rates = mt5.copy_rates_range(symbol, timeframe_code, date_from, date_to)
                data = rates_to_ohlcv(rates)
                row = diagnose_row(mt5, pair, symbol, timeframe, timeframe_code, date_from, date_to, data)
                report_rows.append(row)
                if data.empty:
                    print_no_bars_diagnostic(row)
                    summary["invalid"].append(f"{label}: no bars returned; {row['diagnosis']}")
                    continue
                if args.diagnose_only:
                    summary["diagnosed"].append(f"{label}: {len(data)} range bars available")
                    continue
                data.to_csv(path, index=False)
                if args.validate:
                    try:
                        validate_ohlcv(pd.read_csv(path))
                    except DataValidationError as exc:
                        path.unlink(missing_ok=True)
                        summary["invalid"].append(f"{label}: validation failed: {exc}")
                        row["diagnosis"] = f"Exported file failed OHLCV validation: {exc}"
                        row["suggested_action"] = "Review the exported CSV and MT5 history quality before using it."
                        continue
                summary["exported"].append(str(path))
    finally:
        mt5.shutdown()
    write_export_report(report_rows, runtime_info)
    return summary


def main() -> None:
    args = parse_args()
    summary = export_history(args)
    print("MT5 historical data export summary")
    for key in ("exported", "skipped", "invalid", "diagnosed"):
        print(f"{key}: {len(summary[key])}")
        for item in summary[key]:
            print(f"  - {item}")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()

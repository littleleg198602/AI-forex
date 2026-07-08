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


def no_bars_diagnosis(mt5: Any, symbol: str, timeframe_code: int) -> tuple[bool, str, str]:
    latest_rates = mt5.copy_rates_from_pos(symbol, timeframe_code, 0, 10)
    latest_bars_available = not rates_to_ohlcv(latest_rates).empty
    if latest_bars_available:
        diagnosis = "Symbol/timeframe exists, but history is missing for the requested date range."
        suggested_action = "Open the symbol and timeframe in MT5, scroll back or use History Center to download the requested period."
    else:
        diagnosis = "MT5 has no available bars for this symbol/timeframe."
        suggested_action = "Confirm the symbol is visible in Market Watch, check broker suffixes, then open the chart/timeframe and download history."
    return latest_bars_available, diagnosis, suggested_action


def print_no_bars_diagnostic(row: dict[str, Any]) -> None:
    print("\nNo bars returned by MT5 historical export.")
    print(f"pair: {row['pair']}")
    print(f"broker symbol: {row['broker_symbol']}")
    print(f"timeframe: {row['timeframe']}")
    print(f"from/to: {row['date_from']} -> {row['date_to']}")
    print(f"mt5.last_error(): {row['mt5_last_error']}")
    print(f"latest_bars_available: {row['latest_bars_available']}")
    print(f"diagnosis: {row['diagnosis']}")
    print(f"suggested_action: {row['suggested_action']}")


def write_export_report(rows: list[dict[str, Any]], report_path: Path | None = None) -> None:
    report_path = report_path or REPORT_PATH
    report_path.parent.mkdir(exist_ok=True)
    lines = ["# MT5 Export Report", "", "Data-only historical export diagnostics. No trading actions are performed.", ""]
    if rows:
        lines.append(pd.DataFrame(rows).to_markdown(index=False))
    else:
        lines.append("No export attempts recorded.")
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def export_history(args: argparse.Namespace) -> dict[str, list[str]]:
    mt5 = load_mt5_module()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, list[str]] = {"exported": [], "skipped": [], "invalid": []}
    report_rows: list[dict[str, Any]] = []
    date_from = parse_utc_date(args.date_from)
    date_to = parse_utc_date(args.date_to)
    if date_from >= date_to:
        raise ValueError("--from must be earlier than --to")

    if not mt5.initialize():
        raise RuntimeError("Could not initialize local MetaTrader 5 terminal. Open MT5 locally and try again.")
    try:
        for pair in args.pairs:
            for timeframe in args.timeframes:
                symbol = pair
                path = csv_path(output_dir, pair, timeframe)
                label = f"{pair}_{timeframe}"
                timeframe_code = timeframe_value(mt5, timeframe)
                if path.exists() and not args.overwrite:
                    summary["skipped"].append(f"{label}: exists")
                    report_rows.append({
                        "pair": pair,
                        "broker_symbol": symbol,
                        "timeframe": timeframe,
                        "date_from": date_from.isoformat(),
                        "date_to": date_to.isoformat(),
                        "status": "skipped",
                        "mt5_last_error": "",
                        "latest_bars_available": "",
                        "diagnosis": "Output file exists and overwrite was not requested.",
                        "suggested_action": "Use --overwrite to replace the existing file.",
                    })
                    continue
                rates = mt5.copy_rates_range(symbol, timeframe_code, date_from, date_to)
                data = rates_to_ohlcv(rates)
                if data.empty:
                    last_error = mt5.last_error()
                    latest_available, diagnosis, suggested_action = no_bars_diagnosis(mt5, symbol, timeframe_code)
                    row = {
                        "pair": pair,
                        "broker_symbol": symbol,
                        "timeframe": timeframe,
                        "date_from": date_from.isoformat(),
                        "date_to": date_to.isoformat(),
                        "status": "no_bars",
                        "mt5_last_error": last_error,
                        "latest_bars_available": latest_available,
                        "diagnosis": diagnosis,
                        "suggested_action": suggested_action,
                    }
                    print_no_bars_diagnostic(row)
                    report_rows.append(row)
                    summary["invalid"].append(f"{label}: no bars returned; {diagnosis}")
                    continue
                data.to_csv(path, index=False)
                if args.validate:
                    try:
                        validate_ohlcv(pd.read_csv(path))
                    except DataValidationError as exc:
                        path.unlink(missing_ok=True)
                        summary["invalid"].append(f"{label}: validation failed: {exc}")
                        report_rows.append({
                            "pair": pair,
                            "broker_symbol": symbol,
                            "timeframe": timeframe,
                            "date_from": date_from.isoformat(),
                            "date_to": date_to.isoformat(),
                            "status": "failed_validation",
                            "mt5_last_error": "",
                            "latest_bars_available": "",
                            "diagnosis": f"Exported file failed OHLCV validation: {exc}",
                            "suggested_action": "Review the exported CSV and MT5 history quality before using it.",
                        })
                        continue
                summary["exported"].append(str(path))
                report_rows.append({
                    "pair": pair,
                    "broker_symbol": symbol,
                    "timeframe": timeframe,
                    "date_from": date_from.isoformat(),
                    "date_to": date_to.isoformat(),
                    "status": "exported",
                    "mt5_last_error": "",
                    "latest_bars_available": "",
                    "diagnosis": f"Exported {len(data)} bars.",
                    "suggested_action": "Run csv-only backtests after reviewing data coverage.",
                })
    finally:
        mt5.shutdown()
    write_export_report(report_rows)
    return summary


def main() -> None:
    args = parse_args()
    summary = export_history(args)
    print("MT5 historical data export summary")
    for key in ("exported", "skipped", "invalid"):
        print(f"{key}: {len(summary[key])}")
        for item in summary[key]:
            print(f"  - {item}")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()

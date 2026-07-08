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


def export_history(args: argparse.Namespace) -> dict[str, list[str]]:
    mt5 = load_mt5_module()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, list[str]] = {"exported": [], "skipped": [], "invalid": []}
    date_from = parse_utc_date(args.date_from)
    date_to = parse_utc_date(args.date_to)
    if date_from >= date_to:
        raise ValueError("--from must be earlier than --to")

    if not mt5.initialize():
        raise RuntimeError("Could not initialize local MetaTrader 5 terminal. Open MT5 locally and try again.")
    try:
        for pair in args.pairs:
            for timeframe in args.timeframes:
                path = csv_path(output_dir, pair, timeframe)
                label = f"{pair}_{timeframe}"
                if path.exists() and not args.overwrite:
                    summary["skipped"].append(f"{label}: exists")
                    continue
                rates = mt5.copy_rates_range(pair, timeframe_value(mt5, timeframe), date_from, date_to)
                data = rates_to_ohlcv(rates)
                if data.empty:
                    summary["invalid"].append(f"{label}: no bars returned")
                    continue
                data.to_csv(path, index=False)
                if args.validate:
                    try:
                        validate_ohlcv(pd.read_csv(path))
                    except DataValidationError as exc:
                        path.unlink(missing_ok=True)
                        summary["invalid"].append(f"{label}: validation failed: {exc}")
                        continue
                summary["exported"].append(str(path))
    finally:
        mt5.shutdown()
    return summary


def main() -> None:
    args = parse_args()
    summary = export_history(args)
    print("MT5 historical data export summary")
    for key in ("exported", "skipped", "invalid"):
        print(f"{key}: {len(summary[key])}")
        for item in summary[key]:
            print(f"  - {item}")


if __name__ == "__main__":
    main()

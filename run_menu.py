"""Local interactive launcher for safe forex-ai-lab research workflows."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "local_launcher.yaml"
PYTHON = sys.executable
FORBIDDEN_TERMS = [
    "order" + "_" + "send",
    "API" + "_" + "KEY",
    "SEC" + "RET",
    "PASS" + "WORD",
    "TO" + "KEN",
    "live" + " " + "executor",
    "broker" + " " + "executor",
]
SCAN_SUFFIXES = {".py"}
SKIP_SCAN_PARTS = {".git", ".venv", "venv", "__pycache__", "tests"}


def pause() -> None:
    input("\nPress Enter to continue...")


def print_command(command: list[str]) -> None:
    print("\n$ " + " ".join(command))


def run_command(command: list[str]) -> int:
    print_command(command)
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        print(f"\nCommand failed with exit code {completed.returncode}.")
    return completed.returncode


def install_dependencies() -> None:
    run_command([PYTHON, "-m", "pip", "install", "-r", "requirements.txt"])
    print("\nMetaTrader5 is optional and is needed only for historical data export from a local MT5 terminal.")
    answer = input("Install optional MetaTrader5 package now? [y/N]: ").strip().lower()
    if answer == "y":
        run_command([PYTHON, "-m", "pip", "install", "MetaTrader5"])


def run_tests() -> None:
    run_command([PYTHON, "-m", "pytest"])


def mt5_notice() -> None:
    print("\nBefore exporting MT5 historical data:")
    print("- Open MetaTrader 5.")
    print("- Sign in to an account, demo is fine.")
    print("- Check that symbols are visible in Market Watch.")
    print("- If your symbol names have suffixes such as EURUSD.r, adjust local config/symbol_map.yaml workflow manually.")
    print("- Export is data-only and does not trade.")


def export_mt5_small() -> None:
    mt5_notice()
    run_command([
        PYTHON,
        "scripts/export_mt5_history.py",
        "--pairs", "EURUSD", "GBPUSD",
        "--timeframes", "M15", "H1",
        "--from", "2026-06-30",
        "--to", "2026-07-08",
        "--output", "data/raw",
        "--validate",
    ])


def export_mt5_medium() -> None:
    mt5_notice()
    run_command([
        PYTHON,
        "scripts/export_mt5_history.py",
        "--pairs", "EURUSD", "GBPUSD",
        "--timeframes", "M15", "H1",
        "--from", "2025-01-01",
        "--to", "2026-07-08",
        "--output", "data/raw",
        "--validate",
        "--overwrite",
    ])


def load_launcher_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing launcher config: {CONFIG_PATH}")
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def diagnose_mt5_data() -> None:
    mt5_notice()
    run_command([
        PYTHON,
        "scripts/export_mt5_history.py",
        "--pairs", "EURUSD", "GBPUSD",
        "--timeframes", "M15", "H1",
        "--from", "2026-06-30",
        "--to", "2026-07-08",
        "--output", "data/raw",
        "--diagnose-only",
    ])


def export_mt5_full() -> None:
    mt5_notice()
    print("Full export may fail for lower timeframes if MT5 has not downloaded deep history. Run small test first.")
    config = load_launcher_config()
    command = [
        PYTHON,
        "scripts/export_mt5_history.py",
        "--pairs", *config["default_pairs"],
        "--timeframes", *config["default_timeframes"],
        "--from", str(config["default_from"]),
        "--to", str(config["default_to"]),
        "--output", str(config["output_dir"]),
        "--validate",
        "--overwrite",
    ]
    run_command(command)


def run_csv_backtest() -> None:
    run_command([PYTHON, "scripts/run_backtest.py", "--data-mode", "csv-only"])


def run_synthetic_backtest() -> None:
    run_command([PYTHON, "scripts/run_backtest.py", "--data-mode", "synthetic-demo"])


def generate_reports() -> None:
    run_command([PYTHON, "scripts/generate_report.py"])


def open_folder(folder: str) -> None:
    path = ROOT / folder
    path.mkdir(exist_ok=True)
    if os.name == "nt":
        run_command(["explorer", str(path)])
    else:
        print(f"Open this folder manually: {path}")


def iter_scanned_files() -> Iterable[Path]:
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if any(part in SKIP_SCAN_PARTS for part in path.parts):
            continue
        yield path


def safety_scan() -> int:
    print("\nSafety scan: checking Python code outside tests and docs.")
    warnings: list[str] = []
    for path in iter_scanned_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for term in FORBIDDEN_TERMS:
            if term in text:
                warnings.append(f"{path.relative_to(ROOT)} contains forbidden term: {term}")
    if warnings:
        print("\nWARNING: Potentially unsafe terms found. Nothing was changed automatically.")
        for warning in warnings:
            print(f"- {warning}")
        return 1
    print("No forbidden execution or sensitive markers found in scanned Python code.")
    return 0


def full_local_research_run() -> None:
    steps = [
        ("Run tests", lambda: run_command([PYTHON, "-m", "pytest"])),
        ("Run CSV-only backtest", lambda: run_command([PYTHON, "scripts/run_backtest.py", "--data-mode", "csv-only"])),
        ("Generate reports", lambda: run_command([PYTHON, "scripts/generate_report.py"])),
        ("Safety scan", safety_scan),
    ]
    for label, step in steps:
        print(f"\n=== {label} ===")
        code = step()
        if code != 0:
            print(f"Stopping full run after failed step: {label}")
            return


def show_menu() -> None:
    print("""
FOREX AI LAB - LOCAL LAUNCHER

1 - Install / update dependencies
2 - Run tests
3 - Export MT5 history - small test
4 - Export MT5 history - full configured set
5 - Run CSV-only backtest
6 - Run synthetic demo backtest
7 - Generate reports
8 - Full local research run
9 - Open reports folder
10 - Open results folder
11 - Safety scan
12 - Diagnose MT5 data availability
13 - Export MT5 history - medium test
0 - Exit
""")


def menu_loop() -> None:
    actions = {
        "1": install_dependencies,
        "2": run_tests,
        "3": export_mt5_small,
        "4": export_mt5_full,
        "5": run_csv_backtest,
        "6": run_synthetic_backtest,
        "7": generate_reports,
        "8": full_local_research_run,
        "9": lambda: open_folder("reports"),
        "10": lambda: open_folder("results"),
        "11": safety_scan,
        "12": diagnose_mt5_data,
        "13": export_mt5_medium,
    }
    while True:
        show_menu()
        choice = input("Choose an option: ").strip()
        if choice == "0":
            print("Goodbye.")
            return
        action = actions.get(choice)
        if action is None:
            print("Unknown option.")
            pause()
            continue
        action()
        pause()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local launcher menu for forex-ai-lab.")
    parser.add_argument("--safety-scan", action="store_true", help="Run safety scan and exit")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.safety_scan:
        return safety_scan()
    menu_loop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

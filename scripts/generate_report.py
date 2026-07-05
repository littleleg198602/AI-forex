"""Generate a markdown report from the latest CSV backtest output."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    summary_path = ROOT / "results" / "summary.csv"
    report_path = ROOT / "reports" / "latest_report.md"
    if not summary_path.exists():
        raise FileNotFoundError("Run scripts/run_backtest.py before generating a report")
    summary = pd.read_csv(summary_path)
    lines = ["# Latest forex-ai-lab Backtest Report", "", "Backtest-only research output. Not live-trading advice.", "", summary.to_markdown(index=False), ""]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()

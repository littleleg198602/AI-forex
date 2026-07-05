"""Generate markdown reports from the latest strategy scoreboard and coverage file."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError

ROOT = Path(__file__).resolve().parents[1]
SCOREBOARD = ROOT / "results" / "strategy_scoreboard.csv"
COVERAGE = ROOT / "results" / "data_coverage.csv"
REPORTS = ROOT / "reports"

SCOREBOARD_COLUMNS = [
    "strategy", "pair", "timeframe", "data_source", "trades", "total_return",
    "profit_factor", "max_drawdown", "expectancy", "sharpe_ratio", "wf_pass_rate", "status",
]


def load_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except EmptyDataError:
        return pd.DataFrame()


def coverage_counts(coverage: pd.DataFrame) -> dict[str, int]:
    if coverage.empty:
        return {"csv": 0, "synthetic_sample": 0, "missing": 0, "failed_validation": 0}
    coverage = coverage.fillna("")
    return {
        "csv": int((coverage["data_source"] == "csv").sum()),
        "synthetic_sample": int((coverage["data_source"] == "synthetic_sample").sum()),
        "missing": int((coverage["validation_status"] == "missing").sum()),
        "failed_validation": int((coverage["validation_status"] == "failed_validation").sum()),
    }


def write_latest_report(scoreboard: pd.DataFrame, coverage: pd.DataFrame | None = None) -> None:
    coverage = coverage if coverage is not None else load_csv_or_empty(COVERAGE)
    counts = coverage_counts(coverage)
    lines = [
        "# Latest forex-ai-lab Backtest Report", "",
        "Backtest-only research output. Not live-trading advice.", "",
        "> WARNING: Rows with `synthetic_sample` data are deterministic demo data and cannot justify paper trading.", "",
        "## Data coverage summary", "",
        f"- csv: {counts['csv']}",
        f"- synthetic_sample: {counts['synthetic_sample']}",
        f"- missing: {counts['missing']}",
        f"- failed_validation: {counts['failed_validation']}", "",
        "## Strategy scoreboard", "",
    ]
    if scoreboard.empty:
        lines.append("No strategy rows were generated. In `csv-only` mode this usually means CSV files are missing or failed validation.")
    else:
        lines.append(scoreboard[SCOREBOARD_COLUMNS].to_markdown(index=False))
    lines.append("")
    (REPORTS / "latest_report.md").write_text("\n".join(lines), encoding="utf-8")


def write_pair_matrix(scoreboard: pd.DataFrame) -> None:
    lines = [
        "# Pair and Timeframe Matrix", "",
        "All tables are research-only. `data_source=csv` marks real local CSV input; `synthetic_sample` rows are demo data and cannot make a strategy paper-ready.", "",
    ]
    if scoreboard.empty:
        lines.extend(["No evaluated strategy rows. Review `reports/data_coverage.md` for missing or invalid data.", ""])
        (REPORTS / "pair_matrix.md").write_text("\n".join(lines), encoding="utf-8")
        return
    ranked = scoreboard.sort_values(["status", "data_source", "profit_factor", "sharpe_ratio"], ascending=[True, True, False, False])
    non_reject = scoreboard[scoreboard["status"] != "reject"].copy()
    best_by_pair = non_reject.sort_values(["pair", "data_source", "profit_factor", "sharpe_ratio"], ascending=[True, True, False, False]).groupby("pair").head(1)
    best_by_tf = non_reject.sort_values(["timeframe", "data_source", "profit_factor", "sharpe_ratio"], ascending=[True, True, False, False]).groupby("timeframe").head(1)
    rejected = scoreboard[scoreboard["status"] == "reject"][["strategy", "pair", "timeframe", "data_source", "trades", "profit_factor", "max_drawdown", "sharpe_ratio"]]
    watchlist = scoreboard[scoreboard["status"] == "watchlist"]
    paper = scoreboard[scoreboard["status"] == "paper_candidate"]
    lines.extend([
        "## Best strategy by pair", "", (best_by_pair.to_markdown(index=False) if not best_by_pair.empty else "No non-rejected strategies."), "",
        "## Best strategy by timeframe", "", (best_by_tf.to_markdown(index=False) if not best_by_tf.empty else "No non-rejected strategies."), "",
        "## Strategies to reject by performance", "", (rejected.to_markdown(index=False) if not rejected.empty else "No performance-rejected strategies."), "",
        "## Watchlist", "", (watchlist.to_markdown(index=False) if not watchlist.empty else "No watchlist strategies."), "",
        "## Paper-test candidates", "", (paper.to_markdown(index=False) if not paper.empty else "No paper candidates. Real historical CSV data and walk-forward validation are required."), "",
        "## Full ranking snapshot", "", ranked.head(25).to_markdown(index=False), "",
    ])
    (REPORTS / "pair_matrix.md").write_text("\n".join(lines), encoding="utf-8")


def write_rejected_strategies(scoreboard: pd.DataFrame, coverage: pd.DataFrame | None = None) -> None:
    coverage = coverage if coverage is not None else load_csv_or_empty(COVERAGE)
    lines = ["# Rejected and Skipped Strategies", "", "Performance rejects are evaluated strategy rows. Data skips are pair/timeframe combinations that were not evaluated because data was missing or failed validation.", ""]
    if scoreboard.empty:
        lines.extend(["## Rejected by performance", "", "No evaluated strategy rows.", ""])
    else:
        rejected = scoreboard[scoreboard["status"] == "reject"].copy()
        columns = ["strategy", "pair", "timeframe", "data_source", "trades", "profit_factor", "max_drawdown", "expectancy", "sharpe_ratio", "wf_pass_rate"]
        lines.extend(["## Rejected by performance", "", rejected[columns].to_markdown(index=False) if not rejected.empty else "No performance-rejected strategies.", ""])
    if coverage.empty:
        skipped = pd.DataFrame()
    else:
        skipped = coverage[coverage["validation_status"].isin(["missing", "failed_validation"])]
    display_skipped = skipped.fillna("") if not skipped.empty else skipped
    lines.extend(["## Skipped due to missing or invalid data", "", display_skipped.to_markdown(index=False) if not display_skipped.empty else "No data skips.", ""])
    (REPORTS / "rejected_strategies.md").write_text("\n".join(lines), encoding="utf-8")


def write_data_coverage(coverage: pd.DataFrame) -> None:
    lines = [
        "# Data Coverage", "",
        "Expected pair × timeframe combinations and their data availability. `validation_status=valid` means the dataset passed OHLCV validation; `missing` and `failed_validation` rows were not backtested in csv-only mode.", "",
    ]
    display_coverage = coverage.fillna("") if not coverage.empty else coverage
    lines.append(display_coverage.to_markdown(index=False) if not display_coverage.empty else "No coverage file found. Run `scripts/run_backtest.py` first.")
    lines.append("")
    (REPORTS / "data_coverage.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    scoreboard = load_csv_or_empty(SCOREBOARD)
    coverage = load_csv_or_empty(COVERAGE)
    write_latest_report(scoreboard, coverage)
    write_pair_matrix(scoreboard)
    write_rejected_strategies(scoreboard, coverage)
    write_data_coverage(coverage)
    print(f"Wrote reports to {REPORTS}")


if __name__ == "__main__":
    main()

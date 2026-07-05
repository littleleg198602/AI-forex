"""Generate markdown reports from the latest strategy scoreboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCOREBOARD = ROOT / "results" / "strategy_scoreboard.csv"
REPORTS = ROOT / "reports"


def load_scoreboard() -> pd.DataFrame:
    if not SCOREBOARD.exists():
        raise FileNotFoundError("Run scripts/run_backtest.py before generating reports")
    return pd.read_csv(SCOREBOARD)


def write_latest_report(scoreboard: pd.DataFrame) -> None:
    columns = [
        "strategy", "pair", "timeframe", "data_source", "trades", "total_return",
        "profit_factor", "max_drawdown", "expectancy", "sharpe_ratio", "wf_pass_rate", "status",
    ]
    sample_note = "\n> WARNING: Rows with `synthetic_sample` data are deterministic demo data and cannot justify paper trading.\n"
    lines = ["# Latest forex-ai-lab Backtest Report", "", "Backtest-only research output. Not live-trading advice.", sample_note, scoreboard[columns].to_markdown(index=False), ""]
    (REPORTS / "latest_report.md").write_text("\n".join(lines), encoding="utf-8")


def write_pair_matrix(scoreboard: pd.DataFrame) -> None:
    ranked = scoreboard.sort_values(["status", "profit_factor", "sharpe_ratio"], ascending=[True, False, False])
    non_reject = scoreboard[scoreboard["status"] != "reject"].copy()
    best_by_pair = non_reject.sort_values(["pair", "profit_factor", "sharpe_ratio"], ascending=[True, False, False]).groupby("pair").head(1)
    best_by_tf = non_reject.sort_values(["timeframe", "profit_factor", "sharpe_ratio"], ascending=[True, False, False]).groupby("timeframe").head(1)
    rejected = scoreboard[scoreboard["status"] == "reject"][["strategy", "pair", "timeframe", "data_source", "trades", "profit_factor", "max_drawdown", "sharpe_ratio"]]
    watchlist = scoreboard[scoreboard["status"] == "watchlist"]
    paper = scoreboard[scoreboard["status"] == "paper_candidate"]
    lines = [
        "# Pair and Timeframe Matrix", "",
        "All tables are research-only. `synthetic_sample` rows are demo data and cannot make a strategy paper-ready.", "",
        "## Best strategy by pair", "", (best_by_pair.to_markdown(index=False) if not best_by_pair.empty else "No non-rejected strategies."), "",
        "## Best strategy by timeframe", "", (best_by_tf.to_markdown(index=False) if not best_by_tf.empty else "No non-rejected strategies."), "",
        "## Strategies to reject", "", (rejected.to_markdown(index=False) if not rejected.empty else "No rejected strategies."), "",
        "## Watchlist", "", (watchlist.to_markdown(index=False) if not watchlist.empty else "No watchlist strategies."), "",
        "## Paper-test candidates", "", (paper.to_markdown(index=False) if not paper.empty else "No paper candidates. Real historical CSV data and walk-forward validation are required."), "",
        "## Full ranking snapshot", "", ranked.head(25).to_markdown(index=False), "",
    ]
    (REPORTS / "pair_matrix.md").write_text("\n".join(lines), encoding="utf-8")


def write_rejected_strategies(scoreboard: pd.DataFrame) -> None:
    rejected = scoreboard[scoreboard["status"] == "reject"].copy()
    columns = ["strategy", "pair", "timeframe", "data_source", "trades", "profit_factor", "max_drawdown", "expectancy", "sharpe_ratio", "wf_pass_rate"]
    lines = ["# Rejected Strategies", "", "Rejected rows failed sample-size, profit-factor, drawdown, Sharpe, expectancy, or walk-forward requirements.", "", rejected[columns].to_markdown(index=False) if not rejected.empty else "No rejected strategies.", ""]
    (REPORTS / "rejected_strategies.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    scoreboard = load_scoreboard()
    write_latest_report(scoreboard)
    write_pair_matrix(scoreboard)
    write_rejected_strategies(scoreboard)
    print(f"Wrote reports to {REPORTS}")


if __name__ == "__main__":
    main()

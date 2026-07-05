"""Run all sample strategies across configured pairs and timeframes."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import yaml

from backtester.engine import BacktestEngine
from backtester.metrics import calculate_metrics
from backtester.walk_forward import run_walk_forward
from data_loader.loader import LoadedMarketData, load_pair_timeframe
from selector.strategy_ranker import classify_status
from strategies.registry import load_all_strategies


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def costs_for_pair(costs_config: dict[str, Any], pair: str) -> dict[str, float]:
    costs = dict(costs_config.get("default", {}))
    costs.update(costs_config.get("pairs", {}).get(pair, {}))
    return costs


def evaluate_dataset(dataset: LoadedMarketData, costs: dict[str, float], risk: dict[str, float]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    results_dir = ROOT / "results"
    initial_balance = float(risk["initial_balance"])
    for strategy in load_all_strategies():
        result = BacktestEngine(strategy, dataset.data, costs, risk, pair=dataset.pair).run()
        metrics = calculate_metrics(result.trades, result.equity_curve, initial_balance)
        wf = run_walk_forward(strategy, dataset.data, costs, risk, pair=dataset.pair)
        row = {
            "strategy": strategy.name,
            "pair": dataset.pair,
            "timeframe": dataset.timeframe,
            "data_source": dataset.data_source,
            "start_date": dataset.data.index.min(),
            "end_date": dataset.data.index.max(),
            "trades": metrics["trade_count"],
            "total_return": metrics["total_return"],
            "profit_factor": metrics["profit_factor"],
            "max_drawdown": metrics["max_drawdown"],
            "win_rate": metrics["win_rate"],
            "expectancy": metrics["expectancy"],
            "sharpe_ratio": metrics["sharpe_ratio"],
            "exposure_time": metrics["exposure_time"],
            "wf_segments": wf.segments,
            "wf_passed_segments": wf.passed_segments,
            "wf_pass_rate": wf.pass_rate,
            "wf_avg_test_return": wf.avg_test_return,
            "wf_max_test_drawdown": wf.max_test_drawdown,
        }
        status_input = {**metrics, **row}
        row["status"] = classify_status(status_input, risk, dataset.data_source)
        rows.append(row)
        safe_prefix = f"{strategy.name}_{dataset.pair}_{dataset.timeframe}"
        result.equity_curve.to_csv(results_dir / f"{safe_prefix}_equity.csv")
        pd.DataFrame(result.trades).to_csv(results_dir / f"{safe_prefix}_trades.csv", index=False)
    return rows


def main() -> None:
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    pairs = load_yaml(ROOT / "config" / "pairs.yaml")["pairs"]
    timeframes = load_yaml(ROOT / "config" / "timeframes.yaml")["timeframes"]
    costs_config = load_yaml(ROOT / "config" / "broker_costs.yaml")
    risk_config = load_yaml(ROOT / "config" / "risk.yaml")

    rows: list[dict[str, Any]] = []
    for pair in pairs:
        for timeframe in timeframes:
            dataset = load_pair_timeframe(pair, timeframe, ROOT / "data" / "raw", allow_sample=True)
            rows.extend(evaluate_dataset(dataset, costs_for_pair(costs_config, pair), risk_config))

    scoreboard = pd.DataFrame(rows)
    scoreboard.to_csv(results_dir / "strategy_scoreboard.csv", index=False)
    # Backward-compatible summary for older report consumers.
    scoreboard.to_csv(results_dir / "summary.csv", index=False)
    (results_dir / "strategy_scoreboard.json").write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {len(scoreboard)} rows to {results_dir / 'strategy_scoreboard.csv'}")
    if (scoreboard["data_source"] == "synthetic_sample").any():
        print("WARNING: One or more datasets are synthetic_sample and are not suitable for paper_candidate status.")


if __name__ == "__main__":
    main()

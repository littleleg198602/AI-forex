"""Run all registered strategies across configured pairs and timeframes."""

from __future__ import annotations

import argparse
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
from data_loader.loader import LoadedMarketData, csv_path, load_pair_timeframe
from data_loader.sample_generator import generate_sample_ohlcv
from data_loader.validator import DataValidationError, validate_ohlcv
from selector.strategy_ranker import classify_status
from strategies.registry import load_all_strategies

DATA_MODES = ("csv-only", "synthetic-demo", "mixed")
SCOREBOARD_COLUMNS = ["strategy", "pair", "timeframe", "data_source", "start_date", "end_date", "trades", "total_return", "profit_factor", "max_drawdown", "win_rate", "expectancy", "sharpe_ratio", "exposure_time", "wf_segments", "wf_passed_segments", "wf_pass_rate", "wf_avg_test_return", "wf_max_test_drawdown", "status"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run research-only forex backtests.")
    parser.add_argument(
        "--data-mode",
        choices=DATA_MODES,
        default="csv-only",
        help="csv-only skips missing CSV files; synthetic-demo uses only demo data; mixed uses CSV then synthetic fallback.",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def costs_for_pair(costs_config: dict[str, Any], pair: str) -> dict[str, float]:
    costs = dict(costs_config.get("default", {}))
    costs.update(costs_config.get("pairs", {}).get(pair, {}))
    return costs


def coverage_row(
    pair: str,
    timeframe: str,
    data_source: str,
    validation_status: str,
    csv_exists: bool,
    data: pd.DataFrame | None = None,
    message: str = "",
) -> dict[str, Any]:
    return {
        "pair": pair,
        "timeframe": timeframe,
        "csv_exists": csv_exists,
        "start_date": data.index.min() if data is not None and not data.empty else "",
        "end_date": data.index.max() if data is not None and not data.empty else "",
        "candles": len(data) if data is not None else 0,
        "data_source": data_source,
        "validation_status": validation_status,
        "message": message,
    }


def resolve_dataset(pair: str, timeframe: str, data_dir: Path, data_mode: str) -> tuple[LoadedMarketData | None, dict[str, Any]]:
    path = csv_path(data_dir, pair, timeframe)
    csv_exists = path.exists()
    try:
        if data_mode == "synthetic-demo":
            data = validate_ohlcv(generate_sample_ohlcv(pair, timeframe))
            dataset = LoadedMarketData(pair=pair, timeframe=timeframe, data=data, data_source="synthetic_sample", path=None)
            return dataset, coverage_row(pair, timeframe, "synthetic_sample", "valid", csv_exists, data, "synthetic demo data")
        if csv_exists:
            dataset = load_pair_timeframe(pair, timeframe, data_dir, allow_sample=False)
            return dataset, coverage_row(pair, timeframe, "csv", "valid", True, dataset.data, str(path))
        if data_mode == "mixed":
            dataset = load_pair_timeframe(pair, timeframe, data_dir, allow_sample=True)
            return dataset, coverage_row(pair, timeframe, "synthetic_sample", "valid", False, dataset.data, "missing CSV; synthetic fallback")
        return None, coverage_row(pair, timeframe, "missing", "missing", False, None, "missing CSV in csv-only mode")
    except (DataValidationError, ValueError) as exc:
        return None, coverage_row(pair, timeframe, "csv", "failed_validation", csv_exists, None, str(exc))


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
        row["status"] = classify_status({**metrics, **row}, risk, dataset.data_source)
        rows.append(row)
        safe_prefix = f"{strategy.name}_{dataset.pair}_{dataset.timeframe}"
        result.equity_curve.to_csv(results_dir / f"{safe_prefix}_equity.csv")
        pd.DataFrame(result.trades).to_csv(results_dir / f"{safe_prefix}_trades.csv", index=False)
    return rows


def main() -> None:
    args = parse_args()
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    pairs = load_yaml(ROOT / "config" / "pairs.yaml")["pairs"]
    timeframes = load_yaml(ROOT / "config" / "timeframes.yaml")["timeframes"]
    costs_config = load_yaml(ROOT / "config" / "broker_costs.yaml")
    risk_config = load_yaml(ROOT / "config" / "risk.yaml")

    rows: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for pair in pairs:
        for timeframe in timeframes:
            dataset, coverage_item = resolve_dataset(pair, timeframe, ROOT / "data" / "raw", args.data_mode)
            coverage.append(coverage_item)
            if dataset is None:
                continue
            rows.extend(evaluate_dataset(dataset, costs_for_pair(costs_config, pair), risk_config))

    scoreboard = pd.DataFrame(rows, columns=SCOREBOARD_COLUMNS)
    coverage_df = pd.DataFrame(coverage)
    scoreboard.to_csv(results_dir / "strategy_scoreboard.csv", index=False)
    scoreboard.to_csv(results_dir / "summary.csv", index=False)
    coverage_df.to_csv(results_dir / "data_coverage.csv", index=False)
    (results_dir / "strategy_scoreboard.json").write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    print(f"Data mode: {args.data_mode}")
    print(f"Wrote {len(scoreboard)} strategy rows to {results_dir / 'strategy_scoreboard.csv'}")
    print(f"Wrote {len(coverage_df)} coverage rows to {results_dir / 'data_coverage.csv'}")
    missing_count = int((coverage_df["validation_status"] == "missing").sum()) if not coverage_df.empty else 0
    failed_count = int((coverage_df["validation_status"] == "failed_validation").sum()) if not coverage_df.empty else 0
    synthetic_count = int((coverage_df["data_source"] == "synthetic_sample").sum()) if not coverage_df.empty else 0
    if missing_count or failed_count or synthetic_count:
        print(f"Coverage warning: missing={missing_count}, failed_validation={failed_count}, synthetic_sample={synthetic_count}")


if __name__ == "__main__":
    main()

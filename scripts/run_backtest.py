"""Run all sample strategies on deterministic example OHLCV data."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import yaml

from backtester.engine import BacktestEngine
from backtester.metrics import calculate_metrics
from strategies.registry import load_all_strategies


def make_sample_data(rows: int = 300) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=rows, freq="h", tz="UTC")
    base = 1.10 + np.sin(np.linspace(0, 18, rows)) * 0.004 + np.linspace(0, 0.01, rows)
    close = base + np.cos(np.linspace(0, 40, rows)) * 0.001
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum(open_, close) + 0.0007
    low = np.minimum(open_, close) - 0.0007
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": 1000}, index=index)


def main() -> None:
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    costs_config = yaml.safe_load((ROOT / "config" / "broker_costs.yaml").read_text())
    risk_config = yaml.safe_load((ROOT / "config" / "risk.yaml").read_text())
    costs = costs_config["pairs"].get("EURUSD", costs_config["default"])
    data = make_sample_data()
    rows = []
    all_trades = []
    for strategy in load_all_strategies():
        result = BacktestEngine(strategy, data, costs, risk_config, pair="EURUSD").run()
        metrics = calculate_metrics(result.trades, result.equity_curve, float(risk_config["initial_balance"]))
        rows.append({"strategy": strategy.name, **metrics})
        all_trades.extend(result.trades)
        result.equity_curve.to_csv(results_dir / f"{strategy.name}_equity.csv")
    pd.DataFrame(rows).to_csv(results_dir / "summary.csv", index=False)
    pd.DataFrame(all_trades).to_csv(results_dir / "trades.csv", index=False)
    (results_dir / "summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} strategy summaries to {results_dir / 'summary.csv'}")


if __name__ == "__main__":
    main()

from pathlib import Path

import pandas as pd

from data_loader.loader import load_pair_timeframe
from scripts.run_backtest import costs_for_pair, evaluate_dataset


def write_csv(path: Path) -> None:
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=80, freq="h", tz="UTC"),
        "open": [1.0 + i * 0.001 for i in range(80)],
        "high": [1.01 + i * 0.001 for i in range(80)],
        "low": [0.99 + i * 0.001 for i in range(80)],
        "close": [1.005 + i * 0.001 for i in range(80)],
        "volume": [1000] * 80,
    })
    df.to_csv(path, index=False)


def test_multi_pair_backtest_rows_include_scoreboard_fields(tmp_path):
    write_csv(tmp_path / "EURUSD_H1.csv")
    dataset = load_pair_timeframe("EURUSD", "H1", tmp_path, allow_sample=False)
    rows = evaluate_dataset(
        dataset,
        costs_for_pair({"default": {"spread_pips": 1, "commission_per_lot": 7, "slippage_pips": 0.2}}, "EURUSD"),
        {"initial_balance": 10000, "position_size_lots": 0.1, "max_drawdown_limit": 0.2},
    )
    assert len(rows) == 3
    required = {"strategy", "pair", "timeframe", "data_source", "trades", "wf_segments", "wf_pass_rate", "status"}
    assert required <= rows[0].keys()

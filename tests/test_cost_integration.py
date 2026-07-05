import pandas as pd

from backtester.engine import BacktestEngine
from strategies.base import BaseStrategy


class FlipStrategy(BaseStrategy):
    name = "flip_strategy"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        data["signal"] = [0, 1, -1, 0]
        return data

    def get_parameters(self) -> dict:
        return {}

    def describe(self) -> str:
        return "Test flip strategy."


def test_closed_trades_include_spread_commission_and_slippage_costs():
    data = pd.DataFrame(
        {
            "open": [1.0, 1.0, 1.01, 1.02],
            "high": [1.0, 1.0, 1.01, 1.02],
            "low": [1.0, 1.0, 1.01, 1.02],
            "close": [1.0, 1.0, 1.01, 1.02],
        },
        index=pd.date_range("2024-01-01", periods=4, freq="h", tz="UTC"),
    )
    result = BacktestEngine(
        FlipStrategy(),
        data,
        {"spread_pips": 1.0, "commission_per_lot": 7.0, "slippage_pips": 0.2},
        {"initial_balance": 10000, "position_size_lots": 0.1},
    ).run()
    assert result.trades
    assert all(trade["cost"] > 0 for trade in result.trades)
    assert all(trade["pnl"] == trade["gross_pnl"] - trade["cost"] for trade in result.trades)

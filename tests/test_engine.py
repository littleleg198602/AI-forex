import pandas as pd

from backtester.engine import BacktestEngine
from strategies.base import BaseStrategy


class OneBarDelayedLongStrategy(BaseStrategy):
    name = "one_bar_delayed_long"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        data["signal"] = [0, 1, 1]
        return data

    def get_parameters(self) -> dict:
        return {}

    def describe(self) -> str:
        return "Test strategy."


def test_engine_executes_previous_signal_on_next_open_to_avoid_lookahead():
    data = pd.DataFrame(
        {
            "open": [1.0, 2.0, 3.0],
            "high": [1.0, 2.0, 3.0],
            "low": [1.0, 2.0, 3.0],
            "close": [1.0, 2.0, 3.0],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="h", tz="UTC"),
    )
    result = BacktestEngine(
        OneBarDelayedLongStrategy(),
        data,
        {"spread_pips": 0, "commission_per_lot": 0, "slippage_pips": 0},
        {"initial_balance": 10000, "position_size_lots": 0.1},
    ).run()
    assert result.trades[0]["entry_time"] == data.index[2]
    assert result.trades[0]["entry_price"] == 3.0


def test_engine_rejects_missing_cost_fields():
    data = pd.DataFrame({"open": [1], "high": [1], "low": [1], "close": [1]})
    try:
        BacktestEngine(OneBarDelayedLongStrategy(), data, {"spread_pips": 1}, {"initial_balance": 10000})
    except ValueError as exc:
        assert "Missing required cost fields" in str(exc)
    else:
        raise AssertionError("Expected missing cost configuration to fail")

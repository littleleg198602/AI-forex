import pandas as pd

from strategies.base import BaseStrategy
from strategies.registry import load_all_strategies


def sample_data():
    index = pd.date_range("2024-01-01", periods=60, freq="h", tz="UTC")
    return pd.DataFrame({"open": 1.0, "high": 1.01, "low": 0.99, "close": [1 + i * 0.0001 for i in range(60)], "volume": 100}, index=index)


def test_all_strategies_implement_interface():
    for strategy in load_all_strategies():
        assert isinstance(strategy, BaseStrategy)
        signals = strategy.generate_signals(sample_data())
        assert "signal" in signals.columns
        assert isinstance(strategy.get_parameters(), dict)
        assert strategy.describe()

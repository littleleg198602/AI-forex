import pandas as pd

from backtester.metrics import calculate_metrics


def test_metrics_include_required_risk_fields():
    trades = [{"pnl": 100}, {"pnl": -50}, {"pnl": 25}]
    equity = pd.DataFrame({"equity": [10000, 10100, 10050, 10075], "position": [0, 1, 1, 0]})
    metrics = calculate_metrics(trades, equity, 10000)
    expected = {"total_return", "profit_factor", "max_drawdown", "win_rate", "trade_count", "average_trade", "expectancy", "sharpe_ratio", "exposure_time"}
    assert expected <= set(metrics)
    assert metrics["trade_count"] == 3

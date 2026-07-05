"""Performance and risk metrics for strategy research."""

from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_metrics(trades: list[dict], equity_curve: pd.DataFrame, initial_balance: float) -> dict[str, float]:
    """Calculate required return and risk metrics from trades and an equity curve."""
    pnl = pd.Series([trade["pnl"] for trade in trades], dtype="float64")
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    final_equity = float(equity_curve["equity"].iloc[-1]) if not equity_curve.empty else initial_balance
    total_return = (final_equity - initial_balance) / initial_balance
    gross_profit = wins.sum()
    gross_loss = abs(losses.sum())
    returns = equity_curve["equity"].pct_change().dropna() if not equity_curve.empty else pd.Series(dtype="float64")
    running_max = equity_curve["equity"].cummax() if not equity_curve.empty else pd.Series(dtype="float64")
    drawdown = (equity_curve["equity"] - running_max) / running_max if not equity_curve.empty else pd.Series(dtype="float64")
    exposure = float((equity_curve["position"] != 0).mean()) if not equity_curve.empty and "position" in equity_curve else 0.0
    return {
        "total_return": float(total_return),
        "profit_factor": float(gross_profit / gross_loss) if gross_loss else float("inf") if gross_profit else 0.0,
        "max_drawdown": float(drawdown.min()) if not drawdown.empty else 0.0,
        "win_rate": float((pnl > 0).mean()) if len(pnl) else 0.0,
        "trade_count": int(len(pnl)),
        "average_trade": float(pnl.mean()) if len(pnl) else 0.0,
        "expectancy": float((wins.mean() if len(wins) else 0) * ((pnl > 0).mean() if len(pnl) else 0) - (abs(losses.mean()) if len(losses) else 0) * ((pnl < 0).mean() if len(pnl) else 0)),
        "sharpe_ratio": float(np.sqrt(252) * returns.mean() / returns.std()) if len(returns) > 1 and returns.std() else 0.0,
        "exposure_time": exposure,
    }

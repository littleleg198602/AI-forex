"""Rank strategies by risk-aware metrics, not profit alone."""

from __future__ import annotations


def rank_strategy(metrics: dict[str, float]) -> float:
    """Return a conservative score that penalizes drawdown and low sample size."""
    trade_count = metrics.get("trade_count", 0.0)
    sample_penalty = 0.5 if trade_count < 30 else 1.0
    profit_factor = min(metrics.get("profit_factor", 0.0), 5.0)
    drawdown_penalty = abs(metrics.get("max_drawdown", 0.0)) * 10
    return sample_penalty * (
        profit_factor
        + metrics.get("sharpe_ratio", 0.0)
        + metrics.get("total_return", 0.0)
        - drawdown_penalty
    )

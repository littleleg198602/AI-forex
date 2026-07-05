"""Rank strategies by risk-aware metrics, not profit alone."""

from __future__ import annotations


def rank_strategy(metrics: dict[str, float]) -> float:
    return (
        metrics.get("profit_factor", 0.0)
        + metrics.get("sharpe_ratio", 0.0)
        + metrics.get("total_return", 0.0)
        + metrics.get("max_drawdown", 0.0)
    )

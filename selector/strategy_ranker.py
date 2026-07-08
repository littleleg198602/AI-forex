"""Rank and classify strategies by risk-aware metrics, not profit alone."""

from __future__ import annotations


def rank_strategy(metrics: dict[str, float]) -> float:
    """Return a conservative score that penalizes drawdown and low sample size."""
    trade_count = metrics.get("trade_count", metrics.get("trades", 0.0))
    sample_penalty = 0.5 if trade_count < 30 else 1.0
    profit_factor = min(metrics.get("profit_factor", 0.0), 5.0)
    drawdown_penalty = abs(metrics.get("max_drawdown", 0.0)) * 10
    return sample_penalty * (
        profit_factor
        + metrics.get("sharpe_ratio", 0.0)
        + metrics.get("total_return", 0.0)
        - drawdown_penalty
    )


def classify_status(metrics: dict[str, float], risk: dict[str, float], data_source: str) -> str:
    """Classify strategy research status using conservative rules."""
    trades = int(metrics.get("trade_count", metrics.get("trades", 0)))
    max_drawdown_limit = float(risk.get("max_drawdown_limit", 0.20))
    if trades < 30:
        return "reject"
    if metrics.get("profit_factor", 0.0) < 1.1:
        return "reject"
    if abs(metrics.get("max_drawdown", 0.0)) > max_drawdown_limit:
        return "reject"
    if metrics.get("sharpe_ratio", 0.0) < 0:
        return "reject"
    wf_segments = int(metrics.get("wf_segments", 0))
    wf_passed_segments = int(metrics.get("wf_passed_segments", 0))
    wf_pass_rate = float(metrics.get("wf_pass_rate", 0.0))
    if wf_segments == 0 or wf_pass_rate <= 0:
        return "reject"
    if metrics.get("expectancy", 0.0) <= 0:
        return "watchlist"
    if data_source != "csv":
        return "watchlist"
    # Be intentionally strict: one lucky passing segment should never create a
    # paper candidate. Require a majority pass rate and at least two passing
    # test windows before paper review.
    if wf_pass_rate < 0.67 or wf_passed_segments < 2:
        return "watchlist"
    return "paper_candidate"

"""Walk-forward validation helpers.

Segments are chronological and never train on data that occurs after test data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from backtester.engine import BacktestEngine
from backtester.metrics import calculate_metrics
from strategies.base import BaseStrategy


@dataclass(frozen=True)
class WalkForwardSplit:
    segment: int
    train: pd.DataFrame
    test: pd.DataFrame


@dataclass(frozen=True)
class WalkForwardSummary:
    segments: int
    passed_segments: int
    pass_rate: float
    avg_test_return: float
    max_test_drawdown: float
    segment_results: list[dict[str, Any]]


def split_walk_forward(df: pd.DataFrame, segments: int = 3, train_fraction: float = 0.6) -> list[WalkForwardSplit]:
    """Split data into chronological train/test windows without look-ahead bias."""
    if segments <= 0:
        raise ValueError("segments must be positive")
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    if len(df) < segments * 4:
        return []

    ordered = df.sort_index()
    base_size = len(ordered) // segments
    remainder = len(ordered) % segments
    windows: list[pd.DataFrame] = []
    start = 0
    for segment_index in range(segments):
        stop = start + base_size + (1 if segment_index < remainder else 0)
        window = ordered.iloc[start:stop].copy()
        if len(window) >= 4:
            windows.append(window)
        start = stop

    splits: list[WalkForwardSplit] = []
    for index, window in enumerate(windows, start=1):
        split_at = int(len(window) * train_fraction)
        if split_at <= 0 or split_at >= len(window):
            continue
        train = window.iloc[:split_at].copy()
        test = window.iloc[split_at:].copy()
        if train.index.max() >= test.index.min():
            raise ValueError("Walk-forward split would leak future data")
        splits.append(WalkForwardSplit(segment=index, train=train, test=test))
    return splits


def run_walk_forward(
    strategy: BaseStrategy,
    data: pd.DataFrame,
    costs: dict[str, float],
    risk: dict[str, float],
    pair: str,
    segments: int = 3,
    train_fraction: float = 0.6,
    min_profit_factor: float = 1.1,
) -> WalkForwardSummary:
    """Evaluate strategy stability over chronological test segments."""
    segment_results: list[dict[str, Any]] = []
    for split in split_walk_forward(data, segments=segments, train_fraction=train_fraction):
        # Train data is intentionally reserved for future model selection; sample
        # strategies currently have fixed parameters, so only test metrics are run.
        _ = split.train
        result = BacktestEngine(strategy, split.test, costs, risk, pair=pair).run()
        metrics = calculate_metrics(result.trades, result.equity_curve, float(risk["initial_balance"]))
        passed = bool(
            metrics["trade_count"] > 0
            and metrics["profit_factor"] >= min_profit_factor
            and metrics["expectancy"] > 0
            and metrics["max_drawdown"] >= -float(risk.get("max_drawdown_limit", 1.0))
        )
        segment_results.append({
            "segment": split.segment,
            "test_start": split.test.index.min(),
            "test_end": split.test.index.max(),
            "test_return": metrics["total_return"],
            "test_drawdown": metrics["max_drawdown"],
            "test_trades": metrics["trade_count"],
            "passed": passed,
        })

    segment_count = len(segment_results)
    passed_segments = sum(1 for item in segment_results if item["passed"])
    returns = [item["test_return"] for item in segment_results]
    drawdowns = [item["test_drawdown"] for item in segment_results]
    return WalkForwardSummary(
        segments=segment_count,
        passed_segments=passed_segments,
        pass_rate=passed_segments / segment_count if segment_count else 0.0,
        avg_test_return=float(sum(returns) / segment_count) if segment_count else 0.0,
        max_test_drawdown=float(min(drawdowns)) if drawdowns else 0.0,
        segment_results=segment_results,
    )

"""Simple vector-assisted event backtest engine for OHLCV data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from backtester.costs import apply_cost_to_pnl, calculate_round_turn_cost, pip_size
from strategies.base import BaseStrategy


@dataclass
class BacktestResult:
    trades: list[dict[str, Any]]
    equity_curve: pd.DataFrame


class BacktestEngine:
    """Backtest a single strategy on one OHLCV DataFrame with explicit costs."""

    def __init__(self, strategy: BaseStrategy, data: pd.DataFrame, costs: dict[str, float], risk: dict[str, float], pair: str = "EURUSD") -> None:
        self.strategy = strategy
        self.data = data.sort_index().copy()
        self.costs = costs
        self.risk = risk
        self.pair = pair

    def run(self) -> BacktestResult:
        required = {"open", "high", "low", "close"}
        missing = required - set(self.data.columns)
        if missing:
            raise ValueError(f"Missing OHLC columns: {sorted(missing)}")

        signals = self.strategy.generate_signals(self.data).dropna(subset=["close"])
        initial_balance = float(self.risk.get("initial_balance", 10_000.0))
        lots = float(self.risk.get("position_size_lots", 0.1))
        equity = initial_balance
        position = 0
        entry_price = 0.0
        entry_time = None
        trades: list[dict[str, Any]] = []
        equity_points = []

        for timestamp, row in signals.iterrows():
            signal = int(row.get("signal", 0))
            close = float(row["close"])
            if position and signal != position:
                gross_pnl = (close - entry_price) * position * 100_000 * lots
                if self.pair.endswith("JPY"):
                    gross_pnl = gross_pnl / max(close, pip_size(self.pair))
                cost = calculate_round_turn_cost(
                    close,
                    self.pair,
                    lots,
                    float(self.costs.get("spread_pips", 0)),
                    float(self.costs.get("commission_per_lot", 0)),
                    float(self.costs.get("slippage_pips", 0)),
                )
                pnl = apply_cost_to_pnl(gross_pnl, cost)
                equity += pnl
                trades.append({
                    "strategy": self.strategy.name,
                    "pair": self.pair,
                    "entry_time": entry_time,
                    "exit_time": timestamp,
                    "side": "long" if position == 1 else "short",
                    "entry_price": entry_price,
                    "exit_price": close,
                    "gross_pnl": gross_pnl,
                    "cost": cost,
                    "pnl": pnl,
                    "return_pct": pnl / initial_balance,
                })
                position = 0
            if signal in (1, -1) and position == 0:
                position = signal
                entry_price = close
                entry_time = timestamp
            unrealized = (close - entry_price) * position * 100_000 * lots if position else 0.0
            equity_points.append({"timestamp": timestamp, "equity": equity + unrealized, "position": position})

        equity_curve = pd.DataFrame(equity_points).set_index("timestamp") if equity_points else pd.DataFrame(columns=["equity", "position"])
        return BacktestResult(trades=trades, equity_curve=equity_curve)

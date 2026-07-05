"""Simple event backtest engine for OHLCV data.

Signals are assumed to be known only after a bar closes. To avoid look-ahead
bias, orders are executed on the next bar open using the previous bar's signal.
"""

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
        self._validate_costs()

    def _validate_costs(self) -> None:
        required = ("spread_pips", "commission_per_lot", "slippage_pips")
        missing = [key for key in required if key not in self.costs]
        if missing:
            raise ValueError(f"Missing required cost fields: {missing}")
        negative = [key for key in required if float(self.costs[key]) < 0]
        if negative:
            raise ValueError(f"Cost fields cannot be negative: {negative}")

    def _gross_pnl(self, entry_price: float, exit_price: float, position: int, lots: float) -> float:
        gross_pnl = (exit_price - entry_price) * position * 100_000 * lots
        if self.pair.endswith("JPY"):
            gross_pnl = gross_pnl / max(exit_price, pip_size(self.pair))
        return float(gross_pnl)

    def _trade_cost(self, exit_price: float, lots: float) -> float:
        return calculate_round_turn_cost(
            exit_price,
            self.pair,
            lots,
            float(self.costs["spread_pips"]),
            float(self.costs["commission_per_lot"]),
            float(self.costs["slippage_pips"]),
        )

    def _close_trade(
        self,
        trades: list[dict[str, Any]],
        position: int,
        entry_price: float,
        entry_time: Any,
        exit_price: float,
        exit_time: Any,
        lots: float,
        initial_balance: float,
    ) -> float:
        gross_pnl = self._gross_pnl(entry_price, exit_price, position, lots)
        cost = self._trade_cost(exit_price, lots)
        pnl = apply_cost_to_pnl(gross_pnl, cost)
        trades.append({
            "strategy": self.strategy.name,
            "pair": self.pair,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "side": "long" if position == 1 else "short",
            "entry_price": entry_price,
            "exit_price": exit_price,
            "gross_pnl": gross_pnl,
            "cost": cost,
            "pnl": pnl,
            "return_pct": pnl / initial_balance,
        })
        return pnl

    def run(self) -> BacktestResult:
        required = {"open", "high", "low", "close"}
        missing = required - set(self.data.columns)
        if missing:
            raise ValueError(f"Missing OHLC columns: {sorted(missing)}")

        signals = self.strategy.generate_signals(self.data).dropna(subset=["open", "close"]).copy()
        initial_balance = float(self.risk.get("initial_balance", 10_000.0))
        lots = float(self.risk.get("position_size_lots", 0.1))
        if initial_balance <= 0:
            raise ValueError("initial_balance must be positive")
        if lots <= 0:
            raise ValueError("position_size_lots must be positive")

        equity = initial_balance
        position = 0
        entry_price = 0.0
        entry_time = None
        previous_signal = 0
        trades: list[dict[str, Any]] = []
        equity_points = []

        for timestamp, row in signals.iterrows():
            execution_signal = previous_signal
            open_price = float(row["open"])
            close_price = float(row["close"])

            if position and execution_signal != position:
                equity += self._close_trade(
                    trades,
                    position,
                    entry_price,
                    entry_time,
                    open_price,
                    timestamp,
                    lots,
                    initial_balance,
                )
                position = 0

            if execution_signal in (1, -1) and position == 0:
                position = execution_signal
                entry_price = open_price
                entry_time = timestamp

            unrealized = self._gross_pnl(entry_price, close_price, position, lots) if position else 0.0
            equity_points.append({"timestamp": timestamp, "equity": equity + unrealized, "position": position})
            previous_signal = int(row.get("signal", 0))

        if position and len(signals):
            final_timestamp = signals.index[-1]
            final_close = float(signals.iloc[-1]["close"])
            equity += self._close_trade(
                trades,
                position,
                entry_price,
                entry_time,
                final_close,
                final_timestamp,
                lots,
                initial_balance,
            )
            equity_points.append({"timestamp": final_timestamp, "equity": equity, "position": 0})

        equity_curve = pd.DataFrame(equity_points).set_index("timestamp") if equity_points else pd.DataFrame(columns=["equity", "position"])
        return BacktestResult(trades=trades, equity_curve=equity_curve)

"""Trading cost helpers for backtests."""

from __future__ import annotations

PIP_SIZE_BY_JPY = 0.01
DEFAULT_PIP_SIZE = 0.0001


def pip_size(pair: str = "EURUSD") -> float:
    """Return pip size for a forex pair."""
    return PIP_SIZE_BY_JPY if pair.endswith("JPY") else DEFAULT_PIP_SIZE


def calculate_round_turn_cost(
    price: float,
    pair: str,
    lots: float,
    spread_pips: float,
    commission_per_lot: float,
    slippage_pips: float,
) -> float:
    """Estimate full trade cost in account currency.

    The model includes spread, entry+exit slippage, and round-turn commission.
    It is intentionally conservative for research and not broker-specific.
    """
    units = 100_000 * lots
    pip_value = units * pip_size(pair)
    market_cost = (spread_pips + 2 * slippage_pips) * pip_value
    commission = commission_per_lot * lots
    return float(market_cost + commission)


def apply_cost_to_pnl(gross_pnl: float, cost: float) -> float:
    """Subtract costs from gross PnL."""
    return float(gross_pnl - cost)

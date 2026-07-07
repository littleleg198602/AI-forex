"""Registry of available research strategies."""

from __future__ import annotations

from strategies.base import BaseStrategy
from strategies.ema_crossover import EMACrossoverStrategy
from strategies.london_breakout import LondonBreakoutStrategy
from strategies.rsi_mean_reversion import RSIMeanReversionStrategy

STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {
    EMACrossoverStrategy.name: EMACrossoverStrategy,
    RSIMeanReversionStrategy.name: RSIMeanReversionStrategy,
    LondonBreakoutStrategy.name: LondonBreakoutStrategy,
}


def load_all_strategies() -> list[BaseStrategy]:
    """Instantiate all registered strategies with default parameters."""
    return [strategy_class() for strategy_class in STRATEGY_REGISTRY.values()]


def get_strategy(name: str) -> BaseStrategy:
    """Instantiate a registered strategy by name."""
    if name not in STRATEGY_REGISTRY:
        raise KeyError(f"Unknown strategy: {name}")
    return STRATEGY_REGISTRY[name]()

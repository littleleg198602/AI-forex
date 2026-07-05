"""Common strategy interface used by every research strategy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class BaseStrategy(ABC):
    """Abstract base class for all backtest-only forex strategies.

    Implementations must return a DataFrame containing a ``signal`` column where
    ``1`` means long, ``-1`` means short, and ``0`` means flat/no position.
    """

    name: str = "base_strategy"

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a copy of input OHLCV data with indicators added."""
        return df.copy()

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals from prepared OHLCV data."""

    @abstractmethod
    def get_parameters(self) -> dict[str, Any]:
        """Return serializable strategy parameters."""

    @abstractmethod
    def describe(self) -> str:
        """Return a human-readable strategy description."""

"""Placeholder helpers for future walk-forward validation."""

from __future__ import annotations

import pandas as pd


def split_walk_forward(df: pd.DataFrame, train_fraction: float = 0.7) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_at = int(len(df) * train_fraction)
    return df.iloc[:split_at].copy(), df.iloc[split_at:].copy()

import pandas as pd

from backtester.walk_forward import split_walk_forward


def test_walk_forward_split_has_no_lookahead_bias():
    df = pd.DataFrame(
        {"open": range(60), "high": range(60), "low": range(60), "close": range(60)},
        index=pd.date_range("2024-01-01", periods=60, freq="h", tz="UTC"),
    )
    splits = split_walk_forward(df, segments=3, train_fraction=0.6)
    assert len(splits) == 3
    for split in splits:
        assert split.train.index.max() < split.test.index.min()

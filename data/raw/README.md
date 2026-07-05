# Raw OHLCV data

Place real historical OHLCV CSV files here for research backtests.

Expected filename convention:

```text
EURUSD_M15.csv
GBPUSD_H1.csv
USDJPY_M5.csv
```

Required CSV columns:

```text
datetime,open,high,low,close,volume
```

Use clear timestamps readable by pandas, preferably UTC ISO timestamps. Large real historical datasets should not be committed to GitHub. Keep only this README and `.gitkeep` in git unless a tiny test fixture is explicitly needed.

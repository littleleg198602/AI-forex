# Data Import

`forex-ai-lab` is research/backtest-only. Data import tools may read historical prices, but they must never place trades, store broker credentials, or automate account execution.

## Manual CSV import

Put historical OHLCV CSV files into `data/raw/` using the existing filename convention:

```text
data/raw/EURUSD_M15.csv
data/raw/GBPUSD_H1.csv
data/raw/USDJPY_M5.csv
```

Required columns:

```text
datetime,open,high,low,close,volume
```

Timestamps should be unambiguous and preferably UTC. The loader validates columns, non-empty data, unique sorted datetime, missing values, positive prices, high/low consistency, and open/close inside high/low.

## Backtest data modes

Use CSV-only mode for real research:

```bash
python scripts/run_backtest.py --data-mode csv-only
```

Use synthetic demo mode only to prove the pipeline runs:

```bash
python scripts/run_backtest.py --data-mode synthetic-demo
```

Use mixed mode when you want CSV where available and explicit synthetic fallback elsewhere:

```bash
python scripts/run_backtest.py --data-mode mixed
```

Reports show `data_source` as `csv`, `synthetic_sample`, or `missing`, and `reports/data_coverage.md` lists every expected pair/timeframe combination.

## Optional MetaTrader 5 historical export

`MetaTrader5` is optional and is not listed in `requirements.txt`, because it is platform-specific and usually unavailable in Linux CI. Install it only on a local machine with MetaTrader 5 already configured:

```bash
python -m pip install MetaTrader5
```

Export historical bars:

```bash
python scripts/export_mt5_history.py --pairs EURUSD GBPUSD --timeframes M15 H1 --from 2023-01-01 --to 2026-07-05 --output data/raw --validate
```

The exporter is data-only. It reads historical bars from the local terminal and writes CSV files. It does not ask for login, password, server, API key, or account secrets, and it does not contain trading-order functionality.

## Why sample data is not enough

Synthetic/sample data is deterministic demo data. It is useful for testing the code path, but it must never decide paper/live readiness. `paper_candidate` requires real local CSV data plus risk, sample-size, and walk-forward checks.

## Why large real data is not committed

Historical OHLCV datasets can be large, licensed, or broker-specific. Keep large real CSV files out of GitHub and store them in local or approved data storage. The repository tracks `data/raw/README.md` and `.gitkeep`, not large data dumps.

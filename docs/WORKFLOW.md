# Research Workflow

1. **Data import**: add real historical OHLCV CSV files to `data/raw/` manually or export historical bars with the optional data-only MT5 exporter.
2. **Prepare data**: use `<PAIR>_<TIMEFRAME>.csv` filenames and required `datetime,open,high,low,close,volume` columns.
3. **Data validation**: validate required columns, sorted unique datetimes, positive OHLC values, high/low consistency, and missing values before backtesting.
4. **Data coverage review**: review `reports/data_coverage.md` so every strategy result has a known source (`csv`, `synthetic_sample`, `missing`, or `failed_validation`).
5. **Add a strategy**: implement `BaseStrategy`, register it in `strategies/registry.py`, and add tests.
6. **Backtest**: run the strategy against prepared OHLCV data with spread, commission, and slippage enabled.
7. **Walk-forward validation**: evaluate chronological train/test segments without using future data.
8. **Report**: generate CSV and Markdown reports in `results/` and `reports/`.
9. **Quality review**: check for implementation bugs, overfitting, unrealistic fills, missing costs, and unsafe risk assumptions.
10. **Paper candidate**: only after enough trades, real historical CSV data, sufficient data coverage, acceptable drawdown, positive expectancy, and walk-forward validation can a strategy be marked as a paper candidate.
11. **Stable**: stable status requires manual approval and fresh backtests. Stable does not mean live-ready.

Before evaluating any strategy, the data source must be explicit and reviewed. No strategy may be marked `paper_candidate` using only synthetic/sample data.

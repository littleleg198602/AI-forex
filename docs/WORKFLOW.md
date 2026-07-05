# Research Workflow

1. **Prepare data**: place historical OHLCV CSV files in `data/raw/` using `<PAIR>_<TIMEFRAME>.csv` names.
2. **Data validation**: validate required columns, sorted unique datetimes, positive OHLC values, high/low consistency, and missing values before backtesting.
3. **Add a strategy**: implement `BaseStrategy`, register it in `strategies/registry.py`, and add tests.
4. **Backtest**: run the strategy against prepared OHLCV data with spread, commission, and slippage enabled.
5. **Walk-forward validation**: evaluate chronological train/test segments without using future data.
6. **Report**: generate CSV and Markdown reports in `results/` and `reports/`.
7. **Quality review**: check for implementation bugs, overfitting, unrealistic fills, missing costs, and unsafe risk assumptions.
8. **Paper candidate**: only after enough trades, real historical CSV data, acceptable drawdown, positive expectancy, and walk-forward validation can a strategy be marked as a paper candidate.
9. **Stable**: stable status requires manual approval and fresh backtests. Stable does not mean live-ready.

No strategy may be marked `paper_candidate` using only synthetic/sample data.

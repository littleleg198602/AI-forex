# Research Workflow

1. **Add a strategy**: implement `BaseStrategy`, register it in `strategies/registry.py`, and add tests.
2. **Backtest**: run the strategy against prepared OHLCV data with spread, commission, and slippage enabled.
3. **Report**: generate CSV and Markdown reports in `results/` and `reports/`.
4. **Quality review**: check for implementation bugs, overfitting, unrealistic fills, and unsafe risk assumptions.
5. **Paper candidate**: only after multiple robust tests can a strategy be marked as a paper candidate.
6. **Stable**: stable status requires manual approval and fresh backtests. Stable does not mean live-ready.

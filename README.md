# forex-ai-lab

`forex-ai-lab` is a safe forex strategy laboratory for loading research strategies, backtesting them on historical-style OHLCV data, calculating risk-aware metrics, and generating reports. It intentionally excludes live trading, broker execution, credentials, and real-account automation.

## What is included

- Uniform `BaseStrategy` interface for all strategies.
- Strategy registry with three examples: EMA crossover, RSI mean reversion, and London breakout.
- Backtest engine for pandas OHLCV DataFrames.
- Explicit spread, commission, and slippage cost handling.
- Required metrics: total return, profit factor, max drawdown, win rate, trade count, average trade, expectancy, Sharpe ratio, and exposure time.
- CSV/Markdown reporting into `results/` and `reports/`.
- Safety rules and agent workflow documentation.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run tests

```bash
pytest
```

## Run sample backtest

```bash
python scripts/run_backtest.py
python scripts/generate_report.py
```

Outputs:

- `results/summary.csv`
- `results/trades.csv`
- `results/*_equity.csv`
- `reports/latest_report.md`

## Adding a strategy

1. Create a class in `strategies/` that inherits `BaseStrategy`.
2. Implement `prepare_data(df)`, `generate_signals(df)`, `get_parameters()`, and `describe()`.
3. Add the class to `STRATEGY_REGISTRY`.
4. Add or update tests.
5. Run `pytest`, `python scripts/run_backtest.py`, and `python scripts/generate_report.py`.

## Safety boundary

This project is research-only. Do not add live trading executors, broker credentials, automatic real-account execution, or claims that a strategy is live-ready based on one backtest.

# forex-ai-lab

`forex-ai-lab` is a safe forex strategy laboratory for loading research strategies, validating OHLCV data, running multi-pair/multi-timeframe backtests, calculating risk-aware metrics, performing walk-forward validation, and generating reports. It intentionally excludes live trading, broker execution, credentials, and real-account automation.

## What is included

- Uniform `BaseStrategy` interface for all strategies.
- Strategy registry with three examples: EMA crossover, RSI mean reversion, and London breakout.
- CSV data loader and strict OHLCV validator.
- Deterministic synthetic sample data generator for demos when CSV files are missing.
- Multi-pair and multi-timeframe backtest runner.
- Backtest engine for pandas OHLCV DataFrames using next-bar execution to reduce look-ahead bias.
- Explicit spread, commission, and slippage cost handling.
- Required metrics: total return, profit factor, max drawdown, win rate, trade count, average trade, expectancy, Sharpe ratio, and exposure time.
- Walk-forward stability fields in the strategy scoreboard.
- CSV/Markdown reporting into `results/` and `reports/`.
- Safety rules and agent workflow documentation.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Prepare CSV data

Place validated historical OHLCV CSV files in `data/raw/` using this naming convention:

```text
data/raw/EURUSD_M15.csv
data/raw/GBPUSD_H1.csv
data/raw/USDJPY_M5.csv
```

Required CSV columns:

```text
datetime,open,high,low,close,volume
```

Validation rejects missing columns, empty files, duplicate or unsorted datetimes, missing values, non-positive prices, `high < low`, and open/close values outside the high/low range.

## Sample data vs real historical data

If a configured pair/timeframe CSV is missing, `scripts/run_backtest.py` creates deterministic `synthetic_sample` data so the project remains runnable. Synthetic sample rows are clearly marked in reports and are **not** sufficient for `paper_candidate` status. Real historical CSV rows are marked as `csv` in `data_source`.



## Windows local launcher

1. Download ZIP or `git clone` this repository.
2. Double-click `START_WINDOWS.bat` from the project root.
3. Choose menu option `1` to install/update dependencies.
4. Open MetaTrader 5 locally if you want to export historical data.
5. Choose menu option `3` for a small MT5 history export test.
6. Choose menu option `5` to run the CSV-only backtest.
7. Choose menu option `7` to generate reports.
8. Reports are in `reports/`; use menu option `9` to open the folder.

See `docs/LOCAL_LAUNCHER.md` for all menu options and safety notes.

## Real historical data

For real research, put OHLCV CSV files into `data/raw/` and run CSV-only mode so missing data is skipped instead of replaced with synthetic data:

```bash
python scripts/run_backtest.py --data-mode csv-only
```

Synthetic demo mode is only for pipeline checks and cannot create paper candidates:

```bash
python scripts/run_backtest.py --data-mode synthetic-demo
```

Optional local MetaTrader 5 historical export is available when the platform-specific `MetaTrader5` Python package is installed locally. It is intentionally data-only and does not store credentials or send orders:

```bash
python scripts/export_mt5_history.py --pairs EURUSD GBPUSD --timeframes M15 H1 --from 2023-01-01 --to 2026-07-05 --output data/raw --validate
```

See `docs/DATA_IMPORT.md` for manual CSV import, MT5 export notes, data coverage, and why large real CSV files should usually stay out of GitHub.

## Run tests

```bash
pytest
```

## Run multi-pair backtest

```bash
python scripts/run_backtest.py --data-mode csv-only
python scripts/generate_report.py
```

The runner reads pairs from `config/pairs.yaml`, timeframes from `config/timeframes.yaml`, costs from `config/broker_costs.yaml`, and risk limits from `config/risk.yaml`.

Outputs:

- `results/strategy_scoreboard.csv`
- `results/strategy_scoreboard.json`
- per-combination equity/trade CSV files in `results/`
- `reports/latest_report.md`
- `reports/pair_matrix.md`
- `reports/rejected_strategies.md`

## Reading reports

- `latest_report.md`: compact scoreboard with status and walk-forward pass rate.
- `pair_matrix.md`: best non-rejected strategy by pair/timeframe plus watchlist and paper-test sections.
- `rejected_strategies.md`: rejected strategy combinations and key rejection metrics.

Statuses:

- `reject`: insufficient trades, weak profit factor, excessive drawdown, negative Sharpe, failed walk-forward, or otherwise unsafe.
- `watchlist`: not rejected but not eligible for paper testing, often because data is synthetic/sample or expectancy/walk-forward is marginal.
- `paper_candidate`: enough real CSV data, sufficient trades, acceptable drawdown, positive expectancy, and walk-forward support. This still does not mean live-ready.

## Adding a strategy

1. Create a class in `strategies/` that inherits `BaseStrategy`.
2. Implement `prepare_data(df)`, `generate_signals(df)`, `get_parameters()`, and `describe()`.
3. Add the class to `STRATEGY_REGISTRY`.
4. Add or update tests.
5. Run `pytest`, `python scripts/run_backtest.py`, and `python scripts/generate_report.py`.


## M15 no bars returned troubleshooting

If H1 exports work but M15 returns no bars, run diagnose-only mode to verify which MT5 terminal Python sees, whether latest bars are available, and whether only the requested date range is missing:

```bash
python scripts/export_mt5_history.py --pairs GBPUSD EURUSD --timeframes M15 H1 --from 2026-06-30 --to 2026-07-08 --output data/raw --diagnose-only
```

Then review `reports/mt5_export_report.md`. If `terminal_path` or terminal name/company does not match your open MT5 terminal, start the intended terminal. Open the exact broker symbol and M15 chart, ensure it is in Market Watch, scroll back to download history, and retry a shorter recent range first.

## Safety boundary

This project is research-only. Do not add live trading executors, broker credentials, automatic real-account execution, optimizer automation, or claims that a strategy is live-ready based on one backtest.

# Local Windows Launcher

The local launcher is a convenience wrapper for research-only workflows. It does not add live trading, broker execution, account automation, credentials, or strategy deployment.

## Quick start

1. Download ZIP or `git clone` this repository to your Windows PC.
2. Open the project folder.
3. Double-click `START_WINDOWS.bat`.
4. In the menu, choose `1 - Install / update dependencies`.
5. Open MetaTrader 5 locally if you want to export historical bars.
6. Choose `3 - Export MT5 history - small test` to verify connection and latest data availability.
7. Optionally choose `13 - Export MT5 history - medium test` to verify longer history before a full export.
8. Choose `5 - Run CSV-only backtest`.
9. Choose `7 - Generate reports`.
10. Choose `9 - Open reports folder`.

PowerShell users can run `START_WINDOWS.ps1`. If PowerShell execution policy blocks it, use `START_WINDOWS.bat` or launch PowerShell with a process-level bypass for this script.

## Menu options

- `1`: install or update Python dependencies; optionally installs `MetaTrader5` for data export only.
- `2`: run `pytest`.
- `3`: export a small recent MT5 historical data sample for EURUSD/GBPUSD on M15/H1 to verify connection and latest data availability.
- `4`: export the configured local set from `config/local_launcher.yaml`; use it only after MT5 has downloaded enough history and the small/medium tests pass.
- `5`: run `python scripts/run_backtest.py --data-mode csv-only`.
- `6`: run `python scripts/run_backtest.py --data-mode synthetic-demo`.
- `7`: generate reports.
- `8`: run tests, CSV-only backtest, report generation, and safety scan.
- `9`: open `reports/`.
- `10`: open `results/`.
- `11`: run a safety scan for execution/secret markers in Python code outside tests.
- `12`: diagnose MT5 data availability for EURUSD/GBPUSD on M15/H1 without saving CSV files.
- `13`: export a medium MT5 historical data sample for EURUSD/GBPUSD on M15/H1 to verify longer history.

## MT5 export notes

Before export:

- Open MetaTrader 5.
- Sign in to an account; demo is fine.
- Make sure symbols are visible in Market Watch.
- If your broker uses suffixes such as `EURUSD.r`, adjust your local symbol workflow before export.
- Export is data-only and does not trade.

Exported CSV files are written to `data/raw/` and validated by the existing OHLCV validator when `--validate` is used. The small test uses a short recent range to prove that Python can read current bars from MT5. The medium test checks a longer range. Run the full configured export only after these checks confirm that MT5 has downloaded the required history.

## M15 no bars returned troubleshooting

Use menu option `12 - Diagnose MT5 data availability` when H1 works but M15 returns no bars. It runs diagnose-only mode and writes `reports/mt5_export_report.md` without saving CSV files.

Check the report fields for terminal path/company/name and runtime account/server details. If they do not match the terminal you have open, Python is connected to a different MT5 terminal. Then open the correct symbol and M15 chart in MT5, make sure the symbol is in Market Watch, scroll back to load history, and retry a shorter recent date range.

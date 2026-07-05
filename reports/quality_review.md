# Quality Review

## Scope

Quality review of the data import modes, data-only MT5 history exporter, data coverage reports, status classification, and safety boundary. This project remains research/backtest-only.

## Review checklist

| Area | Result | Notes |
|:--|:--|:--|
| Data modes | Pass | `csv-only` is the default and skips missing CSV files; `synthetic-demo` uses only sample data; `mixed` prefers CSV and marks fallback sample data. |
| CSV-only safety | Pass | Missing pair/timeframe combinations are written to coverage as `missing`, not silently replaced with sample data. |
| Synthetic demo safety | Pass | Synthetic rows are marked `synthetic_sample`; status rules prevent sample-only `paper_candidate`. |
| Data coverage | Pass | `results/data_coverage.csv` and `reports/data_coverage.md` list each expected pair/timeframe with source and validation status. |
| MT5 exporter | Pass | Export script is data-only, uses optional dependency detection, exports historical OHLCV CSV, validates output when requested, and stores no credentials. |
| Trading/execution boundary | Pass | No live executor, order placement code, optimizer, API key, password, token, or credential storage was added. |
| Reports | Pass | Reports show counts for `csv`, `synthetic_sample`, `missing`, and `failed_validation`, and separate data skips from performance rejects. |
| Costs | Pass | Evaluated strategy rows still use `BacktestEngine`, which requires spread, commission, and slippage fields. |
| Tests | Improved | Added tests for data modes, data coverage report output, MT5 exporter safety, missing CSV behavior, and project execution-boundary strings. |

## Issues found and fixes applied

| Severity | Issue | Fix |
|:--|:--|:--|
| High | The previous runner defaulted to sample fallback, which could make real-research runs accidentally use synthetic data. | Added explicit `--data-mode` and made `csv-only` the default. Missing CSVs are skipped and reported as missing. |
| Medium | Reports showed sample warnings but did not summarize data coverage counts. | Added coverage counts to `latest_report.md` and a dedicated `data_coverage.md` report. |
| Medium | Rejections due to missing/invalid data were not clearly separated from strategy performance rejects. | Updated `rejected_strategies.md` to include separate skipped-data sections. |
| Low | MT5 import workflow was undocumented. | Added `docs/DATA_IMPORT.md` and `data/raw/README.md`. |

## Remaining recommendations

1. Add a small, redistributable CSV fixture for CI that demonstrates `csv` status without committing large datasets.
2. Add checksum or metadata support for locally managed historical datasets.
3. Keep MT5 export manual and data-only; never extend it into execution or account automation.

## Verdict

The project now defaults to real CSV-only research behavior and makes missing, failed, CSV, and synthetic data explicit in reports. No live trading, broker executor, optimizer, order-placement function, or secrets were added.

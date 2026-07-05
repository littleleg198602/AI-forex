# Quality Review

## Scope

Quality review of the new data loader, multi-pair/multi-timeframe backtest runner, walk-forward validation, status classification, reporting layer, and safety boundary. This project remains research/backtest-only.

## Review checklist

| Area | Result | Notes |
|:--|:--|:--|
| OHLCV loader validation | Pass | Required columns, empty data, missing values, invalid datetimes, duplicate datetimes, unsorted datetimes, non-positive prices, negative volume, high/low consistency, and open/close range are rejected. |
| Duplicate/unsorted data | Pass | Duplicate datetime and non-monotonic datetime values fail validation before any backtest can run. |
| Backtest future-data use | Pass | Strategy signals are generated from bar data, then the engine executes the previous signal on the next bar open. |
| Walk-forward future-data use | Pass | Each segment is chronological and `train.index.max() < test.index.min()` is enforced. Current sample strategies have fixed parameters; train data is reserved for future model-selection work and is not allowed to include test/future rows. |
| Synthetic/sample data handling | Pass | Missing CSV data is marked as `synthetic_sample`; reports display warnings and status classification prevents sample-only `paper_candidate`. |
| Status strictness | Strengthened | Paper-candidate status now requires real CSV data, at least 30 trades, acceptable drawdown, profit factor >= 1.1, non-negative Sharpe, positive expectancy, walk-forward pass rate >= 0.67, and at least two passed segments. |
| Reports | Pass | `latest_report.md` and `pair_matrix.md` explicitly warn that synthetic/sample data cannot justify paper trading. |
| Costs | Pass | Backtest initialization requires spread, commission, and slippage fields; integration tests confirm closed trades subtract positive costs from gross PnL. |
| Live trading / secrets | Pass | No live trading executor, broker integration, API key, password, token, or credential-handling code was added. |
| Tests | Improved | Added tests for unsorted datetime, missing/zero OHLC values, cost integration, report synthetic warnings, and stricter walk-forward status classification. |

## Issues found and fixes applied

| Severity | Issue | Fix |
|:--|:--|:--|
| Medium | Status classification was acceptable but still allowed `paper_candidate` with only one passed walk-forward segment when pass rate reached the threshold. | Tightened classification to require `wf_pass_rate >= 0.67` and `wf_passed_segments >= 2` for `paper_candidate`. |
| Low | Tests covered duplicate datetime and invalid OHLC values but did not explicitly test unsorted datetime, missing values, and non-positive prices. | Added data-loader tests for unsorted datetime, missing values, and zero prices. |
| Low | Tests verified missing cost fields but did not prove realized trades actually subtract spread/commission/slippage. | Added an integration test that closes trades and asserts positive cost and `pnl = gross_pnl - cost`. |
| Low | Report generation created synthetic warnings, but this behavior was not tested directly. | Added report tests checking `synthetic_sample` and paper-readiness warnings. |

## Remaining recommendations

1. Add real historical CSV fixtures for a small subset of pairs/timeframes so paper-candidate behavior can be tested without synthetic data.
2. Add more detailed transaction-cost sensitivity reports by pair and timeframe.
3. Add explicit tests for JPY PnL assumptions and non-USD account currency limitations.
4. Keep all optimizer work out of this phase; parameter optimization requires separate anti-overfitting controls.

## Verdict

The data and walk-forward layers are safer after this review. The main risks are now covered by tests: bad data rejection, no-look-ahead engine timing, no-look-ahead walk-forward splits, cost subtraction, status strictness, and report warnings. No live trading, broker executor, optimizer, or secrets were added.

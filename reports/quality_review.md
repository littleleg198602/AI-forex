# Quality Review

## Scope

Review of the current research-only forex backtesting laboratory. The review focused on look-ahead bias, signal timing, cost handling, metrics, strategy safety, accidental live-trading risk, configuration safety, and test coverage.

## Findings and fixes

| Severity | Area | Problem found | Fix applied |
|:--|:--|:--|:--|
| High | Backtest timing | The original engine generated a signal from the current bar close and could enter or exit at that same close. That is look-ahead biased because the close is only known after the bar finishes. | The engine now treats signals as close-of-bar decisions and executes the previous bar's signal on the next bar open. |
| Medium | Open trades | The original engine could leave the final position unrealized while metrics read the last equity value. | The engine now closes any remaining open position at the final close and records the trade with costs. |
| Medium | Costs | Cost configuration fields could silently default to zero if missing, which can hide spread, commission, or slippage omissions. | The engine now validates required cost keys and rejects negative costs. |
| Medium | Risk metrics | Sharpe ratio and expectancy worked for simple cases but lacked input validation and had implicit assumptions. | Metrics now validate positive initial balance, make expectancy components explicit, sanitize infinite returns, and accept `periods_per_year`. |
| Low | Strategy ranking | The ranker could over-reward profit factor and under-penalize small samples. | The ranker now caps profit factor, penalizes drawdown, and applies a small-sample penalty below 30 trades. |
| Low | Tests | Initial tests checked interfaces but did not verify look-ahead prevention or missing cost validation. | Added engine tests for next-open execution and cost validation, plus metric validation tests. |

## Strategy review

- **EMA crossover**: Uses indicators computed from historical/current close only. It is acceptable only when the engine executes on the next bar, which is now enforced.
- **RSI mean reversion**: Uses rolling close-based RSI. It is acceptable only with next-bar execution. It can be risky in strong trends, so reports should review drawdown and exposure, not only profit.
- **London breakout**: Uses previous rolling high/low via `.shift(1)`, which avoids using the active bar's high/low range as the breakout reference. It remains a sample strategy and is not live-ready.

## Safety review

- No live trading executor, broker login, API key, password, or account connection was found.
- Configuration files contain only sample pairs, timeframes, costs, and risk parameters.
- The project remains backtest/research-only.

## Remaining recommendations

1. Add realistic historical data fixtures and test multiple pairs/timeframes.
2. Add explicit stop-loss/take-profit and position-sizing modules before serious research use.
3. Add walk-forward and out-of-sample tests before marking any strategy as a paper candidate.
4. Add tests for JPY pair PnL conversion and non-USD account currency assumptions.
5. Add transaction-cost sensitivity tests to ensure conclusions do not depend on one cost profile.

## Verdict

The most important look-ahead and silent-cost issues have been fixed. The system is still a research scaffold, not a production-grade backtester and not live-trading ready.

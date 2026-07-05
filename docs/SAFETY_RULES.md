# Safety Rules

- No martingale position sizing.
- No grid strategy without fixed, explicit risk.
- No increasing lot size after a loss.
- No live trading in this repository.
- No trading decisions based on a single backtest result.
- No ignoring spread, commission, or slippage.
- No automatic deployment to live or funded accounts.
- Every result must include risk metrics, not only profit.
- No strategy may be considered usable based only on synthetic/sample data.
- No strategy may become `paper_candidate` without real CSV data.
- No strategy may become `paper_candidate` when data coverage is insufficient or unclear.
- No strategy may become `paper_candidate` without a sufficient number of trades.
- No strategy may pass review without walk-forward validation.
- No secrets, passwords, API keys, tokens, broker logins, or account credentials may be committed.
- MT5 export is data-only historical import, never execution or live trading.

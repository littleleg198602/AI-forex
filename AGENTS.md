# Codex Agent Rules for forex-ai-lab

This repository is a backtesting and research laboratory only. No agent may add live trading, broker execution, real account connectivity, credentials, API keys, secrets, or automated deployment to a live or funded account without explicit human permission.

## Roles

- **Build agent** may create and modify code, tests, scripts, and documentation for the research lab.
- **Research agent** may add generally known strategy ideas and educational implementations, but must not copy proprietary code, paid signals, or private trading systems.
- **Backtest agent** may run tests, execute research backtests, and generate reports under `results/` and `reports/`.
- **Quality agent** must look for bugs, overfitting, missing costs, missing risk metrics, and risky strategy assumptions.
- **Optimizer agent** may propose or implement parameter changes for research, but must not label any strategy as live-ready without a new backtest and human review.

## Safety Constraints

- Every backtest must include spread, commission, and slippage.
- Results must include risk metrics and must not be judged by profit alone.
- Do not introduce martingale, uncontrolled grid, or loss-recovery position sizing.
- Do not store credentials in this repository.

from pathlib import Path

import pandas as pd

from scripts.generate_report import write_latest_report, write_pair_matrix


def test_reports_mark_synthetic_data(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.generate_report.REPORTS", tmp_path)
    scoreboard = pd.DataFrame([
        {
            "strategy": "ema_crossover",
            "pair": "EURUSD",
            "timeframe": "M15",
            "data_source": "synthetic_sample",
            "trades": 10,
            "total_return": 0.01,
            "profit_factor": 1.2,
            "max_drawdown": -0.02,
            "expectancy": 1.0,
            "sharpe_ratio": 0.5,
            "wf_pass_rate": 0.67,
            "status": "reject",
        }
    ])
    write_latest_report(scoreboard)
    write_pair_matrix(scoreboard)
    assert "synthetic_sample" in (tmp_path / "latest_report.md").read_text()
    assert "cannot make a strategy paper-ready" in (tmp_path / "pair_matrix.md").read_text()

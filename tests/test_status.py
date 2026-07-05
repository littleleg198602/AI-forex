from selector.strategy_ranker import classify_status


def base_metrics(**overrides):
    data = {
        "trade_count": 40,
        "profit_factor": 1.4,
        "max_drawdown": -0.05,
        "sharpe_ratio": 0.8,
        "expectancy": 10,
        "wf_segments": 3,
        "wf_pass_rate": 0.67,
    }
    data.update(overrides)
    return data


def test_status_rejects_small_sample():
    assert classify_status(base_metrics(trade_count=29), {"max_drawdown_limit": 0.2}, "csv") == "reject"


def test_status_requires_real_csv_for_paper_candidate():
    assert classify_status(base_metrics(), {"max_drawdown_limit": 0.2}, "synthetic_sample") == "watchlist"
    assert classify_status(base_metrics(), {"max_drawdown_limit": 0.2}, "csv") == "paper_candidate"

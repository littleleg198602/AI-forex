from backtester.costs import apply_cost_to_pnl, calculate_round_turn_cost, pip_size


def test_pip_size_handles_jpy_pairs():
    assert pip_size("USDJPY") == 0.01
    assert pip_size("EURUSD") == 0.0001


def test_costs_reduce_pnl():
    cost = calculate_round_turn_cost(1.1, "EURUSD", 0.1, 1.0, 7.0, 0.2)
    assert cost > 0
    assert apply_cost_to_pnl(100, cost) < 100

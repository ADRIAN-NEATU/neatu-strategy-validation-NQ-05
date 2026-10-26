"""Unit tests for the toolkit and a look-ahead test for the example strategy. Run: python -m pytest -q"""
import math

import numpy as np
import pandas as pd

from riskval import (profit_factor, max_drawdown_r, max_drawdown_pct, sharpe, mean_and_pf_ci, expected_range,
                     drawdown_distribution, historical_var, expected_shortfall, sharpe_threshold, deflated_sharpe,
                     probabilistic_sharpe, compare_to_benchmark, match_trades)
from examples.demo_orb import synthetic_days, first_breakout


def test_profit_factor_and_drawdown_by_hand():
    r = [2, -1, -1, 3, -1]
    assert profit_factor(r) == 5 / 3
    assert max_drawdown_r(r) == 2          # 2 -> 1 -> 0
    assert max_drawdown_r([-1, -1, 4]) == 2  # drawdown counts from the starting point
    assert profit_factor([1, 2]) == math.inf


def test_max_drawdown_pct_compounds():
    assert abs(max_drawdown_pct([0.10, -0.50, 0.20]) - 0.50) < 1e-12


def test_sharpe_scale_invariant():
    d = np.random.default_rng(1).normal(0.001, 0.01, 1000)
    assert abs(sharpe(d) - sharpe(3 * d)) < 1e-9


def test_bootstrap_ci_contains_true_mean_and_is_reproducible():
    r = np.random.default_rng(2).normal(0.2, 1.0, 400)
    a = mean_and_pf_ci(r, n_boot=2000, rng=np.random.default_rng(5))
    b = mean_and_pf_ci(r, n_boot=2000, rng=np.random.default_rng(5))
    assert a == b
    assert a["mean_lo"] < r.mean() < a["mean_hi"]


def test_expected_range_is_ordered():
    rng = np.random.default_rng(3)
    daily = np.where(rng.random(1000) < 0.3, rng.normal(0.2, 1, 1000), 0.0)
    q = expected_range(daily, daily != 0, 250, n_paths=300, rng=np.random.default_rng(0))
    assert (q.loc[0.05] <= q.loc[0.5]).all() and (q.loc[0.5] <= q.loc[0.95]).all()


def test_more_risk_means_deeper_drawdowns():
    daily = np.random.default_rng(4).normal(0.1, 1, 2000)
    lo = drawdown_distribution(daily, 0.005, n_paths=500, rng=np.random.default_rng(0))
    hi = drawdown_distribution(daily, 0.02, n_paths=500, rng=np.random.default_rng(0))
    assert hi["dd_p95"] > lo["dd_p95"] and hi["p_dd_limit"] >= lo["p_dd_limit"]


def test_var_and_es_on_known_sample():
    x = np.r_[np.full(99, 0.01), -0.05]
    assert historical_var(x, 0.95) <= expected_shortfall(x, 0.95)
    assert abs(expected_shortfall(x, 0.99) - 0.05) < 1e-12


def test_deflated_sharpe_falls_with_more_trials():
    sr, var = 0.08, 0.0004
    p = [deflated_sharpe(sr, var, n, 2000, 0.0, 3.0) for n in (10, 100, 1000, 10000)]
    assert all(a > b for a, b in zip(p, p[1:]))
    assert sharpe_threshold(1000, var) > sharpe_threshold(10, var)
    assert abs(probabilistic_sharpe(0.0, 0.0, 1000, 0.0, 3.0) - 0.5) < 1e-12


def test_benchmark_beta_recovered():
    rng = np.random.default_rng(6)
    b = rng.normal(0, 0.01, 3000)
    s = 0.5 * b + rng.normal(0.0002, 0.005, 3000)
    out = compare_to_benchmark(s, b)
    assert abs(out["beta"] - 0.5) < 0.05


def test_reconcile_counts():
    a = pd.DataFrame({"date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]), "side": [1, -1, 1], "r": [1.0, -1.0, 0.5]})
    b = pd.DataFrame({"date": pd.to_datetime(["2024-01-03", "2024-01-04", "2024-01-05"]), "side": [-1, -1, 1], "r": [-0.9, 0.2, 1.0]})
    m = match_trades(a, b)
    assert m["same_day"] == 2 and m["same_side"] == 1


def test_toolkit_finds_no_edge_on_random_data():
    """Regression test for a real bug: booking stop-outs at exactly -1R made random data look profitable."""
    from examples.demo_orb import trade_r
    rs = [trade_r(d, s, cost_r=0.0) for d in synthetic_days(1500, seed=3) if (s := first_breakout(d))]
    ci = mean_and_pf_ci(rs, n_boot=1000, rng=np.random.default_rng(0))
    assert ci["mean_lo"] < 0 < ci["mean_hi"]


def test_example_strategy_has_no_lookahead():
    """Cutting each day right after the signal bar must not change the signal."""
    for d in synthetic_days(200, seed=11):
        sig = first_breakout(d)
        if sig:
            assert first_breakout(d[: sig[0] + 1]) == sig

"""Bootstrap tools: confidence intervals and a forecast range for a future (out-of-sample) period.

Block bootstrap keeps short-range clustering (losing streaks, volatile weeks) that an i.i.d. resample would destroy."""
import numpy as np
import pandas as pd

from .metrics import profit_factor, max_drawdown_r


def block_indices(n_out, n_in, block, rng):
    """Circular block bootstrap: random start points, `block` consecutive days each, trimmed to n_out."""
    starts = rng.integers(0, n_in, n_out // block + 1)
    idx = (starts[:, None] + np.arange(block)) % n_in
    return idx.ravel()[:n_out]


def mean_and_pf_ci(trade_r, n_boot=10000, level=0.95, rng=None):
    """Percentile confidence intervals for the average R and the profit factor; P(mean <= 0)."""
    rng = rng or np.random.default_rng(0)
    r = np.asarray(trade_r, float)
    s = r[rng.integers(0, len(r), (n_boot, len(r)))]
    means = s.mean(1)
    pfs = np.where(s > 0, s, 0).sum(1) / np.maximum(-np.where(s < 0, s, 0).sum(1), 1e-12)
    a = (1 - level) / 2 * 100
    return dict(mean_lo=float(np.percentile(means, a)), mean_hi=float(np.percentile(means, 100 - a)),
                pf_lo=float(np.percentile(pfs, a)), pf_hi=float(np.percentile(pfs, 100 - a)),
                p_mean_le_0=float((means <= 0).mean()))


def expected_range(daily_r, traded, horizon_days, n_paths=10000, block=20, quantiles=(0.05, 0.5, 0.95), rng=None):
    """Forecast what a future period of `horizon_days` should look like, from in-sample daily results.

    daily_r: result in R per trading day (0 on days without a trade); traded: bool per day.
    Freeze the output (and hash it) BEFORE looking at the out-of-sample data."""
    rng = rng or np.random.default_rng(0)
    y_all, t_all = np.asarray(daily_r, float), np.asarray(traded, bool)
    rows = []
    for _ in range(n_paths):
        ix = block_indices(horizon_days, len(y_all), block, rng)
        y, t = y_all[ix], t_all[ix]
        rt = y[t]
        rows.append((len(rt), profit_factor(rt), (rt > 0.05).mean(), rt.mean(), y.sum(), max_drawdown_r(y)))
    S = pd.DataFrame(rows, columns=["trades", "profit_factor", "win_rate", "avg_r", "net_r", "max_drawdown_r"])
    out = S.quantile(list(quantiles))
    out.attrs["p_pf_below_1"] = float((S.profit_factor < 1).mean())
    return out

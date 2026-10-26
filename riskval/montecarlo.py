"""Monte Carlo of compounded equity at a given risk per trade: how deep can drawdowns get?"""
import numpy as np

from .bootstrap import block_indices


def drawdown_distribution(daily_r, risk_per_trade, horizon_days=252, n_paths=10000, block=20, limit=0.10, rng=None):
    """daily_r in R; risk_per_trade as a fraction (0.005 = 0.5 %). Returns drawdown and return percentiles and the
    probability of touching a drawdown of `limit` (e.g. a prop-firm 10 % max-loss rule) within the horizon."""
    rng = rng or np.random.default_rng(0)
    y = np.asarray(daily_r, float)
    idx = np.stack([block_indices(horizon_days, len(y), block, rng) for _ in range(n_paths)])
    eq = np.cumprod(1 + risk_per_trade * y[idx], axis=1)
    mdd = (1 - eq / np.maximum.accumulate(np.maximum(eq, 1.0), axis=1)).max(1)
    ret = eq[:, -1] - 1
    return dict(dd_median=float(np.median(mdd)), dd_p95=float(np.percentile(mdd, 95)), dd_p99=float(np.percentile(mdd, 99)),
                p_dd_limit=float((mdd >= limit).mean()), ret_p5=float(np.percentile(ret, 5)),
                ret_median=float(np.median(ret)), p_loss=float((ret < 0).mean()))

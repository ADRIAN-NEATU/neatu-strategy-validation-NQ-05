"""Performance metrics. Trade results are in R (1R = the amount risked on that trade); daily results are returns."""
import numpy as np


def profit_factor(r):
    """Gross wins / gross losses. inf when there are no losses."""
    r = np.asarray(r, float)
    loss = -r[r < 0].sum()
    return float("inf") if loss == 0 else float(r[r > 0].sum() / loss)


def max_drawdown_r(r):
    """Largest peak-to-trough fall of the cumulative R curve (starting from 0)."""
    c = np.cumsum(np.asarray(r, float))
    if len(c) == 0:
        return 0.0
    peak = np.maximum.accumulate(np.r_[0.0, c])[1:]
    return float(np.max(peak - c))


def max_drawdown_pct(returns):
    """Largest peak-to-trough fall of compounded equity (starting from 1)."""
    e = np.cumprod(1 + np.asarray(returns, float))
    peak = np.maximum.accumulate(np.maximum(e, 1.0))
    return float(np.max(1 - e / peak)) if len(e) else 0.0


def sharpe(daily, periods=252):
    d = np.asarray(daily, float)
    return float(d.mean() / d.std(ddof=1) * np.sqrt(periods))


def cagr(daily, periods=252):
    d = np.asarray(daily, float)
    return float(np.prod(1 + d) ** (periods / len(d)) - 1)


def summary(trade_r, daily=None, win_threshold=0.05):
    """Standard table row. A trade counts as a win above +0.05R (break-even exits are not wins)."""
    r = np.asarray(trade_r, float)
    out = dict(trades=int(len(r)), win_rate=float((r > win_threshold).mean()) if len(r) else float("nan"),
               profit_factor=profit_factor(r), net_r=float(r.sum()), avg_r=float(r.mean()) if len(r) else float("nan"),
               max_drawdown_r=max_drawdown_r(r))
    if daily is not None:
        out.update(sharpe=sharpe(daily), cagr=cagr(daily), max_drawdown_pct=max_drawdown_pct(daily))
    return out

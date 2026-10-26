"""Strategy vs a buy-and-hold benchmark: performance side by side, correlation, beta and alpha (OLS with t-stats)."""
import numpy as np

from .metrics import sharpe, cagr, max_drawdown_pct


def compare_to_benchmark(strategy, bench, periods=252):
    """strategy and bench: aligned daily returns (same days, same length)."""
    s, b = np.asarray(strategy, float), np.asarray(bench, float)
    X = np.c_[np.ones(len(b)), b]
    coef, *_ = np.linalg.lstsq(X, s, rcond=None)
    resid = s - X @ coef
    se = np.sqrt(np.diag(resid.var(ddof=2) * np.linalg.inv(X.T @ X)))

    def kp(x):
        return dict(cagr=cagr(x, periods), vol=float(x.std(ddof=1) * np.sqrt(periods)), sharpe=sharpe(x, periods),
                    max_drawdown=max_drawdown_pct(x))
    return dict(strategy=kp(s), benchmark=kp(b), correlation=float(np.corrcoef(s, b)[0, 1]),
                beta=float(coef[1]), beta_t=float(coef[1] / se[1]),
                alpha_annual=float(coef[0] * periods), alpha_t=float(coef[0] / se[0]))

"""Historical Value-at-Risk and Expected Shortfall, reported as positive loss fractions."""
import numpy as np


def historical_var(returns, level=0.99):
    return float(-np.percentile(np.asarray(returns, float), (1 - level) * 100))


def expected_shortfall(returns, level=0.99):
    x = np.asarray(returns, float)
    cut = np.percentile(x, (1 - level) * 100)
    return float(-x[x <= cut].mean())

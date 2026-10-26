"""Probabilistic and Deflated Sharpe Ratio (Bailey & Lopez de Prado, 2012 / 2014).

All Sharpe ratios here are per period (e.g. daily), not annualised."""
import math
from statistics import NormalDist

_Z = NormalDist()
_EULER = 0.5772156649


def probabilistic_sharpe(sr, sr_ref, n_obs, skew, kurtosis):
    """P(true Sharpe > sr_ref) given an observed Sharpe `sr` over n_obs periods. kurtosis is NOT excess (normal = 3)."""
    den = math.sqrt(max(1 - skew * sr + (kurtosis - 1) / 4 * sr * sr, 1e-12))
    return _Z.cdf((sr - sr_ref) * math.sqrt(n_obs - 1) / den)


def sharpe_threshold(n_trials, sr_variance):
    """Expected maximum Sharpe among n_trials skill-less strategies whose Sharpe ratios have variance sr_variance."""
    return math.sqrt(sr_variance) * ((1 - _EULER) * _Z.inv_cdf(1 - 1 / n_trials)
                                     + _EULER * _Z.inv_cdf(1 - 1 / (n_trials * math.e)))


def deflated_sharpe(sr, sr_variance, n_trials, n_obs, skew, kurtosis):
    """Probability that the selected strategy has skill after correcting for having tried n_trials variants."""
    return probabilistic_sharpe(sr, sharpe_threshold(n_trials, sr_variance), n_obs, skew, kurtosis)

"""Demo: the full validation pipeline on a PUBLIC example strategy with EXAMPLE parameters and SYNTHETIC data.

The example strategy is a plain opening-range breakout (not the private strategy): after the first RANGE_BARS
5-minute bars, enter on the first close beyond the range, stop at the other side, exit at the last bar of the day.
On random-walk data it has no edge, and the toolkit should say so: profit factor near 1, confidence interval around 0.

Run from the repo root:  python -m examples.demo_orb"""
import numpy as np
import pandas as pd

from riskval import (summary, mean_and_pf_ci, expected_range, drawdown_distribution, historical_var,
                     expected_shortfall)

RANGE_BARS = 6          # example value: the first 30 minutes
BARS_PER_DAY = 78       # 5-minute bars in a 6.5-hour session


def synthetic_days(n_days, seed=7):
    """Random-walk intraday closes with day-to-day volatility clustering. No edge by construction."""
    rng = np.random.default_rng(seed)
    vol = np.exp(np.cumsum(rng.normal(0, 0.05, n_days)) * 0.3) * 0.001
    days, price = [], 100.0
    for v in vol:
        path = price * np.exp(np.cumsum(rng.normal(0, v, BARS_PER_DAY)))
        days.append(path)
        price = path[-1]
    return days


def first_breakout(closes, range_bars=RANGE_BARS):
    """(bar index, side, range high, range low) of the first close beyond the opening range, or None.
    Uses only bars up to the signal bar, so truncating the day after the signal never changes the answer."""
    hi, lo = closes[:range_bars].max(), closes[:range_bars].min()
    for i in range(range_bars, len(closes)):
        if closes[i] > hi:
            return i, 1, hi, lo
        if closes[i] < lo:
            return i, -1, hi, lo
    return None


def trade_r(closes, sig, cost_r=0.02):
    i, side, hi, lo = sig
    entry, stop = closes[i], (lo if side > 0 else hi)
    risk = abs(entry - stop)
    for c in closes[i + 1:]:
        if (c - stop) * side <= 0:
            # exit at the close that crossed the stop: the loss can exceed 1R (booking exactly -1R would flatter it)
            return (c - entry) * side / risk - cost_r
    return (closes[-1] - entry) * side / risk - cost_r


def main():
    days = synthetic_days(2000)
    daily, traded, rs = [], [], []
    for d in days:
        sig = first_breakout(d)
        r = trade_r(d, sig) if sig else 0.0
        daily.append(r)
        traded.append(sig is not None)
        if sig:
            rs.append(r)
    daily, traded = np.array(daily), np.array(traded)
    print("Example opening-range breakout on synthetic random-walk data (expected: no edge)\n")
    print(pd.Series(summary(rs)).round(3).to_string())
    ci = mean_and_pf_ci(rs, n_boot=2000)
    print(f"\n95% CI average R: {ci['mean_lo']:+.3f} .. {ci['mean_hi']:+.3f} | PF {ci['pf_lo']:.2f} .. {ci['pf_hi']:.2f} | "
          f"P(avg R <= 0) {ci['p_mean_le_0']:.2f}")
    print("\nForecast for the next 500 trading days (freeze this before looking at new data):")
    q = expected_range(daily, traded, 500, n_paths=1000)
    print(q.round(2).to_string())
    print(f"chance of a losing period (PF < 1): {q.attrs['p_pf_below_1']:.0%}")
    for risk in (0.005, 0.02):
        m = drawdown_distribution(daily, risk, n_paths=2000)
        print(f"\nMonte Carlo 1 year at {risk:.1%} risk: max drawdown p95 {m['dd_p95']:.1%} | P(10% drawdown) {m['p_dd_limit']:.1%}")
    print(f"\nDaily VaR99 at 1% risk: {historical_var(0.01 * daily):.2%} | ES99: {expected_shortfall(0.01 * daily):.2%}")


if __name__ == "__main__":
    main()

"""Reconcile two independent implementations (e.g. a research engine and a trading platform) trade by trade."""
import numpy as np
import pandas as pd

from .metrics import profit_factor


def match_trades(a, b):
    """a, b: DataFrames with columns date, side (+1/-1), r. At most one trade per day per implementation."""
    A, B = a.set_index("date"), b.set_index("date")
    both = A.index.intersection(B.index)
    return dict(trades_a=int(len(A)), trades_b=int(len(B)), same_day=int(len(both)),
                share_of_a=float(len(both) / len(A)) if len(A) else float("nan"),
                same_side=int((A.loc[both, "side"].to_numpy() == B.loc[both, "side"].to_numpy()).sum()),
                corr_r=float(np.corrcoef(A.loc[both, "r"], B.loc[both, "r"])[0, 1]) if len(both) > 2 else float("nan"),
                pf_only_a=profit_factor(A.loc[A.index.difference(both), "r"]),
                pf_only_b=profit_factor(B.loc[B.index.difference(both), "r"]))


def as_frame(dates, sides, r):
    return pd.DataFrame({"date": pd.to_datetime(dates), "side": sides, "r": r})

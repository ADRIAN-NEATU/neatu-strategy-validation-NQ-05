"""riskval: validation toolkit for trading strategies, applied the way a model validator would.

Works on trade-level results (R per trade) and daily returns; it never needs the strategy's rules."""
from .metrics import profit_factor, max_drawdown_r, max_drawdown_pct, sharpe, cagr, summary  # noqa: F401
from .bootstrap import block_indices, mean_and_pf_ci, expected_range  # noqa: F401
from .montecarlo import drawdown_distribution  # noqa: F401
from .var import historical_var, expected_shortfall  # noqa: F401
from .dsr import probabilistic_sharpe, sharpe_threshold, deflated_sharpe  # noqa: F401
from .benchmark import compare_to_benchmark  # noqa: F401
from .reconcile import match_trades  # noqa: F401
from .io_tradingview import load_tradingview_trades  # noqa: F401

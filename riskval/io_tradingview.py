"""Read a TradingView Strategy Tester trade export ("Export trades" CSV) into one row per position.

Partial exits (several rows sharing an entry) are merged. With fixed-fraction sizing (risk a fraction of equity before
each trade), R per trade = net PnL / (risk_fraction x equity before the trade)."""
import pandas as pd


def load_tradingview_trades(path, initial_capital, risk_fraction):
    D = pd.read_csv(path)
    D["time"] = pd.to_datetime(D["Date and time"])
    ent = D[D.Type.str.startswith("Entry")].set_index("Trade number")
    ex = D[D.Type.str.startswith("Exit")].set_index("Trade number")
    legs = pd.DataFrame({"entry": ent.time, "side": ent.Type.str.endswith("long").map({True: 1, False: -1}),
                         "price": ent["Price USD"], "qty": ent["Size (qty)"], "exit": ex.time,
                         "pnl": ex["Net PnL USD"], "cum": ex["Cumulative PnL USD"]}).sort_index()
    legs["cum_before"] = legs.cum.shift(1).fillna(0.0)
    P = legs.groupby(["entry", "side"], sort=False).agg(price=("price", "first"), qty=("qty", "sum"), pnl=("pnl", "sum"),
                                                        cum_before=("cum_before", "first"), exit=("exit", "max")).reset_index()
    P["equity_before"] = initial_capital + P.cum_before
    P["r"] = P.pnl / (risk_fraction * P.equity_before)
    P["ret"] = P.pnl / P.equity_before
    P["date"] = P.entry.dt.normalize()
    return P

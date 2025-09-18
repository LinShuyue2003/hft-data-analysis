
import numpy as np
import pandas as pd

"""
Feature engineering: resampling to bars, returns, volatility, spread metrics.
"""

def resample_trades(trades: pd.DataFrame, rule: str = "1s") -> pd.DataFrame:
    """Aggregate tick trades to time bars.

    Output columns:
    - open, high, low, close (from price)
    - vwap
    - vol (sum of qty)
    - ntrades (count)
    """
    d = trades.copy()
    d = d.set_index("ts").sort_index()
    agg = {
        "price": ["first","max","min","last"],
        "qty": "sum",
    }
    out = d.resample(rule).agg(agg)
    out.columns = ["open","high","low","close","vol"]
    out["ntrades"] = d["price"].resample(rule).count()
    # VWAP
    out["vwap"] = (d["price"] * d["qty"]).resample(rule).sum() / d["qty"].resample(rule).sum()
    return out

def add_returns(df_bar: pd.DataFrame, price_col: str = "close") -> pd.DataFrame:
    """Add simple, log returns and absolute log returns."""
    d = df_bar.copy()
    d["ret"] = d[price_col].pct_change(fill_method=None)
    d["logret"] = np.log(d[price_col]).diff()
    d["absret"] = d["logret"].abs()
    return d

def rolling_vol(d: pd.DataFrame, col: str = "logret", window: int = 60, min_periods: int = 20) -> pd.Series:
    """Rolling volatility (std of returns) with safety on min periods."""
    return d[col].rolling(window=window, min_periods=min_periods).std()

def compute_spread_from_book(book: pd.DataFrame) -> pd.DataFrame:
    """Compute mid price and spread in basis points when bid/ask exist."""
    b = book.copy().set_index("ts").sort_index()
    if not {"bid","ask"}.issubset(b.columns):
        return b
    b["mid"] = (b["bid"] + b["ask"]) / 2.0
    b["spread"] = b["ask"] - b["bid"]
    b["spread_bp"] = (b["spread"] / b["mid"]) * 10000.0
    return b

def merge_trade_book(bars: pd.DataFrame, book_features: pd.DataFrame) -> pd.DataFrame:
    """Merge bar-level features with nearest-forward book snapshot."""
    if "mid" not in book_features.columns and "spread_bp" not in book_features.columns:
        return bars
    b = book_features[[c for c in ["mid","spread_bp"] if c in book_features.columns]].copy()
    b = b.sort_index()
    # Align by forward-fill to bar timestamps
    merged = bars.join(b.resample(bars.index.freq or "1s").last()).ffill()
    return merged

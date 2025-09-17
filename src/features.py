"""
Feature engineering for microstructure analytics.
"""
from __future__ import annotations
import pandas as pd
import numpy as np

def mid_from_book(book: pd.DataFrame) -> pd.Series:
    return (book["bid"] + book["ask"]) / 2.0

def spread_from_book(book: pd.DataFrame) -> pd.Series:
    return (book["ask"] - book["bid"]).abs()

def resample_trades(trades: pd.DataFrame, rule: str = "1s") -> pd.DataFrame:
    """
    Aggregates trades to a time bar (e.g., 1s, 5s).
    Returns columns: price_last, vwap, vol
    """
    g = trades.set_index("ts").sort_index()
    vol = g["qty"].resample(rule).sum().rename("vol")
    notional = (g["price"] * g["qty"]).resample(rule).sum()
    vwap = (notional / vol).rename("vwap")
    price_last = g["price"].resample(rule).last().rename("price_last")
    out = pd.concat([price_last, vwap, vol], axis=1)
    return out.dropna(how="all").reset_index()

def log_returns(series: pd.Series) -> pd.Series:
    s = series.dropna().astype(float)
    return np.log(s / s.shift(1))

def rolling_vol(returns: pd.Series, window: int = 60) -> pd.Series:
    """
    Rolling standard deviation for given window length (in bars).
    """
    return returns.rolling(window=window, min_periods=max(5, window//5)).std()

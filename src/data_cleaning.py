"""
Utilities for cleaning and normalizing tick-level data.
Robust to Binance Data Vision formats (headerless, alt column names),
and timestamps in seconds / milliseconds / microseconds.
"""
from __future__ import annotations
import pandas as pd
import numpy as np

def _detect_epoch_unit(max_val: float) -> str:
    """
    Infer epoch unit from magnitude.
    ~1e9  -> seconds
    ~1e12 -> milliseconds
    ~1e15 -> microseconds
    """
    if max_val > 1e14:   # definitely microseconds
        return "us"
    if max_val > 1e12:   # definitely milliseconds
        return "ms"
    return "s"

def to_datetime(series, unit: str | None = None) -> pd.Series:
    """
    Robust timestamp parsing. Accepts ISO strings or epoch (s/ms/us).
    """
    s = series.copy()
    # If already datetime-like, just coerce to UTC
    if np.issubdtype(s.dtype, np.datetime64):
        return pd.to_datetime(s, utc=True, errors="coerce")
    # Numeric epoch
    if np.issubdtype(s.dtype, np.number):
        if unit is None:
            unit = _detect_epoch_unit(float(np.nanmax(s)))
        return pd.to_datetime(s, unit=unit, utc=True, errors="coerce")
    # Strings -> let pandas parse
    return pd.to_datetime(s, utc=True, errors="coerce")

def _standardize_trade_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Map common alt column names to ['ts','price','qty'].""" 
    df = df.copy()
    # Timestamp candidates
    if "ts" not in df:
        for c in ["timestamp", "T", "time", "date"]:
            if c in df:
                df["ts"] = df[c]
                break
    # Price candidates
    if "price" not in df:
        for c in ["p", "Price", "close"]:
            if c in df:
                df["price"] = df[c]
                break
    # Qty/size candidates
    if "qty" not in df:
        for c in ["quantity", "q", "size", "amount"]:
            if c in df:
                df["qty"] = df[c]
                break
    return df

def clean_trades(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expect columns: ['ts', 'price', 'qty']
    But will auto-map common alternatives from Binance Vision aggTrades:
    ['timestamp','price','quantity'] -> ['ts','price','qty']
    """
    df = _standardize_trade_cols(df)
    df = df.copy()
    if "ts" not in df:
        raise ValueError("Trades must have a 'ts' (or 'timestamp'/'T') column.")
    df["ts"] = to_datetime(df["ts"])

    if "price" not in df:
        raise ValueError("Trades missing required column: price (or 'p').")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    if "qty" not in df:
        raise ValueError("Trades missing required column: qty (or 'quantity'/'q'/'size').")
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce")

    df = df.dropna(subset=["ts", "price", "qty"]).sort_values("ts")
    df = df[(df["price"] > 0) & (df["qty"] > 0)]
    df = df.drop_duplicates(subset=["ts", "price", "qty"])
    return df.reset_index(drop=True)

def clean_book(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expect columns: ['ts', 'bid', 'ask'].
    Accepts timestamp in s/ms/us or ISO string.
    """
    df = df.copy()
    if "ts" not in df:
        for c in ["timestamp", "T", "time", "date"]:
            if c in df:
                df["ts"] = df[c]
                break
        if "ts" not in df:
            raise ValueError("Book must have a 'ts' column.")
    df["ts"] = to_datetime(df["ts"])

    for col in ("bid", "ask"):
        if col not in df:
            raise ValueError(f"Book missing required column: {col}")
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["ts", "bid", "ask"]).sort_values("ts")
    df = df[(df["bid"] > 0) & (df["ask"] > 0) & (df["ask"] >= df["bid"])]
    df = df.drop_duplicates(subset=["ts"])
    return df.reset_index(drop=True)

import numpy as np
import pandas as pd

"""
Utilities for cleaning trades and order book data.
Handles headerless Binance aggTrades (a,p,q,f,l,T,m,M) and normalizes to ts/price/qty.
"""

def to_datetime(s: pd.Series) -> pd.Series:
    """Convert mixed timestamp inputs to timezone-naive pandas datetime64[ns] in UTC."""
    if pd.api.types.is_datetime64_any_dtype(s):
        s = pd.to_datetime(s, errors="coerce")
        if hasattr(s.dtype, "tz") and s.dtype.tz is not None:
            try:
                s = s.dt.tz_convert("UTC").dt.tz_localize(None)
            except Exception:
                s = s.dt.tz_localize(None)
        return s
    if pd.api.types.is_integer_dtype(s) or pd.api.types.is_float_dtype(s):
        x = pd.to_numeric(s, errors="coerce").astype("float64")
        mx = np.nanmax(x)
        if mx < 1e11:
            unit = "s"
        elif mx < 1e14:
            unit = "ms"
        elif mx < 1e17:
            unit = "us"
        else:
            unit = "ns"
        return pd.to_datetime(x, unit=unit, utc=True, errors="coerce").dt.tz_localize(None)
    s = pd.to_datetime(s, utc=True, errors="coerce")
    try:
        return s.dt.tz_localize(None)
    except Exception:
        return s


def _ensure_ts(df: pd.DataFrame) -> pd.DataFrame:
    ts_cols = [c for c in df.columns if str(c).lower() in {"ts","timestamp","time","datetime","t"}]
    if ts_cols:
        df = df.rename(columns={ts_cols[0]: "ts"})
    return df


def _rename_binance_aggtrades(df: pd.DataFrame) -> pd.DataFrame:
    """If DataFrame looks like headerless Binance aggTrades, rename columns accordingly."""
    cols = list(df.columns)
    # Case 1: already named like a,p,q,f,l,T,m,M
    if set(cols) >= {"a","p","q","f","l","T","m","M"}:
        return df.rename(columns={"p":"price", "q":"qty", "T":"ts"})
    # Case 2: numeric columns 0..7 -> map to a,p,q,f,l,T,m,M
    if len(cols) == 8 and all(str(c).isdigit() for c in cols):
        mapping = {0:"a",1:"p",2:"q",3:"f",4:"l",5:"T",6:"m",7:"M"}
        df = df.rename(columns=mapping)
        return df.rename(columns={"p":"price","q":"qty","T":"ts"})
    return df


def clean_trades(df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning for trades; robust to headerless Binance aggTrades.
    
    Ensures columns: ts (datetime), price (float), qty (float).
    """
    df = _rename_binance_aggtrades(df.copy())
    df = _ensure_ts(df)

    if "ts" in df.columns:
        df["ts"] = to_datetime(df["ts"])

    if "price" not in df.columns:
        for alt in ("p","close","last_price","Price"):
            if alt in df.columns:
                df = df.rename(columns={alt:"price"}); break

    if "qty" not in df.columns:
        for alt in ("q","size","amount","volume","quantity","Qty"):
            if alt in df.columns:
                df = df.rename(columns={alt:"qty"}); break

    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
    if "qty" in df.columns:
        df["qty"] = pd.to_numeric(df["qty"], errors="coerce")

    df = df.dropna(subset=["ts"]).sort_values("ts").reset_index(drop=True)
    return df


def clean_book(df: pd.DataFrame) -> pd.DataFrame:
    df = _ensure_ts(df.copy())
    if "ts" in df.columns:
        df["ts"] = to_datetime(df["ts"])
    df = df.dropna(subset=["ts"]).sort_values("ts").reset_index(drop=True)
    if "bid" not in df.columns:
        for alt in ("best_bid","b","bidPrice"):
            if alt in df.columns: df = df.rename(columns={alt:"bid"}); break
    if "ask" not in df.columns:
        for alt in ("best_ask","a","askPrice"):
            if alt in df.columns: df = df.rename(columns={alt:"ask"}); break
    for std, alts in {"bid_size":("bsize","bidSize","best_bid_size"), "ask_size":("asize","askSize","best_ask_size")}.items():
        if std not in df.columns:
            for alt in alts:
                if alt in df.columns: df = df.rename(columns={alt:std}); break
    return df

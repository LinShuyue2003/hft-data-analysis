"""
Convert Binance Vision aggTrades CSV into pseudo order book (bid/ask).

Handles:
- headerless CSV (first row is data, not header)
- timestamp in microseconds / milliseconds / seconds
- price as string

Usage:
    python -m scripts.convert_trades_to_book \
        --trades data/raw/binance/BTCUSDT/BTCUSDT-aggTrades-2025-08-01.csv \
        --out data/raw/binance/BTCUSDT/book.csv \
        --spread-frac 0.0001
"""
from __future__ import annotations
import pandas as pd
import click
import numpy as np

COLS = ["aggTradeId","price","quantity","firstTradeId","lastTradeId","timestamp","isBuyerMaker","isBestMatch"]

def _read_aggtrades(path: str) -> pd.DataFrame:
    """Read aggTrades CSV robustly (with or without header)."""
    # Try headerless
    df = pd.read_csv(path, header=None)
    if df.shape[1] >= 8 and str(df.iloc[0,0]).isdigit():
        df = df.iloc[:, :8]
        df.columns = COLS
    else:
        df = pd.read_csv(path)
        if not set(["timestamp","price","quantity"]).issubset(df.columns):
            df = pd.read_csv(path, header=None, names=COLS)
    return df

def _infer_unit(ts_series: pd.Series) -> str:
    mx = float(np.nanmax(pd.to_numeric(ts_series, errors="coerce")))
    if mx > 1e14:
        return "us"
    if mx > 1e12:
        return "ms"
    return "s"

@click.command()
@click.option("--trades", required=True, help="Path to aggTrades CSV")
@click.option("--out", required=True, help="Output book CSV")
@click.option("--spread-frac", default=0.0001, show_default=True, type=float,
              help="Relative half-spread to apply around trade price")
def main(trades: str, out: str, spread_frac: float):
    df = _read_aggtrades(trades)

    ts_col = "timestamp"
    price_col = "price"
    if ts_col not in df.columns:
        raise ValueError("CSV must have a 'timestamp' column.")
    if price_col not in df.columns:
        raise ValueError("CSV must have a 'price' column.")

    unit = _infer_unit(df[ts_col])
    ts = pd.to_datetime(pd.to_numeric(df[ts_col], errors="coerce"), unit=unit, utc=True)
    price = pd.to_numeric(df[price_col], errors="coerce")

    bid = price * (1 - spread_frac)
    ask = price * (1 + spread_frac)

    out_df = pd.DataFrame({"ts": ts, "bid": bid, "ask": ask}).dropna()
    out_df.to_csv(out, index=False)
    print(f"✅ Pseudo order book saved to {out} with unit={unit}, rows={len(out_df)}")

if __name__ == "__main__":
    main()

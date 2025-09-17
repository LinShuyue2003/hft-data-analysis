"""
Prepare/clean data and write processed parquet for downstream steps.
Supports running with only trades or only book.
"""
from __future__ import annotations
import pathlib
import click
import pandas as pd
from src.data_cleaning import clean_trades, clean_book

TRADE_COLS = [
    "aggTradeId","price","quantity","firstTradeId",
    "lastTradeId","timestamp","isBuyerMaker","isBestMatch"
]

@click.command()
@click.option("--use-sample", is_flag=True, help="Use bundled sample CSVs")
@click.option("--trades", default="", help="Path to trades CSV (aggTrades/trades)")
@click.option("--book", default="", help="Path to book CSV (ts,bid,ask)")
def main(use_sample, trades, book):
    base = pathlib.Path(".")
    if use_sample:
        trades = base / "data" / "sample" / "sample_trades.csv"
        book = base / "data" / "sample" / "sample_book.csv"
    else:
        trades = pathlib.Path(trades) if trades else None
        book = pathlib.Path(book) if book else None

    out_dir = base / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    # === Trades ===
    if trades and trades.exists():
        try:
            tdf_raw = pd.read_csv(trades)
            if "timestamp" not in tdf_raw.columns and "T" not in tdf_raw.columns:
                tdf_raw = pd.read_csv(trades, header=None, names=TRADE_COLS)
        except Exception:
            tdf_raw = pd.read_csv(trades, header=None, names=TRADE_COLS)

        tdf = clean_trades(tdf_raw)
        tdf.to_parquet(out_dir / "trades.parquet", index=False)
        print(f"Wrote trades.parquet ({len(tdf)} rows)")
    else:
        print("No trades file provided or path does not exist. Skipping trades.")

    # === Book ===
    if book and book.exists():
        bdf_raw = pd.read_csv(book)
        bdf = clean_book(bdf_raw)
        bdf.to_parquet(out_dir / "book.parquet", index=False)
        print(f"Wrote book.parquet ({len(bdf)} rows)")
    else:
        print("No book file provided or path does not exist.")

if __name__ == "__main__":
    main()
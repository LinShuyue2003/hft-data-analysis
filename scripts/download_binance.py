"""
CLI for downloading historical trades from Binance and saving CSV.
"""
from __future__ import annotations
import click
from src.downloader import download_agg_trades

@click.group()
def cli():
    pass

@cli.command("trades")
@click.option("--symbol", required=True, help="e.g., BTCUSDT")
@click.option("--start", required=True, help="UTC start time, e.g., '2025-08-01 00:00'")
@click.option("--end", required=True, help="UTC end time, e.g., '2025-08-01 06:00'")
@click.option("--out", default="data/raw/binance/BTCUSDT", show_default=True)
def trades(symbol, start, end, out):
    out_file = download_agg_trades(symbol, start, end, out_dir=out)
    print(f"Wrote {out_file}")

if __name__ == "__main__":
    cli()

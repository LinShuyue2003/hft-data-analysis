"""
End-to-end pipeline: load data, clean, compute features, fit, and plot.
"""
from __future__ import annotations
import pathlib
import click
import pandas as pd
import numpy as np

from src.data_cleaning import clean_trades, clean_book
from src.features import mid_from_book, spread_from_book, resample_trades, log_returns, rolling_vol
from src.fit import fit_candidates
from src.viz import hist_plot, ecdf_plot, ts_plot
from src.report import make_report

@click.command()
@click.option("--use-sample", is_flag=True, help="Use bundled synthetic data")
@click.option("--trades", default="", help="Path to trades CSV")
@click.option("--book", default="", help="Path to book CSV")
@click.option("--bar", default="1s", show_default=True, help="Resample rule for trades aggregation")
@click.option("--fits-only", is_flag=True, help="Skip report & plots")
@click.option("--symbol", default="DEMO", help="Symbol label for report")
def main(use_sample, trades, book, bar, fits_only, symbol):
    base = pathlib.Path(".")
    # Resolve inputs
    if use_sample:
        trades = base / "data" / "sample" / "sample_trades.csv"
        book = base / "data" / "sample" / "sample_book.csv"
    else:
        trades = pathlib.Path(trades)
        book = pathlib.Path(book)

    # Load
    def smart_read(path: pathlib.Path, kind: str):
        if not path.exists():
            raise FileNotFoundError(path)
        if path.suffix == ".parquet":
            df = pd.read_parquet(path)
            return df  # 已经清洗过
        elif path.suffix == ".csv":
            df = pd.read_csv(path)
            if kind == "trades":
                from src.data_cleaning import clean_trades
                return clean_trades(df)
            elif kind == "book":
                from src.data_cleaning import clean_book
                return clean_book(df)
            else:
                return df
        else:
            raise ValueError(f"Unsupported file type: {path}")

    tdf = smart_read(trades, "trades")
    bdf = smart_read(book, "book")

    # Compute spread & mid
    bdf["mid"] = (bdf["bid"] + bdf["ask"]) / 2
    bdf["spread"] = (bdf["ask"] - bdf["bid"]).abs()

    # Resample trades to bars
    bars = resample_trades(tdf, rule=bar)
    # Compute returns on mid synchronized to bars via asof merge
    bars = pd.merge_asof(bars.sort_values("ts"), bdf[["ts", "mid"]].sort_values("ts"), on="ts", direction="nearest")
    bars["ret"] = np.log(bars["mid"] / bars["mid"].shift(1))

    # Rolling volatility (e.g., 60 bars ≈ 60s if bar=1s)
    bars["roll_vol"] = bars["ret"].rolling(60, min_periods=10).std()

    # Fitting
    spread_fit = fit_candidates(bdf["spread"].dropna().values, candidates=("expon", "lognorm", "norm"))
    volume_fit = fit_candidates(tdf["qty"].dropna().values, candidates=("lognorm", "expon", "norm"))
    returns_fit = fit_candidates(bars["ret"].abs().dropna().values, candidates=("expon", "lognorm", "norm"))

    # Save tables
    tables_dir = pathlib.Path("results/tables"); tables_dir.mkdir(parents=True, exist_ok=True)
    spread_fit.to_csv(tables_dir / "spread_fit.csv", index=False)
    volume_fit.to_csv(tables_dir / "volume_fit.csv", index=False)
    returns_fit.to_csv(tables_dir / "returns_fit.csv", index=False)

    # Plots
    figs_dir = pathlib.Path("results/figures"); figs_dir.mkdir(parents=True, exist_ok=True)
    hist_plot(bdf["spread"].dropna().values, "Bid–Ask Spread", "Spread", str(figs_dir/"spread_hist.png"))
    hist_plot(tdf["qty"].dropna().values, "Trade Volume", "Qty", str(figs_dir/"volume_hist.png"))
    hist_plot(bars["ret"].dropna().values, "Short-Horizon Returns", "Returns", str(figs_dir/"returns_hist.png"))
    ts_plot(bars.dropna(subset=["roll_vol"]), "ts", "roll_vol", "Rolling Volatility", str(figs_dir/"volatility_timeseries.png"))

    if not fits_only:
        # Produce report
        out_html = "reports/summary.html"
        window = f"{bars['ts'].min()} – {bars['ts'].max()}"
        make_report(symbol=symbol, window=str(window),
                    spread_fit_df=spread_fit, volume_fit_df=volume_fit, returns_fit_df=returns_fit,
                    out_html=out_html)
        print(f"Report written to {out_html}")

    print("Done. Tables in results/tables, figures in results/figures.")

if __name__ == "__main__":
    main()


import os, sys
import click
import pandas as pd

# Make 'src' importable for both `python scripts/run_all.py` and `python -m scripts.run_all`
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in [PROJECT_ROOT, os.path.join(PROJECT_ROOT, "src")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from data_cleaning import clean_trades, clean_book
from features import resample_trades, add_returns, rolling_vol, compute_spread_from_book, merge_trade_book
from fit import fit_candidates, select_candidates_for_variable
from report import build_report, default_context
import viz

def _read_csv_auto(path: str) -> pd.DataFrame:
    """Read CSV and auto-detect headerless Binance aggTrades (8 columns)."""
    try:
        head = pd.read_csv(path, header=None, nrows=1)
        ncols = head.shape[1]
    except Exception:
        return pd.read_csv(path)

    # Heuristic: if 8 columns and no header, assume aggTrades format
    if ncols == 8:
        names = ["a", "p", "q", "f", "l", "T", "m", "M"]
        return pd.read_csv(path, header=None, names=names)
    # Otherwise assume file already has headers
    return pd.read_csv(path)

def _read_any(path: str) -> pd.DataFrame:
    """Read parquet OR CSV (including compressed)."""
    p = str(path).lower()
    if p.endswith(('.parquet', '.pq')):
        return pd.read_parquet(path)
    if p.endswith(('.csv', '.csv.gz', '.csv.zip', '.csv.bz2')):
        return _read_csv_auto(path)
    try:
        return pd.read_parquet(path)
    except Exception:
        return _read_csv_auto(path)

@click.command()
@click.option("--trades", type=click.Path(exists=False), help="Path to trades file (.parquet or .csv)." )
@click.option("--book", type=click.Path(exists=False), default=None, help="Path to top-of-book file (.parquet or .csv)." )
@click.option("--bar", default="1s", show_default=True, help="Bar interval, e.g. 1s, 100ms, 1min." )
@click.option("--symbol", default="BTCUSDT", show_default=True, help="Symbol label for report/figures." )
@click.option("--use-sample", is_flag=True, help="Use bundled sample data without specifying --trades/--book.")
def main(trades: str, book: str, bar: str, symbol: str, use_sample: bool):
    """Run the full analysis pipeline: clean → features → fit → visualize → HTML report."""
    results_dir = os.path.join(PROJECT_ROOT, "results")
    figs_dir = os.path.join(results_dir, "figures"); os.makedirs(figs_dir, exist_ok=True)
    tbls_dir = os.path.join(results_dir, "tables"); os.makedirs(tbls_dir, exist_ok=True)
    rep_dir = os.path.join(PROJECT_ROOT, "reports"); os.makedirs(rep_dir, exist_ok=True)

    if use_sample:
        # Keep your original file names if different
        trades = trades or os.path.join(PROJECT_ROOT, "data", "sample", "sample_trades.parquet")
        if not os.path.exists(trades):
            alt = os.path.join(PROJECT_ROOT, "data", "sample", "sample_trades.csv")
            if os.path.exists(alt): trades = alt
        book = book or os.path.join(PROJECT_ROOT, "data", "sample", "sample_book.parquet")
        if not os.path.exists(book):
            alt = os.path.join(PROJECT_ROOT, "data", "sample", "sample_book.csv")
            if os.path.exists(alt): book = alt

    if not trades or not os.path.exists(trades):
        raise click.UsageError("Trades path missing. Provide --trades or --use-sample.")
    tdf = _read_any(trades)
    tdf = clean_trades(tdf)

    bdf = None
    if book:
        if not os.path.exists(book):
            raise click.UsageError(f"Book path does not exist: {book}")
        bdf = _read_any(book)
        bdf = clean_book(bdf)
        bdf = compute_spread_from_book(bdf)

    # === Features ===
    bars = resample_trades(tdf, rule=bar)
    bars = add_returns(bars, price_col="close")
    bars["vol_roll"] = rolling_vol(bars, col="logret", window=60, min_periods=20)
    if bdf is not None and {"mid","spread_bp"}.issubset(bdf.columns):
        bars = merge_trade_book(bars, bdf)

    # === Fitting per variable ===
    # volume from trades (tick size) and from bars (vol): both are useful; we'll use trades qty
    fit_tables = {}
    def _save_table(df, name):
        # Round numeric columns
        df = df.round(4)

        # Format params column nicely if exists
        if "params" in df.columns:
            def fmt_params(p):
                if isinstance(p, str):
                    return p  # already string
                try:
                    return "(" + ", ".join([f"{float(x):.4f}" for x in p]) + ")"
                except Exception:
                    return str(p)
            df["params"] = df["params"].apply(fmt_params)

        path = os.path.join(tbls_dir, f"{name}.csv")
        df.to_csv(path, index=False)
        return path

    # spread
    if "spread_bp" in bars.columns:
        cand = select_candidates_for_variable("spread")
        df_fit = fit_candidates(bars["spread_bp"].values, cand, positive_only=True)
        fit_tables["spread_fit"] = _save_table(df_fit, "spread_fit")

    # volume (tick-level qty)
    if "qty" in tdf.columns:
        cand = select_candidates_for_variable("volume")
        df_fit = fit_candidates(tdf["qty"].values, cand, positive_only=True)
        fit_tables["volume_fit"] = _save_table(df_fit, "volume_fit")

    # returns
    if "logret" in bars.columns:
        cand = select_candidates_for_variable("returns")
        df_fit = fit_candidates(bars["logret"].values, cand, positive_only=False)
        fit_tables["returns_fit"] = _save_table(df_fit, "returns_fit")
        # absret
        cand = select_candidates_for_variable("absret")
        df_fit = fit_candidates(bars["absret"].values, cand, positive_only=True)
        fit_tables["absret_fit"] = _save_table(df_fit, "absret_fit")

    # === Figures ===
    figs = []

    # price and volatility
    if {"close","vol_roll"}.issubset(bars.columns):
        p = os.path.join(figs_dir, "ts_price_vol.png")
        viz.ts_plot(bars[["close","vol_roll"]].dropna(), ["close","vol_roll"], title="Close & Rolling Volatility", path=p)
        figs.append({"title":"Close & Rolling Volatility","path":os.path.relpath(p, rep_dir),"caption":"Bar close price and rolling volatility."})

    # spread visuals
    if "spread_bp" in bars.columns:
        x = bars["spread_bp"].dropna().values
        p1 = os.path.join(figs_dir, "spread_hist_ecdf.png")
        viz.hist_with_ecdf(x, title="Spread (bp)", path=p1)
        p2 = os.path.join(figs_dir, "spread_qq_t.png")
        viz.qq_plot(x, dist_name="lognorm", path=p2)
        p3 = os.path.join(figs_dir, "spread_tail.png")
        viz.loglog_tail_plot(x, path=p3)
        figs += [
            {"title":"Spread histogram & ECDF","path":os.path.relpath(p1, rep_dir),"caption":"Distribution of spread in basis points."},
            {"title":"Spread QQ vs lognormal","path":os.path.relpath(p2, rep_dir),"caption":"QQ plot for lognormal fit."},
            {"title":"Spread tail (CCDF)","path":os.path.relpath(p3, rep_dir),"caption":"Heavy-tail inspection in log-log scale."},
        ]

    # volume visuals (tick qty)
    if "qty" in tdf.columns:
        x = tdf["qty"].dropna().values
        p1 = os.path.join(figs_dir, "volume_hist_ecdf.png")
        viz.hist_with_ecdf(x, title="Trade size (qty)", path=p1)
        p2 = os.path.join(figs_dir, "volume_qq_lognorm.png")
        viz.qq_plot(x, dist_name="lognorm", path=p2)
        p3 = os.path.join(figs_dir, "volume_tail.png")
        viz.loglog_tail_plot(x, path=p3)
        figs += [
            {"title":"Trade size histogram & ECDF","path":os.path.relpath(p1, rep_dir),"caption":"Distribution of trade sizes."},
            {"title":"Trade size QQ vs lognormal","path":os.path.relpath(p2, rep_dir),"caption":"QQ plot for lognormal fit."},
            {"title":"Trade size tail (CCDF)","path":os.path.relpath(p3, rep_dir),"caption":"Heavy-tail inspection of trade sizes."},
        ]

    # returns visuals
    if "logret" in bars.columns:
        x = bars["logret"].dropna().values
        p1 = os.path.join(figs_dir, "returns_hist_ecdf.png")
        viz.hist_with_ecdf(x, title="Log returns", path=p1)
        p2 = os.path.join(figs_dir, "returns_qq_t.png")
        viz.qq_plot(x, dist_name="t", path=p2)
        figs += [
            {"title":"Log returns histogram & ECDF","path":os.path.relpath(p1, rep_dir),"caption":"Distribution of bar log returns."},
            {"title":"Returns QQ vs Student-t","path":os.path.relpath(p2, rep_dir),"caption":"QQ plot for Student-t fit."},
        ]
        # |returns| ACF
        p3 = os.path.join(figs_dir, "acf_abs_returns.png")
        viz.acf_abs_returns(bars["absret"].values, nlags=60, path=p3)
        figs.append({"title":"ACF of |returns|","path":os.path.relpath(p3, rep_dir),"caption":"Volatility clustering diagnostic."})

    # intraday heatmap (use spread_bp if present, else absret)
    if "spread_bp" in bars.columns:
        p = os.path.join(figs_dir, "heatmap_spread.png")
        viz.intraday_heatmap(bars, value_col="spread_bp", path=p)
        figs.append({"title":"Intraday heatmap (spread bp)","path":os.path.relpath(p, rep_dir),"caption":"Minute × date mean spread."})
    elif "absret" in bars.columns:
        p = os.path.join(figs_dir, "heatmap_absret.png")
        viz.intraday_heatmap(bars, value_col="absret", path=p)
        figs.append({"title":"Intraday heatmap (|returns|)","path":os.path.relpath(p, rep_dir),"caption":"Minute × date mean |returns|."})

    # === Tables for report context ===
    import pandas as pd
    stats_tables = []
    for name, csvp in fit_tables.items():
        df = pd.read_csv(csvp)
        # Round floats and truncate long strings
        df = df.round(4)
        if "params" in df.columns:
            df["params"] = df["params"].astype(str).apply(lambda s: s[:40] + "..." if len(s) > 40 else s)
        # Add CSS class 'stats'
        stats_tables.append({"name": name, "table": df.to_html(index=False, classes="stats", justify="center")})

    # === Build report ===
    ctx = default_context(title="HFT Microstructure Summary", symbol=symbol, bar=bar)
    ctx["figures"] = figs
    ctx["stats_tables"] = stats_tables
    ctx["notes"] = [
        "Spreads and trade sizes show right heavy tails (lognormal/gamma/pareto candidates).",            "Short-horizon returns exhibit symmetric heavy tails (Student-t) and volatility clustering (|returns| ACF).",            "When order book is available, spread in bps is computed against midprice.",
    ]
    out_html = os.path.join(PROJECT_ROOT, "reports", "summary.html")
    build_report(out_html, ctx)
    print(f"[OK] Report saved to: {out_html}")

if __name__ == "__main__":
    main()

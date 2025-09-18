
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats

"""
Visualization utilities: hist/ECDF/QQ/log-log tail/intraday heatmap/ACF.
"""

def hist_with_ecdf(x, bins=50, title="", path=None):
    """Draw histogram and ECDF side-by-side and save to path if provided."""
    x = np.asarray(x)
    x = x[~np.isnan(x)]
    fig = plt.figure(figsize=(10,4))
    ax1 = fig.add_subplot(1,2,1)
    ax2 = fig.add_subplot(1,2,2)
    ax1.hist(x, bins=bins, alpha=0.8)
    ax1.set_title(f"Histogram | {title}")
    xs = np.sort(x)
    ecdf = np.arange(1, xs.size+1)/xs.size
    ax2.plot(xs, ecdf)
    ax2.set_ylim(0,1)
    ax2.set_title(f"ECDF | {title}")
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=120)
    plt.close(fig)

def qq_plot(x, dist_name="norm", path=None):
    """QQ plot versus a theoretical distribution."""
    x = np.asarray(x)
    x = x[~np.isnan(x)]
    dist = getattr(stats, dist_name)
    params = dist.fit(x)
    (osm, osr), (slope, intercept, r) = stats.probplot(x, dist=dist, sparams=params)
    fig, ax = plt.subplots(figsize=(5,4))
    ax.scatter(osm, osr, s=10)
    xs = np.linspace(np.min(osm), np.max(osm), 100)
    ax.plot(xs, slope*xs + intercept, lw=1)
    ax.set_title(f"QQ vs {dist_name}")
    if path:
        fig.savefig(path, dpi=120)
    plt.close(fig)

def loglog_tail_plot(x, path=None):
    """Complementary CDF on log-log scale to inspect heavy tails."""
    x = np.asarray(x)
    x = x[~np.isnan(x)]
    x = x[x > 0]
    if x.size == 0:
        return
    xs = np.sort(x)
    ccdf = 1.0 - np.arange(1, xs.size+1)/xs.size
    fig, ax = plt.subplots(figsize=(5,4))
    ax.loglog(xs, ccdf, marker=".", linestyle="none")
    ax.set_title("Log-Log Tail (CCDF)")
    if path:
        fig.savefig(path, dpi=120)
    plt.close(fig)

def ts_plot(df, cols, title="", path=None):
    """Simple time series plot for selected columns."""
    fig, ax = plt.subplots(figsize=(10,4))
    df[cols].plot(ax=ax)
    ax.set_title(title)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=120)
    plt.close(fig)

def intraday_heatmap(df_bar: pd.DataFrame, value_col: str, path=None):
    """Minute-of-day x date heatmap for an aggregated metric."""
    d = df_bar.copy().sort_index()
    d["date"] = d.index.date
    d["min_of_day"] = d.index.hour*60 + d.index.minute
    pivot = d.pivot_table(index="min_of_day", columns="date", values=value_col, aggfunc="mean")
    fig, ax = plt.subplots(figsize=(6,4))
    im = ax.imshow(pivot.values, aspect="auto", origin="lower")
    ax.set_title(f"Intraday heatmap: {value_col}")
    ax.set_xlabel("Date"); ax.set_ylabel("Minute of day")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=120)
    plt.close(fig)

def acf_abs_returns(abs_returns: np.ndarray, nlags: int = 60, path=None):
    """Plot ACF of absolute returns to highlight volatility clustering."""
    from statsmodels.tsa.stattools import acf
    import numpy as np
    import matplotlib.pyplot as plt

    x = np.asarray(abs_returns)
    x = x[~np.isnan(x)]
    acf_vals = acf(x, nlags=nlags, fft=True, missing="conservative")

    fig, ax = plt.subplots(figsize=(6,4))
    try:
        # Older matplotlib (<=3.7) accepted use_line_collection
        ax.stem(range(len(acf_vals)), acf_vals, use_line_collection=True)
    except TypeError:
        # Newer matplotlib (>=3.8) removed it
        ax.stem(range(len(acf_vals)), acf_vals)
    ax.set_title("ACF of |returns|")
    ax.set_xlabel("Lag")
    ax.set_ylabel("ACF")
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=120)
    plt.close(fig)


import os
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS = os.path.join(PROJECT_ROOT, "results")
TABLES = os.path.join(RESULTS, "tables")

def _read_csv_safe(path):
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

def summarize_spread(bars):
    """Return median/iqr of spread in basis points."""
    if "spread_bp" not in bars.columns:
        return None
    s = bars["spread_bp"].dropna()
    return {
        "median_bp": float(np.median(s)),
        "p25_bp": float(np.quantile(s, 0.25)),
        "p75_bp": float(np.quantile(s, 0.75)),
        "n": int(s.shape[0]),
    }

def realized_vol_stats(bars):
    """Compute realized volatility stats over the whole window (not annualized)."""
    import numpy as np
    import pandas as pd

    if "logret" not in bars.columns:
        return None

    # Use the same-length index as the series (avoid length mismatch)
    r = bars["logret"].dropna()
    if r.empty:
        return None

    rv_total = float(np.square(r).sum())

    per_hour = None
    if isinstance(r.index, pd.DatetimeIndex):
        # 'H' -> 'h' to avoid FutureWarning; group with matching index length
        key = r.index.floor("h")
        per_hour = r.groupby(key).apply(lambda x: float(np.square(x).sum()))

    return {
        "rv_total": rv_total,
        "rv_per_hour_min": float(per_hour.min()) if per_hour is not None and len(per_hour) else None,
        "rv_per_hour_median": float(per_hour.median()) if per_hour is not None and len(per_hour) else None,
        "rv_per_hour_max": float(per_hour.max()) if per_hour is not None and len(per_hour) else None,
    }

def top_fit_params(df, name):
    """Get top-ranked distribution and key params from a fit table."""
    if df.empty: return None
    row = df.iloc[0]
    return {
        "name": name,
        "best_dist": row.get("distribution"),
        "params": str(row.get("params"))[:80],
        "aic": float(row.get("aic")) if "aic" in row else None,
        "ks_p": float(row.get("ks_p")) if "ks_p" in row else None,
    }

def _parse_params_numbers(params_str: str):
    """Extract all floats from a free-form params string like '(np.float64(1.23), 0.0, 4.5e-6)'."""
    import re
    return [float(x) for x in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", str(params_str))]

def student_t_nu(returns_fit):
    """Extract nu (df) parameter of Student-t if present (SciPy t.fit -> df, loc, scale)."""
    if returns_fit.empty:
        return None
    t_rows = returns_fit[returns_fit["distribution"].str.lower() == "t"]
    if t_rows.empty:
        return None
    nums = _parse_params_numbers(t_rows.iloc[0]["params"])
    return float(nums[0]) if nums else None

def pareto_alpha(volume_fit):
    """Extract alpha (shape) of Pareto if present (SciPy pareto: b, loc, scale)."""
    if volume_fit.empty:
        return None
    p_rows = volume_fit[volume_fit["distribution"].str.lower() == "pareto"]
    if p_rows.empty:
        return None
    nums = _parse_params_numbers(p_rows.iloc[0]["params"])
    return float(nums[0]) if nums else None

if __name__ == "__main__":
    # You can dump a feather/parquet of bars in run_all, or re-create here if needed.
    # For now, we read fit tables and (optionally) a cached bars parquet if you exported it.
    spread_fit = _read_csv_safe(os.path.join(TABLES, "spread_fit.csv"))
    volume_fit = _read_csv_safe(os.path.join(TABLES, "volume_fit.csv"))
    returns_fit = _read_csv_safe(os.path.join(TABLES, "returns_fit.csv"))

    # If you exported bars to results/bars.parquet in run_all, you can load it:
    bars_path = os.path.join(RESULTS, "bars.parquet")
    bars = pd.read_parquet(bars_path) if os.path.exists(bars_path) else pd.DataFrame()
    if not bars.empty and "ts" in bars.columns:
        bars["ts"] = pd.to_datetime(bars["ts"])
        bars = bars.set_index("ts").sort_index()

    spread_stats = summarize_spread(bars) if not bars.empty else None
    rv_stats = realized_vol_stats(bars) if not bars.empty else None

    summary = {
        "spread_best": top_fit_params(spread_fit, "spread"),
        "volume_best": top_fit_params(volume_fit, "volume"),
        "returns_best": top_fit_params(returns_fit, "returns"),
        "student_t_nu": student_t_nu(returns_fit),
        "pareto_alpha": pareto_alpha(volume_fit),
        "spread_stats": spread_stats,
        "rv_stats": rv_stats,
    }
    print(summary)

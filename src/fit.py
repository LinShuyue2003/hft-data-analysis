"""
Distribution fitting and model selection utilities.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats

def _aic(nll, k):
    return 2*k + 2*nll

def _bic(nll, k, n):
    return np.log(n)*k + 2*nll

def fit_candidates(x: np.ndarray, candidates=("norm", "lognorm", "expon")) -> pd.DataFrame:
    """
    Fits candidate distributions using MLE and ranks by AIC and BIC.
    Returns a DataFrame with parameters and metrics.
    """
    x = np.asarray(x)
    x = x[np.isfinite(x)]
    x = x[~np.isnan(x)]
    x = x[x > 0] if (x >= 0).all() else x  # crude guard for strictly positive dists

    rows = []
    n = len(x)
    for name in candidates:
        dist = getattr(stats, name)
        params = dist.fit(x)
        # Negative log likelihood
        nll = -np.sum(dist.logpdf(x, *params))
        k = len(params)
        aic = _aic(nll, k)
        bic = _bic(nll, k, n)
        # KS test
        ks_stat, ks_p = stats.kstest(x, name, args=params)
        rows.append({
            "distribution": name,
            "params": params,
            "AIC": aic,
            "BIC": bic,
            "KS_stat": ks_stat,
            "KS_p": ks_p,
        })
    df = pd.DataFrame(rows).sort_values(["AIC", "BIC"]).reset_index(drop=True)
    return df


import numpy as np
import pandas as pd
from typing import List, Dict, Any
from scipy import stats

"""
Distribution fitting utilities with extended candidates and diagnostics.
"""

def select_candidates_for_variable(var: str) -> List[str]:
    """Return default distribution candidates for a given variable type.

    var in {"spread", "volume", "returns", "absret"}
    """
    mapping = {
        "spread": ["lognorm","gamma","expon","pareto"],
        "volume": ["lognorm","gamma","pareto"],
        "returns": ["t","laplace","norm"],
        "absret": ["expon","lognorm","gamma"],
    }
    return mapping.get(var, ["norm"])

def _anderson_ad_stat(data: np.ndarray, dist_name: str) -> float:
    """Compute an Anderson–Darling-like statistic.

    For distributions unsupported by scipy.stats.anderson, we approximate by
    transforming data to uniform via CDF and using the classic AD formula.
    """
    data = np.asarray(data)
    data = data[~np.isnan(data)]
    n = data.size
    if n == 0:
        return np.nan
    dist = getattr(stats, dist_name)
    params = dist.fit(data)
    u = np.clip(dist.cdf(data, *params), 1e-12, 1 - 1e-12)
    u = np.sort(u)
    i = np.arange(1, n + 1)
    ad = -n - (1.0 / n) * np.sum((2 * i - 1) * (np.log(u) + np.log(1 - u[::-1])))
    return float(ad)

def fit_candidates(data: np.ndarray, candidates: List[str], positive_only: bool = False) -> pd.DataFrame:
    """Fit multiple distributions and return a ranked table by AIC.

    Columns: distribution, params, aic, bic, ks_stat, ks_p, ad_stat
    """
    x = np.asarray(data).astype("float64")
    x = x[~np.isnan(x)]
    if positive_only:
        x = x[x > 0]
    rows: List[Dict[str, Any]] = []
    if x.size == 0:
        return pd.DataFrame(columns=["distribution","params","aic","bic","ks_stat","ks_p","ad_stat"])
    for name in candidates:
        try:
            dist = getattr(stats, name)
            params = dist.fit(x)
            ll = np.sum(dist.logpdf(x, *params))
            k = len(params)
            aic = 2 * k - 2 * ll
            bic = np.log(x.size) * k - 2 * ll
            ks_stat, ks_p = stats.kstest(x, name, args=params)
            ad_stat = _anderson_ad_stat(x, name)
            rows.append({
                "distribution": name,
                "params": params,
                "aic": aic,
                "bic": bic,
                "ks_stat": ks_stat,
                "ks_p": ks_p,
                "ad_stat": ad_stat,
            })
        except Exception:
            continue
    if not rows:
        return pd.DataFrame(columns=["distribution","params","aic","bic","ks_stat","ks_p","ad_stat"])
    return pd.DataFrame(rows).sort_values(["aic","bic"]).reset_index(drop=True)

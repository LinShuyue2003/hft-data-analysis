
import numpy as np
from fit import fit_candidates, select_candidates_for_variable

def test_fit_candidates_basic():
    x = np.random.lognormal(mean=0, sigma=1, size=500)
    df = fit_candidates(x, select_candidates_for_variable("volume"), positive_only=True)
    assert not df.empty
    assert set(["distribution","aic","bic"]).issubset(df.columns)

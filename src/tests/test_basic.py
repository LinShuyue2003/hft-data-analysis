import numpy as np
from fit import fit_distributions

def test_fit_nonempty():
    data = np.random.lognormal(mean=0, sigma=1, size=100)
    res = fit_distributions(data, ["lognorm","gamma"]).reset_index(drop=True)
    assert not res.empty
    assert "aic" in res.columns

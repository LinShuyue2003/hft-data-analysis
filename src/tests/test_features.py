
import pandas as pd
import numpy as np
from features import resample_trades, add_returns

def test_resample_and_returns():
    ts = pd.date_range("2025-01-01", periods=100, freq="S")
    df = pd.DataFrame({"ts": ts, "price": np.linspace(100, 101, 100), "qty": 1.0})
    bars = resample_trades(df, rule="10s")
    bars = add_returns(bars)
    assert "close" in bars.columns and "logret" in bars.columns

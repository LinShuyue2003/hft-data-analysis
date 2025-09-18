
import pandas as pd
from data_cleaning import to_datetime

def test_to_datetime_tz():
    s = pd.to_datetime(["2024-01-01T00:00:00Z","2024-01-01T00:00:01Z"])
    s = s.tz_convert("UTC") if getattr(s.dtype, 'tz', None) is not None else s.tz_localize("UTC")
    out = to_datetime(s)
    assert getattr(out.dtype, 'tz', None) is None

"""
Binance REST downloader (historical aggregated trades) and helpers.
"""
from __future__ import annotations
import time
import math
import json
import pathlib
from datetime import datetime, timezone
from typing import Optional, List
import requests
import pandas as pd

BASE = "https://api.binance.com"

def _to_ms(dt_str: str) -> int:
    dt = pd.to_datetime(dt_str, utc=True)
    return int(dt.timestamp() * 1000)

def download_agg_trades(symbol: str, start: str, end: str, out_dir: str, limit: int = 1000) -> str:
    """
    Downloads aggregated trades between [start, end] into a CSV.
    Returns the output file path.
    """
    s_ms, e_ms = _to_ms(start), _to_ms(end)
    symbol = symbol.upper()
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    last_id: Optional[int] = None
    while True:
        params = {"symbol": symbol, "limit": limit}
        if last_id is not None:
            params["fromId"] = last_id + 1
        else:
            params.update({"startTime": s_ms, "endTime": min(e_ms, s_ms + 60*60*1000)})  # 1h chunks

        r = requests.get(f"{BASE}/api/v3/aggTrades", params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        for d in data:
            ts = d["T"]  # ms
            if ts < s_ms or ts > e_ms:
                continue
            rows.append({
                "ts": ts,
                "price": float(d["p"]),
                "qty": float(d["q"]),
                "is_maker": bool(d["m"]),
                "first_id": d["a"],
            })
        last_id = data[-1]["a"]
        # Respect rate limits
        time.sleep(0.2)

        # Stop if we passed end
        if rows and rows[-1]["ts"] >= e_ms:
            break

    df = pd.DataFrame(rows)
    out_file = out_dir / f"{symbol}_aggTrades_{start.replace(' ', '_')}_{end.replace(' ', '_')}.csv"
    df.to_csv(out_file, index=False)
    return str(out_file)

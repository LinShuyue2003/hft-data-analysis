
"""
Binance REST downloader with retry/backoff for aggregated trades.
"""
from __future__ import annotations
import time, math, json, pathlib, sys
import pandas as pd
import requests
from typing import Optional

BASE = "https://api.binance.com/api/v3/aggTrades"

def _sleep_backoff(attempt: int):
    time.sleep(min(60, 2 ** attempt))

def _fetch(symbol: str, start_ms: int, end_ms: int, limit: int = 1000, session: Optional[requests.Session] = None):
    """Fetch a page from aggTrades with retries and 429 handling."""
    url = BASE
    ses = session or requests.Session()
    params = {"symbol": symbol.upper(), "startTime": start_ms, "endTime": end_ms, "limit": limit}
    attempt = 0
    while True:
        try:
            r = ses.get(url, params=params, timeout=15)
            if r.status_code == 429:
                _sleep_backoff(attempt); attempt += 1; continue
            if r.status_code >= 500:
                _sleep_backoff(attempt); attempt += 1; continue
            r.raise_for_status()
            data = r.json()
            return data
        except Exception:
            if attempt >= 6:
                raise
            _sleep_backoff(attempt); attempt += 1

def download_agg_trades(symbol: str, start_ms: int, end_ms: int, out_csv: str):
    ses = requests.Session()
    cur = start_ms
    rows = []
    while cur < end_ms:
        batch = _fetch(symbol, cur, min(cur + 60_000, end_ms), session=ses)
        if not batch:
            cur += 60_000; continue
        for it in batch:
            rows.append({
                "T": it.get("T"), "p": float(it.get("p")), "q": float(it.get("q"))
            })
            cur = max(cur, it.get("T")+1)
        time.sleep(0.1)
    df = pd.DataFrame(rows).rename(columns={"T":"ts","p":"price","q":"qty"})
    pathlib.Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    return out_csv

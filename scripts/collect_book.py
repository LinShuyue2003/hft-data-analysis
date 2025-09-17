"""
Collects best bid/ask via Binance WebSocket and writes CSV rows.
"""
from __future__ import annotations
import json
import time
from datetime import datetime, timezone
import pathlib
import click
from websocket import create_connection
import pandas as pd

@click.command()
@click.option("--symbol", required=True, help="e.g., btcusdt")
@click.option("--minutes", default=5, show_default=True, type=int)
@click.option("--out", default="data/raw/binance/BTCUSDT", show_default=True)
def main(symbol: str, minutes: int, out: str):
    symbol = symbol.lower()
    url = f"wss://stream.binance.com:9443/ws/{symbol}@bookTicker"
    ws = create_connection(url, timeout=5)
    end_time = time.time() + minutes * 60
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    out_file = out / f"{symbol}_book_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.csv"
    with open(out_file, "w") as f:
        f.write("ts,bid,ask\n")
        while time.time() < end_time:
            try:
                msg = json.loads(ws.recv())
                # event time in ms
                ts = msg.get("E", int(time.time()*1000))
                bid = float(msg["b"])
                ask = float(msg["a"])
                f.write(f"{ts},{bid},{ask}\n")
            except Exception:
                # reconnect
                try:
                    ws.close()
                except Exception:
                    pass
                time.sleep(1)
                ws = create_connection(url, timeout=5)
    ws.close()
    print(f"Wrote {out_file}")

if __name__ == "__main__":
    main()


import json, time, gzip, sys
import websocket

"""
Minimal WebSocket collector with heartbeat and simple reconnect.
"""

def run_ws(url, out_path, ping_interval=15):
    """Connect to WS, write lines to file with periodic heartbeats."""
    def on_message(ws, message):
        with open(out_path, 'a', encoding='utf-8') as f:
            f.write(message.strip() + '\n')

    def on_error(ws, error):
        print("[WS] error:", error, file=sys.stderr)

    def on_close(ws, close_status_code, close_msg):
        print("[WS] closed", close_status_code, close_msg)

    ws = websocket.WebSocketApp(url, on_message=on_message, on_error=on_error, on_close=on_close)
    while True:
        try:
            ws.run_forever(ping_interval=ping_interval, ping_timeout=10)
        except Exception as e:
            print("[WS] reconnect after error:", e, file=sys.stderr)
            time.sleep(3)
        else:
            break

"""
Generate a simple HTML report with embedded figures and fit tables.
"""
from __future__ import annotations
import json
import pathlib
from jinja2 import Template

TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>HFT Microstructure Report</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; }
    h1, h2 { margin: 0.4em 0; }
    .fig { margin: 16px 0; }
    table { border-collapse: collapse; margin: 12px 0; }
    td, th { border: 1px solid #ddd; padding: 6px 10px; text-align: right; }
    th { background: #fafafa; }
    .caption { color: #666; font-size: 0.9em; }
  </style>
</head>
<body>
  <h1>HFT Microstructure Analysis</h1>
  <p class="caption">Symbol: {{ symbol }} | Data window: {{ window }}</p>

  <h2>Distributions & Fits</h2>
  <div class="fig">
    <img src="../results/figures/spread_hist.png" width="600">
    <div class="caption">Bid–ask spread histogram</div>
  </div>
  <div class="fig">
    <img src="../results/figures/volume_hist.png" width="600">
    <div class="caption">Trade volume histogram</div>
  </div>
  <div class="fig">
    <img src="../results/figures/returns_hist.png" width="600">
    <div class="caption">Short-horizon returns histogram (mid-price)</div>
  </div>

  <h2>Roll Volatility</h2>
  <div class="fig">
    <img src="../results/figures/volatility_timeseries.png" width="800">
    <div class="caption">Rolling volatility (e.g., on 1s bars)</div>
  </div>

  <h2>Fit Tables</h2>
  <h3>Spread</h3>
  {{ spread_table|safe }}
  <h3>Volume</h3>
  {{ volume_table|safe }}
  <h3>Returns (abs)</h3>
  {{ returns_table|safe }}

</body>
</html>
"""

def render_table_html(df):
    if df is None: return "<p>No data.</p>"
    return df.to_html(index=False, float_format=lambda x: f"{x:.4g}")

def make_report(symbol: str, window: str, spread_fit_df, volume_fit_df, returns_fit_df, out_html: str):
    tpl = Template(TEMPLATE)
    html = tpl.render(
        symbol=symbol,
        window=window,
        spread_table=render_table_html(spread_fit_df),
        volume_table=render_table_html(volume_fit_df),
        returns_table=render_table_html(returns_fit_df),
    )
    pathlib.Path(out_html).write_text(html, encoding="utf-8")
    return out_html

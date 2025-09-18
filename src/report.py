
import os
from datetime import datetime
from typing import Dict, Any, List

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    _HAS_JINJA2 = True
except Exception:
    _HAS_JINJA2 = False

"""
HTML report builder. If Jinja2 is unavailable, falls back to a minimal template.
"""

def build_report(output_html: str, context: Dict[str, Any], templates_dir: str = "templates") -> None:
    """Render the report to HTML."""
    os.makedirs(os.path.dirname(output_html) or ".", exist_ok=True)
    if _HAS_JINJA2:
        env = Environment(loader=FileSystemLoader(templates_dir), autoescape=select_autoescape())
        tpl = env.get_template("report.html")
        html = tpl.render(**context)
    else:
        rows_figs = []
        for fig in context.get("figures", []):
            rows_figs.append(f"""
            <div class='card'>
                <h3>{fig.get('title','')}</h3>
                <img src="{fig.get('path','')}" style="max-width:100%"/>
                <p class='caption'>{fig.get('caption','')}</p>
            </div>
            """.strip())
        rows_tbls = []
        for tb in context.get("stats_tables", []):
            rows_tbls.append(f"""
            <div class='card'>
                <h3>{tb.get('name','')}</h3>
                {tb.get('table','')}
            </div>
            """.strip())
        notes_html = "".join([f"<li>{n}</li>" for n in context.get("notes", [])])
        html = f"""
        <html><head><meta charset='utf-8'><title>{context.get('title','HFT Report')}</title>
        <style>
        body {{ font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 24px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 16px; }}
        .card {{ border: 1px solid #eee; border-radius: 12px; padding: 12px; box-shadow: 0 1px 6px rgba(0,0,0,0.06);}}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 6px; text-align: right; }}
        th {{ background:#fafafa; text-align: left; }}
        </style></head><body>
        <h1>{context.get('title','HFT Report')}</h1>
        <div>Generated at {context.get('generated_at','')} · Symbol {context.get('symbol','')} · Bar {context.get('bar','')}</div>
        <h2>Key Figures</h2>
        <div class='grid'>{''.join(rows_figs)}</div>
        <h2>Statistics</h2>
        <div class='grid'>{''.join(rows_tbls)}</div>
        <h2>Notes</h2><ul>{notes_html}</ul>
        </body></html>"""
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)

def default_context(title: str, symbol: str, bar: str) -> Dict[str, Any]:
    """Create a default context shell."""
    return {
        "title": title,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "symbol": symbol,
        "bar": bar,
        "stats_tables": [],
        "figures": [],
        "notes": [],
    }

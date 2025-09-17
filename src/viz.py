"""
Matplotlib/Plotly visualizations.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from plotly.offline import plot
import plotly.graph_objs as go
from typing import Optional

def hist_plot(data, title, xlabel, outfile: Optional[str] = None, bins=50, density=True):
    fig, ax = plt.subplots(figsize=(8,5))
    ax.hist(data, bins=bins, density=density, alpha=0.7)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Density" if density else "Count")
    ax.grid(True, alpha=0.3)
    if outfile:
        fig.savefig(outfile, dpi=160, bbox_inches="tight")
    plt.close(fig)

def ecdf_plot(data, title, xlabel, outfile: Optional[str] = None):
    x = np.sort(data)
    y = np.arange(1, len(x)+1) / len(x)
    fig, ax = plt.subplots(figsize=(8,5))
    ax.plot(x, y, lw=1.5)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Empirical CDF")
    ax.grid(True, alpha=0.3)
    if outfile:
        fig.savefig(outfile, dpi=160, bbox_inches="tight")
    plt.close(fig)

def ts_plot(ts_df: pd.DataFrame, x_col: str, y_col: str, title: str, outfile: Optional[str] = None):
    fig, ax = plt.subplots(figsize=(10,4))
    ax.plot(ts_df[x_col], ts_df[y_col], lw=1.0)
    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel(y_col)
    ax.grid(True, alpha=0.3)
    if outfile:
        fig.savefig(outfile, dpi=160, bbox_inches="tight")
    plt.close(fig)

def plotly_timeseries(ts_df: pd.DataFrame, x_col: str, y_col: str, title: str, html_out: Optional[str] = None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts_df[x_col], y=ts_df[y_col], mode="lines", name=y_col))
    fig.update_layout(title=title, xaxis_title="Time", yaxis_title=y_col, template="plotly_white")
    if html_out:
        plot(fig, filename=html_out, auto_open=False, include_plotlyjs="cdn")

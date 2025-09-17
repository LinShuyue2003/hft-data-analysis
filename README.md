# HFT Data Analysis (Crypto Tick-Level)

A compact, resume-ready project that analyzes **tick-level (trade & order book)** data on crypto markets to study:
- **Bid–ask spread distribution**
- **Trade volume distribution**
- **Short-horizon volatility patterns**

It includes **data cleaning**, **distribution fitting** (AIC/BIC, KS test), and **visualizations**. You can run a **quick demo** using the bundled sample data, or download/collect live data from Binance.

---

## 🚀 Quick Start

```bash
# 1) Create a virtual environment (Python 3.9+ recommended)
python -m venv .venv && source .venv/bin/activate    # (Windows) .venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run end-to-end demo with bundled sample data
python scripts/run_all.py --use-sample

open reports/summary.html   # Windows: start reports\summary.html
```

To use **real data**, see the *Data Options* section below.

---

## 📦 Project Structure

```
hft-data-analysis/
├─ data/
│  ├─ raw/                 # downloaded data (Binance REST/WebSocket)
│  └─ sample/              # small sample CSVs that work offline
├─ src/                    # core library code
├─ scripts/                # CLI scripts
├─ results/                # figures + tables
├─ reports/                # generated HTML report
├─ requirements.txt        # dependencies
├─ README.md               # this file
└─ LICENSE                 # MIT
```

---

## 🧠 What you’ll learn / show on resume

- Data cleaning and normalization for **tick-level microstructure data**
- Modeling **spread, volume, short-horizon returns** and volatility
- Fitting **lognormal, normal, exponential, power-law**; model selection via **AIC/BIC**, sanity via **KS test**
- Publishing a clean, documented, **open-source** analytics project

---

## 🧰 Data Options

### Option A — Use bundled sample data (instant)
Good for quickly running the pipeline and generating plots.
- `data/sample/sample_trades.csv` (synthetic trades)
- `data/sample/sample_book.csv`   (synthetic best bid/ask)

### Option B — Download historical trades from Binance (REST)
```bash
python scripts/download_binance.py trades --symbol BTCUSDT --start "2025-08-01" --end "2025-08-01 06:00" --out data/raw/binance/BTCUSDT
```
This uses **/api/v3/aggTrades** and paginates. No API key needed for public endpoints.

### Option C — Collect live best bid/ask for spreads (WebSocket)
```bash
python scripts/collect_book.py --symbol btcusdt --minutes 10 --out data/raw/binance/BTCUSDT
```
This listens to `wss://stream.binance.com:9443/ws/<symbol>@bookTicker` and stores timestamped bid/ask snapshots.

> **Note**: Binance spot API is rate-limited and live book snapshots are best-effort. For historical *book* data, use a third-party dataset (e.g., CryptoTick) and place CSVs under `data/raw/` with columns: `ts, bid, ask` (UTC ISO or epoch ms).

---

## 🔬 Analyses

- **Spread distribution**: histogram, empirical CDF, fitted distributions
- **Volume distribution**: single-trade and 1s/5s aggregation
- **Short-horizon returns & volatility**: log returns on mid-price; rolling sigma

Key outputs go to `results/figures` and `results/tables` and are embedded into `reports/summary.html`.

---

## 🧪 Run individual steps

```bash
# Clean and prepare data
python scripts/prepare_data.py --use-sample

# Generate figures + tables
python scripts/run_all.py --use-sample

# Distribution fits only
python scripts/run_all.py --use-sample --fits-only
```

---

## 🖼️ Example Figures (after running)
- `spread_hist.png`: Bid–ask spread histogram
- `volume_hist.png`: Trade volume histogram
- `returns_hist.png`: Short-horizon returns histogram
- `volatility_timeseries.png`: Rolling volatility

---

## 📊 Reproducibility

- All scripts are deterministic given the same CSV inputs.
- Use `--seed` to control randomness where applicable.

---

## 📄 License

This project is licensed under the MIT License. See `LICENSE` for details.

---
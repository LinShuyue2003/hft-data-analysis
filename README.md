
# High-Frequency Trading Data Analysis

[![CI](https://github.com/LinShuyue2003/hft-data-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/LinShuyue2003/hft-data-analysis/actions)

This project performs **tick-level quantitative analysis** on cryptocurrency trading data (e.g., Binance BTCUSDT).  
It provides **data cleaning, distribution fitting, visualization, and report generation** to study microstructure patterns such as spread distribution, trade volume tails, short-term volatility, and intraday regularities.

---

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/LinShuyue2003/hft-data-analysis.git
cd hft-data-analysis

# Create virtual environment
python -m venv .venv
source .venv/bin/activate     # Linux/Mac
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt
```

Dependencies include: `pandas numpy scipy matplotlib statsmodels click jinja2 pyarrow`.

---

### 2. Run with Sample Data

```bash
python scripts/run_all.py --use-sample
```

Outputs:
- Figures: `results/figures/*`  
- Tables: `results/tables/*.csv`  
- Report: `reports/summary.html`

---

### 3. Download Real Data

#### Automatic Download (requires Binance API access)

```bash
# Download trades for one day
python -m scripts.download_binance trades --symbol BTCUSDT --date 2025-08-01 --out data/raw/binance/BTCUSDT

# Download top-of-book snapshots (WebSocket collection for 30–60 minutes)
python -m scripts.collect_book --symbol BTCUSDT --out data/raw/binance/BTCUSDT/book.csv
```

#### If You Can Only Get Trades (no book data)

Use the simulator to create synthetic book data:

```bash
python -m scripts.convert_trades_to_book --trades data/raw/binance/BTCUSDT/BTCUSDT-aggTrades-2025-08-01.csv --out data/raw/binance/BTCUSDT/book.csv
```

This produces a pseudo-book file that can be used for spread analysis.

#### In Restricted Regions (US/China)

If Binance API is not accessible, you need to manually download:  
- **Trade file**: `BTCUSDT-aggTrades-YYYY-MM-DD.csv`  
- **Book file**: `book.csv` (or generated via `simulate_book.py`)  

Then place them in:  
```
data/raw/binance/BTCUSDT/
 ├── BTCUSDT-aggTrades-YYYY-MM-DD.csv
 └── book.csv
```

---

### 4. Data Cleaning

Data cleaning is automatically handled inside `run_all.py`.  
It supports three cases:

1. Only `--trades` provided → cleans trades.  
2. Only `--book` provided → cleans book snapshots.  
3. Both provided → merges trades and book data.  

You can also run cleaning standalone:

```bash
python -m scripts.prepare_data --trades data/raw/binance/BTCUSDT/BTCUSDT-aggTrades-2025-08-01.csv --book data/raw/binance/BTCUSDT/book.csv
```

Outputs:
```
data/processed/trades.parquet
data/processed/book.parquet
```

---

### 5. Generate Report

#### From raw CSV (auto-clean inside pipeline)

```bash
python scripts/run_all.py --trades data/raw/binance/BTCUSDT/BTCUSDT-aggTrades-2025-08-01.csv --book data/raw/binance/BTCUSDT/book.csv --bar 1s --symbol BTCUSDT
```

#### From cleaned Parquet

```bash
python scripts/run_all.py --trades data/processed/trades.parquet --book data/processed/book.parquet --bar 1s --symbol BTCUSDT 
```

Generates: `reports/summary.html`

---

## 📂 Project Structure

```
├── scripts/
│   ├── run_all.py          # Main pipeline: clean → features → fit → visualize → report
│   ├── download_binance.py # Download trades
│   ├── collect_book.py     # Collect book snapshots
│   ├── convert_trades_to_book.py    # Generate pseudo-book from trades (for users without book data)
│   └── prepare_data.py       # Standalone cleaning
├── src/
│   ├── data_cleaning.py    # Cleaning functions
│   ├── features.py         # Feature engineering
│   ├── fit.py              # Distribution fitting
│   ├── viz.py              # Visualization
│   ├── report.py           # Report generation
│   └── tests/              # Unit tests
├── data/
│   ├── sample/             # Sample data
│   ├── raw/                # Raw data (csv)
│   └── processed/          # Cleaned data (parquet)
├── results/                # Figures & tables
├── reports/                # HTML reports
├── requirements.txt
└── README.md
```

---

## 📜 License

This project is released under the [MIT License](LICENSE).

---

## 📈 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.


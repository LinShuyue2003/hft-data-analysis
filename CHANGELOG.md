
# Changelog

All notable changes to this project will be documented in this file.

## [v0.2.0] - 2025-09-18
### Added
- Distribution fitting enhancements: spread → lognorm/gamma/expon/pareto, returns → Student-t/Laplace/Normal, etc.
- Visualization: QQ plots, log-log tail plots, intraday heatmaps, |returns| autocorrelation.
- HTML report: improved layout, table formatting, figure grid (3 per row).
- Robust parsing: automatic recognition of Binance headerless CSV (aggTrades format).
- Simulated book generator (`simulate_book.py`) for users with trades only.
- Engineering improvements: CSV/Parquet auto-detection, Windows-compatible entrypoint.

### Changed
- Params column in fit tables formatted into concise strings for readability.
- Cleaner CSS for HTML tables and figures.

## [v0.1.0] - 2025-08-01
### Added
- Initial pipeline: cleaning, feature extraction, distribution fitting, visualization.
- Automatic HTML report generation.
- Sample dataset for demonstration.

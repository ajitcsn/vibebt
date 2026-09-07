# VibeBT data sources

## Default cash-equity backtesting: official NSE bhavcopy

`npm run data:nse` imports end-of-day EQ-series OHLCV direct from NSE's
CM UDiFF Common Bhavcopy Final ZIP archives. It stores one CSV per symbol plus
a source URL, UTC fetch time, and SHA-256 checksum in `data/nse_daily/manifest.json`.
These are visible as `Cash equities · NSE official` in the scrip picker.

This direct archive import is deliberately preferred to `nsepy`: VibeBT has a
small, inspectable schema check against NSE's current published report rather
than relying on an intermediary's changing scraper. The files are unadjusted
EOD bars, so corporate actions must still be reviewed for long-history results.

## Optional: local Kite cache

VibeBT also enumerates eligible daily `*_SPOT` cash equities and indices, plus
`*_FUT_CONT` continuous-futures research series, from the supplied Kite cache.
The UI receives this list from `GET /api/series` and runs a selected series
through `POST /api/backtest`.

Before a series appears or runs, VibeBT rejects missing or duplicate dates,
non-finite values, negative volume, and impossible OHLC bars. It reports the
cache's latest daily observation with every result. A cache more than seven
calendar days old is visibly marked stale.

Cash-equity/index results are account-value simulations. Continuous futures are
displayed in research points only until point-in-time lot-size and contract-roll
data are available.

## Public event archive

`npm run ingest:public` runs the reproducible public-source collector. It stores
compressed monthly files under `data/public_market/`, together with source URLs,
fetch timestamps and SHA-256 checksums. Existing monthly files are skipped, so
the same command is safe to resume after a network interruption.

It backfills:

- NSE corporate actions, including published ex-dates and record dates;
- NSE timestamped announcements in strategy-relevant disclosure classes;
- India VIX from the supplied local Kite cache; and
- SEBI's original monthly FPI trade archives.

The collector does not fabricate analyst estimates, historical valuation
snapshots, earnings surprises, or intraday VWAP. Those need paid or separately
licensed point-in-time data before they can appear in a real backtest.

## Optional free exploration import: Alpha Vantage BSE daily OHLCV

Use a free Alpha Vantage API key to import the provider's compact daily spot
OHLCV file into a separate, provenance-tagged folder:

```sh
VIBEBT_ALPHA_VANTAGE_KEY=your_key \
  python scripts/import_alpha_vantage.py RELIANCE.BSE
```

The importer validates every OHLCV row, stores the raw CSV in
`data/imports/alpha_vantage/`, and writes a sidecar provenance JSON file. It
does not blend that import into futures results.

Alpha Vantage's free daily endpoint requires an API key and the full-history
variant may have plan limits. Treat this source as a lightweight spot-data
exploration path, not a substitute for a complete Indian-market backtest feed.

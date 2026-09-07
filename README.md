# VibeBT

VibeBT is an Indian-market, daily-bar research workspace. It turns a selected, supported strategy recipe into a reproducible single-instrument backtest using cached OHLCV data.

It is research software, not trading advice or an order-execution system.

## Run locally

VibeBT can run from official NSE daily cash-equity data alone. The supplied
`kite-futures-cache` remains optional for its existing indices and continuous-futures research series.

```sh
npm install
npm run data
```

In another terminal:

```sh
npm run dev
```

The browser uses same-origin `/api` calls. During development, Vite forwards them to the daily-data service on port `8765`.

## Use official NSE cash-equity data, no Kite login

Fetch the default liquid-equity universe from NSE's UDiFF Common Bhavcopy Final
archives, then restart the API so it rebuilds its instrument catalogue:

```sh
npm run data:nse
npm run data
```

`data:nse` fetches roughly 400 calendar days by default. Limit the first run,
or choose your own universe, with `npm run data:nse -- --days 30 --symbols RELIANCE,INFY,TCS`.
It writes separate, provenance-tagged `*_NSE_SPOT.csv` files under
`data/nse_daily/`. NSE data is never merged into a Kite series.

## Refresh daily market data

Kite access tokens expire daily. When VibeBT reports stale data, authenticate
in the browser and then refresh the cache:

```sh
npm run data:login
npm run data:refresh
```

Restart `npm run data` after the refresh so the API rebuilds its instrument catalogue.

## Validate a release

```sh
npm run verify
```

This checks all registered daily compilers against cached data, deterministic next-open and stop/target rules, and the production frontend build.

## Free hosted hobby deployment

This repository includes `render.yaml` and a self-contained Docker build for one
free Render web service. It builds the Vite workspace and serves it from the same Python service as the API
and committed `data/nse_daily/` equity files. Connect the private GitHub
repository in Render, select the Blueprint, and deploy. No database is needed
for the current static monthly-snapshot data model.

Free Render instances sleep after 15 minutes without traffic and can take about
a minute to wake. The committed data stays available after a restart; refresh
it locally with `npm run data:nse`, commit the changed `data/nse_daily/` files,
and Render redeploys automatically.

## Environment

Copy values from `.env.example` only as needed. The important settings are:

- `VIBEBT_NSE_DATA`, location of imported official NSE daily equity files.
- `VIBEBT_KITE_CACHE`, optional location of the broker daily-data cache project.
- `VIBEBT_PYTHON`, Python interpreter with `numpy` and `pandas` installed.
- `VIBEBT_ALLOWED_ORIGINS`, comma-separated browser origins only if the API is cross-origin.
- `VIBEBT_MAX_CONCURRENT_RUNS` and `VIBEBT_MAX_REQUESTS_PER_MINUTE`, single-node API guardrails.

## Product boundary

VibeBT currently supports daily, single-series research. It does not yet provide point-in-time equity universes, corporate-action-safe long-history equity returns, tradable futures contract rolls, margin, or order execution. See [BACKTEST_CONTRACT.md](BACKTEST_CONTRACT.md) before treating a result as evidence.

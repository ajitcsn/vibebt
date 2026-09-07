# Release readiness

## Implemented release controls

- The frontend uses same-origin API paths by default. Development uses a local Vite proxy, while a deployed reverse proxy can keep UI and API on one origin.
- The API validates request size, inputs, cached daily dates, finite OHLCV values, and impossible daily bars. It does not repair market history silently.
- Backtests are rate limited and concurrency limited for a single-node service. User input receives validation errors; unexpected failures are logged server-side and return a generic error.
- Results disclose data coverage, data-as-of date, stale cache status, template version, normalized strategy recipe, execution rules, and limitations.
- Users can export the complete result, including the exact returned bars and recipe, as JSON.
- Automated verification covers all registered compilers, risk wiring, fixed holding exits, cash-equity short rejection, next-open execution, conservative stop/target tie handling, and the frontend build.

## Production gate, do not waive this

Before marketing long-horizon Indian cash-equity results as production-grade, obtain and ingest data that covers corporate actions, delistings, point-in-time universe membership, liquidity/capacity, and effective-dated charges. Before offering futures returns, add point-in-time contracts, lot sizes, rolls, margin, settlement, and position sizing.

Until those data sets exist, the application must keep the current "daily single-instrument research" warning visible. No UI or commentary may call a result a recommendation, signal to trade, or live performance.

## Operator checks before each release

```sh
npm run verify
npm run data
curl http://127.0.0.1:8765/health
```

Then check one cash equity, one index, one futures research series, an invalid request, a stale-data warning if relevant, and a mobile viewport. Publish only after the cached data freshness date is acceptable for the intended use.

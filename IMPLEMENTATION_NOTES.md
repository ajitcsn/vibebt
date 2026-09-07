# VibeBT implementation notes

## Implemented from the expert reviews

### Product focus

VibeBT now centres the credible first job: test one selected Indian daily series with a fully specified rule, inspect what happened, change one input, and keep the idea. The visible daily library contains only the 20 registered strategy compilers, five supported confirmations, exact stop/target rules, and supported exits.

### Truthful strategy contract

The frontend sends a complete recipe to `POST /api/backtest`:

```text
series, signal, side, filters, exit, stop, target, EMA parameters,
commission bps, slippage bps, starting capital, allocation, test period
```

The bridge validates every field and returns the normalized specification with each run. Cash equities and spot indices reject short requests. Unsupported controls are absent from the active workspace rather than being silently approximated.

### Daily execution rules

- A signal uses a completed daily close and first fills at the next daily open.
- Stop and target values are exact percent, ATR, or risk/reward rules, not Boolean flags.
- ATR at entry uses the prior completed bar, avoiding same-day look-ahead.
- An overnight gap through a level fills at the open.
- A daily bar that touches both stop and target uses the stop-first rule.
- A stop/target exit cannot reopen at a price that happened earlier in the same bar.
- Account equity is marked to the daily close while a position is open.
- Largest drawdown is calculated from that mark-to-market account-equity series and returned as a peak-to-trough interval.

### Workspace and chart

- The desktop workspace is a 3:1:1 analysis, builder, and blocks layout.
- The builder stays in place. The block list and scratchpad scroll internally.
- Scrip is the only backtest target. The old, misleading universe/scope control is removed from the active flow.
- Test period changes the sample and metrics. Viewport controls only zoom/pan the rendered chart.
- Price candles, strategy equity, drawdown highlight, and buy-and-hold are separated and labelled.
- Tooltip values appear only inside a chart panel and include date, OHLC, equity, drawdown, and available trade event.
- The drawdown label is HTML outside the transformed SVG geometry, so zoom cannot stretch it.
- The interface uses auto-run deliberately, with an explicit updating/current status instead of a competing decorative Run button.
- Both dark and light themes use the same design tokens. Mobile is a practical vertical workspace.

### Trader workflow

- Results include return, net P&L or points, maximum drawdown, completed trades, win rate, profit factor, time in market, data coverage, execution policy, and limitations.
- The trade table exposes each entry, exit, direction, exit reason, points, and P&L.
- Commentary is generated only from returned metrics and dates. It makes no causal market claim.
- Surprise Me chooses only registered daily signals and exact risk/exit configurations.

## Known deliberate limits

- This is still daily, single-instrument research, not a portfolio/universe backtester.
- Continuous futures remain research series until point-in-time contracts, rolls, lot sizes, margin, and settlement are modelled.
- Cash-equity corporate-action, delisting, point-in-time index membership, liquidity/capacity, and all effective-dated statutory charges are not yet complete enough for a production-grade long-history result.
- The frontend now uses same-origin API paths and a Vite development proxy. It is deployment-ready behind a reverse proxy, but this work does not publish or host the product.

## Verification run

```sh
/Users/ajitc/Desktop/projects/kite-futures-cache/.venv/bin/python scripts/verify_daily_backtester.py
npm run build
```

The verification script exercises all 20 daily compilers, exact risk wiring, a fixed holding exit, long-only cash-equity validation, and mark-to-market output fields.

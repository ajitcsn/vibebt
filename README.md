# VibeBT

### A visual workspace for testing Indian-market trading ideas

VibeBT turns a market hunch into an explicit daily-bar backtest. Pick an NSE cash equity, combine a signal with confirmations, exits, stops and targets, then inspect the actual candles, equity path, drawdown and every trade.

It is built for curious, non-technical traders who want a better question than “would this have worked?”

> **Market reality is the product constraint.** VibeBT shows observed daily OHLCV bars, uses next-open fills, applies costs, and refuses to substitute a different strategy when a requested rule lacks a compiler.

## What you can do

| Explore | Build | Inspect |
| --- | --- | --- |
| Choose an NSE cash equity and test period | Click or drag strategy blocks into a recipe | Read candle, equity and drawdown charts with hover values |
| Browse supported indicators and risk rules | Change EMA, MACD, stop and target settings inside the active blocks | Review fills, fees, slippage, metrics and individual trades |
| Save unfinished ideas in a scratchpad | Name, save and revisit strategies | Export the complete run and its assumptions as JSON |

The chart stays central, while the builder, block library and scratchpad remain within reach.

## Run it locally

You need Node.js 22+ and Python 3.12+.

```sh
git clone https://github.com/ajitcsn/vibebt.git
cd vibebt
npm install
python3 -m pip install -r requirements.txt
npm run data
```

Open [http://localhost:8765](http://localhost:8765). One service serves the workspace and backtesting API together.

### Refresh the official NSE snapshot

The repository includes a reproducible daily snapshot for 19 liquid equities. To refresh the default universe from NSE's current UDiFF bhavcopy archives:

```sh
npm run data:nse
```

Restart `npm run data` after a refresh. The importer records every archive URL, UTC fetch time and SHA-256 checksum in `data/nse_daily/manifest.json`.

Try a smaller custom import first:

```sh
npm run data:nse -- --days 30 --symbols RELIANCE,INFY,TCS
```

## How a test works

```text
Completed daily bar
       ↓
Strategy and filters observe its known values
       ↓
Order fills at the next daily open
       ↓
Daily high/low checks stop and target
       ↓
Equity, benchmark, drawdown and trades are recorded
```

These rules prevent the most common accidental fantasy results:

- Signals are observed at the completed close and fill at the following open.
- Slippage and commission apply on both sides of every fill.
- A gap through a stop or target fills at the open.
- When a daily bar reaches both stop and target, the stop takes priority.
- Cash equities and indices are long-only in the current daily engine.
- A visible block runs only when it has an exact registered compiler.

See [BACKTEST_CONTRACT.md](BACKTEST_CONTRACT.md) for the detailed execution contract and [MARKET_REALITY.md](MARKET_REALITY.md) for data principles.

## Data sources

### Official NSE cash equities

The default source is NSE's CM UDiFF Common Bhavcopy Final archive. VibeBT imports the `EQ` series only and keeps each symbol in a separate, provenance-tagged file. The visible scrip picker labels these instruments **Cash equities · NSE official**.

The data is end-of-day OHLCV. Long-history results require care around splits, bonuses, dividends, liquidity and symbol changes. VibeBT preserves this limit in the run metadata instead of hiding it.

### Optional local broker cache

If you have the companion `kite-futures-cache` project, VibeBT can also expose its cached indices and continuous-futures research series. Those instruments remain separate from official NSE equity files.

Read [DATA_SOURCES.md](DATA_SOURCES.md) for source provenance and scope.

## Supported daily strategy families

VibeBT currently includes 20 exact daily compilers:

EMA crossover, MACD, RSI, Supertrend, Bollinger Bands, ATR expansion, Stochastic, ADX, CCI, Williams %R, rate of change, momentum, OBV, MFI, Donchian Channels, Keltner Channels, SMA crossover, Ichimoku, Parabolic SAR, and buy-and-hold.

The block library can contain ideas beyond that list. The API returns a clear message when a chosen block has no exact compiler yet, rather than changing the rule behind the user’s back.

## Deploy it

`render.yaml` and the multi-stage `Dockerfile` deploy the UI, API and committed NSE snapshot as one service. This is the shortest hosted setup:

1. Create a Render web service from this repository.
2. Select the Blueprint and its free plan, or a small always-on plan.
3. Render builds the Docker image and exposes one URL for the whole workspace.

The free plan sleeps after 15 idle minutes. For an always-on personal instance, an Oracle Cloud Always Free VM is a good first option; a 1–2 GB VPS is the simple paid fallback.

## Development checks

```sh
npm run verify
```

This validates all registered compilers, execution rules and the production frontend build.

## Project boundaries

VibeBT is research software. It currently supports one daily instrument per run. It does not provide point-in-time universes, fully corporate-action-adjusted history, tradable futures rolls, margin models, intraday execution or order routing.

Treat results as a structured way to investigate an idea. Check the source data, assumptions, liquidity, robustness and out-of-sample behaviour before acting on any result.

## Contributing

Contributions are welcome, especially for source adapters with clear licensing and provenance, point-in-time corporate-action handling, fully specified strategy compilers, reproducible verification cases, and accessibility improvements.

Please keep the core promise intact: every visible result must trace back to actual market data and explicit execution assumptions.

## License

License selection is pending. Do not redistribute market data beyond the terms of its original provider.

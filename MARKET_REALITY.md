# VibeBT Market Reality Directive

Everything in VibeBT must reflect actual market conditions or be explicitly labeled unavailable.

## Non-negotiable rules

1. **No fabricated market outputs.** Prices, candles, equity curves, returns, metrics, trade lists, annotations, and commentary must come from real data and an identified calculation.
2. **No cosmetic interpolation.** Do not smooth, invent, fill, or beautify a price or equity series in a way that changes its market path. Charts plot actual observations, with transparent display-only downsampling where necessary.
3. **No hidden assumptions.** Execution timing, costs, slippage, spreads, funding, contract rolls, position sizing, benchmarks, corporate actions, and data coverage must be visible and versioned.
4. **No look-ahead.** Signals may use only information available at the simulated decision time. Fundamentals, events, index membership, and corporate actions must be point-in-time when relevant.
5. **No unsupported simulation.** If the data, execution model, or strategy compiler cannot support a user-selected block, VibeBT must block the run or show a clear limitation. It must not silently substitute another strategy or result.
6. **Every output has provenance.** A completed run records the data source, instrument/series, date range, data version, engine version, strategy definition, and assumptions.
7. **Commentary is evidence-bound.** Explanations and chart annotations may summarize computed facts, but cannot invent causal stories, predictions, or confidence.

## Implementation test

Before shipping a feature, ask: “Could a trader trace this visible claim to a real market observation and a documented calculation?” If not, remove it, label it unavailable, or build the required data and engine support first.

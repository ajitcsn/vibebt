# VibeBT daily backtest contract

The current local engine supports only the controls below. The interface must not present any other daily rule as active.

| Control | Exact current meaning |
| --- | --- |
| Scrip | One selected cached daily cash-equity, index-spot, or continuous-futures series. |
| Market | Filters the scrip catalogue. Cash equity and index tests are long-only. |
| Signal | One of the 20 versioned daily strategy compilers in `strategy_registry.py`. |
| Indicator periods | EMA and SMA crossover periods are editable. MACD uses editable fast EMA, slow EMA, and signal EMA periods. Each is validated and returned with the run. |
| Confirmation | Up to two: 50-day average direction, relative volume, or RSI confirmation. Each uses information available before the fill day. |
| Entry | Next daily open after a completed daily signal. |
| Exit | Signal reversal or an exact 5, 10, or 20 daily-bar holding limit. |
| Stop | None, percent, or ATR rule. The selected rule's value is editable. A gap fills at the open. |
| Target | None, percent, or a multiple of the actual stop distance. If stop and target are both touched intraday, stop fills first. |
| Fees and slippage | User-entered basis points per side, applied to the fill price on entry and exit. |
| Capital and allocation | Starting cash and percentage allocated to a single long cash-equity/index position. |
| Test period | The tested sample, not chart zoom. Indicator warm-up bars are not included in the returned result. |
| Viewport | Chart-only zoom and pan. It does not recalculate metrics. |

## Deliberate limits

- Daily data only.
- One selected series, not a portfolio or point-in-time stock universe.
- Continuous futures are research series only. Contract choice, rolls, historical lots, margin, and settlement are not yet modelled.
- Cash-equity corporate actions, survivorship, price bands, and liquidity/capacity still require additional point-in-time data before long historical results should be treated as production-grade.
- The product is research and education, never personalised investment advice.

## Result provenance

Each response carries the selected series, test range, template/version, full strategy specification, execution rule, data coverage, and limitations. Equity is marked to the daily close while a position is open; maximum drawdown is calculated from that account-equity series.

Before a cached series can be tested, VibeBT requires sorted, unique daily dates; finite positive OHLC values; non-negative volume; and a valid OHLC range. It returns the cache's data-as-of date and marks a source older than seven calendar days as stale. It never repairs invalid market bars in the backtester.

# VibeBT strategy, data, and Surprise Me implementation report

## Decision

VibeBT should become a **typed strategy compiler**, not a collection of loosely
connected UI blocks. A user-visible block is either:

1. compiled into a versioned, testable backtest rule with the required data;
2. shown as unavailable with the missing requirement; or
3. excluded from Surprise Me.

This protects the product directive: no approximate substitution, no invented
returns, no unlabelled costs, and no causal commentary that the data cannot
support.

## 1. Current state and gaps

The supplied Kite cache already provides real NSE cash-equity, index spot, and
daily continuous-futures OHLCV data. Continuous futures include OI. The current
bridge exposes 56 cash equities, 59 continuous futures, and 5 index series.

The current exact compiler supports three signal families:

- 20/50 EMA crossover with a 200-day trend filter;
- MACD trend;
- RSI mean reversion.

The UI exposes more blocks than the compiler supports. That is acceptable only
when unsupported selections are blocked. It is not acceptable for Surprise Me,
which must choose only complete, runnable templates.

## 2. Target architecture

```text
Source adapters -> immutable raw store -> normalized, point-in-time store
                                           |
UI blocks -> typed strategy specification -> compiler -> execution simulator
                                           |                 |
                                           +-> validator      +-> run artifact
                                                              |
                                                    metrics, trades, charts,
                                                    annotations and provenance
```

### 2.1 Data layers

| Layer | Store | Purpose | Mutation rule |
| --- | --- | --- | --- |
| Raw | Parquet in object storage | Exact vendor response, one partition per provider/instrument/date | Append only |
| Normalized bars | Parquet/Iceberg | Canonical OHLCV/OI, exchange calendar, adjusted fields | New version, never overwrite |
| Reference | Postgres | Instrument master, lots, expiries, sectors, symbol aliases | Effective-dated |
| Point-in-time facts | Postgres/Parquet | Results, filings, estimates, dividends, constituents, FII/DII | `published_at` is mandatory |
| Run artifacts | Object storage + Postgres index | Definition, hashes, trades, daily equity, metrics, commentary evidence | Immutable |

Each run must record `data_version`, `instrument_version`, `compiler_version`,
`execution_model_version`, `strategy_hash`, timestamp, and all input ranges.

### 2.2 Core tables

```text
bars(instrument_id, timeframe, ts, open, high, low, close, volume, oi,
     source, source_version, ingested_at)

instruments(instrument_id, symbol, exchange, asset_type, underlying_id,
            expiry, lot_size, tick_size, effective_from, effective_to)

facts(fact_id, instrument_id, fact_type, value_json, period_end,
      published_at, source, source_document, source_version)

strategy_templates(template_id, version, spec_json, required_capabilities,
                   status, display_name, diversity_tags)

backtest_runs(run_id, strategy_hash, universe_hash, data_version,
              execution_model_version, status, started_at, completed_at)
```

## 3. Data acquisition plan

### 3.1 Prices, volume, OI, and instrument master

Keep the supplied Kite cache as the initial adapter. Kite's historical API
offers minute through daily candles, accepts `continuous=1` for futures and
`oi=1` for OI data. Continuous history requires a live-contract token and is
daily-only, so intraday futures need a separate expiry-stitching pipeline.
[Kite historical-data documentation](https://kite.trade/docs/connect/v3/historical/)

Implement these jobs:

1. **Instrument-master snapshot, daily before market open.** Persist all NSE
   and NFO rows. This is needed to resolve expired contracts, lot-size changes,
   expiry calendars, and F&O eligibility at the historical decision date.
2. **Daily bars, after final-candle cutoff.** Fetch a small overlap, validate,
   then replace only the provisional final bar in a new data version.
3. **Intraday bars, after session close.** Store each contract separately.
   Build a declared front-month/next-month roll series only after the roll rule
   is approved and versioned.
4. **Quality checks.** Reject duplicate timestamps, invalid OHLC ordering,
   impossible negative volume/OI, unexpected gaps, and incorrect timezone.

Do not publish local Kite data to users until the relevant agreement permits
that usage. NSE's policy covers EOD and historical data and says redistribution
is governed by the agreement; commercial use requires the relevant terms.
[NSE data-sharing policy](https://www.nseindia.com/static/market-data/nse-data-policy)

### 3.2 Corporate actions and cash-equity adjustments

Cash-equity swing strategies need point-in-time splits, bonuses, rights, and
dividends. Store both:

- `raw_close`: tradable historical close;
- `adjusted_close`: a documented total-return or split-adjusted research field.

Entries and exits use raw tradable prices. A corporate-action engine adjusts
share quantity, cost basis, and cash distributions on the effective date. Never
apply a current adjusted series to a historical rule without preserving the
version and effective date.

### 3.3 Fundamentals and results events

For every reported fact, store `period_end`, `published_at`, original document,
filing timestamp, currency/unit, restatement flag, and source ID. The compiler
may join a fact to a bar only when `published_at <= decision_timestamp`.

The “earnings surprise” block additionally requires a point-in-time consensus
estimate. A result being positive is not a surprise. Until estimates are
licensed and historized, expose only a narrower block such as “first session
after results filing”, marked as **event timing, no surprise claim**.

### 3.4 Macro, FII/DII, VIX, and calendar events

- **India VIX:** store daily index bars as a regime input, not as a causal
  explanation.
- **FII/DII flows:** store published aggregate flows with release timestamp.
  They can gate a broad-market strategy but must not be represented as a
  stock-specific flow signal.
- **RBI, Budget, expiry, month-end:** maintain an exchange/session calendar,
  event timestamp, and source document. A calendar event is valid without a
  forecast; its performance still needs the same execution model.
- **Index membership and sector labels:** effective-date every change. Never
  evaluate a past Nifty 50 universe using today's constituents.

## 4. Compiler contract

### 4.1 Typed strategy specification

The UI must emit a constrained JSON object, never executable user code.

```json
{
  "version": "1.0",
  "universe": {"kind": "cash_equity", "members": "nifty_50_pit"},
  "signal": {"kind": "ema_cross", "fast": 20, "slow": 50},
  "filters": [{"kind": "close_above_sma", "period": 200}],
  "side": "long_only",
  "entry": {"kind": "next_bar_open"},
  "exit": {"kind": "opposite_signal"},
  "risk": {"stop": null, "target": null},
  "timeframe": "1d"
}
```

Every compiler implementation returns either a `CompiledStrategy` with its
capabilities and assumptions, or a structured error such as:

```json
{"code":"MISSING_POINT_IN_TIME_CONSENSUS",
 "message":"Earnings surprise needs historical consensus estimates."}
```

### 4.2 Compiler stages

1. **Validate.** Confirm compatible asset type, timeframe, data coverage,
   universe, side, and order model.
2. **Resolve universe point-in-time.** Produce eligible symbols for every
   decision date, applying liquidity and F&O membership at that date.
3. **Materialize features.** Indicators only use bars closed before the signal
   bar. Fundamental and event joins obey `published_at`.
4. **Generate signals.** Output one of `long`, `short`, `flat` per instrument
   and decision timestamp, plus evidence values.
5. **Simulate orders.** Convert signals to next-bar orders, enforce liquidity,
   position limits, stops/targets and no-look-ahead intrabar tie rules.
6. **Account.** Apply asset-specific costs, tax/charges policy, quantity/lot
   rules, corporate actions, futures rolls and margin assumptions.
7. **Emit artifact.** Trades, daily mark-to-market equity, metrics, warnings,
   source hashes and evidence for each annotation.

## 5. Block implementation matrix

| UI block group | First exact implementations | Needed data/compiler | Do not ship as runnable until |
| --- | --- | --- | --- |
| Price/technical | EMA cross, SMA trend, RSI, MACD, breakout, gap, ATR, Bollinger, volume ratio | OHLCV; indicator compiler | Warm-up, next-bar execution and split treatment tested |
| Price patterns | inside/outside day, higher highs, range break | OHLC | Pattern definitions, tie rules and bar-close timing fixed |
| Futures | OI change, expiry week, basis/roll | Contract OI, expiry, futures/spot, roll series | Expiry-specific or declared continuous roll model exists |
| Intraday | ORB, VWAP, intraday RSI, VWAP exit | 5/15/60m bars, session calendar | Contract stitching, session cutoff, realistic intraday costs |
| Cash-equity filters | liquidity, market cap, sector, delivery volume | Point-in-time reference/security data | Each fact has an effective date |
| Fundamental | profitability, revenue growth, debt, ROE, P/E, cash flow | Point-in-time filings/fundamentals | Restatements and publication lags handled |
| Corporate/event | results day, dividend ex-date, RBI, Budget | Event calendar with released timestamp | Event definition is exact; no false “surprise” label |
| Flows/regime | FII/DII, India VIX, Nifty trend | Aggregate flows, VIX, index bars | Scope is labelled market-wide, not stock-specific |
| Entries/exits | next open, next close, breakout, fixed hold, opposite signal, MA, RSI, trailing, stop/target | Order simulator + OHLC | Fill ordering and same-bar stop/target rule documented |
| Direction | long cash equity, long/short futures | Asset eligibility and margin model | Cash equity shorting is not silently enabled |
| Timeframes | daily first, 60m, 15m, 5m, weekly/monthly | Resampler/session calendar | Base bars and execution resolution are compatible |

## 6. Strategy template sequence

Implement templates, not arbitrary block combinations, first. Each template
has a human name, exact JSON specification, data requirements, tests, and
minimum coverage. Add free-form block composition only when its compiler can
prove every combination is valid.

### Phase A: daily price strategies

1. EMA 20/50 with SMA 200 filter, cash equity long-only.
2. RSI(2) or RSI(14) oversold bounce, cash equity long-only.
3. MACD trend, cash equity long-only and futures long/short variants.
4. 20-day breakout with volume confirmation.
5. 20-day pullback in 200-day uptrend.
6. Supertrend trend following, provided the exact ATR and multiplier are
   exposed in the strategy definition.
7. Buy-and-hold benchmark on the same asset/universe and dates.

### Phase B: futures and regime strategies

1. Futures EMA/MACD with declared continuous-roll caveat.
2. OI-price quadrant filter only after contract-level OI is validated.
3. VIX regime gate for Nifty futures, clearly a filter rather than a cause.
4. Expiry-week templates only with calendar and contract-expiry handling.

### Phase C: intraday strategies

1. Opening-range breakout.
2. VWAP reversion.
3. Intraday trend pullback.

All must use session-aware bars, spread/slippage assumptions calibrated from
actual liquid instruments, and forced end-of-session square-off where relevant.

### Phase D: event and fundamental strategies

1. Results-filing timing, no surprise estimate.
2. Dividend ex-date research template with corporate-action accounting.
3. Revenue/ROE/debt screen with filing-lag joins.
4. Earnings surprise only after point-in-time consensus data is procured.

## 7. Execution models

Maintain distinct models. A strategy must declare one; VibeBT must never apply
futures costs to cash equity or vice versa.

| Model | Allowed side | Quantity | Costs | Required caveat |
| --- | --- | --- | --- | --- |
| Cash equity EOD | Long only initially | Shares/notional | Brokerage, taxes, slippage as percent/notional | Corporate actions and liquidity |
| Futures daily | Long/short | Historical contract lot size | Bid/ask proxy, brokerage/taxes, slippage | Roll methodology and margin |
| Futures intraday | Long/short | Contract lot size | Higher session-aware slippage | Contract-specific history |
| Index spot benchmark | Long only | Index points/normalized capital | No tradability claim | Benchmark only, unless instrument proxy used |

Rupee P&L is unavailable until historical lot sizes, actual position sizing, and
the relevant cost schedule are effective-dated. Until then, display points and
say so.

## 8. Metrics and chart windows

The selected chart range is also the selected **metric window**. For 1W, 1M,
3M and 6M:

1. fetch enough prior bars solely for indicator warm-up;
2. create signals using only those prior and in-window bars;
3. report equity points, drawdown, closed trade count, win rate and profit
   factor only for the selected visible window;
4. display a `warmup_bars` provenance field;
5. show `no closed trades` rather than inventing a win rate or profit factor.

Metrics must state whether open positions are marked to market or excluded. The
first release should state **realised closed-trade equity**, then add a separate
marked-to-market curve once it is tested.

## 9. Surprise Me, done properly

### 9.1 Curated template catalogue

Do not randomize raw blocks. Store approved templates like:

```text
id, version, asset_type, timeframe, style, regime, data_requirements,
compiler_status, min_bars, min_trades, definition_hash
```

Example diversity tags:

```text
trend, mean_reversion, breakout, pullback, event_timing,
cash_equity, index_futures, daily, intraday
```

Only templates with `compiler_status = runnable`, adequate local coverage, and
an approved execution model enter the candidate set.

### 9.2 Selection algorithm

```text
candidate = runnable templates
          ∩ current instrument type
          ∩ available data/timeframe
          ∩ user risk and direction constraints
          ∩ coverage rules

score = diversity_bonus
      + untried_template_bonus
      + parameter_distance_from_recent_runs
      - repeat_penalty
      - low_coverage_penalty

select weighted-random(candidate, score, seed)
```

Use a saved seed for reproducibility. Record why the template was eligible and
show a plain-language statement such as: “A daily RSI pullback template was
chosen because you last explored trend strategies.” Do not select based on
future P&L or current best performer; that is selection bias.

### 9.3 Parameter randomisation guardrails

Randomize only whitelisted, tested parameter sets. For example:

```text
RSI period:       [2, 5, 14]
Oversold level:   [10, 20, 30]
Holding period:   [2, 5, 10] daily bars
EMA pairs:        [(10,30), (20,50), (50,100)]
Breakout windows: [20, 55]
```

Every combination must be validated before it is shown. Never randomly attach
an unsupported stop, target, event filter, short side, or intraday execution.

### 9.4 Product behavior

- **Ready:** load the template and immediately request the run.
- **Unavailable:** never select it; show it separately in the block library
  with its missing data/compiler requirement.
- **No result:** show a real flat/empty closed-trade result and explain that no
  qualifying trade closed in the selected period.
- **Novelty:** avoid repeating the same strategy family until the catalogue is
  too small; then say that choices are limited.

## 10. Test and release gates

### Compiler unit tests

- indicator values match frozen fixtures;
- signal uses only data available at the decision timestamp;
- cross, breakout, gap, stop and target edge cases have explicit tie rules;
- invalid combinations return structured errors;
- cash strategies cannot short; futures strategies require contract metadata.

### Backtest integration tests

- known fixture produces exact trades and daily equity;
- one-window run and the corresponding slice of a full-history run agree under
  the documented warm-up/realisation rule;
- costs, splits, dividends, expiry rolls, and lot changes appear in provenance;
- no bar has a future timestamp; no duplicated fills;
- same strategy/data versions produce byte-stable artifacts.

### Data-quality tests

- source coverage, missing sessions, duplicate bars, OHLC invariants;
- vendor/revision diff alerts;
- fundamental publication time precedes every use;
- symbol, ISIN and contract mappings have effective dates.

### Release gate

No block or Surprise Me template reaches production without a compiler test,
data-coverage test, execution-model declaration, and one saved golden run.

## 11. Delivery roadmap

### Milestone 1: make the current daily product trustworthy

- Move compiler definitions from bridge conditionals into a strategy registry.
- Add cash-equity percentage/notional cost model and corporate-action policy.
- Finish EMA, RSI, MACD, breakout, pullback, Supertrend and benchmark.
- Add run provenance panel and selected-window metric tests.
- Replace current Surprise Me with a 6–8 template catalogue.

### Milestone 2: broaden the data model

- Historical instrument master, lot-size and expiry snapshots.
- Point-in-time Nifty constituents, sector/liquidity data and corporate actions.
- Results-event calendar and filing facts.
- Object storage, dataset manifest, ingestion jobs, data-quality dashboard.

### Milestone 3: futures and intraday correctness

- Explicit futures roll engine and historical cost/lot tables.
- Contract-level intraday cache and session calendar.
- ORB and VWAP templates, capacity/slippage calibration.

### Milestone 4: fundamental and event compilers

- Point-in-time fundamentals and result timestamps.
- Licensed estimate history before enabling true earnings surprise.
- FII/DII and VIX regime templates with carefully limited claims.

## 12. Immediate implementation order

1. Create `StrategyDefinition`, `Capability`, and `CompiledStrategy` types.
2. Extract the existing EMA/MACD/RSI mappings into versioned template files.
3. Add six daily runnable templates and a deterministic Surprise Me selector.
4. Add selected-window metrics and golden fixtures before adding more blocks.
5. Create data manifests and source-version hashes for the current Kite cache.
6. Build the point-in-time reference and corporate-action pipelines.
7. Add event/fundamental compilers only after their historical data contracts
   pass the release gate.

## 13. Proposed repository and service layout

Keep the UI, API, compute engine and ingestion code separate. The current
single local bridge is useful for development, but it should not remain the
production boundary.

```text
apps/
  web/                         Vite UI
  api/                         HTTP API, auth, validation, run retrieval
  worker/                      asynchronous backtest and ingestion workers
packages/
  strategy-schema/             JSON schema, types and capability rules
  compiler/                    strategy registry and compiler implementations
  engine/                      orders, fills, accounting, metrics
  data-contracts/              normalized schemas and validators
  commentary/                  evidence-bound annotation generator
  fixtures/                    frozen bars, facts and golden runs
infra/
  migrations/                  Postgres migrations
  docker/                      API and worker images
  jobs/                        scheduled ingestion definitions
```

### 13.1 Runtime responsibility

| Component | Does | Must not do |
| --- | --- | --- |
| Web app | Build strategy spec, show capability state, request or retrieve a run | Read market files, calculate returns, store vendor secrets |
| API | Authenticate, validate spec, create idempotent run request, serve artifacts | Run long jobs synchronously |
| Worker | Resolve data version, compile, simulate, persist immutable artifact | Trust browser-provided prices or strategy code |
| Data job | Fetch, validate, version and publish datasets | Rewrite historical data silently |
| Commentary service | Read artifact facts and write traceable annotations | Invent market causes or make forecasts |

## 14. Strategy registry design

The registry is the single source of truth for UI availability, Surprise Me,
compiler dispatch and provenance.

```python
@dataclass(frozen=True)
class StrategyTemplate:
    id: str
    version: str
    title: str
    spec: dict
    tags: tuple[str, ...]
    requirements: tuple[str, ...]
    asset_types: tuple[str, ...]
    timeframes: tuple[str, ...]
    minimum_bars: int
    status: Literal["runnable", "building", "blocked"]

@dataclass(frozen=True)
class CompiledStrategy:
    definition_hash: str
    signals: DataFrame
    order_policy: OrderPolicy
    execution_model: str
    evidence_columns: tuple[str, ...]
    warnings: tuple[str, ...]
```

Example template file, stored as reviewed JSON/YAML rather than generated at
runtime:

```yaml
id: cash-rsi-pullback-v1
version: 1.0.0
title: RSI pullback in an uptrend
asset_types: [equity]
timeframes: [1d]
minimum_bars: 252
requirements: [ohlcv, corporate_actions]
tags: [mean_reversion, cash_equity, daily]
status: runnable
spec:
  signal: {kind: rsi_cross_up, period: 14, threshold: 30}
  filters: [{kind: close_above_sma, period: 200}]
  side: long_only
  entry: {kind: next_bar_open}
  exit: {kind: fixed_holding_period, bars: 5}
  risk: {stop: null, target: null}
```

`status: building` templates can appear in the block library with a precise
missing-capability explanation. `status: blocked` templates cannot be suggested
or sent to the API.

## 15. Capability resolution

Resolve availability before a user presses Run.

```python
def capability_check(spec, dataset_manifest, instrument, execution_model):
    required = required_capabilities(spec)
    available = dataset_manifest.capabilities_for(instrument, spec.timeframe)

    failures = []
    if not required <= available:
        failures.append(missing_capabilities(required, available))
    if spec.side == "short" and instrument.asset_type == "equity":
        failures.append("CASH_EQUITY_SHORT_NOT_ENABLED")
    if spec.uses_event("earnings_surprise") and not available.has("pit_consensus"):
        failures.append("MISSING_POINT_IN_TIME_CONSENSUS")
    if spec.timeframe in {"5m", "15m", "60m"} and not available.has("session_bars"):
        failures.append("MISSING_INTRADAY_SESSION_BARS")
    return failures
```

The UI receives a structured response, not a generic failure:

```json
{
  "runnable": false,
  "blockedBlocks": ["Earnings surprise", "After results"],
  "reason": "Historical consensus estimates are not loaded for this universe.",
  "nextRequirement": "Add a point-in-time estimates provider."
}
```

## 16. Compiler implementation details

### 16.1 Indicator compiler

Indicators are deterministic feature functions that accept sorted bars and
parameters. They return `NaN` until enough bars exist. Signals are calculated
at the bar close and filled only at the next eligible bar.

```python
def compile_ema_cross(bars, fast, slow, trend_period):
    fast_ema = ema(bars.close, fast)
    slow_ema = ema(bars.close, slow)
    trend = sma(bars.close, trend_period)
    crossed_up = (fast_ema > slow_ema) & (fast_ema.shift(1) <= slow_ema.shift(1))
    crossed_down = (fast_ema < slow_ema) & (fast_ema.shift(1) >= slow_ema.shift(1))
    desired = where(crossed_up & (bars.close > trend), LONG,
              where(crossed_down, FLAT, HOLD))
    return desired, {"fast_ema": fast_ema, "slow_ema": slow_ema, "trend": trend}
```

The compiler must specify whether a crossing in the last bar is executable. It
usually is not executable until the following market bar is available.

### 16.2 Event compiler

Event data is not a bar. Convert it into a decision-time-aligned signal only
after the event became public.

```python
event_bar = next_exchange_bar_after(event.published_at)
signal[event_bar] = LONG
order_time = next_exchange_bar_after(event_bar.close_time)
```

If a result is published after the close, next-session open may be valid. If it
is published during the session, use the predefined event policy. Do not infer
publication time from a calendar date.

### 16.3 Fundamental compiler

Create an as-of join:

```sql
SELECT bar.*, fact.value
FROM bars bar
LEFT JOIN LATERAL (
  SELECT value
  FROM facts
  WHERE facts.instrument_id = bar.instrument_id
    AND facts.fact_type = 'roe'
    AND facts.published_at <= bar.decision_timestamp
  ORDER BY facts.published_at DESC
  LIMIT 1
) fact ON true;
```

This prevents using a quarterly value before an investor could know it.

### 16.4 Multi-instrument and portfolio compiler

Universe strategies cannot be simulated by looping symbols and adding their
returns. They need a portfolio layer:

- selection date and rebalance schedule;
- ranking tie-break rules;
- maximum positions and sector caps;
- cash allocation for unfilled/absent candidates;
- delisted symbol and survivorship treatment;
- position sizing and minimum liquidity;
- portfolio-level drawdown and turnover.

Ship single-scrip templates first. Label Nifty/sector block choices as
**portfolio mode, building** until this layer exists.

## 17. Execution-engine specification

### 17.1 Order lifecycle

```text
signal close -> order created -> next eligible open/limit trigger
             -> fill or no-fill -> position -> exit order -> fill -> ledger
```

For every fill, persist:

```text
run_id, order_id, instrument_id, decision_ts, submit_ts, fill_ts,
side, quantity, requested_price, fill_price, spread/slippage, fees,
reason, source_bar_ids
```

### 17.2 Stop and target policy

Daily OHLC does not reveal intrabar ordering. If both a stop and target lie
inside the same bar, a deterministic policy is mandatory. The conservative
first release should choose the adverse fill, state it in provenance, and allow
later models only when intraday bars support them.

### 17.3 Costs

Model costs by instrument class and effective date:

```text
cost_schedule(asset_type, exchange, effective_from, effective_to,
              brokerage_rule, exchange_fee_rule, tax_rule, stamp_rule,
              slippage_model)
```

Use actual per-trade notional where charges are percentage-based. A fixed
“one point” cost cannot be a permanent cash-equity model. Before a verified
schedule exists, label cash results **gross of costs** and prevent any claim of
net profitability.

## 18. API contract

### 18.1 Create or retrieve a run

```http
POST /v1/backtests
Idempotency-Key: <strategy_hash + data_version + execution_version>
```

```json
{
  "strategy": {"templateId": "cash-rsi-pullback-v1", "version": "1.0.0"},
  "instrument": "RELIANCE_SPOT",
  "range": {"kind": "3M", "end": "latest"},
  "dataVersion": "kite-2026-09-02.1"
}
```

Return `202 Accepted` with a `runId` for non-cached work, or `200` when the
artifact already exists. The browser polls or subscribes to status. It never
waits for a long calculation while a drag action is in progress.

### 18.2 Artifact response

```json
{
  "runId": "bt_...",
  "status": "completed",
  "provenance": {
    "instrument": "RELIANCE_SPOT",
    "assetType": "equity",
    "dataVersion": "...",
    "compilerVersion": "...",
    "executionModel": "cash-eod-v1",
    "window": "2026-06-01/2026-08-31",
    "warmupBars": 252
  },
  "metrics": {},
  "equity": [],
  "trades": [],
  "annotations": []
}
```

### 18.3 Live editing behavior

Debounce a drag/change by 300–500 ms. First request the capability check. Only
send a backtest request once the resulting strategy hash is valid. Abort stale
browser requests, but allow an already-started worker run to complete and cache
its artifact for the next identical request.

## 19. Commentary and annotations

Annotations are derived from artifact facts, not an unconstrained language
model. Build an `AnnotationFact` record with a calculation and source series:

```json
{
  "kind": "max_drawdown",
  "start": "2025-01-08",
  "trough": "2025-03-12",
  "value": -124.5,
  "unit": "points",
  "calculationVersion": "drawdown-v1"
}
```

The commentary layer can say “the largest realised-equity drawdown occurred
between these dates.” It must not say why it happened unless a linked,
time-stamped event rule supports that statement. It cannot call a result robust
without predefined statistical checks.

## 20. Surprise Me template backlog

The first usable catalogue should contain enough variety that random selection
does not feel like different EMA settings.

| Template | Style | Asset | Data readiness | Priority |
| --- | --- | --- | --- | --- |
| EMA trend cross | Trend | Cash equity / futures | Ready | P0 |
| RSI pullback in uptrend | Mean reversion | Cash equity | Ready | P0 |
| MACD trend | Trend | Cash equity / futures | Ready | P0 |
| 20-day breakout + volume | Breakout | Cash equity | OHLCV ready | P0 |
| Pullback to 20-day EMA | Pullback | Cash equity | OHLCV ready | P0 |
| Supertrend | Trend | Cash equity / futures | Indicator implementation | P1 |
| Nifty benchmark | Benchmark | Index | Ready | P0 |
| VIX-gated Nifty trend | Regime | Futures | VIX alignment | P1 |
| Results filing follow-through | Event | Cash equity | Event timestamps | P2 |
| ORB | Intraday | Futures | Contract intraday/roll work | P2 |
| VWAP reversion | Intraday | Equity/futures | Intraday and cost work | P2 |

Each row becomes eligible only after its golden fixture passes. The Surprise Me
selector must draw across styles before repeating a style, not optimise for the
best historical metric.

## 21. Acceptance criteria for the next release

The release is ready when all statements below are true:

- Cash equity, F&O futures, and index benchmark have visibly different
  execution and cost labels.
- A 1W, 1M, 3M, 6M, 1Y or All selection recalculates metrics from that exact
  visible window and records warm-up separately.
- Each visible runnable block returns a stable compiler result or a specific
  capability explanation before Run is enabled.
- Surprise Me can select at least six materially distinct runnable templates.
- No Surprise Me selection can generate an unsupported compiler error.
- Every completed result links to exact bars/facts, configuration and data
  version.
- Local development and production API use the same strategy schema and
  golden-test suite.

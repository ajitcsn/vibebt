# VibeBT Technical Product Requirements Document

**Status:** Proposed implementation specification  
**Version:** 1.0  
**Companion document:** [Product PRD](./PRD.md)  
**Market reality directive:** [MARKET_REALITY.md](./MARKET_REALITY.md)  
**Primary platform:** Responsive web application  

## 1. Technical objective

### 1.0 Market reality is a system invariant

All VibeBT outputs must reflect actual market conditions. The system may downsample a real series for display, but cannot smooth, invent, or cosmetically interpolate it. Unsupported blocks must fail validation or show an explicit limitation, never silently map to a different strategy. Every completed run requires data, engine, strategy, and assumption provenance.

Build a two-screen web application where a non-technical user can construct a trading hypothesis with visual blocks or plain-language controls, run a reproducible historical backtest, understand the result, and compare one variation without leaving the primary Workspace.

The implementation must preserve one source of truth:

> Blocks UI ↔ canonical strategy document ↔ plain-language sentence ↔ validated backtest plan

Blocks and sentence controls are two editors for the same document. Neither stores a separate representation. Every result is tied to an immutable strategy version, engine version, data version, and assumption set.

## 2. Scope

### 2.1 MVP screens

1. **Workspace:** start actions, catalog drawer, strategy builder, inline results, and inline comparison.
2. **Library:** saved strategies and recent runs.

Settings, glossary entries, strategy details, methodology, authentication, and test assumptions open as drawers, popovers, dialogs, or bottom sheets. They are not separate primary routes unless a shareable public URL requires one.

### 2.2 MVP market scope

- Liquid NSE equities, Nifty index universes, and major Indian ETFs.
- Daily bars as the canonical stored frequency.
- Weekly and monthly strategies derived from daily data.
- A limited set of event-relative daily strategies when reliable point-in-time event data is available.
- Long strategies first. Short selling may remain behind a feature flag until borrow assumptions are defined.

### 2.3 Out of scope

- Live trading or broker connectivity.
- Tick and sub-minute data.
- User-written code.
- Automatic parameter optimization.
- Four-way strategy comparison.
- Social feeds, points, badges, streaks, or other game systems.
- Free-form AI execution of ambiguous strategies.

## 3. Proposed architecture

Use a modular architecture that can be deployed simply at first and separated later.

### 3.1 Web application

- **Next.js and React with TypeScript** for the Workspace, Library, server-rendered catalog content, and share pages.
- A typed client state layer for the current draft strategy, last successful run, pinned comparison, and unsaved state.
- A server-state query library for catalog, run status, results, and Library data.
- A proven accessible drag-and-drop library rather than custom pointer handling.
- An SVG-capable chart library with accessible tabular fallbacks.

### 3.2 Application API

- **Python FastAPI** service for strategy validation, compilation, run creation, result retrieval, and catalog operations.
- Generated OpenAPI types consumed by the TypeScript client.
- Authentication may be handled by the web application, but authorization is enforced again by the API.

### 3.3 Backtest execution

- Python worker processes execute normalized backtest plans.
- Vectorized data operations use Polars, DuckDB, or equivalent columnar tools.
- A durable job queue separates interactive requests from computation.
- Redis may provide short-lived job state, rate limits, and cache coordination.
- PostgreSQL stores application records and run metadata.
- Object storage holds larger immutable artifacts such as equity curves, trade lists, breakdowns, and data manifests.

### 3.4 Data layer

- Vendor market data is transformed into an internal adjusted-bar schema.
- Fundamental and event records contain both the effective period and the timestamp when the information became publicly available.
- Dataset snapshots are versioned. A completed run always references a specific snapshot or manifest.
- Provider-specific fields remain behind adapters and never leak into the public strategy schema.

### 3.5 Initial deployment shape

The API and worker can share one repository and domain package while running as separate processes. Do not split compilation, validation, metrics, and catalog logic into independent services during the MVP. The first separation boundary is the asynchronous backtest worker because it has different compute and scaling needs.

## 4. Core domains

The system contains six domains:

1. **Strategy authoring:** blocks, sentence controls, parameters, and draft state.
2. **Strategy definition:** typed, versioned, provider-independent rules.
3. **Validation and compilation:** compatibility, data readiness, normalization, and executable plan creation.
4. **Backtesting:** signals, execution, portfolio state, costs, metrics, and artifacts.
5. **Catalog and Library:** templates, saved versions, run history, and sharing.
6. **Explanation:** deterministic summaries, warnings, glossary content, and next-test suggestions.

Each domain must have explicit types and test boundaries. UI labels must not be used as engine identifiers.

## 5. Canonical strategy document

### 5.1 Design requirements

The strategy document must be:

- Human-inspectable JSON.
- Strictly typed and schema-versioned.
- Immutable once attached to a completed run or public share.
- Independent of visual layout and data provider.
- Expressive enough for technical, fundamental, event-driven, and mixed strategies.
- Constrained enough to validate before execution.

### 5.2 Example

```json
{
  "schemaVersion": "1.0",
  "name": "The Bounce",
  "universe": {
    "type": "index_members",
    "id": "sp500",
    "membershipPolicy": "point_in_time"
  },
  "entry": {
    "direction": "long",
    "conditions": {
      "operator": "and",
      "items": [
        {
          "type": "price_change",
          "operator": "lte",
          "value": -5,
          "unit": "percent",
          "lookback": { "value": 1, "unit": "session" }
        },
        {
          "type": "rsi",
          "period": 14,
          "operator": "lt",
          "value": 30
        }
      ]
    },
    "execution": { "type": "next_open" }
  },
  "exit": {
    "items": [
      { "type": "bars_held", "value": 5, "unit": "session" }
    ],
    "precedence": "first_triggered"
  },
  "portfolio": {
    "sizing": "equal_weight",
    "maxConcurrentPositions": 10
  },
  "test": {
    "timeframe": "1d",
    "startDate": "2014-01-01",
    "endDate": "2024-12-31",
    "benchmark": "NIFTY50",
    "initialCapital": 100000,
    "commissionBps": 1,
    "slippageBps": 5
  }
}
```

### 5.3 Stable identifiers

Condition types, operators, units, universe identifiers, and execution types use stable machine identifiers. Display labels and icons are localizable metadata. Changing “Price falls” to different copy must not invalidate strategies or cached runs.

### 5.4 Complexity limits

The MVP schema and validator enforce:

- One universe.
- Long direction by default.
- Up to three entry conditions.
- `AND` or `OR` at one nesting level.
- One entry execution rule.
- Up to two exit rules.
- One timeframe and test range.
- One portfolio sizing model.

Unsupported nesting cannot be created in the UI or accepted through the API.

## 6. Visual fill-in-the-blanks composer

### 6.1 Layout

The Blocks editor is the default authoring mode for first-time users. A live sentence summary sits immediately above it.

```text
When price falls 5% in one day, buy Nifty 50 stocks at the next open,
hold for five days, then sell.

WHEN     [ Price falls: 5% / 1 day ]  [ + condition ]
TRADE    [ Nifty 50 stocks          ]  [ Buy        ]
ENTER    [ Next market open         ]
EXIT     [ Hold: 5 trading days     ]
TEST ON  [ Daily ] [ Jan 2014–Dec 2024 ]

[ Test assumptions ]                         [ Run backtest ]
```

Desktop uses a two-column authoring region with the block tray beside the canvas. Mobile stacks the rows and opens the tray as a bottom sheet. Results render beneath the authoring region on both layouts.

### 6.2 Block anatomy

Every draggable/selectable block contains:

- A stable block type identifier.
- A visible icon.
- A basic-language label.
- A one-line example or explanation when space allows.
- Parameter definitions with defaults and allowed ranges.
- Compatible slot types.
- Data requirements.
- Optional technical terminology.

Example metadata:

```json
{
  "type": "price_change",
  "label": "Price falls",
  "icon": "arrow-down-right",
  "technicalLabel": "Negative price return",
  "slots": ["entry_condition"],
  "defaults": {
    "operator": "lte",
    "value": -5,
    "unit": "percent",
    "lookback": { "value": 1, "unit": "session" }
  },
  "requires": ["ohlcv_daily"]
}
```

Icons come from one consistent SVG icon set. Icons are decorative reinforcement and never replace text.

### 6.3 Slot types

The canvas exposes typed slots:

- `entry_condition`
- `universe`
- `direction`
- `entry_execution`
- `exit_rule`
- `timeframe`
- `date_range`

Slots declare whether they are required, their maximum number of blocks, and compatible block types. Compatibility is determined from the registry, not hard-coded inside individual React components.

### 6.4 User input sequence

#### Start

The user chooses one of three inputs in the Workspace:

1. **Surprise me:** requests a coherent server-generated strategy and hydrates every required slot.
2. **Start with a hunch:** creates an empty strategy with safe defaults for execution, timeframe, benchmark, and costs.
3. **Browse ideas:** opens the catalog drawer; selecting an idea copies its strategy into the local draft.

No account is required to create or run the first strategy.

#### Select a slot or block

- Desktop pointer users may drag a block from the tray into a compatible slot.
- Any user may select a blank slot to open a tray filtered to compatible blocks.
- Keyboard users focus a slot, press Enter or Space, navigate the filtered list, and confirm a block.
- Touch users tap a slot and select a block in a bottom sheet.

Drag-and-drop is an enhancement, never the only authoring path.

#### Configure parameters

After placement, the block enters an inline configuration state. Only required parameters appear.

- Small enumerations use segmented buttons.
- Numeric values use a text-capable number input with optional stepper controls.
- Ranges may include a slider, but must retain typed inputs for precision and accessibility.
- Symbols and universes use searchable selection.
- Dates use presets plus an explicit date-range control.
- Units are displayed beside values and cannot be inferred silently.

Defaults produce a valid common configuration. Committing the values updates the canonical strategy draft.

#### Edit, move, lock, or remove

- Selecting a filled block reopens its parameter control.
- Dragging or using a Move action transfers it only to a compatible slot.
- Removing it restores the blank and may make the strategy temporarily unready.
- Locking a block affects only **Surprise me** or **Change unlocked parts**. It is UI draft metadata and is not part of the executable strategy.

#### Run

The **Run backtest** action is disabled until local structural validation passes. When disabled, the nearest issue is visible beside its slot and the action exposes a concise summary such as “Add an exit rule.”

On submission:

1. Flush pending input edits into the draft.
2. Validate locally for immediate feedback.
3. Send the full strategy document to server validation.
4. Normalize it and return its content hash.
5. Reuse a permitted cached result or enqueue a new run.
6. Show progress inline without hiding the builder.
7. Render results beneath the builder when complete.

### 6.5 Sentence synchronization

The sentence renderer is deterministic. It uses the canonical strategy document plus localized phrase templates. It does not use a language model.

Example phrase templates:

```text
price_change + lte + negative value → "price falls {abs(value)}% in {lookback}"
execution.next_open              → "at the next market open"
exit.bars_held                   → "hold for {value} trading days"
```

Direct sentence editing is implemented as tappable phrase chips, not unrestricted text. Selecting a phrase focuses the same parameter control used by its block. This prevents the sentence and Blocks views from diverging.

### 6.6 Visual states

Every slot supports these states:

- Empty required.
- Empty optional.
- Valid and filled.
- Selected/editing.
- Valid drop target.
- Invalid drop target.
- Locally invalid parameter.
- Server-invalid or data unavailable.
- Locked against random replacement.

Color cannot be the only state indicator. Use outline style, icon, text, and accessible status messaging.

### 6.7 Undo and draft persistence

- Maintain at least 30 local authoring actions for undo/redo.
- Autosave anonymous drafts in browser storage.
- Save authenticated drafts to the server after a short debounce.
- Never overwrite an immutable saved strategy version. Editing creates a draft child.
- Preserve the current draft through authentication redirects and recoverable network errors.

### 6.8 Persistent explorer, scratchpad, and live preview

The Workspace has three concurrent areas: the primary chart/result view, the composer, and a visible secondary column containing the block explorer plus scratchpad. The explorer is searchable and grouped by Indian-market signal, filter, universe, entry, exit, protection, target, and timeframe. It does not require route navigation or a modal to access blocks.

Scratchpad items are UI-only references containing a group and type. Store them in browser storage for anonymous users and sync them to a private server record for authenticated users. Dragging a scratchpad item into a slot applies the same typed block as dragging it from the explorer.

After a locally valid draft change, schedule a preview request with a 350–600 ms debounce. Cancel or ignore any in-flight preview whose draft revision is older than the current draft. The API can return a cached result immediately or enqueue a low-priority preview job. The UI labels this output **Live preview** until the user requests a full backtest. A full run pins exact data, engine, and assumption versions and receives normal interactive priority.

Do not run a preview while a required slot is empty or the draft is semantically invalid. Instead, retain the last valid chart, mark it stale, and show the specific missing rule beside the relevant slot.

## 7. Frontend component model

Suggested component boundaries:

- `WorkspaceShell`
- `StartBar`
- `CatalogDrawer`
- `StrategySummarySentence`
- `StrategyComposer`
- `ComposerRow`
- `TypedSlot`
- `BlockTray`
- `StrategyBlock`
- `BlockParameterEditor`
- `TestAssumptionsDrawer`
- `ReadinessPanel`
- `RunAction`
- `InlineRunProgress`
- `ResultSummary`
- `RealityCheck`
- `ResultCharts`
- `PinnedComparison`
- `LibraryList`

The components receive typed domain data and dispatch domain actions. They do not assemble API payloads or implement condition compatibility themselves.

### 7.1 Draft state

The client draft store contains:

- Canonical strategy document.
- UI-only block locks.
- Selected slot and active parameter editor.
- Undo/redo patches.
- Validation issues keyed by JSON path.
- Dirty state and last saved revision.
- Last completed run ID.
- Pinned comparison run ID.

Use immutable updates so undo history and dirty-path calculation remain predictable.

### 7.2 Responsive behavior

- At wide widths, the tray is persistent and the canvas retains all five rows.
- At medium widths, the tray becomes collapsible.
- On mobile, a selected slot opens a bottom sheet and rows stack vertically.
- Dragging is disabled when it causes scroll conflict; tap selection remains available.
- Results may collapse secondary charts, but the verdict and five primary metrics remain visible.

## 8. Block and ingredient registry

### 8.1 Registry responsibilities

The registry is shared conceptually by frontend and backend through generated schemas or a versioned manifest. It defines:

- Stable block identifier.
- Display metadata and icon key.
- Compatible slot types.
- Parameter schema and defaults.
- Allowed operators and ranges.
- Required datasets.
- Supported timeframes and asset classes.
- Sentence templates.
- Compiler handler identifier.
- Availability or feature flag.

The backend is authoritative. The frontend may cache a registry manifest for rendering and local validation.

### 8.2 Initial ingredient set

Ship a small complete set rather than a broad inconsistent set.

Entry conditions:

- Price rises or falls over a period.
- Price above or below moving average.
- Moving-average crossover.
- RSI above or below a threshold, labeled as recent strength or oversold/overbought.
- Price reaches a recent high or low.
- Volume above or below its average.
- Earnings event, if point-in-time data is ready.
- Profitability or valuation filter, only with point-in-time fundamentals.

Exits:

- Hold for a fixed number of sessions.
- Profit target.
- Stop loss.
- Opposite signal.

Universes:

- Major Nifty index members with point-in-time membership.
- Major ETFs.
- Selected sectors.
- Individual supported symbols.

## 9. Validation and compilation

### 9.1 Validation layers

#### Layer 1: client structural validation

Immediate checks for required slots, parameter types, local ranges, and manifest-declared compatibility. This improves interaction speed but is not trusted for execution.

#### Layer 2: server schema validation

Reject unknown fields, unsupported nesting, invalid operators, invalid ranges, and schema-version mismatches.

#### Layer 3: semantic validation

Check combinations such as:

- Fundamental signals on unsupported intraday timeframes.
- An exit horizon outside available data.
- Short direction when disabled.
- A benchmark outside supported coverage.
- Event timing without reliable publication timestamps.
- A universe whose historical membership is unavailable.
- Mutually exclusive conditions.

#### Layer 4: data readiness

Resolve the internal dataset requirements and confirm coverage for the requested dates, universe, and timeframe. Return the earliest valid start date and estimated opportunity count where inexpensive.

### 9.2 Issue contract

Every issue includes:

```json
{
  "code": "TIMEFRAME_NOT_SUPPORTED",
  "severity": "error",
  "path": "/entry/conditions/items/1",
  "message": "Company results can currently be tested only daily or slower.",
  "suggestions": [
    { "action": "set_timeframe", "value": "1d", "label": "Use daily" }
  ]
}
```

Messages use basic language. The code and path remain stable for UI behavior and analytics.

### 9.3 Normalization

Before hashing or execution:

- Fill explicit documented defaults.
- Sort only semantically unordered structures.
- Normalize dates, units, numeric precision, and identifiers.
- Remove UI-only state.
- Resolve the strategy schema version.

Generate a content hash from canonical serialized JSON plus engine version, dataset version, and calculation-affecting assumptions. This key supports caching and reproducibility.

### 9.4 Compilation

Compilation transforms the normalized strategy into an internal execution plan:

1. Resolve universe membership per session.
2. Resolve data dependencies and warm-up periods.
3. Build condition expression nodes.
4. Define when signals become observable.
5. Define entry and exit execution timestamps.
6. Define portfolio and overlap policy.
7. Attach costs and benchmark.
8. Produce a deterministic plan or structured compilation errors.

The compiler cannot evaluate arbitrary user code or expressions.

## 10. Backtest engine

### 10.1 Execution rules

- Signals based on a completed daily bar execute no earlier than the next tradable bar unless the rule explicitly uses earlier available information.
- Market calendars determine valid sessions.
- Corporate actions and adjusted values follow documented calculation rules.
- Entry and exit precedence are deterministic.
- Maximum concurrent positions and insufficient cash behavior are explicit.
- Commission and slippage are included by default.
- The engine records rejected or skipped trades with reasons.

### 10.2 Bias controls

- Point-in-time index membership when testing historical index universes.
- Delisted securities included when licensed data permits.
- Fundamentals joined by public availability timestamp.
- Events joined by reliable announcement timestamp and timezone.
- Warm-up data excluded from the visible test period.
- No same-bar use of a value that was unavailable at execution time.

A capability must remain unavailable if the required bias controls cannot be met.

### 10.3 Result artifacts

Each successful run produces:

- Headline metrics.
- Benchmark metrics.
- Equity and benchmark series.
- Drawdown series.
- Trade list with signal and execution timestamps.
- Period and regime breakdowns where supported.
- Distribution data for wins, losses, and holding periods.
- Exposure and concentration measures.
- Reality Check inputs and warnings.
- Data and calculation manifest.

### 10.4 Primary metrics

- Total return and annualized return when appropriate.
- Maximum drawdown.
- Number of completed trades.
- Win rate, average win, and average loss.
- Benchmark return and excess return.

Secondary metrics include volatility, exposure, profit factor, Sharpe ratio, turnover, and cost impact.

## 11. Deterministic result explanation

Headline copy and warnings come from tested rules, not a language model.

Examples:

- If trades are below the minimum sample threshold, lead with the low-sample warning.
- If one year contributes most excess return, describe period concentration.
- If the strategy underperforms the benchmark with lower drawdown, describe that tradeoff rather than calling it a failure.
- If nearby parameters change the conclusion materially, flag instability.

An optional language model may later rephrase approved facts, but it cannot calculate metrics, suppress warnings, or invent explanations.

## 12. API contract

### 12.1 Strategy and registry

- `GET /v1/ingredients` returns the versioned block registry available to the user.
- `POST /v1/strategies/validate` validates a draft and returns normalized data, issues, data readiness, and a plain-language sentence.
- `POST /v1/strategies/generate` creates a coherent random strategy using optional family and locked-path constraints.
- `POST /v1/strategies` saves a new immutable strategy version or draft.
- `GET /v1/strategies/{id}` returns an authorized strategy version.

### 12.2 Runs

- `POST /v1/runs` validates and creates or reuses a run.
- `GET /v1/runs/{id}` returns status, progress stage, summary, and artifact links.
- `GET /v1/runs/{id}/trades` returns a paginated trade list.
- `GET /v1/runs/{id}/series` returns requested chart series with resolution controls.
- `POST /v1/runs/{id}/pin` records a comparison selection for an authenticated user.

Run creation is idempotent when given the same strategy hash and caller idempotency key.

### 12.3 Catalog and Library

- `GET /v1/catalog` supports filters and cursor pagination.
- `GET /v1/library` returns saved strategies and recent runs.
- `POST /v1/library/saves` saves a strategy version.
- `DELETE /v1/library/saves/{id}` removes the user’s save relationship, not the immutable shared strategy.

### 12.4 Run state

Run status values:

- `queued`
- `resolving_data`
- `computing_signals`
- `simulating_trades`
- `calculating_results`
- `completed`
- `failed`
- `cancelled`

The client receives updates through server-sent events or short polling. WebSockets are unnecessary for the MVP unless infrastructure already supports them.

## 13. Persistence model

Core records:

- `users`
- `ideas`
- `strategy_versions`
- `strategy_drafts`
- `backtest_runs`
- `run_artifacts`
- `dataset_versions`
- `engine_versions`
- `catalog_publications`
- `user_saves`
- `comparison_pins`

### 13.1 Strategy versions

Store canonical JSON, schema version, content hash, parent version ID, author, visibility, created timestamp, and optional idea ID. Completed runs reference a strategy version and never a mutable draft.

### 13.2 Runs

Store status, owner, strategy version, normalized recipe hash, engine version, dataset version, queue timestamps, completion timestamp, summary metrics, warning codes, failure code, and artifact manifest location.

### 13.3 Data retention

- Anonymous drafts remain in browser storage only unless a run requires temporary server storage.
- Authenticated drafts follow documented retention and deletion policy.
- Shared strategy versions remain addressable while published, with ownership and deletion rules defined before launch.
- Large generated artifacts may be regenerated or expired only if the immutable recipe and exact required data snapshot remain available.

## 14. Random strategy generation

The generator operates on curated templates and compatibility metadata. It does not randomly choose every field independently.

Generation steps:

1. Select a supported strategy family.
2. Select a template containing typed empty slots.
3. Preserve user-locked JSON paths.
4. Fill remaining slots from compatible weighted ingredients.
5. Choose parameters from curated ranges.
6. Validate semantics and data readiness.
7. Reject ideas below a configurable estimated sample threshold unless marked experimental.
8. Return the complete strategy, sentence, short hypothesis, and caveats.

Use a seed so generated results can be reproduced in tests. The API may accept the previous strategy hash to reduce immediate repeats.

## 15. Inline results and comparison

### 15.1 Results rendering

The result region appears below the composer and begins with:

1. Deterministic one-sentence verdict.
2. Five primary metrics.
3. Equity curve against benchmark.
4. Reality Check warnings.
5. Two next-test suggestions.

Secondary charts and metrics remain collapsed by default.

### 15.1a Chart navigation and annotations

The primary return chart supports fixed view ranges of 1Y, 3Y, 5Y, and All, plus zoom in/out controls. Range changes query or select a slice of the same immutable result series. Zoom is a client display transform over the selected range; it never recalculates metrics or changes the backtest recipe.

For large series, the API returns resolution-aware points and preserves extrema during downsampling. The client requests a higher-resolution window after a zoom or pan settles, with cancellation keyed by run ID, range, resolution, and client request sequence.

The explanation service may emit no more than two chart annotations per selected range. Each annotation contains start/end timestamps, an anchor timestamp/value, category, severity, title, deterministic body text, and supporting result facts. Categories include regime change, drawdown, benchmark divergence, trade concentration, cost sensitivity, and data warning. The chart draws a pointer at the anchor; the accessible text counterpart appears directly below the chart.

Annotations must be fact-backed. They may not imply causality where the engine has only observed correlation.

### 15.1b Trader review

Return a deterministic review card with four bounded sections: return quality, risk discipline, execution realism, and disconfirming evidence. This card is not investment advice and must not issue buy, sell, or position-size instructions. Its purpose is to help users distinguish an attractive curve from a usable, robust strategy.

### 15.2 Comparison

The user may pin one completed run. After modifying and rerunning the strategy, the result region shows:

- Changed strategy paths and human labels.
- Return, drawdown, trade count, and benchmark-edge deltas.
- Whether added return came with added risk.
- Period stability differences where calculable.

Only two runs are compared in the MVP. The comparison is computed from stored result artifacts and strategy documents, not from chart pixels or client-side approximations.

## 16. Accessibility requirements

- Meet WCAG 2.2 AA across the core authoring and result flow.
- Every drag operation has a click, tap, and keyboard equivalent.
- Blocks expose visible labels and accessible names.
- Slots announce label, required state, current value, compatibility, and errors.
- Drop target changes are announced through an appropriate live region without excessive chatter.
- Focus returns predictably after block placement, parameter editing, drawer closure, and run completion.
- Profit and loss never rely on color alone.
- Charts have concise text summaries and accessible data tables.
- Reduced-motion settings remove roll, drag, and result-transition animation.
- Touch targets meet minimum size guidance.

Accessibility tests must include completing a full strategy and backtest without a pointer.

## 17. Performance requirements

- Workspace shell usable within 2.5 seconds at the 75th percentile on a representative mobile connection, excluding external authentication.
- Local block placement and parameter changes reflected within 100 milliseconds.
- Server validation response within 500 milliseconds at the 95th percentile when no data scan is required.
- Cached run summary returned within 1 second at the 95th percentile.
- Typical uncached daily backtest for the supported universe completes within 15 seconds at the 90th percentile.
- Progress feedback begins within 500 milliseconds after run submission.
- Large time series are downsampled for display while preserving full artifacts for calculations.

Performance targets should be measured with production-like universe sizes and histories before public beta.

## 18. Reliability and reproducibility

- Same normalized recipe, engine version, and dataset version must produce identical result artifacts within documented floating-point tolerances.
- Worker retries must not create duplicate completed runs.
- Run stages must be resumable or safely restartable.
- A failed run returns a stable failure code and user-safe explanation.
- Dataset ingestion is atomic at the manifest level. Runs cannot see partial datasets.
- Share pages display calculation and data version metadata.

Backtest engine golden tests cover known strategies against small fixed datasets with hand-verified trades.

## 19. Security and privacy

- Strategies and runs are private by default.
- Every non-public resource is authorization-checked by owner or explicit share permission.
- Public share tokens are high entropy and revocable.
- Apply request size limits, schema depth limits, rate limits, and run quotas.
- Do not evaluate user-provided code, templates, SQL, or expressions.
- Sanitize user-provided names and notes before rendering.
- Encrypt network traffic and managed storage using platform standards.
- Keep vendor credentials and data entitlements server-side.
- Do not send private strategy contents or notes to general analytics.
- Record administrative publication and moderation actions in an audit log.

## 20. Observability

### 20.1 Technical telemetry

- API latency and error rate by endpoint.
- Queue wait and execution time by run stage.
- Worker CPU, memory, and failure code.
- Dataset coverage and ingestion failures.
- Cache hit rate.
- Validation issue frequency by code.
- Client error boundaries and failed draft recovery.

Trace a run from API request through worker completion using a correlation ID. Do not include private strategy JSON in logs.

### 20.2 Product telemetry

Track the events defined in the Product PRD plus:

- Composer mode selected.
- Slot selected.
- Block placed, configured, moved, removed, or locked.
- Placement method: drag, click, tap, or keyboard.
- Validation issue shown and resolved.
- Draft restored.

Parameters containing symbols, user notes, or unpublished strategy details should be excluded or coarsened.

## 21. Testing strategy

### 21.1 Unit tests

- Strategy schema parsing and migrations.
- Block compatibility.
- Sentence rendering.
- Normalization and hashing.
- Compiler handlers.
- Metric calculations.
- Deterministic result-summary rules.

### 21.2 Property and invariant tests

- Generated strategies always validate or return a controlled rejection.
- Normalization is idempotent.
- UI-only state never changes the recipe hash.
- No trade executes before its signal is observable.
- Portfolio value reconciles from cash and positions.
- Costs never improve returns.

### 21.3 Integration tests

- Strategy validation through compilation.
- Run creation, queue processing, artifacts, and result retrieval.
- Dataset version pinning.
- Cached-run reuse and authorization.
- Save, edit, version, and share behavior.

### 21.4 End-to-end tests

- Build The Bounce through drag-and-drop and run it.
- Build the same strategy using keyboard-only selection and confirm identical JSON.
- Load a catalog idea, change one block, rerun, and compare.
- Recover an anonymous draft after refresh.
- Handle invalid data coverage and failed runs.
- Complete the core flow on a narrow mobile viewport.

### 21.5 Financial correctness tests

- Hand-authored fixtures for splits, dividends, delistings, holidays, gaps, event timestamps, index membership changes, and fundamental publication delays.
- Golden trade lists independently reviewed for each initial ingredient.
- Regression snapshots for headline metrics and warnings.

## 22. Delivery plan

### Phase 1: authoring foundation

- Canonical strategy schema and migrations.
- Ingredient registry.
- Blocks composer with click/tap and keyboard placement.
- Parameter editors and sentence synchronization.
- Local validation, undo/redo, and draft persistence.
- Static result fixtures for frontend development.

Drag-and-drop may follow click/tap placement within this phase because semantic authoring is the critical behavior.

### Phase 2: backtest vertical slice

- Daily OHLCV ingestion for a narrow supported universe.
- Server validation and compilation.
- Worker queue and deterministic engine.
- One technical entry condition, one universe, next-open execution, and fixed-hold exit.
- Inline run progress and core results.

The milestone is a correct end-to-end version of **The Bounce**.

### Phase 3: MVP breadth

- Initial technical ingredient set.
- Approved fundamental and event ingredients where point-in-time data is ready.
- Weekly/monthly aggregation.
- Reality Check, trade inspection, comparison, catalog drawer, Library, and sharing.
- Performance, accessibility, and security hardening.

### Phase 4: private alpha

- Seed catalog.
- Production data manifests and monitoring.
- Moderated user testing.
- Correctness review and documented methodology.
- Feature flags for incomplete ingredients or providers.

## 23. Technical acceptance criteria

The MVP is technically ready when:

1. Blocks, sentence chips, saved JSON, and compiled plans represent the same strategy without loss.
2. A user can complete the authoring flow through drag, click/tap, or keyboard and receive the same result.
3. Invalid combinations are prevented locally and rejected authoritatively by the server.
4. Every completed run references immutable strategy, engine, dataset, and assumption versions.
5. A repeated identical recipe produces the same results within documented tolerances.
6. Technical, approved fundamental, and approved event blocks use the same registry and compiler interfaces.
7. Results, warnings, and comparisons render inline in the Workspace.
8. The two-primary-screen constraint is maintained.
9. Core performance targets hold against production-like data.
10. Accessibility, financial fixture, authorization, and failure-recovery test suites pass.

## 24. Decisions required before implementation

1. Select and license a data provider that supports the required point-in-time behavior.
2. Confirm the exact initial equity universe and historical-membership policy.
3. Decide whether short strategies are excluded or feature-flagged.
4. Approve the first 12–20 ingredients and their beginner-facing labels.
5. Define commission, slippage, capital, overlap, and benchmark defaults.
6. Set anonymous and authenticated run quotas.
7. Confirm retention rules for run artifacts and public shares.
8. Assign independent ownership for validating financial correctness.

## 25. First engineering spike

Before building the complete interface, implement one thin vertical slice:

1. Render the five typed slots.
2. Place **Price falls**, **Nifty 50 stocks**, **Buy**, **Next open**, **Hold**, and **Daily** blocks using both pointer and keyboard.
3. Edit the percentage, lookback, and holding period inline.
4. Produce the canonical JSON and deterministic sentence.
5. Validate and normalize it through the API.
6. Run it against a small fixed dataset.
7. Render the verdict, five primary metrics, equity curve, and trade list below the composer.

This spike should prove the highest-risk contract: a simple visual action becomes a precise, reproducible financial test without exposing code or losing meaning.

## 26. Workspace state machines

### 26.1 Draft lifecycle

The client must model draft state explicitly:

```text
empty
  → editing
  → locally_valid
  → server_validating
  → server_valid | server_invalid
  → submitting
  → clean_after_submission

Any document change after submission:
clean_after_submission → editing
```

Rules:

- Only `locally_valid` or `server_valid` drafts may be submitted.
- A validation response applies only if its client revision matches the latest draft revision.
- A stale server response is discarded without changing visible errors.
- Loading a catalog item, generated idea, or Library version replaces the draft only after preserving the current recoverable snapshot.
- A completed run never marks a subsequently edited draft as clean.

Each mutation increments a monotonically increasing `draftRevision`. Debounced server validation includes that revision, and the client ignores mismatched responses.

### 26.2 Run lifecycle

```text
idle
  → creating
  → queued
  → running
  → completed
  → pinned | idle

creating | queued | running → failed
queued | running           → cancelled
```

The server owns run status. The client may display optimistic stage text but cannot infer completion from elapsed time. Terminal states are `completed`, `failed`, and `cancelled`.

### 26.3 Composer interaction lifecycle

```text
slot_idle
  → slot_focused
  → tray_open
  → block_selected
  → configuring
  → committed

configuring → cancelled → previous slot value
```

Dragging joins the lifecycle at `block_selected`. Dropping opens `configuring` when parameters require confirmation; otherwise it commits immediately. Escape cancels the active transient action and restores focus to its originating slot.

## 27. Detailed API payloads

### 27.1 Validate a strategy

Request:

```http
POST /v1/strategies/validate
Content-Type: application/json
```

```json
{
  "clientRevision": 42,
  "strategy": { "schemaVersion": "1.0" },
  "options": {
    "includeSentence": true,
    "includeOpportunityEstimate": true
  }
}
```

Response:

```json
{
  "clientRevision": 42,
  "valid": true,
  "normalizedStrategy": { "schemaVersion": "1.0" },
  "strategyHash": "sha256:...",
  "sentence": "When price falls ...",
  "issues": [],
  "readiness": {
    "supported": true,
    "earliestStartDate": "2001-01-02",
    "estimatedOpportunities": 1834,
    "datasetRequirements": ["ohlcv_daily", "index_membership_sp500"]
  }
}
```

The server may omit an expensive opportunity estimate and return `null` with a reason. This must not block a run when all required data is available.

### 27.2 Create a run

Request:

```http
POST /v1/runs
Idempotency-Key: 8f0e...
Content-Type: application/json
```

```json
{
  "strategy": { "schemaVersion": "1.0" },
  "clientRevision": 42,
  "requestedArtifacts": [
    "summary",
    "equity_curve",
    "drawdowns",
    "trade_list",
    "period_breakdown"
  ]
}
```

Accepted response:

```json
{
  "runId": "run_01J...",
  "status": "queued",
  "cache": "miss",
  "strategyVersionId": "strv_01J...",
  "strategyHash": "sha256:...",
  "statusUrl": "/v1/runs/run_01J...",
  "eventsUrl": "/v1/runs/run_01J.../events"
}
```

Cached response uses the same contract with `status: completed` and `cache: hit`. Authorization and visibility are checked before returning another user’s cached artifacts. Computation may be deduplicated globally while ownership records remain separate.

### 27.3 Run status response

```json
{
  "runId": "run_01J...",
  "status": "computing_signals",
  "progress": {
    "stage": 2,
    "totalStages": 4,
    "label": "Finding historical matches"
  },
  "createdAt": "2026-09-02T10:00:00Z",
  "startedAt": "2026-09-02T10:00:01Z",
  "completedAt": null,
  "result": null,
  "failure": null
}
```

Do not expose unreliable percentage-complete values. Stage progress is sufficient unless the worker can measure total work accurately.

### 27.4 Error envelope

Every API error uses one envelope:

```json
{
  "error": {
    "code": "STRATEGY_INVALID",
    "message": "This idea needs an exit rule before it can be tested.",
    "requestId": "req_01J...",
    "retryable": false,
    "issues": [
      {
        "code": "REQUIRED_SLOT_EMPTY",
        "path": "/exit/items",
        "message": "Add an exit rule."
      }
    ]
  }
}
```

HTTP status conventions:

- `400` malformed request.
- `401` unauthenticated protected request.
- `403` authenticated but unauthorized.
- `404` resource absent or intentionally concealed.
- `409` stale revision, immutable-version conflict, or idempotency conflict.
- `422` well-formed but invalid strategy.
- `429` quota or rate limit.
- `503` temporary data or worker unavailability.

## 28. Data ingestion and point-in-time model

### 28.1 Ingestion pipeline

```text
Vendor delivery
  → immutable raw landing zone
  → schema and entitlement checks
  → normalization
  → corporate-action reconciliation
  → point-in-time joins and coverage checks
  → partitioned analytical files
  → dataset manifest publication
```

Publishing the manifest is the atomic commit. Workers read only published manifests.

### 28.2 Daily bars

Normalized bar fields:

- Internal instrument ID.
- Trading session date.
- Exchange and calendar ID.
- Raw open, high, low, close, and volume.
- Adjusted values or the corporate-action factors required to calculate them.
- Vendor revision identifier.
- Ingested timestamp.

Instrument identity must not depend only on ticker symbols. Symbol changes map to a stable internal instrument ID with effective date ranges.

### 28.3 Corporate actions

Store splits, cash dividends, symbol changes, mergers, and delistings separately from bars. The engine chooses raw or adjusted fields according to calculation semantics. Entry and exit prices, indicator values, and shareholder-return comparisons must follow one documented adjustment policy.

### 28.4 Index membership

Membership records contain internal instrument ID, index ID, inclusion timestamp, exclusion timestamp, source, and dataset version. Universe resolution occurs for each trading session. Using today’s membership for historical tests is prohibited.

### 28.5 Fundamentals

Each fundamental observation contains:

- Instrument ID.
- Fiscal period end.
- Public availability timestamp.
- Original filing or vendor timestamp.
- Value and unit.
- Restatement/version identifier.
- Ingested timestamp.

The engine joins the newest observation whose public availability timestamp is no later than the signal evaluation time. Restated values cannot silently replace what a market participant knew historically.

### 28.6 Events

Events contain event type, instrument or market scope, scheduled timestamp when applicable, actual public timestamp, timezone, source confidence, and revision history. Strategies that depend on a precise event time are enabled only for sources with sufficient timestamp quality.

### 28.7 Dataset manifest

Every published dataset version records:

- Immutable version ID.
- Source versions.
- Covered asset types and date ranges.
- File or partition checksums.
- Normalization-code version.
- Known gaps and limitations.
- Publication timestamp.
- Superseded version, if any.

Completed runs retain the manifest ID. Reprocessing data creates a new manifest and never mutates historical run provenance.

## 29. Worker execution and concurrency

### 29.1 Job payload

The queue message contains identifiers, not large strategy or market-data payloads:

```json
{
  "runId": "run_01J...",
  "strategyVersionId": "strv_01J...",
  "engineVersion": "engine_1.0.0",
  "datasetVersion": "data_2026_09_01",
  "recipeHash": "sha256:...",
  "requestedArtifacts": ["summary", "equity_curve", "trade_list"]
}
```

The worker loads immutable inputs, verifies their hashes, acquires a lease for the run, and updates stage transitions transactionally.

### 29.2 Idempotency and leases

- Only one active worker lease exists per run.
- Leases expire and can be reclaimed after worker loss.
- Artifact writes use temporary object keys followed by atomic manifest publication.
- A retry verifies existing artifact checksums before recomputing.
- Final database completion occurs only after the artifact manifest is durable.
- Duplicate queue delivery is expected and safe.

### 29.3 Resource controls

Before enqueueing, estimate cost from universe size, date range, timeframe, and ingredient dependencies. Enforce configured bounds for anonymous and authenticated tiers.

Workers apply:

- Maximum instruments per run.
- Maximum historical range.
- Memory and wall-clock limits.
- Maximum trade/artifact rows.
- Cancellation checks between major stages.

Failure codes distinguish invalid strategy, missing data, quota, timeout, worker fault, and internal calculation failure.

### 29.4 Priority

Interactive user runs receive higher priority than catalog precomputation and maintenance jobs. Repeated rerolls cannot monopolize workers; rate limits apply by user, anonymous session, and IP risk signals.

## 30. Cache design

### 30.1 Cache key

```text
SHA-256(
  canonical strategy JSON
  + strategy schema version
  + engine version
  + dataset manifest ID
  + metric definition version
  + requested artifact profile
)
```

Display-only settings, strategy name, UI block order for commutative conditions, and lock state do not affect the key.

### 30.2 Cache layers

- Browser cache for registry, catalog, and already viewed result payloads.
- Application cache for registry and run-status reads.
- Durable artifact reuse by recipe hash for completed runs.

Never cache authorization decisions in shared result payloads. Private annotations and ownership metadata are joined after artifact lookup.

### 30.3 Invalidation

Immutable run artifacts are not invalidated. A new engine, dataset, or metric version produces a different key. Catalog snapshots may be re-run against newer versions and must display their calculation date and provenance.

## 31. Repository and module boundaries

Recommended monorepo shape:

```text
apps/
  web/                 Next.js Workspace and Library
  api/                 FastAPI routes and orchestration
  worker/              queue consumer and run lifecycle
packages/
  strategy-schema/     JSON Schema and generated TS/Python types
  ingredient-registry/ manifests, labels, compatibility, defaults
  ui/                  accessible blocks, slots, charts, drawers
  backtest-domain/     compiler, execution model, metrics
  data-domain/         internal schemas and provider adapters
  explanation/         deterministic verdict and warning rules
infra/
  migrations/          database migrations
  deployment/          service and worker definitions
tests/
  fixtures/            immutable financial correctness datasets
  golden/              expected plans, trades, and metrics
```

If TypeScript and Python packages cannot share generated code directly, JSON Schema is the contract source. CI regenerates both language bindings and fails when generated files differ.

### 31.1 Dependency direction

- UI depends on generated strategy types and the registry manifest.
- API orchestration depends on domain packages.
- Compiler depends on strategy types and data interfaces, not HTTP or database implementations.
- Engine depends on compiled plans and abstract data access.
- Provider adapters implement data interfaces but cannot alter engine semantics.
- Explanation depends on result facts and warning inputs, never raw UI state.

Circular dependencies are prohibited.

## 32. Schema and engine versioning

### 32.1 Strategy schema migration

Persist the schema version with every document. Readers support the current version and explicitly maintained older versions. Migration functions are pure and chained:

```text
v1.0 document → migrate_1_0_to_1_1 → v1.1 document
```

Never rewrite immutable historical strategy JSON in place. A migrated editable copy becomes a new version. Historical runs continue to display the original recipe.

### 32.2 Engine version

Increment the engine version when execution, cost, metric, or portfolio semantics change. Copy changes and visual changes do not require a new engine version.

### 32.3 Registry version

The registry manifest has its own version. Removing an ingredient from authoring does not make historical strategies unreadable. Compiler support must remain available or the old run must render from stored artifacts with a clear legacy label.

### 32.4 Metric definitions

Metric calculations are versioned independently when necessary. Each result exposes a methodology reference so a metric name cannot silently change meaning.

## 33. Continuous integration gates

Every merge to the main branch must pass:

- Type checking and linting.
- Strategy schema compatibility checks.
- Generated-client drift check.
- Unit and integration tests.
- Golden financial regression suite.
- Keyboard-only composer end-to-end test.
- Automated accessibility scan for core states.
- Database migration forward test.
- Dependency and secret scans.

Release candidates additionally run:

- Production-sized performance fixtures.
- Dataset coverage checks.
- Backward rendering of representative older strategy versions.
- Worker retry and duplicate-delivery tests.
- Backup restoration test for run metadata and artifact manifests.

No ingredient becomes generally available until its compiler handler, sentence templates, UI parameter controls, point-in-time data requirements, golden trades, and methodology note are complete.

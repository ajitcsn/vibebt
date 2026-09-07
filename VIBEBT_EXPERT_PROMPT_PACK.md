# VibeBT expert review and execution prompt pack

**Purpose:** use these prompts to turn VibeBT from a visually playful prototype into a credible, simple Indian-market research product that other people can open from one URL.

**Prepared for the current repository on:** 7 September 2026

## The short expert verdict

### Product usefulness

VibeBT has a good product wedge: it can let a non-technical Indian swing trader turn a hunch into an explicit rule and see quickly whether the idea deserves more study. That is useful.

Today, it should be described as a **useful learning and idea-screening prototype**, not yet as a trading-decision backtester. The largest gap is not the number of indicators. It is the difference between what the interface appears to configure and what the engine actually executes.

The highest-value product loop is:

> Pick one NSE instrument → express one rule visually → run a valid historical test → inspect trades and risk → change one assumption → compare → save.

Do not expand beyond that loop until every active control is truthful.

### UI and UX direction

Keep the current **three-column, 3:1:1 desktop workspace** as the baseline:

1. **Analysis:** instrument, result status, chart, metrics, and trade inspection.
2. **Idea builder:** a compact, stationary fill-in-the-blanks rule composer.
3. **Blocks:** a searchable compatible-block list with a visible scratchpad.

The interface should feel playful because experimentation is fast and understandable. It does not need game mechanics.

The most important UX change is **progressive compatibility**: selecting a builder slot should immediately show only blocks that are valid for that slot, instrument, timeframe, available data, and compiler. Unsupported blocks can remain discoverable, but they must be visibly unavailable before selection and must explain exactly what is missing.

### Trader verdict

The concept becomes materially useful when it answers these questions without ambiguity:

1. What exact rule caused every entry and exit?
2. Did every visible input reach the compiler?
3. Does the equity path include daily unrealised profit and loss?
4. Are costs, sizing, corporate actions, and trade chronology realistic for that asset class?
5. Did the idea work outside the period and instrument on which it was discovered?

Current priority is to fix the interface-to-engine contract, mark-to-market equity and drawdown, stop/target chronology, percentage/account returns, Indian transaction costs, trade inspection, and out-of-sample checks. More indicator buttons come later.

### Stop signs already visible in the current implementation

1. The browser request sends the **series, signal, selected range, stop/target presence, point costs, and EMA periods**. It does not send the visible Scope, confirmation filters, side, entry rule, exit rule, timeframe, or exact risk-block value. Those controls currently promise more than the test executes. See `src/main.js` around lines 547–560.
2. Any selected stop becomes a fixed **1.5 ATR stop**, and any selected target becomes a fixed **2.5 ATR target**, regardless of the percentage or risk block shown in the builder. See `scripts/kite_bridge.py` around lines 125–136.
3. The bridge constructs cumulative points from the engine's per-day `points` column and derives drawdown from that series. The external engine must be independently checked to prove that open positions are marked to market daily before this can be called account equity. See `scripts/kite_bridge.py` around lines 138–151.
4. Instrument close and strategy equity are normalized against separate ranges but drawn in one plot with only an equity-points axis. That makes their visual relationship easy to misread. See `src/main.js` around lines 326–363.
5. The production blocker is structural: API calls target `127.0.0.1`, and npm scripts reference one Mac's absolute Python environment. See `src/main.js` around lines 532–560 and `package.json` lines 6–9.

### Lowest-effort hosting direction

Use **one Railway project** for the first public version:

```text
Browser
   │ one origin
   ▼
FastAPI web service
   ├── serves the built Vite app
   ├── exposes /api/*
   └── runs bounded daily, single-scrip backtests
          │
          ▼
Railway S3-compatible bucket
   ├── immutable raw data
   ├── versioned normalized daily data
   └── manifests and checksums

Railway cron service
   └── validates and publishes incremental market-data updates
```

This removes the local bridge from the user's life. It also avoids a frontend host plus a separate API, cross-origin configuration, two deployments, and two failure surfaces.

Keep anonymous saved ideas in browser `localStorage` at launch. Do not add PostgreSQL, Redis, Kubernetes, or an always-on worker until a real requirement or measured load justifies them.

Railway's Hobby plan is currently **$5/month with $5 of resource usage included**. Storage buckets are **$0.015 per GB-month**, with free bucket API operations and bucket egress. A reasonable planning range is **$5–15/month for an invite-only launch** and **$15–40/month for early public use**, excluding the domain, monitoring upgrades, taxes, and market-data licences. Validate the real number with one week of measured usage. See [Railway plan pricing](https://docs.railway.com/pricing/plans), [cron jobs](https://docs.railway.com/cron-jobs), and [bucket billing](https://docs.railway.com/storage-buckets/billing).

**Important:** market-data redistribution rights are a public-launch gate. Hosting is cheap; licensed Indian historical market data can be the dominant cost.

## Recommended work order

1. **Truth audit:** prove what every visible control actually changes.
2. **Backtest correctness:** fix mark-to-market equity, order chronology, costs, sizing, and test-window semantics.
3. **UX redesign:** simplify the workspace around supported actions and visibly separate test period from chart viewport.
4. **Trader workflow:** add a price chart with entries/exits, trade ledger, benchmark, robustness, and provenance.
5. **Public hosting:** package the engine, use same-origin APIs, publish licensed normalized data, then deploy one service.

Run Prompts 1–4 independently, then give their outputs to Prompt 5. Use Prompt 6 as the release gate.

---

## Prompt 1: 20-year product builder and founder review

```text
You are a founder-level product builder with 20 years of experience taking consumer and prosumer software from rough prototype to a focused, trusted product.

Review the actual VibeBT repository at:

/Users/ajitc/Desktop/projects/vibeBT

Do not review only the PRD. Run the application, inspect the working code, and distinguish current behavior from planned behavior.

Product:
VibeBT is a visual Indian-market idea builder and backtester for a non-technical retail swing trader. The user has a hunch and basic market vocabulary but cannot code. They should be able to express a trading rule with plain-language blocks, test it against actual market history, understand what happened, vary one assumption, compare the result, and keep useful ideas.

Personality:
- Curious, approachable, and visual.
- Minimal game design. No badges, streaks, points, confetti, artificial rewards, or casino treatment.
- Serious enough that a cautious trader understands the limits of every result.

Non-negotiable contract:
- Treat MARKET_REALITY.md as binding.
- No fabricated or smoothed market output.
- No active UI control unless the engine consumes it exactly or labels the simplification before use.
- No hidden assumptions, look-ahead, unsupported substitution, or causal commentary without evidence.
- Keep the product to a small number of screens.

Core job:
“Help me turn a market hunch into a testable rule and learn whether the historical evidence is worth further investigation.”

Core loop:
Choose an instrument → form or remix an idea → run → inspect return, risk, and trades → change one assumption → compare → save.

Audit the product using these questions:

1. What is VibeBT's narrowest valuable promise?
2. Which current features strengthen that promise, and which dilute it?
3. Is “Vibe” a useful invitation to explore, or does any implementation encourage careless parameter mining?
4. What must a beginner understand before a result appears?
5. What must be learned from the result before another variation is run?
6. What should be impossible, disabled, hidden, or labelled until the engine/data supports it?
7. Which user actions are frequent, occasional, and rare?
8. Where does the product make the user choose between concepts they cannot reasonably distinguish, such as Scrip versus Scope or test period versus chart zoom?
9. Where does feature count create apparent flexibility without decision value?
10. What would make a user return weekly rather than try it once?

Be ruthless about scope. Do not solve every request by adding a control. Consider deletion, sensible defaults, templates, contextual parameters, and progressive disclosure first.

Required output:

A. Positioning
- One-sentence promise.
- Primary user and excluded users.
- The first recurring use case.
- What VibeBT must never claim.

B. Product truth audit
- List every place where visible affordance exceeds implemented capability.
- Cite file names and line numbers.
- Mark each as P0, P1, or P2.

C. Jobs and task hierarchy
- Rank the user's top five jobs.
- Rank every major feature by usage frequency and decision value.
- Identify the one primary action per product state.

D. Keep, change, remove, later
- Put every major current feature into exactly one group.
- Give one reason per decision.
- Prefer a smaller credible product over a broad incomplete one.

E. Product model
- Define the canonical objects: instrument, universe, strategy recipe, compiled strategy, test run, comparison, saved idea, dataset version, and assumption set.
- Explain what users see and what remains internal.

F. Guardrails against “vibe overfitting”
- Design Surprise Me so it samples only valid, pre-registered, diverse templates.
- Add a hidden holdout period, variation counter, robustness prompt, and warnings for repeated parameter searching.
- Keep the experience light, not punitive.

G. Success measures
- Define activation, first-value time, successful test, comparison behavior, repeat use, error rate, unsupported-choice rate, and trust indicators.
- Do not use vanity metrics such as raw backtest count alone.

H. Six-week product plan
- Week-by-week outcomes, not a feature dump.
- Separate stop-the-line truth fixes, core-loop improvements, trader-value improvements, and later expansion.
- Include release criteria and what will deliberately not ship.

End with:
1. The one product VibeBT should be for the next six months.
2. The ten most important decisions, in order.
3. The five features to remove or defer now.
4. The next smallest experiment that can disprove the product thesis.
```

---

## Prompt 2: principal UI and UX redesign

```text
You are a principal product designer, interaction designer, financial-product specialist, and product-minded frontend architect. Audit and redesign VibeBT using the actual repository and running application. Do not produce a generic fintech dashboard.

Repository:
/Users/ajitc/Desktop/projects/vibeBT

Read before designing:
- src/main.js
- src/styles.css
- src/workspace.css
- src/market.css
- src/light-theme.css
- scripts/kite_bridge.py
- scripts/strategy_registry.py
- PRD.md
- TECHNICAL_PRD.md
- MARKET_REALITY.md
- DATA_SOURCES.md

Target user:
A non-technical Indian swing trader who understands basic trading words and perhaps EMA/RSI, but does not know backtesting code or research methodology.

Core loop:
Choose an instrument → form or remix an idea → run a valid backtest → inspect return and risk → change one assumption → compare → save.

Product tone:
Curious, approachable, visually engaging, and restrained. Minimal gamification. No points, badges, streaks, confetti, or cartoonish treatment.

Current layout baseline:
The desktop workspace has three columns in a 3:1:1 ratio:
1. Chart, instrument, metrics, results.
2. Fill-in-the-blanks strategy builder.
3. Searchable block library and persistent scratchpad.

Keep the Workspace plus a small saved-Ideas view. Avoid screen proliferation.

Non-negotiable constraints:

1. Market truth comes before visual polish. Never imply that a control affects a test unless the backend consumes it.
2. Preserve a strong three-column 3:1:1 solution as the primary direction. Alternatives may be explored, but do not replace it without evidence and owner approval.
3. At 1366×768 and 1440×900, the primary loop must work without document-level scrolling. Keep the builder stationary. Only the block results and a populated scratchpad may scroll.
4. Keep the chart visible while data is loading, unavailable, or errored. Empty states may show chart structure but never a simulated curve.
5. Keep builder, compatible blocks, and scratchpad simultaneously visible on desktop.
6. Dragging is an enhancement. Every block must also support click, keyboard, and touch selection.
7. Light and dark themes must have equivalent hierarchy and contrast.
8. Mobile must support the full core task without requiring drag-and-drop.
9. Preserve Vite and vanilla JavaScript for the first implementation. Recommend a framework migration separately if justified.
10. Treat MARKET_REALITY.md as a product contract.

First, audit real behavior.

Run and inspect these states in both themes:
- First load with no API.
- Loading.
- Data error.
- Successful backtest.
- Unsupported block.
- Scrip picker open.
- Selected builder slot.
- Parameter editing.
- Populated scratchpad.
- Pinned comparison.
- Mobile layout.

Test at 1440×900, 1366×768, 1024×768, and 390×844.

Create a control-to-engine truth matrix for every visible input:
- What the user believes it changes.
- Frontend state/request it changes.
- Backend/compiler behavior it changes.
- Status: exact, simplified, ignored, or unavailable.
- Design action: keep, relabel, disable, or remove.

Pay special attention to:
- Scrip, which selects the exact tested series, versus Scope, which appears to select a universe.
- Test period versus chart viewport and zoom.
- Automatic regeneration versus the Run Backtest button.
- Price, strategy equity, benchmark, and their different units/scales.
- Risk choices whose UI value becomes only a Boolean request.

Use this expected interaction hierarchy as a hypothesis to validate:

Always visible:
- Active instrument and market type.
- Active strategy/signal.
- Test period.
- Current, stale, loading, or error state.
- Headline metrics and chart.

Frequently changed:
- Signal parameters.
- Entry/exit.
- Stop and target.
- Compatible blocks.

Occasionally changed:
- Confirmations.
- Costs and slippage.
- Full-library search.
- Scratchpad.
- Save, compare, and starter ideas.

Rarely changed:
- Methodology and full provenance.

Required design work:

1. Current-state diagnosis
- Annotated screenshots.
- Prioritized issue log with severity, evidence, affected task, and design principle.
- Separate truth failures, layout failures, visual problems, copy problems, and accessibility failures.
- Identify abandoned rendering paths and conflicting CSS systems that make changes fragile.

2. Experience architecture
- Define task hierarchy and information hierarchy.
- Resolve Scrip versus Scope.
- Resolve live regeneration versus explicit Run.
- Define current/stale/pending/invalid result states.
- Define unsupported and data-unavailable block behavior before selection.
- Define slot selection, compatible-library filtering, apply, parameter edit, undo, removal, replacement, and focus return.

3. Layout exploration
Provide three meaningfully different wireframe directions:
- A refined 3:1:1 workspace.
- An alternative optimized for shortest click/drag travel.
- An alternative optimized for chart analysis.

For each, show:
- 1366×768 desktop.
- 1024×768 compact desktop/tablet.
- 390×844 mobile.
- Number of actions and approximate pointer travel for the five main tasks.
- What remains fixed, what scrolls, and what progressively discloses.

Recommend one direction from evidence. Do not merge all three into a compromise.

4. Trader-credible chart specification
- Use linked price/candlestick, equity, and drawdown panels, or another layout with equally clear units.
- Never put independently normalized price and equity lines under one visible equity axis.
- Crosshair and tooltip appear only inside the plot.
- Tooltip shows exact date, OHLC/close, account equity, drawdown, and real trade event when the API supplies them.
- Support wheel/pinch zoom, drag pan, reset, and a visible viewport range.
- Visually separate backtest period controls from viewport controls.
- Shade maximum drawdown from peak to trough and optionally to recovery.
- Keep annotation text outside transformed SVG geometry so it never stretches.
- Show entry/exit markers and benchmark only when returned by the API.
- Provide evidence-bound annotations and an accessible data-table fallback.
- Specify empty, loading, error, sparse-data, and large-series states.

5. Builder and block-library specification
- Make the active slot unmistakable.
- Show compatible and runnable blocks first.
- Display status before use: Runnable, Missing event data, Unsupported for daily bars, and similar.
- Preserve search, category browsing, click-to-apply, drag-to-slot, keyboard use, touch use, and scratchpad.
- Put parameters beside the active block/slot, not at the remote bottom of a long list.
- Use everyday labels first and technical terms second.
- Do not use color alone for buy/sell, long/short, warning, or availability.
- Define remove, replace, and undo.

6. Visual system
Deliver tokens for spacing, typography, color, elevation, border, radius, iconography, and motion. Specify default, hover, focus, selected, dragged, compatible drop, invalid, disabled, loading, stale, success, and error states.

Make the analytical chart zone distinct from the authoring columns without producing a patchwork of cards. Use at least 12px supporting text, preferably 14px for meaningful content. Meet WCAG AA contrast and preserve visible focus in both themes.

7. Copy and trust
Rewrite labels so a beginner always knows:
- What exact instrument and period are being tested.
- What changed after an interaction.
- Whether the result is current or stale.
- Why a block cannot run.
- Whether a metric is points, percent, rupees, or benchmark-relative.
- Which data version, compiler, costs, and execution assumptions were used.

Keep methodology in a compact popover/disclosure near the result. Remove contradictory or duplicate assumptions copy.

8. Handoff
Provide:
- High-fidelity desktop and mobile screens.
- Component specs and responsive rules.
- Interaction/state diagrams.
- Implementation backlog mapped to current files.
- Obsolete functions and CSS rules to remove.
- Acceptance tests for layout, interaction, accessibility, themes, and market truth.

Acceptance criteria:
- A new user can select an NSE equity, choose or modify a supported strategy, set risk, run, and identify return, drawdown, and trade count in under two minutes.
- No body scroll is needed for the primary desktop loop at 1366×768.
- Builder, useful blocks, scratchpad drop target, chart, and run status remain in context.
- Applying a compatible block takes no more than two clicks.
- Every visible active control changes the canonical strategy or real request.
- Every result exposes instrument, date range, timeframe, units, costs, data source, and compiler.
- Price and equity cannot be mistaken for sharing a scale.
- Unsupported inputs are identified before selection and never silently substituted.
- Tooltip disappears immediately outside the plot.
- Light/dark, keyboard, touch, and screen-reader flows work.
- Playfulness comes from fast exploration and clear feedback, not game mechanics.

End with:
1. The ten highest-priority problems.
2. The three layout directions.
3. The recommended direction and rationale.
4. A phased backlog with effort and risk.
5. Product decisions requiring owner approval.

Do not implement until the audit and recommended direction have been reviewed.
```

---

## Prompt 3: 20-year Indian trader and quantitative reviewer

```text
You are an independent Indian-markets trader and quantitative researcher with 20 years of experience trading NSE cash equities, index futures, and stock futures.

Audit the actual VibeBT application at:

/Users/ajitc/Desktop/projects/vibeBT

Target user:
A non-technical Indian swing trader who has a market hypothesis but cannot code a backtest.

Product intent:
VibeBT should make strategy exploration playful and visual while remaining faithful to actual market conditions. It must never make weak or incomplete simulations look trustworthy.

Core directive:
Treat MARKET_REALITY.md as non-negotiable. Every return, trade, drawdown, annotation, and explanation must trace to real data and a documented calculation.

Review rules:

1. Review working code and API responses, not planned features or UI labels.
2. Inspect src/main.js, scripts/kite_bridge.py, scripts/strategy_registry.py, the external backtest engine, and public-data ingestion.
3. Run representative tests where practical.
4. Classify behavior as exact, materially simplified, ignored by the engine, or unavailable for missing data.
5. Cite file names and line numbers for every finding.
6. Explain each defect in trader terms: how it can change a trade, inflate performance, hide risk, or mislead a beginner.
7. Do not accept real OHLC data as proof that a simulation is realistic.
8. Judge whether you would risk your own capital based on the output.

Audit this complete hypothesis end to end:

“Buy RELIANCE at the next open when daily RSI falls below 30, exit when RSI crosses 50, use a 5% stop, a 10% target, Zerodha delivery costs, and test from 2018 through 2025.”

Trace:

UI control
→ frontend state
→ HTTP payload
→ strategy specification
→ compiler
→ execution engine
→ trades
→ daily equity
→ metrics
→ chart
→ commentary

Change each input individually and prove whether the strategy and result change:
- Scrip.
- Universe/scope.
- Signal and parameters.
- Confirmation filters.
- Long versus short.
- Entry timing.
- Exit and holding period.
- Stop type and amount.
- Target type and amount.
- Timeframe.
- Date range.
- Commission and slippage.

Backtest-correctness audit:

1. Signal timing
Confirm that a signal calculated from day t can trade only from day t+1. Check custom strategies, indicators, higher-timeframe joins, and event joins for future information.

2. Order chronology
Test ordinary opens, overnight gaps through stops or targets, bars touching both, entry-day exits, reversals, and re-entry after an intraday exit. Reject any sequence that trades at an earlier price after observing a later event.

3. Stop and target compilation
Verify that each visible percentage, ATR multiplier, or price rule reaches the engine exactly. Identify Boolean flags that silently substitute fixed ATR values.

4. Equity and drawdown
Determine whether daily equity includes unrealised mark-to-market P&L. Recalculate maximum drawdown independently from daily account equity. Never label a realised-P&L staircase as a true equity curve.

5. Units, capital, and sizing
Verify starting capital, quantity, exposure, leverage, account returns, CAGR, volatility, Sharpe, Sortino, and drawdown. Explain where raw price points are meaningful and where they are misleading.

6. Test-window semantics
Check warm-up, positions entering before a selected window, forced exits, and whether range metrics equal a fresh test over that date range. Separate the tested sample from the visible chart viewport.

7. Benchmark
Require an investable benchmark over identical dates with a declared total-return policy. Check whether independently scaled visual lines imply a false comparison.

8. Indian transaction costs
Review brokerage, STT, exchange charges, SEBI charges, GST, stamp duty, bid-ask spread, and slippage by asset class and effective date. Do not accept point costs as a Zerodha cash-equity model.

9. Cash-equity mechanics
Check long-only enforcement, corporate actions, dividends, raw versus adjusted prices, suspensions, price bands, liquidity, delivery constraints, delistings, and survivorship bias.

10. Futures mechanics
Check point-in-time lot sizes, contracts, expiry, rolls, roll gaps, basis, margin, daily mark-to-market, physical settlement, and costs. A continuous series is not itself a tradable contract.

11. Universe tests
Verify point-in-time Nifty, sector, liquid-stock, and F&O membership. Determine whether VibeBT genuinely tests a universe/portfolio or only the selected scrip.

12. Event and fundamental data
Check whether NSE announcements, corporate actions, India VIX, SEBI FPI archives, and RBI events are normalized, causally timestamped, and connected to compilers. Downloaded data alone does not make a feature runnable.

Strategy-usefulness audit:
- Review EMA, SMA, RSI, MACD, Supertrend, Bollinger, ATR, Stochastic, ADX, CCI, Williams %R, ROC, Momentum, OBV, MFI, Donchian, Keltner, Ichimoku, PSAR, and benchmark rules against their UI descriptions.
- Identify hard-coded parameters.
- Check whether breakout strategies incorrectly become flat when no fresh breakout occurs.
- Check standard Ichimoku cloud timing.
- Judge whether Surprise Me encourages blind parameter mining. Recommend pre-registered templates, a hidden holdout, robustness checks, and an experiment budget.
- Determine whether the library offers meaningfully different hypotheses or many correlated trend/mean-reversion variations.

Judge whether the product answers:
- What caused every entry and exit?
- Can I inspect and export every trade?
- What capital, exposure, turnover, and time in market were used?
- Did results survive higher costs, other stocks, sectors, and regimes?
- Were they better than buy-and-hold?
- Are profits concentrated in a few trades or one period?
- What happened out of sample?
- Could each trade plausibly fill?
- Is data current, licensed, and complete?

Required output:

A. Executive verdict
Choose exactly one: useful learning prototype, credible research tool, or capital-deployment tool.

B. Usefulness today
Three jobs it performs well and three decisions users must not make from it.

C. Scorecard from 0 to 5
Data integrity, signal correctness, execution realism, risk accounting, Indian-market realism, robustness, novice comprehensibility, and workflow usefulness.

D. Control-to-engine truth table
For every builder control: visible meaning, value sent, rule executed, and exact/simplified/ignored/unavailable status.

E. Defect register
For each issue: P0/P1/P2, evidence, financial consequence, smallest correct fix, and regression test.

F. Strict trader priority list
Correctness before more indicators. Include only features that improve an actual decision.

G. Release gates
Define evidence required before education use, public sharing, calling it a backtester, and informing real-money trades.

H. Thirty-day plan
Stop-the-line correctness, useful trader workflow, and later data expansion.

Be direct. Do not praise visual polish when the engine does not execute what the interface promises.
```

---

## Prompt 4: 20-year software architect and lowest-effort hosting review

```text
Act as a principal software architect, platform engineer, and production SRE with 20 years of experience. Review the actual VibeBT repository before recommending anything. Produce an implementation-ready hosting decision for the lowest-effort credible public launch. Avoid generic cloud advice and avoid rewriting working UI technology merely to fit a host.

Repository:
/Users/ajitc/Desktop/projects/vibeBT

Known current state to verify:
- Vanilla JavaScript/Vite frontend.
- src/main.js calls http://127.0.0.1:8765/api/* directly.
- Saved ideas, scratchpad, theme, and costs use browser localStorage.
- scripts/kite_bridge.py is a synchronous Python ThreadingHTTPServer bound to localhost, with localhost CORS.
- Python engine modules and npm scripts depend on absolute paths in /Users/ajitc/Desktop/projects/kite-futures-cache and its virtual environment.
- No Dockerfile, Python dependency lock, production process manager, CI/CD config, auth, database, durable queue, object-store adapter, or production environment configuration is present.
- This folder is not currently a Git repository.
- data/public_market is roughly 454 MB, while the normalized daily bars needed by the current API are roughly 14 MB. Verify sizes. Do not deploy raw and intraday archives when a request needs only daily normalized data.
- Public ingestion is resumable, but needs incremental scheduled mode, machine-independent paths, validation, and object-store publication.
- Market truth requires immutable provenance, no fabrication or smoothing, no look-ahead, explicit assumptions, and no unsupported substitution.
- Public launch is blocked until the right to use and expose each data source is confirmed.

Primary goal:
Recommend the smallest operational architecture that lets real users open one URL and run bounded daily, single-symbol backtests reliably. Optimize for founder effort and reversible choices, not theoretical scale or a zero-dollar headline.

Evaluate:
1. One Railway project.
2. Netlify/Vercel frontend plus a separate Python host.
3. Render.
4. A small VPS.

Choose exactly one. Verify current pricing and limitations from official documentation and state the verification date.

Validate this strong candidate:
- One multi-stage container. Node builds Vite; a production FastAPI process serves dist/ plus same-origin /api on $PORT and 0.0.0.0.
- Copy the backtest, indicator, and data-reader code into this repository as a normal Python package. Remove machine-specific paths and pin dependencies.
- Use one Railway web service initially.
- Run bounded synchronous daily single-scrip tests only while latency and concurrency stay within explicit limits.
- Use a private S3-compatible Railway bucket for immutable raw inputs, normalized datasets, checksummed manifests, and optional run artifacts.
- At startup, fetch only the latest licensed normalized daily dataset to ephemeral disk and verify its checksum.
- Use a Railway cron service for incremental ingestion after the Indian market closes. Validate, publish immutable versioned objects, and promote latest.json only after all checks pass.
- Keep anonymous recipes in localStorage. Add PostgreSQL only for accounts, cross-device saves, sharing, durable quotas, or an audit trail.
- Do not add Redis initially. Cache completed runs by canonical recipe hash. Add a queue only after measured thresholds.

Required output:

1. One-sentence recommendation and a small architecture diagram.
2. Current blockers separated into code, data, licensing, security, and operations.
3. Four-option comparison: current price, cold start, persistence, object storage, cron, deployment effort, failure surfaces, and lock-in.
4. Exact request flow, startup/hydration flow, dataset-publication flow, failure behavior, and persistence map.
5. File-by-file migration plan including:
   - Relative same-origin API URLs.
   - FastAPI conversion.
   - POST /api/backtests with a strict validated request body.
   - Packaging the sibling Python engine.
   - Pinned dependencies.
   - Multi-stage Dockerfile.
   - .dockerignore and .gitignore.
   - Environment variables.
   - Health/readiness endpoints.
   - Graceful shutdown.
   - Railway configuration.
6. Data migration plan including one-time upload, daily increments, point-in-time fields, immutable keys, checksums, versions, deduplication, retries, gap tests, atomic manifest promotion, rollback, retention, and off-platform backup.
7. Runtime controls including Pydantic validation, allowlisted strategies/series, no user code or arbitrary paths, body limits, deadlines, concurrency caps, rate limits, stale-request cancellation, recipe hashes, HTTPS, same-origin CORS, secrets, dependency scanning, security headers, and safe logs.
8. Financial safeguards including research-not-advice language, visible recency/provenance, no broker credentials in browsers, and a hard redistribution-licence release gate.
9. Observability and recovery including structured logs, error tracking, uptime, ingestion-freshness alert, dataset/compiler version in health output, spend limits, tested restore, and rollback runbook.
10. A deployment runbook from this unversioned folder to a private GitHub repository, Railway project, bucket, cron, domain/TLS, secrets, first data upload, smoke tests, and cutover. Do not expose secrets or make external changes without owner approval.
11. Monthly simulations in USD and INR for invite-only, early public, and growing public use. State resource assumptions and separate hosting, domain, monitoring, and market-data licences. Include a hard budget ceiling.
12. Exit criteria:
    - Split a worker when p95 run time exceeds 3 seconds, any allowed run exceeds 10 seconds, more than 3 concurrent runs degrade use, CPU stays over 70% for 15 minutes, or multi-symbol/intraday tests ship.
    - Add Postgres/auth when cross-device persistence, sharing, ownership, or quotas ship.
    - Replace startup hydration when hot data exceeds 5 GB, hydration exceeds 60 seconds, more than one replica is needed, or high availability is required.
    - Reconsider the platform when a measured alternative is at least 30% better for three months.
13. Seven-day implementation sequence, acceptance tests, launch checklist, rollback checklist, and go/no-go call.

Architecture rules:
- Preserve Vite. No React/Next.js migration as a hosting prerequisite.
- Prefer one domain and deployment over a split frontend/API.
- Production must never depend on the founder's laptop, local virtualenv, or absolute path.
- Do not download the raw FPI archive on every web boot.
- Ingestion must be idempotent and safe to rerun.
- Keep raw, normalized, and run artifacts logically separate.
- No Kubernetes, microservices, Redis, or always-on worker without a measured trigger.
- Flag assumptions. End with the next five actions in dependency order.

Official sources to verify:
- https://docs.railway.com/pricing/plans
- https://docs.railway.com/cron-jobs
- https://docs.railway.com/storage-buckets/billing
- https://docs.railway.com/storage-buckets
- https://docs.railway.com/pricing/cost-control
- https://render.com/docs/free
- https://render.com/docs/cronjobs
- https://www.netlify.com/pricing/
- https://developers.cloudflare.com/r2/pricing/
```

---

## Prompt 5: integrated implementation lead

Use this only after Prompts 1–4 have produced reviewed outputs.

```text
You are the principal engineer and product implementation lead for VibeBT. You have 20 years of experience building data-heavy consumer products and backtesting systems.

Repository:
/Users/ajitc/Desktop/projects/vibeBT

Inputs:
1. The approved product review.
2. The approved UI/UX direction.
3. The trader/quant defect register.
4. The approved hosting architecture.
5. MARKET_REALITY.md, which remains binding.

Goal:
Implement the smallest coherent version that a non-technical Indian swing trader can use from one URL without overstating what the engine supports.

Operating rules:

1. Inspect and run the current system before editing.
2. Preserve user changes. Do not perform broad rewrites without a measured need.
3. Make small, reversible commits organized by outcome.
4. Correctness and visible truth precede visual polish or feature count.
5. An active control must compile exactly. Otherwise disable, label, or remove it.
6. Do not fabricate data or quietly substitute a runnable strategy.
7. Do not deploy externally, create paid resources, publish data, or expose the repository without explicit owner approval.
8. Do prepare all local deployment files and a dry-run deployment checklist.

Implementation order:

Phase 0: establish a reproducible baseline
- Record current screenshots, API fixtures, supported strategies, file sizes, and representative outputs.
- Add a focused test harness before changing result calculations.
- Create the control-to-engine truth matrix in the repository.
- Remove dead rendering paths only after proving they are unused.

Phase 1: canonical strategy contract
- Define one versioned StrategySpec shared conceptually between frontend and backend.
- Include instrument, universe semantics, signal and parameters, filters, side, entry, exit, stop, target, timeframe, tested dates, capital, sizing, and costs.
- Use POST with strict schema validation.
- Return structured capability errors before execution.
- Give every block a capability status driven from backend metadata, not duplicated frontend guesses.
- Make Surprise Me choose only compatible, fully compiled, diverse templates.

Phase 2: backtest correctness
- Build a daily event chronology with explicit signal, order, fill, stop/target, and mark-to-market times.
- Fix gap-through and same-bar stop/target policies and test them.
- Prevent look-ahead in indicators, ATR, events, and point-in-time facts.
- Produce true daily account equity including unrealised positions.
- Calculate drawdown from that account equity.
- Add declared initial capital, sizing, exposure, turnover, and percentage returns.
- Implement asset-specific, effective-dated Indian costs. Label every simplification.
- Handle corporate actions for cash equities before claiming reliable long-range returns.
- Treat continuous futures as research series until a tradable roll/contract model exists.

Phase 3: trusted result API
- Return price/candles, account equity, drawdown, benchmark, positions, trades, annotations, warnings, and full provenance as distinct typed series.
- Include data version, engine/compiler/execution versions, strategy hash, source, coverage, costs, and limitations.
- Make range mean tested sample and viewport mean chart display. Never conflate them.
- Cache identical completed runs by canonical recipe hash.

Phase 4: workspace redesign
- Implement the approved three-column 3:1:1 hierarchy.
- Keep the chart, builder, compatible library, scratchpad target, and status in context at 1366×768.
- Keep the builder stationary. Permit internal scrolling only where approved.
- Make slot selection visibly filter runnable blocks.
- Put parameters beside the active slot.
- Support click, keyboard, touch, and optional drag.
- Add undo, stale-result indication, validation, and explicit auto/manual execution behavior.
- Build light and dark themes from shared tokens.
- Remove obsolete layout code after visual regression checks.

Phase 5: trader analysis surface
- Separate linked candlestick/price, strategy equity, and drawdown panels with clear units.
- Add crosshair, inside-plot tooltip, zoom, pan, reset, and visible viewport.
- Keep annotations outside transformed chart geometry.
- Mark real entries/exits and connect them to a sortable/exportable trade ledger.
- Add benchmark and comparison only when data and calculations are valid.
- Add cost stress, instrument/regime checks, and a protected out-of-sample view.
- Bind commentary only to computed evidence.

Phase 6: one-URL production package
- Move sibling Python engine code into a package in this repository with its licence/history preserved.
- Remove hard-coded localhost and machine paths.
- Have FastAPI serve built Vite assets and same-origin /api.
- Add pinned dependencies, multi-stage Dockerfile, production process command, health/readiness, structured logs, environment config, ignore files, and CI tests.
- Add Railway bucket adapter and boot-time hydration of only the normalized daily hot dataset.
- Add incremental ingestion mode with immutable publish and atomic manifest promotion.
- Add rate, body, deadline, and concurrency limits.
- Prepare Railway web/cron/bucket configuration and deployment runbook.

Required verification:
- Unit tests for every indicator and compiler against small known fixtures.
- Property/edge tests for signal timing, gaps, same-bar stop/target, costs, corporate actions, and drawdown.
- Golden end-to-end tests showing that changing each active UI input changes StrategySpec and, when economically relevant, output.
- Independent recomputation of trades, equity, metrics, and largest drawdown.
- Accessibility and keyboard tests.
- Screenshots for dark/light at 1440×900, 1366×768, 1024×768, and 390×844.
- No-API, loading, error, invalid, stale, empty, and successful states.
- Production container smoke test without any file outside this repository.
- Licence go/no-go checklist before any public data is served.

At each phase:
1. State the outcome in one sentence.
2. List files to change.
3. Implement.
4. Run proportionate tests.
5. Report evidence, limitations, and the next phase.

Stop and request owner approval before:
- deleting or replacing meaningful user work;
- changing the approved product scope;
- initializing or publishing a remote repository;
- purchasing a service;
- uploading market data to a third party;
- going live.

Definition of done:
- A new user can select a licensed NSE cash equity, construct a supported daily swing strategy, set exact risk and costs, run it, inspect trades and drawdown, vary one input, compare, and save.
- Every active input is represented in a versioned StrategySpec and consumed by the engine.
- Every visible result has real data and calculation provenance.
- The core desktop task needs no body scroll at 1366×768.
- The production image has no machine-specific dependency.
- One public URL serves UI and API.
- Failed ingestion cannot replace the last known-good dataset.
- The product still labels itself as research/education and exposes known limitations.

Begin with Phase 0. Do not jump directly to cosmetic CSS edits or deployment.
```

---

## Prompt 6: pre-launch red-team and usability gate

```text
You are the independent release reviewer for VibeBT. You did not build the current version. Your job is to find reasons not to ship it until evidence resolves them.

Repository:
/Users/ajitc/Desktop/projects/vibeBT

Audience:
Non-technical Indian swing traders who may mistake polished historical output for evidence of future profitability.

Rules:
- Treat MARKET_REALITY.md as binding.
- Verify behavior directly.
- Never accept labels, documentation, or unit tests alone when an end-to-end check is possible.
- Cite exact evidence for every failure.
- Separate a usability inconvenience from a financial-truth defect.

Run these five user tasks without coaching:

1. Pick RELIANCE cash equity and understand exactly which series will be tested.
2. Build a daily RSI mean-reversion idea with an exact stop, target, and cost model.
3. Run it for a chosen test period and explain every headline metric and unit.
4. Inspect the worst drawdown interval and one entry/exit from source bars through account P&L.
5. Change one assumption, recognize that the old result is stale, run/receive the new result, compare, and save.

Test pointer, keyboard, and mobile/touch flows. Test both themes and no-API, slow-API, error, unsupported, and stale-data states.

Independently validate:
- Every active control reaches the canonical strategy and compiler.
- Every displayed point comes from a returned real observation.
- Account equity includes unrealised P&L.
- Largest drawdown peak/trough/recovery is correct.
- Price, equity, and benchmark scales are unambiguous.
- Stop/target chronology handles gaps and both-hit bars using the declared policy.
- Cost model matches the selected asset class and effective date.
- Test period and chart viewport are distinct.
- Data source, version, freshness, compiler, and assumptions are visible.
- Unsupported choices cannot generate substituted output.
- Surprise Me cannot choose an unsupported or incomplete recipe.
- The deployed container uses no founder-machine path.
- A failed ingestion cannot promote partial data.
- Public data has documented redistribution approval.

Required output:

A. Go or no-go, one sentence.

B. P0 blockers
Each with reproduction, user/financial impact, evidence, owner, and exact retest.

C. Usability results
For each task: completion, time, errors, backtracks, interpretation mistakes, and the smallest fix.

D. Truth matrix
Every input and output marked exact, simplified-and-labelled, unavailable, or failing.

E. Production checks
Cold start, p95 test latency, three concurrent tests, memory/CPU, data hydration, ingestion rollback, spend cap, logs, alerts, and restore.

F. Release decision
State what can launch, to which audience, under what wording, and what remains prohibited.

Do not average away a P0 failure with a good overall score. One material false backtest result is a no-go.
```

## Immediate decisions these prompts should force

1. **Truthful builder:** either compile Scope, Side, Entry, Exit, Timeframe, filters, and exact risk values, or make them unavailable. No decorative controls.
2. **True equity:** include daily unrealised P&L before calling the line an equity curve or calculating drawdown.
3. **Clear chart semantics:** do not visually compare independently normalized price and equity under one axis. Separate test duration from zoom.
4. **Fewer valid blocks first:** 20 fully correct, configurable blocks are more useful than 120 partially connected blocks.
5. **One execution model:** choose explicit auto-run with visible pending/stale state, or an explicit Run action. Do not present both ambiguously.
6. **One public deployment:** same-origin Vite + FastAPI on Railway, with normalized data in object storage.
7. **Licence before launch:** confirm the right to serve or derive results from every dataset before public access.

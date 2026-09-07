# VibeBT Product Requirements Document

**Status:** Product definition  
**Product:** VibeBT  
**Version:** 1.0  
**Primary platform:** Responsive web application  
**Technical specification:** [Technical PRD](./TECHNICAL_PRD.md)  
**Market reality directive:** [MARKET_REALITY.md](./MARKET_REALITY.md)  

## 1. Executive summary

### Non-negotiable: reflect actual market conditions

VibeBT must never fabricate prices, results, chart paths, metrics, or commentary. Every visible market claim must be traceable to real data and documented calculations. When a requested idea cannot be tested faithfully, the product must say so rather than substituting a plausible-looking output.

VibeBT is a playful idea playground for people who have trading hunches but cannot code a backtest. It helps them discover, generate, customize, test, compare, and save trading ideas across market conditions and timeframes.

The core promise is:

> Turn “I wonder if…” into an understandable backtest in under two minutes.

VibeBT is not primarily a strategy marketplace, professional quant terminal, broker, or trading signal service. It is a low-pressure experimentation environment. The catalog supplies interesting starting points. The Workspace turns those starting points into precise, testable rules. Results teach the user what happened, what might be misleading, and what to try next.

The main product loop is:

**Discover → Remix → Backtest → Understand → Compare → Save/share → Discover again**

The first release should prioritize this loop over catalog scale, social features, AI chat, live trading, or broad asset coverage.

## 2. Product vision

Most backtesting products begin with a chart, a programming language, or a dense strategy form. That is backwards for VibeBT's audience. Its users begin with curiosity:

- “Does buying after a big red day work?”
- “What happens to airline stocks when oil falls?”
- “Do profitable companies with strong momentum outperform?”
- “Should I buy before earnings and sell the next day?”

VibeBT should make those thoughts feel playable. A user should be able to roll a random idea, swap one ingredient, see how the result changes, and build intuition without first learning syntax or market jargon.

The intended feeling is closer to trying recipe variations than configuring institutional research software. The interface should feel light, curious, and approachable, but not like a game. Personality comes from clear language, idea names, and quick experimentation rather than points, rewards, or elaborate animation.

## 3. Target user

### Primary persona: the curious market explorer

**Profile**

- Has little or no coding experience.
- Understands basic actions such as buy, sell, profit, loss, price change, and perhaps indicators like moving averages or RSI.
- Has watched markets, invested personally, or tried discretionary trading.
- Has ideas but cannot translate them into unambiguous rules.
- Is likely intimidated by professional backtesting tools and skeptical of opaque “AI trading” claims.
- Wants quick feedback, visual explanations, and freedom to experiment.

**Core jobs to be done**

1. When I have a trading hunch, help me turn it into rules I can test.
2. When I do not have an idea, give me interesting and varied starting points.
3. When I get a result, tell me what it means in plain English.
4. When a strategy looks promising, help me test whether it is robust or merely lucky.
5. When I change one part of an idea, show me whether the change helped.

**Example user**

Maya is 29, owns a few stocks and ETFs, and follows finance creators. She understands “buy when the market is oversold” but does not know how to define oversold, retrieve historical data, or avoid look-ahead bias. She wants to explore without risking money and learn through doing.

### Secondary persona: the idea curator

A finance educator, newsletter writer, or experienced trader who wants to publish understandable idea templates. This persona improves catalog quality but should not dictate the initial interface.

### Explicit non-targets for the first release

- Professional quants who need code, custom datasets, tick data, or portfolio optimizers.
- High-frequency and execution-sensitive traders.
- Users seeking automatic trade execution or guaranteed signals.
- Creators selling opaque strategies.

## 4. User problem

Existing tools usually fail this audience in one of four ways:

1. **Blank-canvas problem:** users are asked to specify every rule before they know what is possible.
2. **Translation problem:** natural ideas must be converted into technical expressions or code.
3. **Interpretation problem:** a green equity curve is shown without explaining risk, sample size, or benchmark performance.
4. **Trust problem:** users can accidentally create impossible tests through future data, survivorship bias, missing costs, or excessive tuning.

VibeBT solves these by providing structured inspiration, sentence-like strategy construction, guided variation, plain-language results, and automatic research guardrails.

## 5. Product principles

### 5.1 Start with a spark, never a blank page

Every entry point should offer a usable idea. Randomization should be constrained enough to produce coherent tests, not absurd combinations.

### 5.2 Make the idea readable as a sentence

The strategy definition is the source of truth. A user should be able to read it aloud:

> “When a Nifty 50 stock falls more than 5% in one day and RSI is below 30, buy at the next open, hold for five trading days, then exit.”

### 5.3 One meaningful choice at a time

Default to a simple view with progressive disclosure. Advanced controls appear only when requested or when a result requires them.

### 5.4 Make change visible

When a user adjusts an ingredient, compare the new result with the prior run and explain the difference.

### 5.5 Light personality, minimal gamification

Playfulness should come from the **Surprise me** action, friendly idea names, and the pleasure of changing a rule and immediately seeing the result. Do not use points, badges, streaks, confetti, levels, or reward systems.

### 5.6 Teach at the point of need

Explain unfamiliar terms beside the decision or metric, in one sentence first, with deeper detail optional.

### 5.7 Safe defaults are part of the product

Include costs, use next-bar execution, show benchmarks, disclose data coverage, and flag low sample sizes by default.

## 6. Product strategy and priorities

### Priority 1: the Vibe backtesting loop

This is the reason to return. The product must make it fast and enjoyable to form, run, inspect, and modify an idea.

Required outcome: a new user completes a valid backtest and understands its headline result without documentation.

### Priority 2: idea ingredients and guided variation

Breadth should come from recombinable ingredients rather than thousands of static strategy pages. A smaller, well-tagged primitive library can produce technical, fundamental, and event-driven ideas while keeping the builder coherent.

### Priority 3: trustworthy interpretation

The result area should resist the common error “highest return equals best strategy.” Risk, consistency, benchmark performance, sample size, costs, and robustness must be visible.

### Priority 4: catalog and personal collection

The public catalog makes ideas discoverable. Personal saves, history, variants, and comparisons turn casual use into an ongoing practice.

### Later priorities

Community publishing, creator profiles, collaboration, AI-assisted parsing, live/paper trading, and premium data should follow evidence that users repeatedly complete the core loop.

## 7. Information architecture

VibeBT should have only two primary screens:

1. **Workspace:** the default screen. It contains idea discovery, the editable strategy sentence, backtest controls, results, and comparison. The interface changes in place instead of sending the user through a multi-screen flow.
2. **Library:** saved ideas and recent runs. Selecting an item returns it to the Workspace.

Account settings, methodology, and glossary content live in drawers or lightweight overlays. There is no separate Learn area, idea detail page, results page, or comparison page in the MVP.

A persistent **Surprise me** action in the Workspace generates a valid starting idea.

## 8. The core experience

### 8.1 First-run journey

The first session should avoid account creation until the user tries a backtest.

1. The Workspace opens with three compact starting actions:
   - **Surprise me:** generates a coherent random idea.
   - **Start with a hunch:** opens a guided sentence builder.
   - **Browse ideas:** opens the catalog drawer without leaving the Workspace.
2. The user chooses a broad interest, such as short-term moves, trends, company quality, or market events. “Anything” is the default.
3. VibeBT places the generated idea directly into the editable strategy sentence with a one-line hypothesis.
4. The test runs with safe defaults and a simple progress state.
5. Results expand below the builder on the same screen, beginning with a one-sentence verdict.
6. The user can change a rule or choose one of two practical suggestions, such as reduce risk or test another period.
7. Account creation is requested only when saving, comparing beyond the current session, or sharing.

Target time from landing to first result: **under two minutes**, with fewer than five required choices.

### 8.2 The Workspace builder

The main Workspace contains a visual sentence builder backed by structured rules. It has three layers.

#### Layer A: the idea sentence

The top of the screen always shows a readable, editable sentence composed of tappable chips:

> When **price drops 5% in a day** and **RSI is below 30**, buy **Nifty 50 stocks** at **next open**, hold for **5 days**, then sell.

Selecting a chip opens only the relevant alternatives. A user edits the idea without navigating a large form.

#### Visual fill-in composer

The sentence builder should also have a **Build with blocks** view. It is another way to edit the same strategy, not a separate screen or a second strategy system. Blocks are the default for first-time users; the plain-language sentence remains visible above them as a live summary. Experienced users may switch to direct sentence editing at any time, and both representations remain synchronized.

The Blocks view presents a small fill-in-the-blanks canvas:

> **WHEN** [ drop a signal ] [ + add another ]  
> **TRADE** [ choose market or stocks ] [ buy / short ]  
> **ENTER** [ choose timing ]  
> **EXIT** [ choose an exit ]  
> **TEST ON** [ timeframe ] [ date range ]

Required blanks have a solid outline and plain prompt. Optional blanks use a lighter outline. The **Run backtest** button becomes active when every required blank contains a valid block.

Below or beside the canvas is a compact block tray. Each block combines a simple icon, a basic word or phrase, and a short example:

- **Price ↓:** price falls.
- **Trend ↗:** price is trending up.
- **Speed:** price moves quickly or slowly.
- **Volume:** unusually high or low trading activity.
- **Company:** sales, profit, value, or financial quality.
- **Event:** earnings, dividends, or a calendar event.
- **Buy / Short:** direction of the simulated trade.
- **Hold / Target / Stop:** ways to exit.

Icons support recognition but never appear without words. Technical names such as RSI, moving average, or volatility are shown as optional detail after the everyday label.

##### Exact input behavior

1. **Choose a starting point.** The user selects **Surprise me**, loads a catalog idea, or begins with an empty canvas containing the five rows above.
2. **Place a block.** On desktop, the user drags a block into a compatible blank. On touch devices or with a keyboard, the user taps or selects a blank and then chooses a block from the filtered tray. Dragging is never the only input method.
3. **Set the value.** Dropping a block opens a small inline control for only the necessary value. For example, dropping **Price falls** asks for percentage and period, prefilled as “5%” and “1 day.” Controls use segmented choices, steppers, sliders with typed-value fields, or short searchable pickers.
4. **Read the result as a sentence.** The system immediately translates the canvas into plain language above it. Every change updates the sentence, readiness state, and estimated number of historical opportunities.
5. **Correct problems in place.** Incompatible blocks cannot be dropped. The target briefly explains why and suggests valid alternatives. Removing a block returns that row to a clearly labeled blank.
6. **See a live preview, then run and adjust.** The chart is the main Workspace view and regenerates after a valid rule change. The builder remains visible below it, so the user can change a block, run a full variation, and compare it with the pinned prior result without navigating away.

#### Persistent block explorer and scratchpad

The input stage keeps two secondary interactive areas visible beside the composer: a searchable, grouped block explorer and a scratchpad. The explorer exposes all supported Indian-market blocks without sending users to another screen. The scratchpad accepts dropped blocks for later, then lets users drag those saved blocks into a compatible blank. It is local to the current user and remains visible while they build and inspect the chart.

Example interaction:

1. Drag **Price falls** into **WHEN**, then accept “5% in 1 day.”
2. Drag **Nifty 50 stocks** into **TRADE** and keep **Buy** selected.
3. Choose **Next market open** for **ENTER**.
4. Drag **Hold** into **EXIT** and set it to “5 trading days.”
5. Choose **Daily** and “2014–2024” under **TEST ON**.
6. Read the generated rule sentence, then select **Run backtest**.

The app may preload sensible defaults so the user can run an idea after changing only one or two blocks. Advanced settings such as fees, slippage, position limits, and benchmark stay in a collapsed **Test assumptions** drawer.

On desktop, the block tray sits beside the canvas and results open below it. On mobile, the five rows stack vertically; tapping a blank opens a bottom sheet containing only compatible blocks. Mobile does not require dragging. The current rule sentence and **Run backtest** action remain sticky enough to stay in context without consuming most of the screen.

#### Layer B: ingredient tray

An expandable tray groups available ingredients:

- **Universe:** market, index members, sector, industry, market-cap range, individual symbols.
- **Setup:** trend, momentum, reversal, volatility, volume, valuation, growth, profitability, quality, analyst changes, earnings, dividends, economic events, calendar effects, or price gaps.
- **Confirmation:** optional second or third condition joined by AND/OR.
- **Entry:** next open, next close, limit-like approximation where data supports it.
- **Exit:** fixed bars, profit target, stop loss, trailing stop, opposite condition, or event-relative exit.
- **Position rules:** equal allocation, maximum concurrent positions, long/short direction where supported.
- **Timeframe:** intraday, daily, weekly, monthly, and event-relative presets, constrained by available data.
- **Test period and costs:** visible defaults with advanced editing.

Ingredients should use human names first and definitions second. For example, “Recently oversold” appears before “RSI below 30.”

#### Layer C: live test readiness

A compact panel shows:

- Whether the idea is testable.
- Estimated number of historical opportunities.
- Data availability and earliest valid date.
- Any conflicts or missing choices.
- The single next action needed.

The **Run backtest** button stays visible. Changes after a run switch the action to **Run this variation**.

### 8.3 Vibe randomizer

The randomizer is the signature playful mechanic. It should generate valid hypotheses, not select every field independently.

Users can lock any ingredient and reroll the rest. Example: lock “earnings events” and “technology stocks,” then reroll entry, filter, holding period, or direction.

The MVP has one **Surprise me** action. An optional menu lets users choose a broad family such as technical, fundamental, event-driven, or any. More modes add choice without improving the core task and should not ship initially.

Every generated idea includes:

- A short name.
- The exact rule sentence.
- A one-line hypothesis.
- Expected trade frequency.
- Relevant caveats before running.

Coherence rules should prevent combinations such as intraday exits on daily-only fundamental data, mutually exclusive conditions, or timeframes with inadequate history.

### 8.4 Idea detail and remix

Every catalog idea opens in a side drawer containing:

- Plain-language hypothesis.
- Exact testable rules.
- Ingredient tags.
- Suitable assets and timeframes.
- Default backtest with date, data version, assumptions, and benchmark.
- Result snapshot with a prominent **Load into Workspace** action.
- Creator or VibeBT attribution.
- Fork lineage: what this idea was remixed from.
- Risks and “what would disprove this?” prompt.

Catalog results are illustrative snapshots. Users should rerun them for chosen markets and dates rather than treating a published result as a signal.

### 8.5 Inline results experience

Results should answer questions in a fixed order.

#### 1. What happened?

A plain-language headline, for example:

> This idea beat buy-and-hold over the full test, but most of the advantage came from 2020 and the result varied widely by stock.

The summary must be generated from deterministic result rules before any optional generative explanation.

#### 2. Was it worth the risk?

Show five primary measures:

- Total or annualized return, chosen appropriately for the test length.
- Maximum drawdown.
- Win rate paired with average win and average loss.
- Number of trades.
- Performance relative to the benchmark.

Sharpe ratio, volatility, exposure, profit factor, and other metrics live under **More detail**.

#### 3. When did it work?

Show an equity curve against the benchmark, yearly or regime breakdown, drawdown periods, and a trade distribution. Let users inspect calm, volatile, rising, and falling market periods when enough data exists.

#### 4. Can I trust it?

Display a **Reality Check**, not a single misleading score. It contains:

- Sample size: low, usable, or broad.
- Costs included and cost sensitivity.
- In-sample versus holdout performance when available.
- Parameter sensitivity: whether nearby settings behave similarly.
- Concentration: dependence on a few trades, symbols, or periods.
- Data warnings and possible biases.

Warnings should be direct, such as “Only 14 trades. This is too little evidence for a confident conclusion.”

#### 5. What should I try next?

Offer three context-aware mutations:

- **Make it safer:** reduce concentration, add trend confirmation, or test a broader universe.
- **Try another tempo:** change the holding period or timeframe.
- **Challenge it:** run on a different period, sector, or unseen holdout window.

The product rewards completing robustness checks, not finding the largest return.

#### Chart inspection and annotated commentary

The return chart is the primary result view. Users can select **1Y, 3Y, 5Y, or All**, then zoom in or out without changing the strategy. Zoom changes only the visible history, never the calculation.

The chart should surface at most two concise callouts for the current view. Each callout uses a pointer anchored to a meaningful segment, then explains the market regime, trade concentration, drawdown, or benchmark divergence in plain English. A trader-style review below the chart should cover return quality, risk discipline, execution realism, and what evidence would change the conclusion.

Do not annotate every move. Callouts earn their space only when they materially affect interpretation.

### 8.6 Inline comparison

Users can pin the current result and compare it with one new variation in the same results area. The comparison highlights only changed ingredients and the resulting movement in return, drawdown, trade count, and benchmark edge. Multi-strategy comparison is deferred until there is evidence users need it.

The comparison should answer:

- What changed in the rules?
- Which result improved or worsened?
- Did risk rise to produce the improvement?
- Is the apparent improvement stable across periods?

A “mutation trail” preserves parent-child relationships instead of filling the account with disconnected copies.

### 8.7 Catalog

The catalog is organized around human questions rather than indicator names.

Suggested collections:

- Buy the dip?
- Follow the trend.
- Around earnings.
- Quality at a fair price.
- High-risk experiments.
- Five-minute ideas.
- Learn one concept.
- This week’s community remixes.

Filters include asset universe, timeframe, idea family, trade frequency, complexity, direction, and data availability. Do not default-sort by historical return. Default ranking should blend editorial quality, clarity, robustness, novelty, and engagement.

Catalog cards show the hypothesis and rule before performance. Performance cards display the test period and a visible “historical test, not a forecast” label.

## 9. Supporting different idea types

All ideas should compile into the same internal structure:

**Universe + trigger conditions + entry + exit + sizing + timeframe + assumptions**

### Technical ideas

Initial primitives:

- Price change over a period.
- Moving average level and crossover.
- Relative strength index.
- Breakout or new high/low.
- Gap up/down.
- Volume versus average.
- Volatility or range expansion.
- Relative strength versus benchmark.

### Fundamental ideas

Initial primitives, subject to point-in-time data licensing:

- Revenue or earnings growth.
- Profitability and margins.
- Valuation ratios.
- Debt and balance-sheet quality.
- Return on equity/capital.
- Fundamental change versus prior report.

Fundamental data must use the date it became publicly available, not the fiscal period end. If point-in-time data is unavailable, the feature must not ship with a misleading approximation.

### Event-driven ideas

Initial primitives:

- Earnings announcement.
- Dividend date.
- Large price or volume event.
- Index rebalance or inclusion, if reliable data exists.
- Scheduled macro releases for broad market instruments.
- Calendar events such as month-end or weekday.

Event strategies use relative timing phrasing: “two sessions before earnings” or “next open after the report.” Events with unreliable timestamps or historical coverage should be excluded.

### Combining families

The system should allow a fundamental or event trigger with technical confirmation. Example:

> After a positive earnings surprise, buy only when the stock opens above its 50-day average; exit after ten sessions.

Complexity should be capped in the simple builder: up to three entry conditions, one entry rule, and two exit rules. An advanced mode may expand this later.

## 10. Timeframe strategy

“Different timeframes” should be offered progressively, because each timeframe changes data cost, performance, complexity, and realism.

### MVP

- **Daily bars:** primary experience, strongest balance of speed, breadth, and understandable assumptions.
- **Weekly and monthly:** derived from daily data and offered as simple presets.
- **Event-relative daily tests:** before/after earnings and other supported events.
- Initial assets: liquid NSE equities, Nifty index universes, and major Indian ETFs, with a clear supported-universe definition.

### Next

- **Hourly bars:** selected liquid equities and ETFs.
- More markets and asset classes based on demand and licensed data.

### Later

- **5/15/30-minute bars:** only after realistic spreads, session rules, corporate actions, timestamps, and compute limits are established.
- Crypto or FX as separate market models, not superficial additions to equity assumptions.

Tick-level and sub-minute backtesting are out of scope. They conflict with the beginner audience and require execution modeling the product is not designed to provide.

## 11. Minimal playful design

VibeBT should feel lively, not gamified. The product needs only three playful touches:

- **Surprise me:** generate a coherent idea with one click.
- **Lock and change:** preserve an ingredient while replacing another.
- **Light personality:** memorable idea names, warm copy, and subtle transitions.

Avoid points, badges, levels, streaks, daily rewards, challenges, leaderboards, casino visuals, cash sounds, confetti, mascots, paid rerolls, artificial scarcity, and urgent notifications. The backtest and the insight are the reward.

## 12. Functional requirements

### P0: required for initial launch

1. Browse curated idea cards and inspect them in a side drawer.
2. Generate coherent random ideas from supported ingredients.
3. Lock and reroll individual ingredients.
4. Build and edit an idea through synchronized Sentence and Blocks views.
5. Run daily/weekly/monthly and supported event-relative backtests.
6. Show benchmarked results, costs, risk, trade count, and key warnings.
7. Inspect equity curve, drawdowns, period breakdown, and trade list.
8. Compare the current result with one pinned variation inline.
9. Save ideas and retain run history after account creation.
10. Share a read-only idea/result link with calculation version and date.
11. Provide glossary tooltips and contextual explanations.
12. Clearly disclose historical-data limitations and non-advisory status.

### P1: after core retention is proven

1. Holdout testing and guided parameter sensitivity maps.
2. User-created catalog submissions with moderation.
3. Creator profiles, forks, likes, and collections.
4. Hourly timeframe support.
5. Natural-language idea input that resolves into visible structured rules.
6. Additional regions or asset classes.

### P2: later exploration

1. Collaborative idea rooms.
2. Paper portfolios and forward tests.
3. Alerts for newly completed bars, framed as experiment updates.
4. Export to code or notebook.
5. Broker integration, only after a separate compliance and safety review.

## 13. Backtesting requirements and research integrity

The engine and interface must enforce:

- Next-bar execution by default so a signal does not trade on information from the same completed bar.
- Split and dividend handling appropriate to each calculation.
- Delisted securities and historical index membership where the strategy claims a historical universe.
- Point-in-time fundamentals and events.
- Explicit market calendar, timezone, and session handling.
- Configurable commission and slippage assumptions, with non-zero defaults where appropriate.
- No overlapping trade ambiguity; the position policy must be explicit.
- Deterministic results for the same strategy, data version, and engine version.
- Cached runs keyed by normalized strategy definition and versioned assumptions.
- Visible test period, benchmark, exposure, and data coverage.

Each run should store a reproducible **backtest recipe**:

- Structured strategy definition.
- Universe definition and membership policy.
- Data snapshot/version.
- Engine version.
- Dates and timeframe.
- Costs and execution assumptions.
- Benchmark.
- Results and warnings.

### Guardrails against overfitting

- Warn after repeated optimization against the same period.
- Suggest a holdout period before declaring a variant “better.”
- Show nearby parameter results, not just the selected optimum.
- Flag results dominated by a small number of trades.
- Avoid a one-click optimizer in the initial product.
- Label every result as exploratory historical evidence, not a forecast.

## 14. Conceptual data model

- **Idea:** human-facing title, hypothesis, description, tags, attribution, and default strategy version.
- **Strategy version:** immutable structured rules and parent version.
- **Ingredient:** typed condition/action with valid parameter ranges and compatibility rules.
- **Backtest run:** strategy version, data/engine version, assumptions, status, metrics, warnings, and artifacts.
- **Collection:** curated or user-owned list of ideas.
- **User save:** relationship between user and idea/version with notes and privacy state.
- **Comparison:** selected runs and persisted comparison context.
- **Publication:** public snapshot, moderation state, and disclosure metadata.

Versions must be immutable once a result is shared. Editing creates a child version.

## 15. Trust, safety, and compliance posture

VibeBT should describe itself as an education and research product. It should not present personalized investment recommendations, guarantee performance, or disguise marketing as research.

Required product behaviors:

- Persistent but unobtrusive “historical simulation, not investment advice” context.
- Detailed methodology and assumptions available from every result.
- No “buy now” or “sell now” language in the core product.
- Public strategies require moderation, spam controls, and performance-period disclosure.
- User-entered ideas are private by default.
- Clear deletion and data export controls.
- Age and jurisdiction review before monetization or broker features.

Formal legal review is required before public launch and again before any alerts, subscriptions tied to performance, or execution integration.

## 16. Accessibility and usability

- Meet WCAG 2.2 AA for the core journey.
- Never encode profit/loss or status with color alone.
- Support keyboard navigation for all builder chips and dialogs.
- Give every drag-and-drop action an equivalent tap, click, and keyboard flow.
- Pair every block icon with a visible text label and accessible name.
- Provide reduced-motion behavior for rolls and result animations.
- Use plain language and define metrics in context.
- Keep charts paired with text summaries and accessible data views.
- Preserve an idea during sign-up or accidental navigation.
- Make mobile browsing and simple edits first-class; reserve dense comparisons for larger screens with a usable mobile fallback.

## 17. Success metrics

### North-star metric

**Weekly meaningful experiments:** unique users who run a valid backtest and then perform at least one learning action, such as comparing a variation, inspecting robustness, changing a rule, or saving a conclusion.

This measures learning engagement more accurately than raw runs, which can be inflated by rerolling.

### Activation

- Percentage of new visitors who complete a first backtest.
- Median time to first valid result, target under two minutes.
- Percentage who can correctly answer the result’s plain-language takeaway in usability tests.

### Engagement and retention

- Percentage of activated users who create a variation in the first session.
- Weekly return rate among activated users.
- Ideas saved or annotated after a robustness check.
- Catalog-to-remix conversion.

### Trust and quality

- Percentage of viewed results with assumptions opened.
- Percentage of promising results tested on a holdout or alternate period.
- Rate of runs with severe data warnings.
- User-reported confusing or irreproducible results.
- Backtest reproducibility and engine error rate.

### Guardrail metrics

- Do not optimize for number of runs, highest returns, or time spent alone.
- Monitor whether playful features increase reckless language, misunderstanding, or compulsive behavior.

## 18. Analytics events

Track the minimum events needed to understand the loop:

- `idea_viewed`
- `idea_rolled`, including mode and locked ingredients
- `ingredient_changed`
- `backtest_started`, `backtest_completed`, `backtest_failed`
- `result_section_opened`
- `warning_viewed`
- `variant_created`
- `comparison_created`
- `holdout_run`
- `idea_saved`
- `idea_shared`
- `catalog_filter_used`

Do not send raw personal notes or unpublished strategy text to general analytics systems.

## 19. MVP scope and release phases

### Phase 0: prototype and validation

Build a clickable prototype plus a narrow calculation proof of concept.

Validate:

- Can users explain the idea sentence correctly?
- Can they edit a condition without help?
- Do they understand the result headline and warnings?
- Does rerolling feel inspiring rather than arbitrary?
- Can they distinguish a promising test from a reliable strategy?

Use 8–12 moderated sessions with target users. Test three ideas: a simple technical rule, a technical-plus-fundamental rule, and an earnings event rule.

### Phase 1: private alpha

- Curated catalog of roughly 30 high-quality idea templates.
- 12–20 well-tested ingredients.
- Liquid NSE equities, Nifty index universes, and major Indian ETFs.
- Daily, weekly, monthly, and limited event-relative tests.
- Sentence builder, constrained randomizer, results, variants, compare, save, and share.
- Deterministic engine and versioned recipes.

The objective is quality of the loop, not ingredient count.

### Phase 2: public beta

- Stronger robustness tools.
- Catalog collections and search.
- Carefully moderated user publishing.
- Improved mobile experience and onboarding personalization.

### Phase 3: expansion

- Hourly data, more regions/assets, natural-language input, forward testing, and creator tooling, based on observed demand.

## 20. MVP acceptance criteria

The MVP is ready when:

1. A first-time non-technical user can generate or select an idea, understand its rules, and complete a backtest without assistance.
2. Every result is reproducible from its stored recipe.
3. Results include benchmark, risk, costs, sample size, and relevant data warnings.
4. Users can change one ingredient and clearly see its effect versus the prior run.
5. Technical, fundamental, and event-driven examples can all be represented by the same builder without exposing code.
6. Invalid combinations are prevented before execution.
7. Core flows meet accessibility requirements and work on mobile and desktop.
8. Usability testing shows that most target users do not mistake historical performance for a prediction.

## 21. Key product decisions

### Decision 1: backtesting is the product; the catalog is its ignition

Invest engineering and design effort first in the builder, results, comparison, and trust model. A large catalog without a satisfying remix loop becomes content browsing. A strong loop can create catalog depth through variants later.

### Decision 2: structured rules before free-form AI

Natural-language input is attractive but can hide ambiguity. The initial product should expose explicit, structured rules. Later, AI may propose a structure, but the user must confirm the visible sentence before running it.

### Decision 3: daily-first

Daily data supports more assets, longer histories, event and fundamental joins, faster calculations, clearer assumptions, and lower cost. Intraday should expand only when the model is trustworthy.

### Decision 4: keep playfulness functional

The only playful interactions should help users create or vary an idea. Do not add a reward layer around normal product use. “This does not hold up” remains a useful result without requiring points or celebration.

### Decision 5: no single magic score

A composite score would be easy to compare and easy to misunderstand. Use a compact evidence panel that keeps return, risk, sample, stability, and concentration distinct.

## 22. Risks and mitigations

### Users overfit through endless rerolls

Mitigation: track the experiment trail, warn about repeated tuning, provide holdouts, and avoid sorting variants by return alone.

### Random ideas feel nonsensical

Mitigation: use templates, compatibility rules, minimum sample estimates, curated parameter ranges, and hypothesis text. Randomize inside valid idea families.

### Beginner simplicity makes results inaccurate

Mitigation: simplify presentation, not calculation. Preserve rigorous execution, costs, timestamps, and versioning behind plain-language controls.

### Fundamental data introduces hidden future knowledge

Mitigation: require point-in-time availability dates. Delay the feature if reliable data is not available.

### Data and compute costs grow quickly

Mitigation: daily-first coverage, constrained universes, cached normalized recipes, queued runs, and explicit fair-use limits.

### Playful styling undermines trust

Mitigation: use a calm visual system and restrict playful elements to idea generation, naming, and subtle transitions. Use no reward systems, profit celebrations, or urgency.

### Public catalog becomes a performance-claim marketplace

Mitigation: moderation, standardized test assumptions, fixed disclosure cards, fork history, no return-first ranking, and report controls.

## 23. Open questions to resolve during discovery

1. Which initial market and data provider can support historical constituents, delistings, events, and point-in-time fundamentals within budget?
2. Should the alpha include short selling, given borrow availability and beginner comprehension?
3. What is the smallest ingredient set that still feels creatively broad?
4. Do users prefer choosing a market first or an idea family first?
5. What is the minimum visual personality needed to make experimentation feel inviting?
6. Which plain-language result summary best improves correct interpretation?
7. What limits on run frequency and universe size preserve a fast interactive feel?
8. Which catalog ideas should be editorially authored to demonstrate responsible use?

## 24. Recommended first design prototype

Prototype one primary **Workspace** and one supporting **Library** screen.

The Workspace has four vertically connected regions that update in place:

1. **Start bar:** Surprise me, start with a hunch, or browse ideas in a drawer.
2. **Builder:** synchronized Sentence and Blocks views, visual ingredient tray, timeframe, and Run backtest.
3. **Results:** verdict, five core measures, Reality Check, and two suggested next tests.
4. **Comparison:** an optional inline view of the current result against one pinned variation.

The Library contains saved ideas and recent runs. It should be a simple list, not a separate social or collection experience in the MVP.

Use these prototype ideas:

- **The Bounce:** after a liquid stock drops 5% in one session and RSI is below 30, buy next open and hold five sessions.
- **Quality in Motion:** among profitable large-cap stocks, buy when price crosses above its 50-day average and exit after 20 sessions.
- **Earnings Afterglow:** after a positive earnings surprise and gap up, buy next open and hold ten sessions.

Together they test the breadth of technical, fundamental, and event-driven construction while keeping the interface understandable.

## 25. One-sentence product test

If VibeBT is working, a beginner can say:

> “I had a hunch, turned it into clear rules, tested it, learned where it worked and failed, and found one useful next experiment.”

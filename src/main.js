import './styles.css';
import './release.css';

// In development Vite proxies this path; in production it should share the
// application origin with the API. An explicit URL remains available for a
// deliberately separate API deployment.
const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '');
const TEST_RANGES = ['1W', '1M', '3M', '6M', '1Y', '3Y', '5Y', 'All'];

const SIGNALS = [
  ['ma-cross-up', '╱', 'EMA crossover', 'Trend follows a moving-average cross', 'trend'],
  ['macd-up', '╱', 'MACD trend', 'Momentum turns with the trend', 'trend'],
  ['rsi-low', '◔', 'RSI pullback', 'Oversold price may mean-revert', 'reversion'],
  ['supertrend', '⌁', 'Supertrend', 'Volatility-adjusted trend', 'trend'],
  ['bollinger', '◯', 'Bollinger bounce', 'Price leaves its volatility band', 'reversion'],
  ['atr', '↕', 'ATR expansion', 'A large daily move may continue', 'breakout'],
  ['stochastic', '◔', 'Stochastic swing', 'Momentum reaches an extreme', 'reversion'],
  ['adx', '↗', 'ADX direction', 'Directional trend strength', 'trend'],
  ['cci', '⌁', 'CCI reversal', 'Price is far from its average', 'reversion'],
  ['williams-r', '◒', 'Williams %R', 'Range momentum reaches an extreme', 'reversion'],
  ['roc', '↗', 'Rate of change', 'Price momentum is positive or negative', 'momentum'],
  ['momentum', '→', 'Momentum', 'Price acceleration persists', 'momentum'],
  ['obv', '▥', 'On-balance volume', 'Volume pressure supports the move', 'volume'],
  ['mfi', '₹', 'Money flow index', 'Price and volume reach an extreme', 'reversion'],
  ['donchian', '□', 'Donchian breakout', 'Price leaves its prior range', 'breakout'],
  ['keltner', '║', 'Keltner breakout', 'Price exits its ATR envelope', 'breakout'],
  ['sma', '━', 'SMA crossover', 'Simple moving-average trend', 'trend'],
  ['ichimoku', '☁', 'Ichimoku Cloud', 'Trend and cloud alignment', 'trend'],
  ['psar', '·', 'Parabolic SAR', 'Trailing trend direction', 'trend'],
  ['benchmark', '●', 'Buy and hold', 'Always invested baseline', 'baseline'],
];

const FILTERS = [
  ['above_50_sma', '↗', 'Above 50-day average', 'Keep long signals above the average'],
  ['below_50_sma', '↘', 'Below 50-day average', 'Keep short signals below the average'],
  ['high_relative_volume', '▥', 'High relative volume', 'Require volume above its 20-day average'],
  ['rsi_above_55', '◕', 'RSI above 55', 'Require long momentum confirmation'],
  ['rsi_below_45', '◔', 'RSI below 45', 'Require short momentum confirmation'],
];

const STOPS = [
  ['none', '−', 'No stop'], ['percent:3', '⊘', '3% stop'], ['percent:5', '⊘', '5% stop'],
  ['percent:8', '⊘', '8% stop'], ['atr:1.5', '∿', '1.5 ATR stop'], ['atr:2', '∿', '2 ATR stop'],
];
const TARGETS = [
  ['none', '−', 'No target'], ['percent:5', '◎', '5% target'], ['percent:10', '◎', '10% target'],
  ['percent:15', '◎', '15% target'], ['risk_reward:2', '⚖', '2:1 target'], ['risk_reward:3', '⚖', '3:1 target'],
];
const EXITS = [
  ['signal', '⇄', 'Signal reverses'], ['hold:5', '◫', 'Hold 5 days'], ['hold:10', '◫', 'Hold 10 days'], ['hold:20', '◫', 'Hold 20 days'],
];

const clone = (value) => JSON.parse(JSON.stringify(value));
const defaultDraft = () => ({
  name: 'RSI Pullback',
  signal: 'rsi-low',
  side: 'long',
  filters: [],
  exit: { kind: 'signal', holdBars: 0 },
  stop: { kind: 'percent', value: 5 },
  target: { kind: 'percent', value: 10 },
  params: { emaFast: 20, emaSlow: 50, emaTrend: 200, macdFast: 12, macdSlow: 26, macdSignal: 9 },
  costs: { commissionBps: 5, slippageBps: 5 },
  capital: 100000,
  allocationPct: 100,
});

const persisted = (key, fallback) => {
  try { return JSON.parse(localStorage.getItem(key) || '') || fallback; } catch { return fallback; }
};

const state = {
  draft: normalizeDraft(persisted('vibebt-draft-v2', defaultDraft())),
  selectedSeries: 'RELIANCE_SPOT',
  marketType: 'equity',
  testRange: '1Y',
  activeSlot: 'signal',
  blockSearch: '',
  libraryTab: 'signals',
  series: [],
  templates: [],
  run: null,
  error: '',
  loading: false,
  stale: false,
  theme: localStorage.getItem('vibebt-theme') || 'dark',
  scratchpad: persisted('vibebt-scratchpad-v2', []),
  saved: persisted('vibebt-library-v2', []),
  scripOpen: false,
  scripQuery: '',
  savedOpen: false,
  methodologyOpen: false,
  toast: '',
  chart: { zoom: 1, pan: 1, dragging: null, tooltip: null },
};

function normalizeDraft(draft) {
  const base = defaultDraft();
  return {
    ...base, ...draft,
    filters: Array.isArray(draft?.filters) ? draft.filters.filter((x) => FILTERS.some(([id]) => id === x)).slice(0, 2) : [],
    exit: { ...base.exit, ...(draft?.exit || {}) },
    stop: { ...base.stop, ...(draft?.stop || {}) },
    target: { ...base.target, ...(draft?.target || {}) },
    params: { ...base.params, ...(draft?.params || {}) },
    costs: { ...base.costs, ...(draft?.costs || {}) },
  };
}

function signal(id) { return SIGNALS.find(([value]) => value === id) || SIGNALS[0]; }
function filter(id) { return FILTERS.find(([value]) => value === id); }
function selectedSeries() { return state.series.find((item) => item.key === state.selectedSeries); }
function isFutures() { return selectedSeries()?.instrumentType === 'futures'; }
function text(value) { return String(value ?? '—'); }
function rupees(value) { return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(Number(value || 0)); }
function date(value) { return String(value || '').slice(0, 10); }
function pct(value, digits = 1) { return `${Number(value || 0).toFixed(digits)}%`; }

function app() {
  document.documentElement.dataset.theme = state.theme;
  document.querySelector('#app').innerHTML = workspace();
  bind();
  if (!state.series.length && !state.loading) loadCatalog();
  if (!state.run && !state.loading && !state.error && !state.stale) queueRun(0);
}

function workspace() {
  return `<main class="app-shell">
    <header class="topbar">
      <button class="wordmark" data-action="reset" aria-label="Reset VibeBT workspace">VibeBT</button>
      <p class="product-line">Test a market hunch against daily history.</p>
      <div class="top-actions">
        ${state.run ? '<button class="top-button" data-action="export">Export</button>' : ''}
        <button class="top-button" data-action="open-saved">Saved <span>${state.saved.length}</span></button>
        ${window.matchMedia('(max-width: 520px)').matches ? '' : '<button class="top-button" data-action="methodology">Method</button>'}
        <button class="theme-button" data-action="theme" aria-label="Switch theme">${state.theme === 'dark' ? '☀' : '◐'}</button>
      </div>
    </header>
    <section class="workspace-grid">
      <section class="analysis-column">${analysisPane()}</section>
      <section class="builder-column">${builderPane()}</section>
      <aside class="blocks-column">${blocksPane()}</aside>
    </section>
    ${state.savedOpen ? savedDrawer() : ''}
    ${state.methodologyOpen ? methodologyDrawer() : ''}
    ${state.toast ? `<div class="toast" role="status">${state.toast}</div>` : ''}
  </main>`;
}

function analysisPane() {
  const run = state.run;
  const sourceIsStale = run?.source?.dataStatus === 'stale';
  const runState = state.loading ? 'loading' : state.error ? 'error' : state.stale || sourceIsStale ? 'stale' : 'ready';
  const runLabel = state.loading ? 'Updating test' : state.error ? 'Data unavailable' : state.stale ? 'Result is updating' : sourceIsStale ? `Data as of ${date(run.source.dataAsOf)} (${run.source.dataAgeDays}d old)` : 'Current result';
  return `<section class="analysis-head">
    <div class="instrument-controls">
      <div><span class="micro-label">Market</span><div class="market-toggle">${[['equity', 'Cash equity'], ['futures', 'F&O research'], ['index', 'Index']].map(([id, label]) => `<button class="${state.marketType === id ? 'active' : ''}" data-market="${id}">${label}</button>`).join('')}</div></div>
      <div class="scrip-control"><span class="micro-label">Scrip being tested</span>${scripPicker()}</div>
    </div>
    <div class="test-controls"><div><span class="micro-label">Test period</span><div class="test-tabs">${TEST_RANGES.map((range) => `<button class="${state.testRange === range ? 'active' : ''}" data-range="${range}">${range}</button>`).join('')}</div></div><div class="run-state ${runState}"><i></i>${runLabel}</div></div>
  </section>
  ${run ? results(run) : emptyAnalysis()}`;
}

function scripPicker() {
  const current = selectedSeries() || { label: 'Loading instruments', instrumentType: state.marketType };
  const choices = state.series.filter((item) => item.instrumentType === state.marketType && (`${item.label} ${item.key}`).toLowerCase().includes(state.scripQuery.toLowerCase())).slice(0, 80);
  return `<div class="scrip-picker"><button class="scrip-trigger" data-action="scrip"><span>⌕</span><strong>${escapeHtml(current.label)}</strong><small>${current.instrumentType === 'futures' ? 'Continuous futures' : current.instrumentType === 'index' ? 'Index spot' : 'NSE cash equity'}</small><b>⌄</b></button>${state.scripOpen ? `<div class="scrip-menu"><input data-scrip-query value="${escapeAttr(state.scripQuery)}" placeholder="Search NSE scrips" aria-label="Search scrips"/><div class="scrip-results">${choices.length ? choices.map((item) => `<button data-scrip="${escapeAttr(item.key)}"><strong>${escapeHtml(item.label)}</strong><small>${escapeHtml(item.kind)} · ${date(item.firstDate)} to ${date(item.lastDate)}</small></button>`).join('') : '<p>No cached daily series match.</p>'}</div></div>` : ''}</div>`;
}

function emptyAnalysis() {
  return `<section class="chart-stack empty-state"><div class="chart-toolbar"><div><h1>Market workspace</h1><p>${state.loading ? 'Reading actual cached daily observations.' : 'The chart stays in place while data connects.'}</p></div></div><div class="empty-chart"><svg viewBox="0 0 900 430" preserveAspectRatio="none" aria-hidden="true"><path d="M0 80H900M0 210H900M0 340H900"/></svg><div><strong>${state.loading ? 'Building the real test…' : 'Waiting for daily market data'}</strong><span role="alert">${state.error ? escapeHtml(state.error) : 'Start the daily-data service to load this workspace.'}</span>${state.error ? '<button data-action="retry" style="justify-self:center;border:1px solid var(--line-strong);background:var(--surface-2);color:var(--text);border-radius:6px;padding:6px 9px;font-size:10px">Try again</button>' : ''}</div></div></section>`;
}

function results(run) {
  const m = run.metrics;
  const cashMode = run.source.instrumentType !== 'futures';
  const returns = cashMode ? pct(m['Total return (%)']) : `${Number(m['Total points'] || 0).toFixed(1)} pts`;
  const moneyLabel = cashMode ? `₹${rupees(m['Net P&L'])}` : `${Number(m['Total points'] || 0).toFixed(1)} pts`;
  const drawdownValue = cashMode ? pct(m['Max drawdown (%)']) : `${Number(m['Max drawdown'] || 0).toFixed(1)} pts`;
  const drawdownDetail = cashMode ? `₹${rupees(m['Max drawdown'])} peak to trough` : 'Peak-to-trough research points';
  return `<section class="results-wrap">
    <div class="metrics-row">
      ${metricCard('Return', returns, cashMode ? `Net P&L ${moneyLabel}` : 'Continuous-futures research points', Number(m['Total return (%)'] || m['Total points']) >= 0 ? 'positive' : 'negative')}
      ${metricCard('Largest drawdown', drawdownValue, drawdownDetail, 'negative')}
      ${metricCard('Trades', text(m.Trades), `Win rate ${m['Win rate'] == null ? '—' : pct(m['Win rate'])}`, '')}
      ${metricCard('Time in market', pct(m['Time in market (%)']), `Profit factor ${m['Profit factor'] ?? '—'}`, '')}
    </div>
    <section class="chart-stack">${chartToolbar(run)}${marketChart(run)}${equityChart(run)}</section>
    <section class="analysis-notes">${commentary(run)}</section>
    <section class="trade-table">${trades(run)}</section>
    <p class="provenance"><span>●</span>${escapeHtml(run.source.label)} · ${date(run.source.firstDate)} to ${date(run.source.lastDate)} · ${run.source.rows} daily bars · ${run.source.strategy} · data as of ${date(run.source.dataAsOf)}${run.source.dataStatus === 'stale' ? `, ${run.source.dataAgeDays} days old` : ''} · ${run.source.execution}</p>
  </section>`;
}

function metricCard(label, value, detail, tone) { return `<article class="metric-card ${tone}"><span>${label}</span><strong>${value}</strong><small>${detail}</small></article>`; }

function chartToolbar(run) {
  return `<div class="chart-toolbar"><div><h1>${escapeHtml(run.source.label)} · ${run.source.timeframe}</h1><p>${run.source.unit === 'account value' ? 'Cash-equity account value, price and drawdown shown separately.' : 'Continuous-futures research points with contract-level assumptions pending.'}</p></div><div class="viewport-controls"><span>Viewport</span><button data-chart="out" aria-label="Zoom out">−</button><button data-chart="left" aria-label="Pan left">←</button><button data-chart="right" aria-label="Pan right">→</button><button data-chart="in" aria-label="Zoom in">+</button><button data-chart="reset">Reset</button></div></div>`;
}

function viewport(run) {
  const rows = run.bars;
  const count = Math.max(20, Math.round(rows.length / state.chart.zoom));
  const maxStart = Math.max(0, rows.length - count);
  const start = Math.round(maxStart * state.chart.pan);
  return { rows: rows.slice(start, start + count), start, count };
}

function linePoints(rows, getValue, width, height, padding = 12) {
  const values = rows.map(getValue).map(Number).filter(Number.isFinite);
  const min = Math.min(...values); const max = Math.max(...values);
  const range = Math.max(max - min, Math.abs(max) * .02, 1);
  const y = (value) => height - padding - ((value - min) / range) * (height - padding * 2);
  const x = (index) => padding + index / Math.max(rows.length - 1, 1) * (width - padding * 2);
  return { points: rows.map((row, index) => `${x(index).toFixed(2)},${y(Number(getValue(row))).toFixed(2)}`).join(' '), min, max, x, y };
}

function marketChart(run) {
  const view = viewport(run); const width = 920; const height = 228; const pad = 14;
  const highs = view.rows.map((r) => Number(r.high)); const lows = view.rows.map((r) => Number(r.low));
  const min = Math.min(...lows); const max = Math.max(...highs); const range = Math.max(max - min, 1);
  const x = (index) => pad + index / Math.max(view.rows.length - 1, 1) * (width - pad * 2);
  const y = (value) => height - pad - (Number(value) - min) / range * (height - pad * 2);
  const candleWidth = Math.max(1, Math.min(7, 600 / view.rows.length));
  return `<section class="chart-panel price-panel" data-chart-panel="price"><div class="panel-label"><span>Price</span><small>NSE daily OHLC</small></div><div class="svg-wrap"><svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" data-hover="price">${grid(width, height)}${view.rows.map((row, index) => { const up = Number(row.close) >= Number(row.open); const top = Math.min(y(row.open), y(row.close)); const body = Math.max(1, Math.abs(y(row.open) - y(row.close))); return `<g class="candle ${up ? 'up' : 'down'}"><line x1="${x(index)}" x2="${x(index)}" y1="${y(row.high)}" y2="${y(row.low)}"/><rect x="${x(index) - candleWidth / 2}" y="${top}" width="${candleWidth}" height="${body}"/></g>`; }).join('')}<line class="crosshair" data-crosshair x1="0" x2="0" y1="0" y2="${height}" visibility="hidden"/></svg><div class="chart-tooltip" data-tooltip hidden></div></div><div class="axis-labels"><span>${date(view.rows[0]?.date)}</span><span>${date(view.rows[view.rows.length - 1]?.date)}</span></div></section>`;
}

function equityChart(run) {
  const view = viewport(run); const width = 920; const height = 178;
  const cashMode = run.source.unit === 'account value';
  const { points, min, max, x, y } = linePoints(view.rows, (r) => r.equityPct ?? r.equity, width, height);
  const dd = run.drawdown;
  const peakOriginal = run.bars.findIndex((row) => row.date === dd.peakDate);
  const troughOriginal = run.bars.findIndex((row) => row.date === dd.troughDate);
  const peak = peakOriginal - view.start; const trough = troughOriginal - view.start;
  const highlight = peak >= 0 && trough >= 0 && peak < view.rows.length && trough < view.rows.length;
  const drawdownLabel = cashMode ? pct(dd.percent) : `${Number(dd.points || 0).toFixed(1)} pts`;
  const caption = highlight ? `Largest drawdown ${drawdownLabel} · ${date(dd.peakDate)} to ${date(dd.troughDate)}` : `Largest drawdown ${drawdownLabel} · outside this viewport`;
  const benchmark = run.benchmark.slice(view.start, view.start + view.count);
  const benchmarkLine = linePoints(benchmark, (r) => r.equityPct ?? r.equity, width, height).points;
  const suffix = cashMode ? '%' : ' pts';
  return `<section class="chart-panel equity-panel" data-chart-panel="equity"><div class="panel-label"><span>Account equity</span><small>${cashMode ? 'Return %' : 'Points'}</small></div><div class="drawdown-caption ${highlight ? '' : 'muted'}">${caption}</div><div class="svg-wrap"><svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" data-hover="equity">${grid(width, height)}${highlight ? `<rect class="drawdown-band" x="${Math.min(x(peak), x(trough))}" y="0" width="${Math.abs(x(trough) - x(peak))}" height="${height}"/>` : ''}<polyline class="benchmark-line" points="${benchmarkLine}"/><polyline class="equity-line" points="${points}"/><polyline class="drawdown-line" points="${highlight ? view.rows.slice(peak, trough + 1).map((row, index) => `${x(peak + index)},${y(row.equityPct ?? row.equity)}`).join(' ') : ''}"/><line class="crosshair" data-crosshair x1="0" x2="0" y1="0" y2="${height}" visibility="hidden"/></svg><div class="chart-tooltip" data-tooltip hidden></div></div><div class="axis-labels"><span>${min.toFixed(1)}${suffix}</span><span style="margin-left:auto">${max.toFixed(1)}${suffix}</span><span class="legend" style="margin-left:14px"><i></i> Strategy <b></b> Buy & hold</span></div></section>`;
}

function grid(width, height) { return `<path class="grid-lines" d="M0 ${height*.2}H${width}M0 ${height*.5}H${width}M0 ${height*.8}H${width}"/>`; }

function commentary(run) {
  const m = run.metrics; const dd = run.drawdown; const cashMode = run.source.unit === 'account value';
  const returnSentence = cashMode ? `${pct(m['Total return (%)'])} across the selected test period after the entered costs.` : `${Number(m['Total points'] || 0).toFixed(1)} continuous-futures points across the selected test period.`;
  const riskSentence = `The largest measured ${cashMode ? 'account decline was ' + pct(dd.percent) : 'point decline was ' + Number(dd.points || 0).toFixed(1) + ' points'} from ${date(dd.peakDate)} to ${date(dd.troughDate)}${dd.recoveryDate ? `, recovering by ${date(dd.recoveryDate)}` : ', with no recovery inside the tested sample'}.`;
  return `<article><strong>Result</strong><p>${returnSentence}</p></article><article><strong>Risk</strong><p>${riskSentence}</p></article><article><strong>Evidence</strong><p>${m.Trades || 0} completed trades and ${pct(m['Time in market (%)'])} time in market.</p></article><article><strong>Assumption</strong><p>${escapeHtml(run.source.warning)}</p></article>`;
}

function trades(run) {
  if (!run.trades.length) return `<section class="trades-empty"><strong>No completed trades in this sample.</strong><span>Try a supported signal, period, or confirmation.</span></section>`;
  return `<details class="trades-details"><summary>Inspect ${run.trades.length} completed trades <span>↓</span></summary><div class="table-wrap"><table><thead><tr><th>Entry</th><th>Exit</th><th>Side</th><th>Reason</th><th>Return</th><th>P&L</th></tr></thead><tbody>${run.trades.map((trade) => `<tr><td>${date(trade.entryTime)}</td><td>${date(trade.exitTime)}</td><td>${trade.direction}</td><td>${trade.exitReason}</td><td>${Number(trade.points).toFixed(2)} pts</td><td class="${trade.pnl >= 0 ? 'gain' : 'loss'}">${run.source.unit === 'account value' ? `₹${rupees(trade.pnl)}` : `${Number(trade.pnl).toFixed(1)} pts`}</td></tr>`).join('')}</tbody></table></div></details>`;
}

function builderPane() {
  const draft = state.draft; const sig = signal(draft.signal);
  return `<section class="builder-card">
    <div class="builder-heading"><div><input data-name value="${escapeAttr(draft.name)}" aria-label="Strategy name"/><p>Every active block below compiles into this daily test.</p></div><button class="icon-button" data-action="save" title="Save this idea">♡</button></div>
    <div class="builder-actions"><button data-action="surprise"><span>✦</span> Surprise me</button><button data-action="clear">Reset</button></div>
    <div class="recipe-card tone-when"><span class="recipe-label">WHEN</span>${whenSlot(draft, sig)}</div>
    <div class="recipe-card tone-confirm"><span class="recipe-label">CONFIRM</span><button class="recipe-slot ${state.activeSlot === 'filter' ? 'selected' : ''}" data-slot="filter"><i>${draft.filters.length ? '✓' : '+'}</i><span><strong>${draft.filters.length ? draft.filters.map((id) => filter(id)?.[2]).join(' + ') : 'Optional confirmation'}</strong><small>${draft.filters.length ? 'Only selected daily filters apply' : 'Add up to two supported filters'}</small></span><b>⌄</b></button></div>
    <div class="recipe-card tone-side"><span class="recipe-label">SIDE</span><div class="segmented">${[['long', 'Buy'], ['both', 'Long + short'], ['short', 'Short']].map(([id, label]) => `<button class="${draft.side === id ? 'active' : ''} ${id !== 'long' && !isFutures() ? 'disabled' : ''}" data-side="${id}" ${id !== 'long' && !isFutures() ? 'disabled title="Cash equities are long-only"' : ''}>${label}</button>`).join('')}</div></div>
    <div class="recipe-card tone-enter"><span class="recipe-label">ENTER</span><div class="fixed-rule"><strong>Next market open</strong><small>Signal is calculated from the prior daily close.</small></div></div>
    <div class="recipe-card tone-exit"><span class="recipe-label">EXIT</span><button class="recipe-slot ${state.activeSlot === 'exit' ? 'selected' : ''}" data-slot="exit"><i>⇄</i><span><strong>${exitLabel(draft.exit)}</strong><small>${draft.exit.kind === 'signal' ? 'Close or reverse at next open' : `${draft.exit.holdBars} daily bars maximum`}</small></span><b>⌄</b></button></div>
    <div class="protection-grid"><div class="recipe-card tone-stop"><span class="recipe-label">STOP</span>${riskSlot('stop', draft.stop, '⊘', 'Gap fills use the open')}</div><div class="recipe-card tone-target"><span class="recipe-label">TARGET</span>${riskSlot('target', draft.target, '◎', 'Stop wins an intraday tie')}</div></div>
    ${draft.signal === 'ma-cross-up' || draft.signal === 'sma' ? emaControls() : ''}
    <details class="cost-panel"><summary>Capital and costs <span>↓</span></summary><div><label>Starting capital <input data-number="capital" type="number" min="1000" step="1000" value="${draft.capital}"/></label><label>Capital per trade <input data-number="allocationPct" type="number" min="1" max="100" step="1" value="${draft.allocationPct}"/>%</label><label>Fees / side <input data-number="commissionBps" type="number" min="0" max="500" step="1" value="${draft.costs.commissionBps}"/> bps</label><label>Slippage / side <input data-number="slippageBps" type="number" min="0" max="500" step="1" value="${draft.costs.slippageBps}"/> bps</label></div></details>
    <div class="builder-footer"><span><i></i>${state.loading ? 'Updating from your changes…' : 'Auto-run on. Results use actual cached daily OHLCV.'}</span><button data-action="methodology">Test assumptions</button></div>
  </section>`;
}

function emaControls() { const p = state.draft.params; return `<div class="ema-controls"><span>EMA periods</span><div>${[[5,21,55],[9,21,55],[10,30,100],[20,50,200],[50,100,200]].map((values) => `<button data-ema="${values.join(',')}">${values.join(' / ')}</button>`).join('')}</div><label>Fast <input data-param="emaFast" type="number" min="2" max="250" value="${p.emaFast}"/></label><label>Slow <input data-param="emaSlow" type="number" min="3" max="400" value="${p.emaSlow}"/></label><label>Trend <input data-param="emaTrend" type="number" min="4" max="500" value="${p.emaTrend}"/></label></div>`; }
function whenSlot(draft, sig) { if (draft.signal !== 'macd-up') return `<button class="recipe-slot ${state.activeSlot === 'signal' ? 'selected' : ''}" data-slot="signal"><i>${sig[1]}</i><span><strong>${sig[2]}</strong><small>${sig[3]}</small></span><b>⌄</b></button>`; const p = draft.params; return `<div class="recipe-slot recipe-slot-editable ${state.activeSlot === 'signal' ? 'selected' : ''}"><button class="slot-select" data-slot="signal"><i>${sig[1]}</i><span><strong>${sig[2]}</strong><small>${sig[3]}</small></span><b>⌄</b></button><div class="inline-periods"><label>Fast <input data-param="macdFast" type="number" min="2" max="100" value="${p.macdFast}"/></label><label>Slow <input data-param="macdSlow" type="number" min="3" max="200" value="${p.macdSlow}"/></label><label>Signal <input data-param="macdSignal" type="number" min="2" max="100" value="${p.macdSignal}"/></label></div></div>`; }
function riskSlot(key, rule, icon, detail) { const unit = rule.kind === 'percent' ? '%' : rule.kind === 'atr' ? 'ATR' : ':1'; return `<div class="recipe-slot recipe-slot-editable ${state.activeSlot === key ? 'selected' : ''}"><button class="slot-select" data-slot="${key}"><i>${icon}</i><span><strong>${riskLabel(rule, key)}</strong><small>${detail}</small></span><b>⌄</b></button>${rule.kind !== 'none' ? `<label class="inline-risk"><span>Value</span><input data-risk-number="${key}" type="number" min="0.1" max="100" step="0.1" value="${rule.value}"/><em>${unit}</em></label>` : ''}</div>`; }
function exitLabel(exit) { return exit.kind === 'hold' ? `Hold ${exit.holdBars} days` : 'Signal reverses'; }
function riskLabel(rule, kind) { if (rule.kind === 'none') return `No ${kind}`; if (rule.kind === 'percent') return `${rule.value}% ${kind}`; if (rule.kind === 'atr') return `${rule.value} ATR ${kind}`; return `${rule.value}:1 reward target`; }

function blocksPane() {
  const title = { signal: 'Signals', filter: 'Confirmations', stop: 'Stop loss', target: 'Target', exit: 'Exit rule' }[state.activeSlot] || 'Signals';
  return `<section class="block-library"><div class="library-head"><div><span class="micro-label">Block library</span><h2>${title}</h2><p>Click or drag to apply.</p></div><span class="runnable-chip">Daily runnable</span></div><input class="search" data-search value="${state.blockSearch}" placeholder="Search a runnable block" aria-label="Search blocks"/><div class="library-tabs">${[['signals','Signals'],['filters','Filters'],['risk','Risk'],['exit','Exit']].map(([id,label]) => `<button class="${state.libraryTab === id ? 'active' : ''}" data-tab="${id}">${label}</button>`).join('')}</div><div class="blocks-list-wrap"><div class="blocks-list" data-blocks-list>${blockList()}</div><div class="blocks-scroll-hint" aria-hidden="true">More blocks below <span>↓</span></div></div></section>${scratchpad()}`;
}

function blockList() {
  const query = state.blockSearch.toLowerCase().trim();
  const matches = (items) => items.filter((item) => item.slice(1).join(' ').toLowerCase().includes(query));
  if (state.libraryTab === 'signals') return matches(SIGNALS).map(([id, icon, label, detail, family]) => blockButton('signal', id, icon, label, detail, family)).join('') || noBlocks();
  if (state.libraryTab === 'filters') return matches(FILTERS).map(([id, icon, label, detail]) => blockButton('filter', id, icon, label, detail, 'confirmation', state.draft.filters.includes(id))).join('') || noBlocks();
  if (state.libraryTab === 'risk') return `<p class="library-note">Select the matching slot in the builder, or apply directly here.</p><h3>Stops</h3>${matches(STOPS).map(([id, icon, label]) => blockButton('stop', id, icon, label, 'Exact daily stop rule', 'risk')).join('')}<h3>Targets</h3>${matches(TARGETS).map(([id, icon, label]) => blockButton('target', id, icon, label, 'Exact daily target rule', 'reward')).join('')}`;
  return matches(EXITS).map(([id, icon, label]) => blockButton('exit', id, icon, label, 'Exit rule sent to the engine', 'exit')).join('') || noBlocks();
}

function blockButton(group, id, icon, label, detail, tag, selected = false) { return `<div class="block-row block-${group} ${selected ? 'chosen' : ''}" draggable="true" data-drag="${group}:${id}"><button data-block="${group}:${id}"><i>${icon}</i><span><strong>${label}</strong><small>${detail}</small></span><em>${tag}</em></button><button class="stash-button" data-stash="${group}:${id}" aria-label="Keep ${label} in scratchpad">＋</button></div>`; }
function noBlocks() { return `<p class="no-blocks">No supported blocks match.</p>`; }

function scratchpad() {
  const items = state.scratchpad.filter((item) => typeof item?.group === 'string');
  return `<section class="scratchpad" data-scratchpad><div><span class="micro-label">Scratchpad</span><h2>Keep for later <b>${items.length}</b></h2></div><p>Blocks live here until you apply or remove them.</p><div class="scratch-list">${items.length ? items.map((item, index) => { const definition = findBlock(item.group, item.id); return definition ? `<div draggable="true" data-drag="${item.group}:${item.id}"><i>${definition[1]}</i><span>${definition[2]}</span><button data-remove-scratch="${index}">×</button></div>` : ''; }).join('') : '<span class="scratch-empty">Use ＋ in the library to save a block here.</span>'}</div></section>`;
}

function findBlock(group, id) { return ({ signal: SIGNALS, filter: FILTERS, stop: STOPS, target: TARGETS, exit: EXITS }[group] || []).find(([value]) => value === id); }
function unpackBlock(value) { const index = String(value).indexOf(':'); return index < 0 ? [value, ''] : [value.slice(0, index), value.slice(index + 1)]; }

function savedDrawer() { return `<div class="overlay" data-action="close-saved"></div><aside class="drawer"><div class="drawer-title"><div><span class="micro-label">Saved ideas</span><h2>Experiments worth revisiting</h2></div><button data-action="close-saved">×</button></div>${state.saved.length ? state.saved.map((item, index) => `<button class="saved-item" data-load="${index}"><strong>${escapeHtml(item.name)}</strong><span>${signal(item.signal)[2]} · ${exitLabel(item.exit)}</span><small>${item.filters.length ? item.filters.map((id) => filter(id)?.[2]).join(' + ') : 'No confirmations'}</small></button>`).join('') : '<p class="drawer-empty">Nothing saved yet. Save a clear idea from the builder.</p>'}</aside>`; }
function methodologyDrawer() { return `<div class="overlay" data-action="close-method"></div><aside class="drawer"><div class="drawer-title"><div><span class="micro-label">Test assumptions</span><h2>What the daily test means</h2></div><button data-action="close-method">×</button></div><article class="method-item"><strong>Signal and fill</strong><p>A daily rule observes the completed close and can first fill at the next day’s open.</p></article><article class="method-item"><strong>Stops and targets</strong><p>Open gaps fill at the open. If one daily bar touches both the stop and target, the stop fills first.</p></article><article class="method-item"><strong>Costs</strong><p>Your fees and slippage are applied on both sides as basis points of fill price.</p></article><article class="method-item"><strong>Scope</strong><p>Each run covers one selected daily series. Point-in-time universes and portfolio testing are separate future capabilities.</p></article><article class="method-item"><strong>Review</strong><p>Check corporate actions, liquidity, and robustness before acting on a result.</p></article></aside>`; }

function buildPayload() { const d = state.draft; return { series: state.selectedSeries, signal: d.signal, side: d.side, filters: d.filters, exit: d.exit, stop: d.stop, target: d.target, params: d.params, costs: d.costs, capital: d.capital, allocationPct: d.allocationPct, testRange: state.testRange }; }
function persistDraft() { localStorage.setItem('vibebt-draft-v2', JSON.stringify(state.draft)); }

let latestRequest = 0; let scheduled; let activeRequest;
function queueRun(delay = 350) { clearTimeout(scheduled); activeRequest?.abort(); state.stale = true; state.loading = delay === 0; const token = ++latestRequest; scheduled = setTimeout(() => runBacktest(token), delay); app(); }
async function runBacktest(token) {
  state.loading = true; state.error = ''; app();
  const controller = new AbortController(); activeRequest = controller;
  try {
    const response = await fetch(`${API_BASE}/api/backtest`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(buildPayload()), signal: controller.signal });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || 'Backtest request failed');
    if (token !== latestRequest) return;
    state.run = payload; state.stale = false; state.chart = { zoom: 1, pan: 1, dragging: null, tooltip: null };
  } catch (error) {
    if (error.name === 'AbortError') return;
    if (token !== latestRequest) return;
    state.error = `Daily data service unavailable: ${error.message}`;
  } finally { if (activeRequest === controller) activeRequest = null; if (token === latestRequest) { state.loading = false; app(); } }
}
async function loadCatalog() {
  state.loading = true; app();
  try {
    const [seriesResponse, templateResponse] = await Promise.all([fetch(`${API_BASE}/api/series`), fetch(`${API_BASE}/api/templates`)]);
    const series = await seriesResponse.json(); const templates = await templateResponse.json();
    if (!seriesResponse.ok) throw new Error(series.error || 'Could not read instruments');
    state.series = series.series || []; state.templates = templates.templates || [];
    const current = selectedSeries();
    if (!current) state.selectedSeries = state.series.find((item) => item.instrumentType === 'equity')?.key || state.series[0]?.key || state.selectedSeries;
  } catch (error) { state.error = `Daily data service unavailable: ${error.message}`; }
  finally { state.loading = false; app(); }
}

function applyBlock(group, id) {
  if (group === 'signal') { state.draft.signal = id; state.activeSlot = 'signal'; }
  if (group === 'filter') {
    const filters = new Set(state.draft.filters); filters.has(id) ? filters.delete(id) : filters.add(id);
    state.draft.filters = [...filters].slice(0, 2); state.activeSlot = 'filter';
  }
  if (group === 'stop' || group === 'target') { const [kind, raw] = id.split(':'); state.draft[group] = kind === 'none' ? { kind: 'none' } : { kind, value: Number(raw) }; state.activeSlot = group; }
  if (group === 'exit') { const [kind, raw] = id.split(':'); state.draft.exit = { kind, holdBars: kind === 'hold' ? Number(raw) : 0 }; state.activeSlot = 'exit'; }
  persistDraft(); queueRun();
}

function stash(group, id) { if (!state.scratchpad.some((item) => item.group === group && item.id === id)) state.scratchpad.push({ group, id }); localStorage.setItem('vibebt-scratchpad-v2', JSON.stringify(state.scratchpad)); toast('Saved to scratchpad.'); app(); }
function toast(message) { state.toast = message; clearTimeout(toast.timer); toast.timer = setTimeout(() => { state.toast = ''; app(); }, 2400); }

function bind() {
  document.querySelectorAll('[data-action]').forEach((el) => el.addEventListener('click', action));
  document.querySelectorAll('[data-market]').forEach((el) => el.addEventListener('click', () => { state.marketType = el.dataset.market; const next = state.series.find((item) => item.instrumentType === state.marketType); if (next) state.selectedSeries = next.key; state.scripOpen = false; queueRun(0); }));
  document.querySelectorAll('[data-range]').forEach((el) => el.addEventListener('click', () => { state.testRange = el.dataset.range; queueRun(0); }));
  document.querySelectorAll('[data-slot]').forEach((el) => el.addEventListener('click', () => { state.activeSlot = el.dataset.slot; state.libraryTab = slotTab(state.activeSlot); app(); }));
  document.querySelectorAll('[data-side]').forEach((el) => el.addEventListener('click', () => { state.draft.side = el.dataset.side; persistDraft(); queueRun(); }));
  document.querySelectorAll('[data-tab]').forEach((el) => el.addEventListener('click', () => { state.libraryTab = el.dataset.tab; app(); }));
  document.querySelectorAll('[data-block]').forEach((el) => el.addEventListener('click', () => { const [group, id] = unpackBlock(el.dataset.block); applyBlock(group, id); }));
  document.querySelectorAll('[data-stash]').forEach((el) => el.addEventListener('click', (event) => { event.stopPropagation(); const [group, id] = unpackBlock(el.dataset.stash); stash(group, id); }));
  document.querySelectorAll('[data-remove-scratch]').forEach((el) => el.addEventListener('click', () => { state.scratchpad.splice(Number(el.dataset.removeScratch), 1); localStorage.setItem('vibebt-scratchpad-v2', JSON.stringify(state.scratchpad)); app(); }));
  document.querySelectorAll('[data-drag]').forEach((el) => el.addEventListener('dragstart', (event) => event.dataTransfer.setData('text/plain', el.dataset.drag)));
  document.querySelectorAll('[data-slot]').forEach((el) => { el.addEventListener('dragover', (event) => { event.preventDefault(); el.classList.add('dragover'); }); el.addEventListener('dragleave', () => el.classList.remove('dragover')); el.addEventListener('drop', (event) => { event.preventDefault(); el.classList.remove('dragover'); const [group, id] = unpackBlock(event.dataTransfer.getData('text/plain')); const allowed = { signal: 'signal', filter: 'filter', stop: 'stop', target: 'target', exit: 'exit' }; if (allowed[el.dataset.slot] === group) applyBlock(group, id); }); });
  document.querySelectorAll('[data-scratchpad]').forEach((el) => { el.addEventListener('dragover', (event) => event.preventDefault()); el.addEventListener('drop', (event) => { event.preventDefault(); const [group, id] = unpackBlock(event.dataTransfer.getData('text/plain')); if (findBlock(group, id)) stash(group, id); }); });
  document.querySelectorAll('[data-search]').forEach((el) => el.addEventListener('input', () => { state.blockSearch = el.value; app(); preserveTextCaret('[data-search]'); }));
  document.querySelectorAll('[data-blocks-list]').forEach((el) => { const updateHint = () => el.parentElement.classList.toggle('at-end', el.scrollTop + el.clientHeight >= el.scrollHeight - 2); el.addEventListener('scroll', updateHint); requestAnimationFrame(updateHint); });
  document.querySelectorAll('[data-scrip-query]').forEach((el) => el.addEventListener('input', () => { state.scripQuery = el.value; app(); preserveTextCaret('[data-scrip-query]'); }));
  document.querySelectorAll('[data-scrip]').forEach((el) => el.addEventListener('click', () => { state.selectedSeries = el.dataset.scrip; state.scripOpen = false; state.scripQuery = ''; queueRun(0); }));
  document.querySelectorAll('[data-name]').forEach((el) => el.addEventListener('input', () => { state.draft.name = el.value; persistDraft(); }));
  document.querySelectorAll('[data-number]').forEach((el) => el.addEventListener('change', () => { const value = Number(el.value); if (!Number.isFinite(value)) return; if (['commissionBps', 'slippageBps'].includes(el.dataset.number)) state.draft.costs[el.dataset.number] = value; else state.draft[el.dataset.number] = value; persistDraft(); queueRun(); }));
  document.querySelectorAll('[data-param]').forEach((el) => el.addEventListener('change', () => { state.draft.params[el.dataset.param] = Number(el.value); persistDraft(); queueRun(); }));
  document.querySelectorAll('[data-ema]').forEach((el) => el.addEventListener('click', () => { const [emaFast, emaSlow, emaTrend] = el.dataset.ema.split(',').map(Number); state.draft.params = { ...state.draft.params, emaFast, emaSlow, emaTrend }; persistDraft(); queueRun(); }));
  document.querySelectorAll('[data-macd]').forEach((el) => el.addEventListener('click', () => { const [macdFast, macdSlow, macdSignal] = el.dataset.macd.split(',').map(Number); state.draft.params = { ...state.draft.params, macdFast, macdSlow, macdSignal }; persistDraft(); queueRun(); }));
  document.querySelectorAll('[data-risk-number]').forEach((el) => el.addEventListener('change', () => { const value = Number(el.value); if (!Number.isFinite(value) || value <= 0) return; state.draft[el.dataset.riskNumber] = { ...state.draft[el.dataset.riskNumber], value }; persistDraft(); queueRun(); }));
  document.querySelectorAll('[data-chart]').forEach((el) => el.addEventListener('click', () => chartAction(el.dataset.chart)));
  document.querySelectorAll('[data-hover]').forEach((el) => bindChartHover(el));
  document.querySelectorAll('[data-load]').forEach((el) => el.addEventListener('click', () => { state.draft = normalizeDraft(state.saved[Number(el.dataset.load)]); state.savedOpen = false; persistDraft(); queueRun(0); }));
  if (state.scripOpen) preserveTextCaret('[data-scrip-query]');
}

function preserveTextCaret(selector) {
  requestAnimationFrame(() => {
    const input = document.querySelector(selector);
    if (!input) return;
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
  });
}

function slotTab(slot) { return ({ signal: 'signals', filter: 'filters', stop: 'risk', target: 'risk', exit: 'exit' })[slot] || 'signals'; }
function chartAction(actionName) { if (actionName === 'in') state.chart.zoom = Math.min(5, Number((state.chart.zoom * 1.45).toFixed(2))); if (actionName === 'out') state.chart.zoom = Math.max(1, Number((state.chart.zoom / 1.45).toFixed(2))); if (actionName === 'left') state.chart.pan = Math.max(0, state.chart.pan - .18); if (actionName === 'right') state.chart.pan = Math.min(1, state.chart.pan + .18); if (actionName === 'reset') { state.chart.zoom = 1; state.chart.pan = 1; } app(); }
function bindChartHover(svg) {
  const panel = svg.closest('.chart-panel'); const tooltip = panel.querySelector('[data-tooltip]'); const crosshair = svg.querySelector('[data-crosshair]');
  const show = (event) => { const view = viewport(state.run); const rect = svg.getBoundingClientRect(); const x = event.clientX - rect.left; if (x < 0 || x > rect.width || event.clientY < rect.top || event.clientY > rect.bottom) return hide(); const index = Math.max(0, Math.min(view.rows.length - 1, Math.round(x / rect.width * (view.rows.length - 1)))); const row = view.rows[index]; const related = state.run.trades.filter((trade) => date(trade.entryTime) === date(row.date) || date(trade.exitTime) === date(row.date)); const drawdownText = row.drawdownPct == null ? `${Math.abs(Number(row.drawdown || 0)).toFixed(1)} pts` : pct(row.drawdownPct, 2); tooltip.hidden = false; tooltip.style.left = `${Math.max(4, Math.min(73, x / rect.width * 100))}%`; tooltip.innerHTML = `<strong>${date(row.date)}</strong><span>O ${row.open.toFixed(2)} · H ${row.high.toFixed(2)} · L ${row.low.toFixed(2)} · C ${row.close.toFixed(2)}</span><span>Equity ${row.equityPct == null ? `${Number(row.equity).toFixed(1)} pts` : pct(row.equityPct, 2)} · DD ${drawdownText}</span>${related.length ? `<em>${related.map((t) => `${t.direction} ${date(t.entryTime) === date(row.date) ? 'entry' : t.exitReason}`).join(' · ')}</em>` : ''}`; const viewX = x / rect.width * 920; crosshair.setAttribute('x1', viewX); crosshair.setAttribute('x2', viewX); crosshair.setAttribute('visibility', 'visible'); };
  const hide = () => { tooltip.hidden = true; crosshair.setAttribute('visibility', 'hidden'); };
  svg.addEventListener('pointermove', show); svg.addEventListener('pointerleave', hide); svg.addEventListener('pointerdown', (event) => { state.chart.dragging = { x: event.clientX, pan: state.chart.pan }; svg.setPointerCapture(event.pointerId); }); svg.addEventListener('pointerup', (event) => { state.chart.dragging = null; try { svg.releasePointerCapture(event.pointerId); } catch {} }); svg.addEventListener('wheel', (event) => { event.preventDefault(); state.chart.zoom = Math.max(1, Math.min(5, state.chart.zoom * (event.deltaY < 0 ? 1.18 : 1 / 1.18))); app(); }, { passive: false });
  svg.addEventListener('pointermove', (event) => { if (!state.chart.dragging) return; const shift = (state.chart.dragging.x - event.clientX) / svg.getBoundingClientRect().width; state.chart.pan = Math.max(0, Math.min(1, state.chart.dragging.pan + shift)); app(); });
}

function action(event) {
  const name = event.currentTarget.dataset.action;
  if (name === 'theme') { state.theme = state.theme === 'dark' ? 'light' : 'dark'; localStorage.setItem('vibebt-theme', state.theme); app(); }
  if (name === 'scrip') { state.scripOpen = !state.scripOpen; state.scripQuery = ''; app(); }
  if (name === 'save') { const exists = state.saved.some((item) => JSON.stringify(item) === JSON.stringify(state.draft)); if (!exists) { state.saved.unshift(clone(state.draft)); localStorage.setItem('vibebt-library-v2', JSON.stringify(state.saved)); } toast(exists ? 'This exact idea is already saved.' : 'Saved with its exact recipe.'); app(); }
  if (name === 'surprise') { const options = SIGNALS.filter(([id]) => id !== 'benchmark'); state.draft.signal = options[Math.floor(Math.random() * options.length)][0]; state.draft.filters = []; state.draft.stop = { kind: 'percent', value: [3,5,8][Math.floor(Math.random()*3)] }; state.draft.target = { kind: 'percent', value: [5,10,15][Math.floor(Math.random()*3)] }; state.draft.exit = { kind: 'signal', holdBars: 0 }; state.draft.name = `${signal(state.draft.signal)[2]} idea`; persistDraft(); toast('A fully supported daily recipe is updating.'); queueRun(0); }
  if (name === 'clear' || name === 'reset') { state.draft = defaultDraft(); persistDraft(); queueRun(0); }
  if (name === 'open-saved') { state.savedOpen = true; app(); }
  if (name === 'close-saved') { state.savedOpen = false; app(); }
  if (name === 'methodology') { state.methodologyOpen = true; app(); }
  if (name === 'close-method') { state.methodologyOpen = false; app(); }
  if (name === 'retry') { state.error = ''; loadCatalog(); queueRun(0); }
  if (name === 'export') { exportRun(); }
}

function exportRun() {
  if (!state.run) return;
  const artifact = { exportedAt: new Date().toISOString(), ideaName: state.draft.name, backtest: state.run };
  const blob = new Blob([JSON.stringify(artifact, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob); const anchor = document.createElement('a');
  anchor.href = url; anchor.download = `vibebt-${state.run.source.series.toLowerCase()}-${state.testRange.toLowerCase()}.json`;
  anchor.click(); URL.revokeObjectURL(url); toast('Run exported with its data and assumptions.');
}

function escapeHtml(value) { return String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;'); }
function escapeAttr(value) { return escapeHtml(value); }

app();

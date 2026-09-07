"""VibeBT's explicit daily-bar backtest adapter.

The supplied cache project remains the source of daily OHLCV and indicators.
This module owns the product-facing execution rules so that every visible
VibeBT control has a named, testable meaning. It deliberately supports only
daily, single-instrument strategies for now.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Recipe:
    strategy: str
    params: dict = field(default_factory=dict)
    side: str = "long"
    exit_rule: str = "signal"
    hold_bars: int = 0
    stop: dict = field(default_factory=lambda: {"kind": "none"})
    target: dict = field(default_factory=lambda: {"kind": "none"})
    filters: tuple[str, ...] = ()
    commission_bps: float = 5.0
    slippage_bps: float = 5.0
    capital: float = 100_000.0
    allocation_pct: float = 100.0
    instrument_type: str = "equity"


def _safe_number(value, default=0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if np.isfinite(number) else default


def _directional_signal(raw: pd.Series, side: str) -> pd.Series:
    raw = raw.fillna(0).astype(int)
    if side == "long":
        return raw.clip(lower=0)
    if side == "short":
        return raw.clip(upper=0)
    if side == "both":
        return raw
    raise ValueError("side must be long, short, or both")


def _apply_filters(data: pd.DataFrame, desired: pd.Series, filters: tuple[str, ...]) -> pd.Series:
    """Apply only filters whose values are known at the prior bar close."""
    result = desired.copy()
    for name in filters:
        if name == "above_50_sma":
            sma = data["close"].rolling(50).mean().shift(1)
            result = result.where(~((result > 0) & (data["close"].shift(1) <= sma)), 0)
        elif name == "below_50_sma":
            sma = data["close"].rolling(50).mean().shift(1)
            result = result.where(~((result < 0) & (data["close"].shift(1) >= sma)), 0)
        elif name == "high_relative_volume":
            average = data["volume"].rolling(20).mean().shift(1)
            result = result.where(data["volume"].shift(1) >= average, 0)
        elif name == "rsi_above_55":
            result = result.where(~((result > 0) & (data["rsi"].shift(1) < 55)), 0)
        elif name == "rsi_below_45":
            result = result.where(~((result < 0) & (data["rsi"].shift(1) > 45)), 0)
        else:
            raise ValueError(f"Unsupported daily confirmation: {name}")
    return result.fillna(0).astype(int)


def _risk_level(entry: float, direction: int, atr: float, rule: dict, is_stop: bool, stop_price: float | None = None) -> float | None:
    kind = str(rule.get("kind", "none"))
    value = _safe_number(rule.get("value"))
    if kind == "none":
        return None
    if kind == "percent":
        distance = entry * value / 100
    elif kind == "atr":
        distance = atr * value
    elif kind == "risk_reward" and not is_stop and stop_price is not None:
        distance = abs(entry - stop_price) * value
    else:
        raise ValueError(f"Unsupported {'stop' if is_stop else 'target'} rule: {kind}")
    if distance <= 0:
        return None
    if is_stop:
        return entry - distance if direction == 1 else entry + distance
    return entry + distance if direction == 1 else entry - distance


def _max_drawdown(equity: pd.Series) -> tuple[int, int, int | None, float]:
    peak_index = 0
    trough_index = 0
    worst = 0.0
    peak = float(equity.iloc[0])
    for index, value in enumerate(equity):
        value = float(value)
        if value > peak:
            peak = value
            peak_index = index
        drawdown = value / peak - 1 if peak else 0.0
        if drawdown < worst:
            worst = drawdown
            trough_index = index
            saved_peak = peak_index
    if worst == 0:
        return 0, 0, None, 0.0
    recovery = next((i for i in range(trough_index + 1, len(equity)) if float(equity.iloc[i]) >= float(equity.iloc[saved_peak])), None)
    return saved_peak, trough_index, recovery, worst


def _max_drawdown_points(equity: pd.Series) -> tuple[int, int, int | None, float]:
    peak_index = 0
    trough_index = 0
    peak = float(equity.iloc[0])
    worst = 0.0
    saved_peak = 0
    for index, value in enumerate(equity):
        value = float(value)
        if value > peak:
            peak = value
            peak_index = index
        loss = peak - value
        if loss > worst:
            worst = loss
            trough_index = index
            saved_peak = peak_index
    recovery = next((i for i in range(trough_index + 1, len(equity)) if float(equity.iloc[i]) >= float(equity.iloc[saved_peak])), None)
    return saved_peak, trough_index, recovery, worst


def run_daily_backtest(raw_bars: pd.DataFrame, recipe: Recipe, indicator_module, strategies: dict,
                       start_index: int = 1) -> dict:
    """Run a causal single-series simulation and return typed chart artifacts.

    Signals use completed bar t and are executed at t+1's open. Stops and
    targets are based on ATR known at t, and gap fills always occur at the open.
    When both intraday levels are touched, the stop wins the tie.
    """
    if recipe.instrument_type in {"equity", "index"} and recipe.side != "long":
        raise ValueError("Daily cash equities and indices are long-only in this version.")
    if recipe.instrument_type not in {"equity", "index", "futures"}:
        raise ValueError("Unsupported instrument type")
    if recipe.exit_rule not in {"signal", "hold"}:
        raise ValueError("Unsupported exit rule")
    if not 0 < recipe.allocation_pct <= 100:
        raise ValueError("Allocation must be greater than 0 and at most 100 percent.")
    if recipe.capital <= 0:
        raise ValueError("Starting capital must be positive.")
    if not 0 <= recipe.commission_bps <= 500 or not 0 <= recipe.slippage_bps <= 500:
        raise ValueError("Commission and slippage must be between 0 and 500 basis points.")

    data = indicator_module.add_all(raw_bars, recipe.params).reset_index(drop=True)
    if len(data) < 252:
        raise ValueError("At least 252 daily bars are required for this daily test.")
    try:
        signal_function = strategies[recipe.strategy]
    except KeyError as exc:
        raise ValueError(f"No exact compiler is registered for {recipe.strategy}.") from exc

    # A strategy observes the completed current bar. The resulting intent is
    # shifted one bar so its first possible fill is the next session's open.
    observed = signal_function(data, recipe.params).fillna(0).astype(int)
    desired = _directional_signal(observed, recipe.side).shift(1).fillna(0).astype(int)
    desired = _apply_filters(data, desired, recipe.filters)

    date = data["date"]
    open_ = data["open"].to_numpy(float)
    high = data["high"].to_numpy(float)
    low = data["low"].to_numpy(float)
    close = data["close"].to_numpy(float)
    atr = data["atr"].to_numpy(float)
    fee_rate = recipe.commission_bps / 10_000
    slip_rate = recipe.slippage_bps / 10_000
    cash_mode = recipe.instrument_type in {"equity", "index"}

    start_index = max(1, min(int(start_index), len(data) - 1))
    cash = recipe.capital if cash_mode else 0.0
    position = 0
    quantity = 0.0
    entry_price = 0.0
    entry_fee = 0.0
    entry_index = 0
    stop_price: float | None = None
    target_price: float | None = None
    trades: list[dict] = []
    rows: list[dict] = []
    benchmark_rows: list[dict] = []
    realised_points = 0.0

    first_fill = open_[start_index] * (1 + slip_rate)
    benchmark_quantity = recipe.capital / (first_fill * (1 + fee_rate)) if cash_mode else 1.0
    benchmark_cash = recipe.capital - benchmark_quantity * first_fill * (1 + fee_rate) if cash_mode else 0.0

    def current_equity(mark: float) -> float:
        if cash_mode:
            return cash + position * quantity * mark
        if position == 0:
            return realised_points
        return realised_points + (mark - entry_price) * position * quantity - entry_fee

    def open_position(i: int, direction: int) -> None:
        nonlocal cash, position, quantity, entry_price, entry_fee, entry_index, stop_price, target_price
        fill = open_[i] * (1 + direction * slip_rate)
        if cash_mode:
            deployable = max(0.0, cash * recipe.allocation_pct / 100)
            quantity = deployable / (fill * (1 + fee_rate))
            entry_fee = quantity * fill * fee_rate
            cash -= quantity * fill + entry_fee
        else:
            quantity = 1.0
            entry_fee = fill * fee_rate
        position = direction
        entry_price = fill
        entry_index = i
        known_atr = atr[i - 1] if i > 0 and np.isfinite(atr[i - 1]) else 0.0
        stop_price = _risk_level(fill, direction, known_atr, recipe.stop, True)
        target_price = _risk_level(fill, direction, known_atr, recipe.target, False, stop_price)

    def close_position(i: int, raw_price: float, reason: str) -> None:
        nonlocal cash, position, quantity, entry_price, entry_fee, stop_price, target_price, realised_points
        direction = position
        fill = raw_price * (1 - direction * slip_rate)
        exit_fee = quantity * fill * fee_rate if cash_mode else fill * fee_rate
        gross_pnl = (fill - entry_price) * direction * quantity
        net_pnl = gross_pnl - entry_fee - exit_fee
        per_unit_points = net_pnl / quantity if quantity else 0.0
        if cash_mode:
            cash += quantity * fill - exit_fee
        else:
            realised_points += net_pnl
        trades.append({
            "entryTime": date.iloc[entry_index].isoformat(),
            "exitTime": date.iloc[i].isoformat(),
            "direction": "LONG" if direction == 1 else "SHORT",
            "entry": round(entry_price, 4),
            "exit": round(fill, 4),
            "quantity": round(quantity, 6),
            "points": round(per_unit_points, 4),
            "pnl": round(net_pnl, 2),
            "barsHeld": i - entry_index,
            "exitReason": reason,
        })
        position = 0
        quantity = 0.0
        entry_price = 0.0
        entry_fee = 0.0
        stop_price = target_price = None

    for i in range(start_index, len(data)):
        wanted = int(desired.iloc[i])
        protected_exit = False

        # At the open, a prior-bar signal can close or reverse a position.
        if position and ((recipe.exit_rule == "signal" and wanted != position) or
                         (recipe.exit_rule == "hold" and recipe.hold_bars > 0 and i - entry_index >= recipe.hold_bars)):
            close_position(i, open_[i], "signal" if wanted != position else "time")

        # A gap through a protective level fills at the open. It cannot use the
        # nicer stop or target level once the market has opened beyond it.
        if position:
            gap_stop = (position == 1 and stop_price is not None and open_[i] <= stop_price) or (position == -1 and stop_price is not None and open_[i] >= stop_price)
            gap_target = (position == 1 and target_price is not None and open_[i] >= target_price) or (position == -1 and target_price is not None and open_[i] <= target_price)
            if gap_stop:
                close_position(i, open_[i], "stop gap")
                protected_exit = True
            elif gap_target:
                close_position(i, open_[i], "target gap")
                protected_exit = True

        # A reversal is a valid new order at the same open. A protective exit
        # during this bar is not: reopening would require time travel.
        prior_wanted = int(desired.iloc[i - 1])
        can_enter = wanted != 0 and not protected_exit
        if recipe.exit_rule == "hold":
            can_enter = can_enter and wanted != prior_wanted
        if position == 0 and can_enter:
            open_position(i, wanted)

        # Intraday protective checks happen only for a position still held
        # after the open. Stop wins if both levels are touched in one daily bar.
        if position:
            hit_stop = (position == 1 and stop_price is not None and low[i] <= stop_price) or (position == -1 and stop_price is not None and high[i] >= stop_price)
            hit_target = (position == 1 and target_price is not None and high[i] >= target_price) or (position == -1 and target_price is not None and low[i] <= target_price)
            if hit_stop:
                close_position(i, stop_price, "stop")
            elif hit_target:
                close_position(i, target_price, "target")

        equity_value = current_equity(close[i])
        benchmark_value = benchmark_cash + benchmark_quantity * close[i] if cash_mode else close[i] - first_fill
        rows.append({
            "date": date.iloc[i].isoformat(),
            "open": round(open_[i], 4),
            "high": round(high[i], 4),
            "low": round(low[i], 4),
            "close": round(close[i], 4),
            "volume": _safe_number(data["volume"].iloc[i]),
            "equity": round(equity_value, 4),
            "equityPct": round((equity_value / recipe.capital - 1) * 100, 4) if cash_mode else None,
            "position": position,
        })
        benchmark_rows.append({
            "date": date.iloc[i].isoformat(),
            "equity": round(benchmark_value, 4),
            "equityPct": round((benchmark_value / recipe.capital - 1) * 100, 4) if cash_mode else round(benchmark_value, 4),
        })

    if position:
        close_position(len(data) - 1, close[-1], "end of data")
        rows[-1]["equity"] = round(current_equity(close[-1]), 4)
        rows[-1]["equityPct"] = round((rows[-1]["equity"] / recipe.capital - 1) * 100, 4) if cash_mode else None
        rows[-1]["position"] = 0

    equity = pd.Series([row["equity"] for row in rows], dtype=float)
    peak_i, trough_i, recovery_i, max_dd = _max_drawdown(equity) if cash_mode else _max_drawdown_points(equity)
    for index, row in enumerate(rows):
        peak = float(equity.iloc[:index + 1].max())
        row["drawdownPct"] = round((float(row["equity"]) / peak - 1) * 100, 4) if cash_mode and peak else None
        row["drawdown"] = round(float(row["equity"]) - peak, 4)

    completed = pd.DataFrame(trades)
    trade_measure = "pnl" if cash_mode else "points"
    wins = completed[completed[trade_measure] > 0][trade_measure] if not completed.empty else pd.Series(dtype=float)
    losses = completed[completed[trade_measure] <= 0][trade_measure] if not completed.empty else pd.Series(dtype=float)
    final_equity = float(equity.iloc[-1])
    initial_equity = recipe.capital if cash_mode else 0.0
    profit_factor = None if losses.empty or abs(float(losses.sum())) < 1e-12 else float(wins.sum() / abs(losses.sum()))
    metrics = {
        "Starting capital": round(recipe.capital, 2) if cash_mode else None,
        "Ending equity": round(final_equity, 2),
        "Total return (%)": round((final_equity / recipe.capital - 1) * 100, 2) if cash_mode else None,
        "Net P&L": round(final_equity - initial_equity, 2) if cash_mode else None,
        "Total points": round(final_equity, 2) if not cash_mode else None,
        "Max drawdown (%)": round(max_dd * 100, 2) if cash_mode else None,
        "Max drawdown": round(abs(float(equity.iloc[trough_i]) - float(equity.iloc[peak_i])), 2),
        "Trades": int(len(trades)),
        "Win rate": round(len(wins) / len(trades) * 100, 1) if trades else None,
        "Profit factor": round(profit_factor, 2) if profit_factor is not None else None,
        "Time in market (%)": round(sum(1 for row in rows if row["position"]) / len(rows) * 100, 1),
    }
    drawdown = {
        "peakIndex": peak_i,
        "troughIndex": trough_i,
        "recoveryIndex": recovery_i,
        "peakDate": rows[peak_i]["date"],
        "troughDate": rows[trough_i]["date"],
        "recoveryDate": rows[recovery_i]["date"] if recovery_i is not None else None,
        "percent": round(max_dd * 100, 2) if cash_mode else None,
        "points": round(max_dd, 2) if not cash_mode else None,
    }
    return {
        "bars": rows,
        "benchmark": benchmark_rows,
        "trades": trades,
        "metrics": metrics,
        "drawdown": drawdown,
        "strategySignals": desired.tolist(),
        "data": data,
    }

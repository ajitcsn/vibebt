#!/usr/bin/env python3
"""Deterministic checks for execution rules that must never be guessed."""

from __future__ import annotations

import pandas as pd

from vibebt_backtester import Recipe, run_daily_backtest


class Indicators:
    @staticmethod
    def add_all(frame, params):
        result = frame.copy()
        result["atr"] = 5.0
        result["rsi"] = 50.0
        return result


def bars():
    dates = pd.date_range("2024-01-01", periods=252, freq="B")
    frame = pd.DataFrame({"date": dates, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1_000.0})
    # The first long signal is observed at bar 1. The earliest valid fill is
    # bar 2's open, and that bar touches both a 5% stop and 5% target.
    frame.loc[2, ["high", "low"]] = [106.0, 94.0]
    return frame


def test_next_open_and_stop_tie():
    frame = bars()

    def signal(data, params):
        values = pd.Series(0, index=data.index)
        values.iloc[1:] = 1
        return values

    recipe = Recipe(
        strategy="test", stop={"kind": "percent", "value": 5}, target={"kind": "percent", "value": 5},
        commission_bps=0, slippage_bps=0, capital=100_000, instrument_type="equity",
    )
    result = run_daily_backtest(frame, recipe, Indicators, {"test": signal}, start_index=1)
    first = result["trades"][0]
    assert first["entryTime"] == frame["date"].iloc[2].isoformat(), "signals must fill on the next daily open"
    assert first["exitTime"] == frame["date"].iloc[2].isoformat(), "the tie happens on the entry day"
    assert first["exitReason"] == "stop", "a daily stop/target tie must use the conservative stop fill"
    assert first["exit"] == 95.0, "the stop level, not the target, must be used"


def test_cash_short_rejected():
    recipe = Recipe(strategy="test", side="short", instrument_type="equity")
    try:
        run_daily_backtest(bars(), recipe, Indicators, {"test": lambda data, params: pd.Series(0, index=data.index)})
    except ValueError as exc:
        assert "long-only" in str(exc)
    else:
        raise AssertionError("Cash-equity shorting must not be silently simulated.")


def main():
    test_next_open_and_stop_tie()
    test_cash_short_rejected()
    print("PASS: next-open fills, conservative stop ties, and cash-side guardrails")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fast, repeatable checks for the VibeBT daily backtest contract."""

from __future__ import annotations

from kite_bridge import build_run


BASE = {
    "series": "RELIANCE_SPOT",
    "testRange": "1Y",
    "side": "long",
    "exit": {"kind": "signal"},
    "stop": {"kind": "none"},
    "target": {"kind": "none"},
    "filters": [],
    "params": {"emaFast": 20, "emaSlow": 50, "emaTrend": 200, "macdFast": 12, "macdSlow": 26, "macdSignal": 9},
    "costs": {"commissionBps": 5, "slippageBps": 5},
    "capital": 100_000,
    "allocationPct": 100,
}

SIGNALS = [
    "ma-cross-up", "macd-up", "rsi-low", "supertrend", "benchmark",
    "bollinger", "atr", "stochastic", "adx", "cci", "williams-r",
    "roc", "momentum", "obv", "mfi", "donchian", "keltner", "sma",
    "ichimoku", "psar",
]


def run(signal: str, **updates):
    payload = {**BASE, "signal": signal}
    payload.update(updates)
    return build_run(payload)


def main():
    for signal in SIGNALS:
        result = run(signal)
        assert result["source"]["strategySpec"]["signal"] == signal
        assert len(result["bars"]) == 252
        assert "equity" in result["bars"][0]
        assert "drawdownPct" in result["bars"][0]

    with_stop = run("rsi-low", stop={"kind": "percent", "value": 3})
    without_stop = run("rsi-low", stop={"kind": "none"})
    assert with_stop["source"]["strategySpec"]["stop"]["value"] == 3
    assert with_stop["metrics"] != without_stop["metrics"]

    held = run("rsi-low", exit={"kind": "hold", "holdBars": 5})
    assert held["source"]["strategySpec"]["exit"] == {"kind": "hold", "holdBars": 5}

    macd = run("macd-up", params={"emaFast": 20, "emaSlow": 50, "emaTrend": 200, "macdFast": 8, "macdSlow": 21, "macdSignal": 5})
    assert macd["source"]["strategySpec"]["params"]["macd_fast"] == 8
    assert macd["source"]["strategySpec"]["params"]["macd_slow"] == 21
    assert macd["source"]["strategySpec"]["params"]["macd_signal"] == 5

    try:
        run("rsi-low", side="short")
    except ValueError as exc:
        assert "long-only" in str(exc)
    else:
        raise AssertionError("Cash-equity short request must be rejected")

    print(f"PASS: {len(SIGNALS)} daily compilers, risk wiring, time exit, and equity-side guardrails")


if __name__ == "__main__":
    main()

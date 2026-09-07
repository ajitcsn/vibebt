"""Causal daily indicators owned by VibeBT, independent of any broker SDK."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _rsi(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / length, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / length, adjust=False).mean()
    return (100 - 100 / (1 + gain / loss.replace(0, np.nan))).fillna(50)


def _atr(frame: pd.DataFrame, length: int = 14) -> pd.Series:
    previous = frame["close"].shift()
    true_range = pd.concat([
        frame["high"] - frame["low"],
        (frame["high"] - previous).abs(),
        (frame["low"] - previous).abs(),
    ], axis=1).max(axis=1)
    return true_range.ewm(alpha=1 / length, adjust=False).mean()


def _supertrend(frame: pd.DataFrame, length: int = 10, multiplier: float = 3.0) -> tuple[pd.Series, pd.Series]:
    atr = _atr(frame, length)
    midpoint = (frame["high"] + frame["low"]) / 2
    upper, lower = midpoint + multiplier * atr, midpoint - multiplier * atr
    close = frame["close"].to_numpy(float)
    upper_values, lower_values = upper.to_numpy(copy=True), lower.to_numpy(copy=True)
    direction, line = np.ones(len(frame), dtype=int), np.full(len(frame), np.nan)
    for index in range(1, len(frame)):
        upper_values[index] = min(upper_values[index], upper_values[index - 1]) if close[index - 1] <= upper_values[index - 1] else upper_values[index]
        lower_values[index] = max(lower_values[index], lower_values[index - 1]) if close[index - 1] >= lower_values[index - 1] else lower_values[index]
        if close[index] > upper_values[index - 1]:
            direction[index] = 1
        elif close[index] < lower_values[index - 1]:
            direction[index] = -1
        else:
            direction[index] = direction[index - 1]
        line[index] = lower_values[index] if direction[index] == 1 else upper_values[index]
    return pd.Series(line, index=frame.index), pd.Series(direction, index=frame.index)


def add_all(frame: pd.DataFrame, params: dict | None = None) -> pd.DataFrame:
    """Attach the exact daily fields used by VibeBT's compilers."""
    defaults = {"ema_fast": 20, "ema_slow": 50, "ema_trend": 200, "rsi_len": 14, "atr_len": 14, "bb_len": 20, "bb_mult": 2.0, "st_len": 10, "st_mult": 3.0}
    if params:
        defaults.update(params)
    out = frame.copy().reset_index(drop=True)
    out["ema_fast"] = out["close"].ewm(span=defaults["ema_fast"], adjust=False).mean()
    out["ema_slow"] = out["close"].ewm(span=defaults["ema_slow"], adjust=False).mean()
    out["ema_trend"] = out["close"].ewm(span=defaults["ema_trend"], adjust=False).mean()
    out["rsi"] = _rsi(out["close"], defaults["rsi_len"])
    out["atr"] = _atr(out, defaults["atr_len"])
    out["bb_mid"] = out["close"].rolling(defaults["bb_len"]).mean()
    deviation = out["close"].rolling(defaults["bb_len"]).std()
    out["bb_low"] = out["bb_mid"] - defaults["bb_mult"] * deviation
    out["bb_high"] = out["bb_mid"] + defaults["bb_mult"] * deviation
    out["supertrend"], out["st_dir"] = _supertrend(out, defaults["st_len"], defaults["st_mult"])
    return out

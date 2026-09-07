"""Versioned, runnable daily strategy templates for VibeBT.

This registry is the backend authority for which UI signals can produce a real
run. A UI block that is absent here is intentionally not compiled.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class StrategyTemplate:
    id: str
    version: str
    signal: str
    engine_strategy: str
    title: str
    tags: tuple[str, ...]
    minimum_bars: int = 252
    requirements: tuple[str, ...] = ("daily_ohlcv",)


TEMPLATES = (
    StrategyTemplate("ema-trend-cross-v1", "1.0.0", "ma-cross-up", "EMA crossover (trend)", "EMA trend cross", ("trend", "daily")),
    StrategyTemplate("macd-trend-v1", "1.0.0", "macd-up", "MACD trend", "MACD trend", ("trend", "momentum", "daily")),
    StrategyTemplate("rsi-mean-reversion-v1", "1.0.0", "rsi-low", "RSI mean reversion", "RSI pullback", ("mean_reversion", "daily")),
    StrategyTemplate("supertrend-v1", "1.0.0", "supertrend", "Supertrend", "Supertrend", ("trend", "volatility", "daily")),
    StrategyTemplate("buy-hold-benchmark-v1", "1.0.0", "benchmark", "Buy & hold (benchmark)", "Buy and hold", ("benchmark", "daily")),
    StrategyTemplate("bollinger-reversion-v1", "1.0.0", "bollinger", "Bollinger mean reversion", "Bollinger Bands", ("mean_reversion", "volatility", "daily")),
    StrategyTemplate("atr-expansion-v1", "1.0.0", "atr", "ATR expansion", "ATR expansion", ("breakout", "volatility", "daily")),
    StrategyTemplate("stochastic-reversion-v1", "1.0.0", "stochastic", "Stochastic mean reversion", "Stochastic", ("mean_reversion", "daily")),
    StrategyTemplate("adx-trend-v1", "1.0.0", "adx", "ADX directional trend", "ADX trend", ("trend", "daily")),
    StrategyTemplate("cci-reversion-v1", "1.0.0", "cci", "CCI mean reversion", "CCI", ("mean_reversion", "daily")),
    StrategyTemplate("williams-r-reversion-v1", "1.0.0", "williams-r", "Williams %R mean reversion", "Williams %R", ("mean_reversion", "daily")),
    StrategyTemplate("roc-trend-v1", "1.0.0", "roc", "Rate of change trend", "Rate of change", ("momentum", "daily")),
    StrategyTemplate("momentum-trend-v1", "1.0.0", "momentum", "Momentum trend", "Momentum", ("momentum", "daily")),
    StrategyTemplate("obv-trend-v1", "1.0.0", "obv", "On-balance volume trend", "On-balance volume", ("volume", "trend", "daily")),
    StrategyTemplate("mfi-reversion-v1", "1.0.0", "mfi", "Money flow mean reversion", "Money flow index", ("volume", "mean_reversion", "daily")),
    StrategyTemplate("donchian-breakout-v1", "1.0.0", "donchian", "Donchian breakout", "Donchian Channels", ("breakout", "daily")),
    StrategyTemplate("keltner-breakout-v1", "1.0.0", "keltner", "Keltner breakout", "Keltner Channels", ("breakout", "volatility", "daily")),
    StrategyTemplate("sma-trend-cross-v1", "1.0.0", "sma", "SMA crossover (trend)", "Simple moving average", ("trend", "daily")),
    StrategyTemplate("ichimoku-trend-v1", "1.0.0", "ichimoku", "Ichimoku trend", "Ichimoku Cloud", ("trend", "daily")),
    StrategyTemplate("psar-trend-v1", "1.0.0", "psar", "Parabolic SAR trend", "Parabolic SAR", ("trend", "daily")),
)

BY_SIGNAL = {template.signal: template for template in TEMPLATES}


def resolve(signal: str) -> StrategyTemplate:
    try:
        return BY_SIGNAL[signal]
    except KeyError as exc:
        raise ValueError(
            f"'{signal}' does not yet have an exact local backtest compiler. "
            "VibeBT will not substitute a different strategy."
        ) from exc


def public_catalog() -> list[dict]:
    return [
        {
            "id": template.id,
            "version": template.version,
            "signal": template.signal,
            "title": template.title,
            "tags": template.tags,
            "minimumBars": template.minimum_bars,
            "requirements": template.requirements,
            "status": "runnable",
        }
        for template in TEMPLATES
    ]


def _stateful(entry: pd.Series, exit_rule: pd.Series, short_entry: pd.Series | None = None,
              short_exit: pd.Series | None = None) -> pd.Series:
    """Hold a signal until its documented exit, without future-bar access."""
    position = 0
    values = []
    short_entry = short_entry if short_entry is not None else pd.Series(False, index=entry.index)
    short_exit = short_exit if short_exit is not None else pd.Series(False, index=entry.index)
    for i in range(len(entry)):
        if position == 0:
            if bool(entry.iloc[i]):
                position = 1
            elif bool(short_entry.iloc[i]):
                position = -1
        elif position == 1 and bool(exit_rule.iloc[i]):
            position = 0
        elif position == -1 and bool(short_exit.iloc[i]):
            position = 0
        values.append(position)
    return pd.Series(values, index=entry.index)


def _stochastic(df: pd.DataFrame, length: int = 14) -> pd.Series:
    high = df["high"].rolling(length).max()
    low = df["low"].rolling(length).min()
    return 100 * (df["close"] - low) / (high - low).replace(0, np.nan)


def _cci(df: pd.DataFrame, length: int = 20) -> pd.Series:
    typical = (df["high"] + df["low"] + df["close"]) / 3
    mean = typical.rolling(length).mean()
    deviation = typical.rolling(length).apply(lambda values: np.mean(np.abs(values - values.mean())), raw=True)
    return (typical - mean) / (0.015 * deviation.replace(0, np.nan))


def _adx(df: pd.DataFrame, length: int = 14) -> tuple[pd.Series, pd.Series, pd.Series]:
    up = df["high"].diff()
    down = -df["low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=df.index)
    tr = pd.concat([(df["high"] - df["low"]), (df["high"] - df["close"].shift()).abs(), (df["low"] - df["close"].shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    plus = 100 * plus_dm.ewm(alpha=1 / length, adjust=False, min_periods=length).mean() / atr
    minus = 100 * minus_dm.ewm(alpha=1 / length, adjust=False, min_periods=length).mean() / atr
    dx = 100 * (plus - minus).abs() / (plus + minus).replace(0, np.nan)
    return plus, minus, dx.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()


def _mfi(df: pd.DataFrame, length: int = 14) -> pd.Series:
    typical = (df["high"] + df["low"] + df["close"]) / 3
    flow = typical * df["volume"].fillna(0)
    positive = flow.where(typical.diff() > 0, 0.0).rolling(length).sum()
    negative = flow.where(typical.diff() < 0, 0.0).rolling(length).sum().abs()
    return 100 - 100 / (1 + positive / negative.replace(0, np.nan))


def sig_bollinger(df: pd.DataFrame, p: dict) -> pd.Series:
    return _stateful(df["close"] < df["bb_low"], df["close"] >= df["bb_mid"], df["close"] > df["bb_high"], df["close"] <= df["bb_mid"])


def sig_macd(df: pd.DataFrame, p: dict) -> pd.Series:
    """MACD direction using the exact fast, slow, and signal periods supplied."""
    close = df["close"]
    fast = close.ewm(span=int(p.get("macd_fast", 12)), adjust=False).mean()
    slow = close.ewm(span=int(p.get("macd_slow", 26)), adjust=False).mean()
    macd = fast - slow
    signal = macd.ewm(span=int(p.get("macd_signal", 9)), adjust=False).mean()
    return pd.Series(np.where(macd > signal, 1, np.where(macd < signal, -1, 0)), index=df.index)


def sig_ema_crossover(df: pd.DataFrame, p: dict) -> pd.Series:
    long = (df["ema_fast"] > df["ema_slow"]) & (df["close"] > df["ema_trend"])
    short = (df["ema_fast"] < df["ema_slow"]) & (df["close"] < df["ema_trend"])
    return pd.Series(np.where(long, 1, np.where(short, -1, 0)), index=df.index)


def sig_rsi_meanrev(df: pd.DataFrame, p: dict) -> pd.Series:
    return _stateful(df["rsi"] < 30, df["rsi"] > 50, df["rsi"] > 70, df["rsi"] < 50)


def sig_supertrend(df: pd.DataFrame, p: dict) -> pd.Series:
    return df["st_dir"].fillna(0).astype(int)


def sig_buy_hold(df: pd.DataFrame, p: dict) -> pd.Series:
    return pd.Series(1, index=df.index)


def sig_atr_expansion(df: pd.DataFrame, p: dict) -> pd.Series:
    move = df["close"].diff()
    return pd.Series(np.where(move > df["atr"], 1, np.where(move < -df["atr"], -1, 0)), index=df.index)


def sig_stochastic(df: pd.DataFrame, p: dict) -> pd.Series:
    value = _stochastic(df)
    return _stateful(value < 20, value > 50, value > 80, value < 50)


def sig_adx(df: pd.DataFrame, p: dict) -> pd.Series:
    plus, minus, strength = _adx(df)
    return pd.Series(np.where((strength >= 25) & (plus > minus), 1, np.where((strength >= 25) & (minus > plus), -1, 0)), index=df.index)


def sig_cci(df: pd.DataFrame, p: dict) -> pd.Series:
    value = _cci(df)
    return _stateful(value < -100, value > 0, value > 100, value < 0)


def sig_williams_r(df: pd.DataFrame, p: dict) -> pd.Series:
    high = df["high"].rolling(14).max()
    low = df["low"].rolling(14).min()
    value = -100 * (high - df["close"]) / (high - low).replace(0, np.nan)
    return _stateful(value < -80, value > -50, value > -20, value < -50)


def sig_roc(df: pd.DataFrame, p: dict) -> pd.Series:
    value = df["close"].pct_change(12)
    return pd.Series(np.where(value > 0, 1, np.where(value < 0, -1, 0)), index=df.index)


def sig_momentum(df: pd.DataFrame, p: dict) -> pd.Series:
    value = df["close"] - df["close"].shift(10)
    return pd.Series(np.where(value > 0, 1, np.where(value < 0, -1, 0)), index=df.index)


def sig_obv(df: pd.DataFrame, p: dict) -> pd.Series:
    direction = np.sign(df["close"].diff()).fillna(0)
    obv = (direction * df["volume"].fillna(0)).cumsum()
    mean = obv.rolling(20).mean()
    return pd.Series(np.where(obv > mean, 1, np.where(obv < mean, -1, 0)), index=df.index)


def sig_mfi(df: pd.DataFrame, p: dict) -> pd.Series:
    value = _mfi(df)
    return _stateful(value < 20, value > 50, value > 80, value < 50)


def sig_donchian(df: pd.DataFrame, p: dict) -> pd.Series:
    high = df["high"].rolling(20).max().shift(1)
    low = df["low"].rolling(20).min().shift(1)
    return pd.Series(np.where(df["close"] > high, 1, np.where(df["close"] < low, -1, 0)), index=df.index)


def sig_keltner(df: pd.DataFrame, p: dict) -> pd.Series:
    mid = df["close"].ewm(span=20, adjust=False).mean()
    upper, lower = mid + 2 * df["atr"], mid - 2 * df["atr"]
    return pd.Series(np.where(df["close"] > upper, 1, np.where(df["close"] < lower, -1, 0)), index=df.index)


def sig_sma(df: pd.DataFrame, p: dict) -> pd.Series:
    fast = df["close"].rolling(int(p.get("ema_fast", 20))).mean()
    slow = df["close"].rolling(int(p.get("ema_slow", 50))).mean()
    trend = df["close"].rolling(int(p.get("ema_trend", 200))).mean()
    return pd.Series(np.where((fast > slow) & (df["close"] > trend), 1, np.where((fast < slow) & (df["close"] < trend), -1, 0)), index=df.index)


def sig_ichimoku(df: pd.DataFrame, p: dict) -> pd.Series:
    high, low = df["high"], df["low"]
    tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
    kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
    span_a = (tenkan + kijun) / 2
    span_b = (high.rolling(52).max() + low.rolling(52).min()) / 2
    above = (df["close"] > span_a) & (df["close"] > span_b) & (tenkan > kijun)
    below = (df["close"] < span_a) & (df["close"] < span_b) & (tenkan < kijun)
    return pd.Series(np.where(above, 1, np.where(below, -1, 0)), index=df.index)


def sig_psar(df: pd.DataFrame, p: dict) -> pd.Series:
    highs, lows = df["high"].to_numpy(float), df["low"].to_numpy(float)
    values = np.zeros(len(df))
    if len(df) < 2:
        return pd.Series(values, index=df.index)
    long, sar, extreme, acceleration = highs[1] >= highs[0], lows[0], highs[0], .02
    for i in range(1, len(df)):
        candidate = sar + acceleration * (extreme - sar)
        if long:
            candidate = min(candidate, lows[i - 1], lows[i - 2] if i > 1 else lows[i - 1])
            if lows[i] < candidate:
                long, sar, extreme, acceleration = False, extreme, lows[i], .02
            else:
                sar = candidate
                if highs[i] > extreme:
                    extreme, acceleration = highs[i], min(.2, acceleration + .02)
        else:
            candidate = max(candidate, highs[i - 1], highs[i - 2] if i > 1 else highs[i - 1])
            if highs[i] > candidate:
                long, sar, extreme, acceleration = True, extreme, highs[i], .02
            else:
                sar = candidate
                if lows[i] < extreme:
                    extreme, acceleration = lows[i], min(.2, acceleration + .02)
        values[i] = 1 if long else -1
    return pd.Series(values, index=df.index)


def compiler_strategies() -> dict:
    return {
        "EMA crossover (trend)": sig_ema_crossover,
        "RSI mean reversion": sig_rsi_meanrev,
        "Supertrend": sig_supertrend,
        "Buy & hold (benchmark)": sig_buy_hold,
        "MACD trend": sig_macd,
        "Bollinger mean reversion": sig_bollinger,
        "ATR expansion": sig_atr_expansion,
        "Stochastic mean reversion": sig_stochastic,
        "ADX directional trend": sig_adx,
        "CCI mean reversion": sig_cci,
        "Williams %R mean reversion": sig_williams_r,
        "Rate of change trend": sig_roc,
        "Momentum trend": sig_momentum,
        "On-balance volume trend": sig_obv,
        "Money flow mean reversion": sig_mfi,
        "Donchian breakout": sig_donchian,
        "Keltner breakout": sig_keltner,
        "SMA crossover (trend)": sig_sma,
        "Ichimoku trend": sig_ichimoku,
        "Parabolic SAR trend": sig_psar,
    }

#!/usr/bin/env python3
"""Local API for VibeBT's real daily-market workspace.

This stays deliberately small: it exposes cached daily data, supported
templates, and a typed single-instrument backtest request. It never invents a
result for a UI block the compiler cannot execute.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import threading
import time
from collections import defaultdict, deque
from datetime import date as calendar_date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_ROOT / "dist"
CACHE_PROJECT = Path(os.environ.get("VIBEBT_KITE_CACHE", PROJECT_ROOT.parent / "kite-futures-cache")).expanduser().resolve()
NSE_DATA_DIR = Path(os.environ.get("VIBEBT_NSE_DATA", PROJECT_ROOT / "data" / "nse_daily")).expanduser().resolve()
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import market_indicators as ind  # noqa: E402
from strategy_registry import compiler_strategies, public_catalog, resolve  # noqa: E402
from vibebt_backtester import Recipe, run_daily_backtest  # noqa: E402

STRATEGIES = compiler_strategies()
RANGE_ROWS = {"1W": 5, "1M": 21, "3M": 63, "6M": 126, "1Y": 252, "3Y": 756, "5Y": 1260, "All": None}
INDICATOR_WARMUP_ROWS = 252
SERIES_CATALOG: list[dict] | None = None
ENGINE_VERSION = "vibebt-daily-v2.1"
REQUEST_MAX_BYTES = int(os.environ.get("VIBEBT_REQUEST_MAX_BYTES", "100000"))
MAX_CONCURRENT_RUNS = int(os.environ.get("VIBEBT_MAX_CONCURRENT_RUNS", "2"))
MAX_REQUESTS_PER_MINUTE = int(os.environ.get("VIBEBT_MAX_REQUESTS_PER_MINUTE", "30"))
CONFIGURED_ORIGINS = frozenset(filter(None, (item.strip() for item in os.environ.get("VIBEBT_ALLOWED_ORIGINS", "").split(","))))
LOCAL_ORIGIN = re.compile(r"https?://(?:localhost|127\.0\.0\.1):\d+")
RUN_SEMAPHORE = threading.BoundedSemaphore(max(1, MAX_CONCURRENT_RUNS))
LOG = logging.getLogger("vibebt.api")


class RateLimiter:
    """Small in-process guard for an intentionally single-node daily engine."""

    def __init__(self, limit: int, window_seconds: int = 60):
        self.limit = max(1, limit)
        self.window_seconds = window_seconds
        self.events: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self.lock:
            events = self.events[key]
            while events and events[0] <= now - self.window_seconds:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            return True


BACKTEST_RATE_LIMITER = RateLimiter(MAX_REQUESTS_PER_MINUTE)


def clean(value):
    if hasattr(value, "item"):
        value = value.item()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def validate_daily_frame(frame, series: str):
    """Reject malformed cached data rather than quietly repairing market history."""
    required = {"date", "open", "high", "low", "close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{series} is missing required daily fields: {', '.join(sorted(missing))}.")
    if frame.empty:
        raise ValueError(f"{series} has no daily observations.")
    dates = frame["date"]
    if dates.isna().any() or dates.duplicated().any() or not dates.is_monotonic_increasing:
        raise ValueError(f"{series} has invalid daily dates. Refresh the source cache before testing it.")
    values = frame[["open", "high", "low", "close", "volume"]].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values[:, :4] <= 0).any() or (values[:, 4] < 0).any():
        raise ValueError(f"{series} contains invalid OHLCV values. Refresh the source cache before testing it.")
    open_, high, low, close = values[:, 0], values[:, 1], values[:, 2], values[:, 3]
    if (high < np.maximum(open_, close)).any() or (low > np.minimum(open_, close)).any() or (high < low).any():
        raise ValueError(f"{series} contains impossible OHLC bars. Refresh the source cache before testing it.")
    return frame


def data_age_days(frame) -> int:
    last = frame["date"].iloc[-1]
    last_day = last.date() if hasattr(last, "date") else calendar_date.fromisoformat(str(last)[:10])
    return max(0, (calendar_date.today() - last_day).days)


def _load_nse_series(key: str) -> pd.DataFrame:
    path = NSE_DATA_DIR / f"{key}.csv"
    if not path.is_file():
        raise ValueError(f"Official NSE data file is missing for {key}.")
    return pd.read_csv(path, parse_dates=["date"])


def _load_series(instrument: dict) -> pd.DataFrame:
    if instrument["dataSource"] == "nse_bhavcopy":
        return _load_nse_series(instrument["key"])
    if not CACHE_PROJECT.is_dir():
        raise ValueError("This broker-cached series is unavailable. Select an NSE cash-equity series or configure VIBEBT_KITE_CACHE.")
    sys.path.insert(0, str(CACHE_PROJECT))
    from kite_data import load_series  # local optional source, never required for NSE data
    return load_series("day", instrument["key"])


def available_series() -> list[dict]:
    """Return eligible daily cash equities, indices, and continuous futures."""
    global SERIES_CATALOG
    if SERIES_CATALOG is not None:
        return SERIES_CATALOG
    items = []
    for path in sorted(NSE_DATA_DIR.glob("*_NSE_SPOT.csv")):
        key = path.stem
        try:
            frame = validate_daily_frame(_load_nse_series(key), key)
        except Exception as exc:
            LOG.warning("Excluding invalid official NSE series %s: %s", key, exc)
            continue
        if len(frame) < INDICATOR_WARMUP_ROWS:
            continue
        items.append({
            "key": key,
            "label": key.removesuffix("_NSE_SPOT").replace("-", " "),
            "kind": "Cash equities · NSE official",
            "instrumentType": "equity",
            "dataSource": "nse_bhavcopy",
            "sourceLabel": "NSE UDiFF bhavcopy",
            "rows": int(len(frame)),
            "firstDate": clean(frame["date"].iloc[0]),
            "lastDate": clean(frame["date"].iloc[-1]),
            "hasOi": bool("oi" in frame.columns and frame["oi"].fillna(0).abs().sum() > 0),
            "backtestEligible": True,
        })
    day_dir = CACHE_PROJECT / "cache" / "day"
    if day_dir.is_dir():
        for path in sorted(day_dir.glob("*.parquet")):
            if not (path.name.endswith("_FUT_CONT.parquet") or path.name.endswith("_SPOT.parquet")):
                continue
            key = path.stem
            try:
                frame = validate_daily_frame(_load_series({"key": key, "dataSource": "kite_cache"}), key)
            except Exception as exc:
                LOG.warning("Excluding invalid cached series %s: %s", key, exc)
                continue
            if len(frame) < INDICATOR_WARMUP_ROWS:
                continue
            root = key.rsplit("_", 1)[0]
            is_index = root in {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "INDIAVIX"}
            instrument_type, kind = ("futures", "F&O futures") if key.endswith("_FUT_CONT") else (("index", "Indices") if is_index else ("equity", "Cash equities · broker cache"))
            items.append({"key": key, "label": root.replace("-", " "), "kind": kind, "instrumentType": instrument_type, "dataSource": "kite_cache", "sourceLabel": "Local broker cache", "rows": int(len(frame)), "firstDate": clean(frame["date"].iloc[0]), "lastDate": clean(frame["date"].iloc[-1]), "hasOi": bool("oi" in frame.columns and frame["oi"].fillna(0).abs().sum() > 0), "backtestEligible": True})
    order = {"Cash equities · NSE official": 0, "Cash equities · broker cache": 1, "F&O futures": 2, "Indices": 3}
    SERIES_CATALOG = sorted(items, key=lambda item: (order[item["kind"]], item["label"]))
    return SERIES_CATALOG


def _number(value, default, lower, upper):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if not lower <= result <= upper:
        raise ValueError(f"A value must be between {lower:g} and {upper:g}.")
    return result


def _mapping(value, name):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object.")
    return value


def _risk_rule(value, name):
    rule = _mapping(value, name)
    kind = str(rule.get("kind", "none"))
    if kind not in {"none", "percent", "atr", "risk_reward"}:
        raise ValueError(f"Unsupported {name} rule.")
    if kind == "risk_reward" and name == "stop":
        raise ValueError("Risk/reward is a target rule, not a stop rule.")
    amount = _number(rule.get("value", 0), 0, 0, 100) if kind != "none" else 0
    if kind != "none" and amount <= 0:
        raise ValueError(f"{name.capitalize()} needs a positive value.")
    return {"kind": kind, "value": amount}


def _recipe_from_payload(payload: dict, instrument: dict) -> tuple[Recipe, str, str]:
    if not isinstance(payload, dict):
        raise ValueError("Backtest request must be a JSON object.")
    signal = str(payload.get("signal", "ma-cross-up"))
    template = resolve(signal)
    side = str(payload.get("side", "long"))
    if side not in {"long", "short", "both"}:
        raise ValueError("Side must be long, short, or both.")
    if instrument["instrumentType"] in {"equity", "index"} and side != "long":
        raise ValueError("Cash equities and indices are long-only in this daily version.")
    exit_spec = _mapping(payload.get("exit"), "exit")
    exit_rule = str(exit_spec.get("kind", "signal"))
    if exit_rule not in {"signal", "hold"}:
        raise ValueError("Only signal reversal and fixed-day exits are currently runnable.")
    hold_bars = int(_number(exit_spec.get("holdBars", 0), 0, 0, 90))
    if exit_rule == "hold" and hold_bars < 1:
        raise ValueError("A fixed-day exit needs between 1 and 90 trading days.")
    filters = payload.get("filters", [])
    if not isinstance(filters, list):
        raise ValueError("Filters must be a list.")
    supported_filters = {"above_50_sma", "below_50_sma", "high_relative_volume", "rsi_above_55", "rsi_below_45"}
    filters = tuple(str(item) for item in filters)
    if len(filters) > 2 or not set(filters).issubset(supported_filters):
        raise ValueError("One or more selected confirmations are not yet runnable on daily data.")
    costs = _mapping(payload.get("costs"), "costs")
    params = _mapping(payload.get("params"), "params")
    fast = int(_number(params.get("emaFast", 20), 20, 2, 250))
    slow = int(_number(params.get("emaSlow", 50), 50, 3, 400))
    trend = int(_number(params.get("emaTrend", 200), 200, 4, 500))
    if not fast < slow < trend:
        raise ValueError("EMA periods must satisfy fast < slow < trend.")
    macd_fast = int(_number(params.get("macdFast", 12), 12, 2, 100))
    macd_slow = int(_number(params.get("macdSlow", 26), 26, 3, 200))
    macd_signal = int(_number(params.get("macdSignal", 9), 9, 2, 100))
    if not macd_fast < macd_slow:
        raise ValueError("MACD fast period must be shorter than its slow period.")
    recipe = Recipe(
        strategy=template.engine_strategy,
        params={
            "ema_fast": fast, "ema_slow": slow, "ema_trend": trend,
            "macd_fast": macd_fast, "macd_slow": macd_slow, "macd_signal": macd_signal,
        },
        side=side,
        exit_rule=exit_rule,
        hold_bars=hold_bars,
        stop=_risk_rule(payload.get("stop"), "stop"),
        target=_risk_rule(payload.get("target"), "target"),
        filters=filters,
        commission_bps=_number(costs.get("commissionBps", 5), 5, 0, 500),
        slippage_bps=_number(costs.get("slippageBps", 5), 5, 0, 500),
        capital=_number(payload.get("capital", 100000), 100000, 1_000, 100_000_000),
        allocation_pct=_number(payload.get("allocationPct", 100), 100, 1, 100),
        instrument_type=instrument["instrumentType"],
    )
    return recipe, template.id, template.version


def build_run(payload: dict) -> dict:
    series = str(payload.get("series", "RELIANCE_SPOT"))
    range_name = str(payload.get("testRange", payload.get("range", "All")))
    if range_name not in RANGE_ROWS:
        raise ValueError("Unsupported test period.")
    catalog = {item["key"]: item for item in available_series()}
    if series not in catalog:
        raise ValueError("That series is not available as an eligible cached daily instrument.")
    instrument = catalog[series]
    recipe, template_id, template_version = _recipe_from_payload(payload, instrument)
    frame = validate_daily_frame(_load_series(instrument), series)
    rows = RANGE_ROWS[range_name]
    if rows and len(frame) < rows + INDICATOR_WARMUP_ROWS:
        raise ValueError("This series does not have enough history for that test period and indicator warm-up.")
    engine_bars = frame.tail(rows + INDICATOR_WARMUP_ROWS).copy() if rows else frame.copy()
    start_index = INDICATOR_WARMUP_ROWS if rows else 1
    result = run_daily_backtest(engine_bars, recipe, ind, STRATEGIES, start_index=start_index)
    age = data_age_days(frame)
    warning = (
        "Continuous futures are retained as a research series only. Point-in-time contract, lot-size, roll, and margin rules are not yet available."
        if instrument["instrumentType"] == "futures" else
        "Daily single-instrument research. Corporate-action and liquidity treatment should be reviewed before relying on a long historical cash-equity result."
    )
    if age > 7:
        warning = f"Cached daily data is {age} calendar days old. {warning}"
    return {
        "source": {
            "series": series,
            "label": instrument["label"],
            "instrumentType": instrument["instrumentType"],
            "timeframe": "daily",
            "testRange": range_name,
            "firstDate": result["bars"][0]["date"],
            "lastDate": result["bars"][-1]["date"],
            "rows": len(result["bars"]),
            "templateId": template_id,
            "templateVersion": template_version,
            "strategy": recipe.strategy,
            "strategySpec": {
                "signal": payload.get("signal", "ma-cross-up"), "side": recipe.side,
                "exit": {"kind": recipe.exit_rule, "holdBars": recipe.hold_bars},
                "stop": recipe.stop, "target": recipe.target, "filters": recipe.filters,
                "params": recipe.params, "costs": {"commissionBps": recipe.commission_bps, "slippageBps": recipe.slippage_bps},
                "capital": recipe.capital, "allocationPct": recipe.allocation_pct,
            },
            "data": instrument["sourceLabel"],
            "dataAsOf": clean(frame["date"].iloc[-1]),
            "dataAgeDays": age,
            "dataStatus": "stale" if age > 7 else "current",
            "warning": warning if instrument["dataSource"] != "nse_bhavcopy" else "Official NSE end-of-day cash-equity bars. Results are not corporate-action adjusted; review corporate actions and liquidity before relying on a long historical result.",
            "execution": "Signals are observed at daily close and orders fill at the next daily open. Gap exits fill at the open; if both intraday stop and target are touched, the stop fills first.",
            "unit": "account value" if instrument["instrumentType"] in {"equity", "index"} else "continuous-futures points",
        },
        "metrics": result["metrics"],
        "bars": result["bars"],
        "benchmark": result["benchmark"],
        "trades": result["trades"],
        "drawdown": result["drawdown"],
    }


def payload_from_query(query: dict) -> dict:
    def first(name, default=None):
        values = query.get(name, [default])
        return values[0]
    stop = {"kind": "atr", "value": 1.5} if first("stop") == "1" else {"kind": "none"}
    target = {"kind": "atr", "value": 2.5} if first("target") == "1" else {"kind": "none"}
    return {
        "series": first("series", "RELIANCE_SPOT"), "signal": first("signal", "ma-cross-up"),
        "testRange": first("range", "All"), "side": first("side", "long"),
        "exit": {"kind": first("exit", "signal"), "holdBars": first("holdBars", 0)},
        "stop": stop, "target": target,
        "params": {
            "emaFast": first("emaFast", 20), "emaSlow": first("emaSlow", 50), "emaTrend": first("emaTrend", 200),
            "macdFast": first("macdFast", 12), "macdSlow": first("macdSlow", 26), "macdSignal": first("macdSignal", 9),
        },
        "costs": {"commissionBps": first("commissionBps", 5), "slippageBps": first("slippageBps", 5)},
        "capital": first("capital", 100000), "allocationPct": first("allocationPct", 100),
    }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _origin_allowed(self, origin: str) -> bool:
        return bool(origin and (origin in CONFIGURED_ORIGINS or (not CONFIGURED_ORIGINS and bool(LOCAL_ORIGIN.fullmatch(origin)))))

    def _send_cors_headers(self) -> None:
        origin = self.headers.get("Origin", "")
        if self._origin_allowed(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def send_json(self, status: int, body: dict):
        encoded = json.dumps(body, allow_nan=False).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "same-origin")
            self.send_header("X-Frame-Options", "DENY")
            self._send_cors_headers()
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError):
            return False
        return True

    def send_static(self, request_path: str):
        """Serve the built workspace from the same origin as the research API."""
        relative = request_path.lstrip("/") or "index.html"
        candidate = (STATIC_DIR / relative).resolve()
        try:
            candidate.relative_to(STATIC_DIR.resolve())
        except ValueError:
            return self.send_json(404, {"error": "Not found"})
        if not candidate.is_file():
            candidate = STATIC_DIR / "index.html"  # The Vite app owns client-side routes.
        if not candidate.is_file():
            return self.send_json(404, {"error": "The web build is unavailable. Run npm run build."})
        content_types = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".json": "application/json; charset=utf-8"}
        try:
            payload = candidate.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_types.get(candidate.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-cache" if candidate.name == "index.html" else "public, max-age=31536000, immutable")
            self.end_headers()
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            return False
        return True

    def _route(self, payload: dict):
        client = self.client_address[0]
        if not BACKTEST_RATE_LIMITER.allow(client):
            return self.send_json(429, {"error": "Too many backtest requests. Wait a minute and try again."})
        if not RUN_SEMAPHORE.acquire(blocking=False):
            return self.send_json(429, {"error": "Backtests are busy. Try again in a moment."})
        try:
            return self.send_json(200, build_run(payload))
        except (BrokenPipeError, ConnectionResetError):
            return
        except ValueError as exc:
            return self.send_json(422, {"error": str(exc)})
        except Exception:
            LOG.exception("Backtest failed")
            return self.send_json(500, {"error": "Backtest could not be completed. Check the server log."})
        finally:
            RUN_SEMAPHORE.release()

    def do_OPTIONS(self):  # noqa: N802
        origin = self.headers.get("Origin", "")
        if origin and not self._origin_allowed(origin):
            return self.send_json(403, {"error": "Origin is not allowed."})
        self.send_response(204)
        self._send_cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            ready = (CACHE_PROJECT / "cache" / "day").is_dir() or NSE_DATA_DIR.is_dir()
            return self.send_json(200 if ready else 503, {"ok": ready, "engine": ENGINE_VERSION, "dailyCacheReady": ready, "nseDataReady": NSE_DATA_DIR.is_dir()})
        if parsed.path == "/api/series":
            return self.send_json(200, {"series": available_series(), "timeframes": ["daily"]})
        if parsed.path == "/api/templates":
            return self.send_json(200, {"templates": public_catalog(), "filters": ["above_50_sma", "below_50_sma", "high_relative_volume", "rsi_above_55", "rsi_below_45"]})
        if parsed.path == "/api/backtest":
            return self._route(payload_from_query(parse_qs(parsed.query)))
        return self.send_static(parsed.path)

    def do_POST(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/backtest":
            return self.send_json(404, {"error": "Not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > REQUEST_MAX_BYTES:
                raise ValueError(f"Backtest request must be a JSON body smaller than {REQUEST_MAX_BYTES // 1000} KB.")
            payload = json.loads(self.rfile.read(length))
        except (ValueError, json.JSONDecodeError) as exc:
            return self.send_json(400, {"error": str(exc)})
        return self._route(payload)

    def log_message(self, fmt, *args):
        LOG.info("%s - %s", self.address_string(), fmt % args)


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("VIBEBT_LOG_LEVEL", "INFO").upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    host = os.environ.get("VIBEBT_HOST", "127.0.0.1")
    port = int(os.environ.get("VIBEBT_PORT", os.environ.get("PORT", "8765")))
    LOG.info("Starting %s on %s:%s using cached daily market data", ENGINE_VERSION, host, port)
    ThreadingHTTPServer((host, port), Handler).serve_forever()

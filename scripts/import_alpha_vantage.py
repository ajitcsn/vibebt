#!/usr/bin/env python3
"""Fetch a small, separately-provenanced BSE daily-price import.

This is intentionally not wired into the futures backtester. Alpha Vantage's
free daily endpoint is useful for exploring a symbol, but it is not a
replacement for VibeBT's local continuous-futures history, point-in-time
corporate actions, or contract metadata.
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: VIBEBT_ALPHA_VANTAGE_KEY=... python scripts/import_alpha_vantage.py RELIANCE.BSE")
    api_key = os.environ.get("VIBEBT_ALPHA_VANTAGE_KEY")
    if not api_key:
        raise SystemExit("VIBEBT_ALPHA_VANTAGE_KEY is required. Get a free key from Alpha Vantage.")

    symbol = sys.argv[1].upper()
    params = urlencode({"function": "TIME_SERIES_DAILY", "symbol": symbol, "apikey": api_key, "datatype": "csv"})
    url = f"https://www.alphavantage.co/query?{params}"
    with urlopen(url, timeout=30) as response:  # nosec B310: fixed HTTPS host
        payload = response.read().decode("utf-8")

    rows = list(csv.DictReader(io.StringIO(payload)))
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    if not rows or not required.issubset(rows[0]):
        raise SystemExit(f"Provider did not return daily OHLCV for {symbol}: {payload[:180]}")
    for row in rows:
        datetime.strptime(row["timestamp"], "%Y-%m-%d")
        for field in ("open", "high", "low", "close", "volume"):
            float(row[field])
    rows.sort(key=lambda row: row["timestamp"])

    target = Path("data/imports/alpha_vantage")
    target.mkdir(parents=True, exist_ok=True)
    stem = symbol.replace("/", "_").replace(".", "_")
    with (target / f"{stem}.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)
    (target / f"{stem}.provenance.json").write_text(json.dumps({
        "provider": "Alpha Vantage",
        "endpoint": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "url_without_api_key": f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&datatype=csv",
        "retrievedAt": datetime.now(timezone.utc).isoformat(),
        "rows": len(rows),
        "firstDate": rows[0]["timestamp"],
        "lastDate": rows[-1]["timestamp"],
        "useLimit": "Exploration-only spot OHLCV. Do not combine with Kite futures backtests.",
    }, indent=2) + "\n")
    print(f"Imported {len(rows)} daily OHLCV rows for {symbol} into {target}")


if __name__ == "__main__":
    main()

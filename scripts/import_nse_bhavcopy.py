#!/usr/bin/env python3
"""Import official NSE UDiFF common bhavcopy cash-equity bars into VibeBT.

One official ZIP is fetched per exchange session. The importer only accepts EQ
series rows and records every source URL and checksum, so imported data is
never silently mixed with broker data or synthetic bars.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import ssl
import time
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import certifi
except ImportError:  # Kept explicit so a missing CA bundle fails safely, never insecurely.
    certifi = None

DEFAULT_SYMBOLS = "RELIANCE,HDFCBANK,ICICIBANK,INFY,TCS,SBIN,ITC,LT,AXISBANK,KOTAKBANK,HINDUNILVR,BHARTIARTL,MARUTI,SUNPHARMA,TITAN,BAJFINANCE,NTPC,POWERGRID,TATAMOTORS"
ARCHIVE = "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{day:%Y%m%d}_F_0000.csv.zip"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; VibeBT official-NSE importer/1.0)", "Accept": "application/zip"}
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where()) if certifi else ssl.create_default_context()


def fetch(url: str) -> bytes | None:
    request = Request(url, headers=HEADERS)
    for attempt in range(4):
        try:
            with urlopen(request, timeout=60, context=SSL_CONTEXT) as response:
                payload = response.read()
                if not payload.startswith(b"PK"):
                    raise RuntimeError("NSE did not return a bhavcopy ZIP. Try again later; no data was written.")
                return payload
        except HTTPError as exc:
            if exc.code == 404:
                return None  # Weekend, exchange holiday, or unavailable future session.
            if attempt == 3:
                raise RuntimeError(f"NSE request failed ({exc.code}) for {url}") from exc
        except (URLError, TimeoutError) as exc:
            if attempt == 3:
                raise RuntimeError(f"NSE request failed for {url}: {exc}") from exc
        time.sleep(2 ** attempt)
    return None


def rows_from_zip(payload: bytes, day: date, wanted: set[str]) -> list[dict]:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(names) != 1:
            raise RuntimeError("Official NSE archive has an unexpected CSV layout.")
        text = archive.read(names[0]).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    required = {"TckrSymb", "SctySrs", "OpnPric", "HghPric", "LwPric", "ClsPric", "TtlTradgVol"}
    if not required.issubset(reader.fieldnames or set()):
        raise RuntimeError("Official NSE bhavcopy columns changed. Import stopped before writing data.")
    result = []
    for row in reader:
        symbol = (row.get("TckrSymb") or "").strip().upper()
        if symbol not in wanted or (row.get("SctySrs") or "").strip().upper() != "EQ":
            continue
        try:
            open_, high, low, close = (float(row[field]) for field in ("OpnPric", "HghPric", "LwPric", "ClsPric"))
            volume = float(row["TtlTradgVol"])
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"Invalid NSE OHLCV row for {symbol} on {day.isoformat()}") from exc
        if min(open_, high, low, close) <= 0 or volume < 0 or high < max(open_, close) or low > min(open_, close):
            raise RuntimeError(f"Impossible NSE OHLCV row for {symbol} on {day.isoformat()}")
        result.append({"_symbol": symbol, "date": day.isoformat(), "open": open_, "high": high, "low": low, "close": close, "volume": volume})
    return result


def write_symbol(path: Path, incoming: list[dict]) -> None:
    existing = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            existing = list(csv.DictReader(handle))
    merged = {row["date"]: row for row in existing}
    merged.update({row["date"]: {key: value for key, value in row.items() if key != "_symbol"} for row in incoming})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(merged[key] for key in sorted(merged))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=400, help="calendar days to fetch, including today")
    parser.add_argument("--symbols", default=DEFAULT_SYMBOLS, help="comma-separated NSE equity symbols")
    parser.add_argument("--output", default="data/nse_daily", help="local VibeBT NSE data directory")
    parser.add_argument("--pause", type=float, default=.35, help="seconds between official requests")
    args = parser.parse_args()
    if not 1 <= args.days <= 3000:
        raise SystemExit("--days must be between 1 and 3000")
    symbols = {value.strip().upper() for value in args.symbols.split(",") if value.strip()}
    if not symbols:
        raise SystemExit("Provide at least one symbol")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    manifest, batches = [], {symbol: [] for symbol in symbols}
    today = date.today()
    for offset in range(args.days - 1, -1, -1):
        day = today - timedelta(days=offset)
        if day.weekday() >= 5:
            continue
        url = ARCHIVE.format(day=day)
        payload = fetch(url)
        if payload is None:
            continue
        rows = rows_from_zip(payload, day, symbols)
        for row in rows:
            batches[row["_symbol"]].append(row)
        manifest.append({"date": day.isoformat(), "url": url, "sha256": hashlib.sha256(payload).hexdigest(), "rows": len(rows), "fetchedAt": datetime.now(timezone.utc).isoformat()})
        print(f"{day.isoformat()}: {len(rows)} selected NSE EQ bars")
        time.sleep(args.pause)
    for symbol, bars in batches.items():
        if bars:
            write_symbol(output / f"{symbol}_NSE_SPOT.csv", bars)
    (output / "manifest.json").write_text(json.dumps({"source": "NSE CM UDiFF Common Bhavcopy Final", "symbols": sorted(symbols), "fetchedAt": datetime.now(timezone.utc).isoformat(), "files": manifest}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

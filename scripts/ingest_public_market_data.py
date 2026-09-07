#!/usr/bin/env python3
"""Backfill reproducible, public Indian-market event data for VibeBT.

This intentionally excludes analyst estimates, scraped valuation ratios and
anything that cannot be timestamped. It stores the original published fields
plus fetch metadata, so strategies can use only information available then.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
from http.client import IncompleteRead
import json
import re
import ssl
import sys
import time
from datetime import date, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import certifi

CACHE_PROJECT = Path("/Users/ajitc/Desktop/projects/kite-futures-cache")
ROOT = Path("data/public_market")
NSE_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; VibeBT research collector/1.0)", "Accept": "application/json"}
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
RELEVANT_SUBJECTS = (
    "result", "financial", "board meeting", "dividend", "bonus", "split", "rights", "buyback",
    "merger", "amalgam", "demerger", "acquisition", "contract", "order", "credit rating",
    "investor", "management", "resignation", "appointment",
)


def months(start: date, end: date):
    cursor = date(start.year, start.month, 1)
    while cursor <= end:
        next_month = date(cursor.year + (cursor.month == 12), 1 if cursor.month == 12 else cursor.month + 1, 1)
        last = min(end, date.fromordinal(next_month.toordinal() - 1))
        yield cursor, last
        cursor = next_month


def nse_json(endpoint: str) -> list[dict]:
    request = Request(f"https://www.nseindia.com{endpoint}", headers=NSE_HEADERS)
    for attempt in range(4):
        try:
            with urlopen(request, timeout=45, context=SSL_CONTEXT) as response:
                payload = json.loads(response.read().decode("utf-8"))
                if not isinstance(payload, list):
                    raise ValueError("NSE response is not a list")
                return payload
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            if attempt == 3:
                raise RuntimeError(f"NSE request failed: {endpoint}: {exc}") from exc
            time.sleep(2 ** attempt)
    return []


def fetch_bytes(url: str, headers: dict[str, str]) -> bytes:
    request = Request(url, headers=headers)
    for attempt in range(4):
        try:
            with urlopen(request, timeout=60, context=SSL_CONTEXT) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError, IncompleteRead) as exc:
            if attempt == 3:
                raise RuntimeError(f"Request failed: {url}: {exc}") from exc
            time.sleep(2 ** attempt)
    return b""


def date_arg(day: date) -> str:
    return day.strftime("%d-%m-%Y")


def write_gzip_json(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(rows, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    with gzip.open(path, "wb") as handle:
        handle.write(encoded)
    return hashlib.sha256(encoded).hexdigest()


def announcement_rows(rows: list[dict], fetched_at: str) -> list[dict]:
    selected = []
    for row in rows:
        text = f"{row.get('desc', '')} {row.get('sm_name', '')} {row.get('attchmntText', '')}".lower()
        if any(term in text for term in RELEVANT_SUBJECTS):
            selected.append({"published": row, "fetched_at": fetched_at, "source": "NSE corporate announcements"})
    return selected


def backfill_nse(kind: str, start: date, end: date, manifest: list[dict], pause: float):
    endpoint = "corporate-announcements" if kind == "announcements" else "corporates-corporateActions"
    target = ROOT / "nse" / kind
    for first, last in months(start, end):
        filename = target / f"{first:%Y-%m}.json.gz"
        if filename.exists():
            continue
        query = f"/api/{endpoint}?index=equities&from_date={date_arg(first)}&to_date={date_arg(last)}"
        rows = nse_json(query)
        fetched_at = datetime.now().astimezone().isoformat(timespec="seconds")
        output = announcement_rows(rows, fetched_at) if kind == "announcements" else [
            {"published": row, "fetched_at": fetched_at, "source": "NSE corporate actions"} for row in rows
        ]
        checksum = write_gzip_json(filename, output)
        manifest.append({"source": f"nse_{kind}", "period": f"{first:%Y-%m}", "rows": len(output), "path": str(filename), "sha256": checksum, "fetched_at": fetched_at, "query": query})
        print(f"{kind} {first:%Y-%m}: {len(output)} rows")
        time.sleep(pause)


def backfill_vix(manifest: list[dict]):
    sys.path.insert(0, str(CACHE_PROJECT))
    from kite_data import load_series  # local user-supplied market cache

    frame = load_series("day", "INDIAVIX_SPOT")
    rows = []
    fetched_at = datetime.now().astimezone().isoformat(timespec="seconds")
    for row in frame.itertuples(index=False):
        rows.append({"date": row.date.isoformat(), "open": float(row.open), "high": float(row.high), "low": float(row.low), "close": float(row.close), "fetched_at": fetched_at, "source": "local Kite cache: INDIAVIX_SPOT"})
    filename = ROOT / "derived" / "india_vix_daily.json.gz"
    checksum = write_gzip_json(filename, rows)
    manifest.append({"source": "india_vix", "rows": len(rows), "path": str(filename), "sha256": checksum, "fetched_at": fetched_at, "coverage": [rows[0]["date"], rows[-1]["date"]]})
    print(f"india_vix: {len(rows)} rows")


def backfill_fpi(manifest: list[dict], pause: float):
    """Mirror SEBI's public monthly trade archives without altering them."""
    page = "https://www.sebi.gov.in/statistics/fpi-investment/trade-wise-equity-data-of-fpi.html"
    html = fetch_bytes(page, {"User-Agent": NSE_HEADERS["User-Agent"], "Accept": "text/html"}).decode("utf-8", "replace")
    links = sorted(set(re.findall(r'href="([^"]+\.zip)"', html, flags=re.I)))
    root = "https://www.sebi.gov.in/statistics/fpi-investment/"
    target = ROOT / "sebi" / "fpi_trade_archives"
    for href in links:
        url = urljoin(root, href)
        filename = target / Path(href).name
        if filename.exists():
            continue
        payload = fetch_bytes(url, {"User-Agent": NSE_HEADERS["User-Agent"], "Accept": "application/zip"})
        filename.parent.mkdir(parents=True, exist_ok=True)
        filename.write_bytes(payload)
        fetched_at = datetime.now().astimezone().isoformat(timespec="seconds")
        manifest.append({"source": "sebi_fpi_trade_archive", "path": str(filename), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload), "fetched_at": fetched_at, "url": url})
        print(f"fpi {filename.name}: {len(payload):,} bytes")
        time.sleep(pause)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="start", default="2009-03-01", help="YYYY-MM-DD")
    parser.add_argument("--to", dest="end", default=date.today().isoformat(), help="YYYY-MM-DD")
    parser.add_argument("--sources", default="announcements,actions,vix,fpi", help="comma list: announcements,actions,vix,fpi")
    parser.add_argument("--pause", type=float, default=.45, help="seconds between NSE requests")
    args = parser.parse_args()
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if start > end:
        raise SystemExit("--from must be on or before --to")
    sources = {item.strip() for item in args.sources.split(",") if item.strip()}
    invalid = sources - {"announcements", "actions", "vix", "fpi"}
    if invalid:
        raise SystemExit(f"Unsupported source(s): {', '.join(sorted(invalid))}")
    manifest = []
    if "announcements" in sources:
        backfill_nse("announcements", start, end, manifest, args.pause)
    if "actions" in sources:
        backfill_nse("actions", start, end, manifest, args.pause)
    if "vix" in sources:
        backfill_vix(manifest)
    if "fpi" in sources:
        backfill_fpi(manifest, args.pause)
    ROOT.mkdir(parents=True, exist_ok=True)
    write_gzip_json(ROOT / "manifests" / f"run-{datetime.now():%Y%m%dT%H%M%S}.json.gz", manifest)


if __name__ == "__main__":
    main()

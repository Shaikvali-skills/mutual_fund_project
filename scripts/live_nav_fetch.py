#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
live_nav_fetch.py
==================
Fetches the latest NAV for every scheme in `fund_master` using the free
MFAPI service (https://www.mfapi.in) and appends any new NAV records to
the `nav_history` table in the SQLite database.

MFAPI is a community-run public API for Indian mutual fund NAV data.
Each scheme is identified by its AMFI scheme code, e.g.:
    https://api.mfapi.in/mf/119551          -> full NAV history
    https://api.mfapi.in/mf/119551/latest   -> most recent NAV only

Usage
-----
    python scripts/live_nav_fetch.py
    python scripts/live_nav_fetch.py --db data/db/bluestock_mf.db --mode latest
    python scripts/live_nav_fetch.py --mode full --scheme-code 119551

Modes
-----
    latest  (default) -> fetch only the newest NAV for each scheme (fast,
                          suitable for a daily cron job)
    full               -> re-fetch each scheme's entire NAV history and
                          upsert every date (slower, use for backfills)
"""

import argparse
import logging
import sqlite3
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("live_nav_fetch")

DEFAULT_DB_PATH = Path("data/db/bluestock_mf.db")
API_BASE = "https://api.mfapi.in/mf"
REQUEST_TIMEOUT = 10          # seconds
REQUEST_DELAY = 0.25          # seconds between calls, to be polite to the API
MAX_RETRIES = 3


def get_scheme_codes(conn: sqlite3.Connection, scheme_code: Optional[str] = None) -> list:
    if scheme_code:
        return [str(scheme_code)]
    try:
        rows = conn.execute("SELECT DISTINCT scheme_code FROM fund_master").fetchall()
    except sqlite3.OperationalError:
        log.error("fund_master table not found. Run etl_pipeline.py first.")
        return []
    return [str(r[0]) for r in rows]


def fetch_json(url: str) -> Optional[dict]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            log.warning("Attempt %d/%d failed for %s: %s", attempt, MAX_RETRIES, url, exc)
            time.sleep(1.5 * attempt)
    log.error("Giving up on %s after %d attempts", url, MAX_RETRIES)
    return None


def parse_mfapi_date(date_str: str) -> Optional[str]:
    """MFAPI returns dates as 'DD-MM-YYYY'; convert to ISO 'YYYY-MM-DD'."""
    try:
        return pd.to_datetime(date_str, format="%d-%m-%Y").strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def fetch_latest_nav(scheme_code: str) -> Optional[dict]:
    payload = fetch_json(f"{API_BASE}/{scheme_code}/latest")
    if not payload or "data" not in payload or not payload["data"]:
        return None
    latest = payload["data"][0]
    date = parse_mfapi_date(latest.get("date"))
    nav = latest.get("nav")
    if date is None or nav is None:
        return None
    return {"scheme_code": scheme_code, "date": date, "nav": float(nav)}


def fetch_full_history(scheme_code: str) -> pd.DataFrame:
    payload = fetch_json(f"{API_BASE}/{scheme_code}")
    if not payload or "data" not in payload:
        return pd.DataFrame(columns=["scheme_code", "date", "nav"])

    records = []
    for row in payload["data"]:
        date = parse_mfapi_date(row.get("date"))
        nav = row.get("nav")
        if date is None or nav is None:
            continue
        try:
            records.append({"scheme_code": scheme_code, "date": date, "nav": float(nav)})
        except ValueError:
            continue
    return pd.DataFrame(records)


def upsert_nav_history(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    """Insert only NAV rows that don't already exist for (scheme_code, date)."""
    if df.empty:
        return 0

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS nav_history (
            scheme_code TEXT NOT NULL,
            date TEXT NOT NULL,
            nav REAL NOT NULL,
            PRIMARY KEY (scheme_code, date)
        )
        """
    )
    rows = list(df[["scheme_code", "date", "nav"]].itertuples(index=False, name=None))
    cur = conn.executemany(
        "INSERT OR IGNORE INTO nav_history (scheme_code, date, nav) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    return cur.rowcount if cur.rowcount is not None else 0


def run_latest_mode(conn: sqlite3.Connection, scheme_codes: list) -> None:
    new_rows = []
    for i, code in enumerate(scheme_codes, start=1):
        log.info("[%d/%d] Fetching latest NAV for scheme %s", i, len(scheme_codes), code)
        result = fetch_latest_nav(code)
        if result:
            new_rows.append(result)
        time.sleep(REQUEST_DELAY)

    if not new_rows:
        log.warning("No NAV data retrieved.")
        return

    df = pd.DataFrame(new_rows)
    inserted = upsert_nav_history(conn, df)
    log.info("Fetched %d scheme NAVs, inserted %d new records into nav_history.", len(df), inserted)


def run_full_mode(conn: sqlite3.Connection, scheme_codes: list) -> None:
    total_inserted = 0
    for i, code in enumerate(scheme_codes, start=1):
        log.info("[%d/%d] Backfilling full NAV history for scheme %s", i, len(scheme_codes), code)
        df = fetch_full_history(code)
        inserted = upsert_nav_history(conn, df)
        total_inserted += inserted
        log.info("  -> %d new records inserted for scheme %s", inserted, code)
        time.sleep(REQUEST_DELAY)
    log.info("Full backfill complete. Total new records inserted: %d", total_inserted)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch live/historical NAV data from MFAPI")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH,
                         help="Path to the SQLite database file")
    parser.add_argument("--mode", choices=["latest", "full"], default="latest",
                         help="'latest' fetches only today's NAV; 'full' backfills entire history")
    parser.add_argument("--scheme-code", type=str, default=None,
                         help="Fetch a single scheme code instead of all schemes in fund_master")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.db.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(args.db) as conn:
        scheme_codes = get_scheme_codes(conn, args.scheme_code)
        if not scheme_codes:
            log.error("No scheme codes found — nothing to fetch.")
            return

        log.info("Fetching NAV data for %d scheme(s) in '%s' mode.", len(scheme_codes), args.mode)
        if args.mode == "latest":
            run_latest_mode(conn, scheme_codes)
        else:
            run_full_mode(conn, scheme_codes)


if __name__ == "__main__":
    main()
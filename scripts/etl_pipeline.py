#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
etl_pipeline.py
================
Extracts raw mutual fund CSV files, cleans them, and loads them into the
project's SQLite database (data/db/bluestock_mf.db).

Pipeline stages
---------------
1. Extract   -> read raw CSVs from data/raw/
2. Transform -> remove duplicates, handle missing values, standardize
                column names, convert date columns
3. Load      -> write cleaned CSVs to data/processed/ and load them into
                SQLite tables (fund_master, nav_history, fact_aum,
                investor_transactions)

Usage
-----
    python scripts/etl_pipeline.py
    python scripts/etl_pipeline.py --raw-dir data/raw --db data/db/bluestock_mf.db

Expected raw files (place under data/raw/):
    fund_master.csv
    nav_history.csv
    aum.csv
    investor_transactions.csv
"""

import argparse
import logging
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("etl_pipeline")

# --------------------------------------------------------------------------
# Default paths (overridable via CLI args)
# --------------------------------------------------------------------------
DEFAULT_RAW_DIR = Path("data/raw")
DEFAULT_PROCESSED_DIR = Path("data/processed")
DEFAULT_DB_PATH = Path("data/db/bluestock_mf.db")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lower-case, strip, and snake_case all column names."""
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"[^\w\s]", "", regex=True)
        .str.replace(r"\s+", "_", regex=True)
    )
    return df


def drop_duplicates_report(df: pd.DataFrame, subset=None, name: str = "") -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=subset)
    after = len(df)
    if before != after:
        log.info("  [%s] removed %d duplicate rows (%d -> %d)", name, before - after, before, after)
    return df


def report_missing(df: pd.DataFrame, name: str = "") -> None:
    missing = df.isna().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        log.info("  [%s] missing values:\n%s", name, missing.to_string())


def convert_dates(df: pd.DataFrame, columns) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
    return df


def read_raw_csv(raw_dir: Path, filename: str) -> pd.DataFrame:
    path = raw_dir / filename
    if not path.exists():
        log.warning("Raw file not found, skipping: %s", path)
        return pd.DataFrame()
    log.info("Extracting %s", path)
    return pd.read_csv(path)


# --------------------------------------------------------------------------
# Cleaning routines — one per dataset
# --------------------------------------------------------------------------
def clean_fund_master(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = standardize_columns(df)
    df = drop_duplicates_report(df, subset=["scheme_code"], name="fund_master")
    report_missing(df, "fund_master")

    # Fill sensible defaults / drop rows with no scheme identifier
    df = df.dropna(subset=["scheme_code"])
    for col in ["fund_house", "category", "plan", "scheme_name"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown").str.strip()
    if "expense_ratio" in df.columns:
        df["expense_ratio"] = pd.to_numeric(df["expense_ratio"], errors="coerce")
        df["expense_ratio"] = df["expense_ratio"].fillna(df["expense_ratio"].median())

    df["scheme_code"] = df["scheme_code"].astype(str).str.strip()
    return df.reset_index(drop=True)


def clean_nav_history(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = standardize_columns(df)
    df = convert_dates(df, ["date", "nav_date"])
    date_col = "date" if "date" in df.columns else "nav_date"

    df = drop_duplicates_report(df, subset=["scheme_code", date_col], name="nav_history")
    report_missing(df, "nav_history")

    df["nav"] = pd.to_numeric(df.get("nav"), errors="coerce")
    df = df.dropna(subset=["scheme_code", date_col, "nav"])
    df = df[df["nav"] > 0]  # drop non-positive / corrupt NAV entries

    df["scheme_code"] = df["scheme_code"].astype(str).str.strip()
    df = df.sort_values(["scheme_code", date_col]).reset_index(drop=True)
    df = df.rename(columns={date_col: "date"})
    return df


def clean_aum(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = standardize_columns(df)
    df = convert_dates(df, ["date", "as_of_date"])
    date_col = "date" if "date" in df.columns else "as_of_date"

    df = drop_duplicates_report(df, subset=["scheme_code", date_col], name="fact_aum")
    report_missing(df, "fact_aum")

    df["aum_cr"] = pd.to_numeric(df.get("aum_cr", df.get("aum")), errors="coerce")
    df = df.dropna(subset=["scheme_code", date_col, "aum_cr"])
    df["scheme_code"] = df["scheme_code"].astype(str).str.strip()
    df = df.rename(columns={date_col: "date"})
    return df.reset_index(drop=True)


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = standardize_columns(df)
    df = convert_dates(df, ["transaction_date", "date"])
    date_col = "transaction_date" if "transaction_date" in df.columns else "date"

    df = drop_duplicates_report(df, subset=None, name="investor_transactions")
    report_missing(df, "investor_transactions")

    df["amount"] = pd.to_numeric(df.get("amount"), errors="coerce")
    df = df.dropna(subset=["amount"])

    if "transaction_type" in df.columns:
        df["transaction_type"] = df["transaction_type"].str.strip().str.title()
        df["transaction_type"] = df["transaction_type"].replace(
            {"Sip": "SIP", "Lump Sum": "Lumpsum"}
        )
    df = df.rename(columns={date_col: "transaction_date"})
    return df.reset_index(drop=True)


# --------------------------------------------------------------------------
# Load
# --------------------------------------------------------------------------
def load_table(conn: sqlite3.Connection, df: pd.DataFrame, table: str) -> None:
    if df.empty:
        log.warning("Skipping load for '%s' — no data after cleaning", table)
        return
    df.to_sql(table, conn, if_exists="replace", index=False)
    log.info("Loaded %d rows into table '%s'", len(df), table)


def create_indexes(conn: sqlite3.Connection) -> None:
    stmts = [
        "CREATE INDEX IF NOT EXISTS idx_nav_scheme_date ON nav_history(scheme_code, date)",
        "CREATE INDEX IF NOT EXISTS idx_aum_scheme_date ON fact_aum(scheme_code, date)",
        "CREATE INDEX IF NOT EXISTS idx_fund_master_scheme ON fund_master(scheme_code)",
        "CREATE INDEX IF NOT EXISTS idx_txn_scheme ON investor_transactions(scheme_code)",
    ]
    for stmt in stmts:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError as exc:
            log.debug("Index creation skipped: %s", exc)
    conn.commit()


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def run_pipeline(raw_dir: Path, processed_dir: Path, db_path: Path) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("=== Stage 1/3: Extract ===")
    raw_fund_master = read_raw_csv(raw_dir, "fund_master.csv")
    raw_nav_history = read_raw_csv(raw_dir, "nav_history.csv")
    raw_aum = read_raw_csv(raw_dir, "aum.csv")
    raw_transactions = read_raw_csv(raw_dir, "investor_transactions.csv")

    log.info("=== Stage 2/3: Transform / Clean ===")
    fund_master = clean_fund_master(raw_fund_master)
    nav_history = clean_nav_history(raw_nav_history)
    fact_aum = clean_aum(raw_aum)
    investor_transactions = clean_transactions(raw_transactions)

    datasets = {
        "fund_master": fund_master,
        "nav_history": nav_history,
        "fact_aum": fact_aum,
        "investor_transactions": investor_transactions,
    }

    log.info("=== Stage 3/3: Load ===")
    for name, df in datasets.items():
        if df.empty:
            continue
        out_path = processed_dir / f"{name}.csv"
        df.to_csv(out_path, index=False)
        log.info("Wrote cleaned file: %s (%d rows)", out_path, len(df))

    with sqlite3.connect(db_path) as conn:
        for name, df in datasets.items():
            load_table(conn, df, name)
        create_indexes(conn)

    log.info("ETL pipeline completed successfully. Database: %s", db_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mutual Fund ETL Pipeline")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR,
                         help="Directory containing raw CSV files")
    parser.add_argument("--processed-dir", type=Path, default=DEFAULT_PROCESSED_DIR,
                         help="Directory to write cleaned CSV files")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH,
                         help="Path to the SQLite database file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_pipeline(args.raw_dir, args.processed_dir, args.db)


if __name__ == "__main__":
    main()
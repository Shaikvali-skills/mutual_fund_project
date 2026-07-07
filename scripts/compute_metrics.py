#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_metrics.py
===================
Computes financial performance and risk metrics for every scheme in
`nav_history` and writes the results into the `scheme_performance` table.

Metrics computed
-----------------
    Daily Returns          day-over-day % change in NAV
    CAGR                   compounded annual growth rate
    Volatility             annualized standard deviation of daily returns
    Sharpe Ratio           risk-adjusted return vs. the risk-free rate
    Sortino Ratio          risk-adjusted return using downside deviation
    Beta                   sensitivity to the benchmark (e.g. Nifty 50)
    Alpha                  excess return over the benchmark (CAPM alpha)
    Tracking Error         std. dev. of (fund return - benchmark return)
    Maximum Drawdown       largest peak-to-trough decline
    VaR (95%)              historical Value at Risk at 95% confidence
    CVaR (95%)             expected loss beyond the VaR threshold

Benchmark data
--------------
Provide a benchmark CSV with columns `date,close` (e.g. Nifty 50 daily
closing values) via --benchmark. If omitted, Beta / Alpha / Tracking
Error are skipped and reported as NaN.

Usage
-----
    python scripts/compute_metrics.py
    python scripts/compute_metrics.py --db data/db/bluestock_mf.db \\
        --benchmark data/raw/nifty50.csv --risk-free-rate 0.07
"""

import argparse
import logging
import sqlite3
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("compute_metrics")

DEFAULT_DB_PATH = Path("data/db/bluestock_mf.db")
TRADING_DAYS_PER_YEAR = 252
VAR_CONFIDENCE = 0.95
MIN_OBSERVATIONS = 30  # minimum NAV points required to compute metrics


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
def load_nav_history(conn: sqlite3.Connection) -> pd.DataFrame:
    df = pd.read_sql("SELECT scheme_code, date, nav FROM nav_history", conn)
    df["date"] = pd.to_datetime(df["date"])
    df["scheme_code"] = df["scheme_code"].astype(str)
    return df.sort_values(["scheme_code", "date"])


def load_benchmark(path: Optional[Path]) -> Optional[pd.Series]:
    """Return a daily-return Series indexed by date, or None if unavailable."""
    if path is None or not Path(path).exists():
        if path:
            log.warning("Benchmark file not found: %s — Beta/Alpha/Tracking Error will be NaN.", path)
        return None
    bdf = pd.read_csv(path)
    bdf.columns = [c.strip().lower() for c in bdf.columns]
    if "date" not in bdf.columns or "close" not in bdf.columns:
        log.warning("Benchmark file must have 'date' and 'close' columns. Skipping benchmark metrics.")
        return None
    bdf["date"] = pd.to_datetime(bdf["date"])
    bdf = bdf.sort_values("date").set_index("date")
    returns = bdf["close"].pct_change().dropna()
    returns.name = "benchmark_return"
    return returns


# --------------------------------------------------------------------------
# Metric calculations
# --------------------------------------------------------------------------
def compute_cagr(nav_series: pd.Series, dates: pd.Series) -> float:
    start_nav, end_nav = nav_series.iloc[0], nav_series.iloc[-1]
    days = (dates.iloc[-1] - dates.iloc[0]).days
    if days <= 0 or start_nav <= 0:
        return np.nan
    years = days / 365.25
    return (end_nav / start_nav) ** (1 / years) - 1


def compute_annualized_return(daily_returns: pd.Series) -> float:
    mean_daily = daily_returns.mean()
    return (1 + mean_daily) ** TRADING_DAYS_PER_YEAR - 1


def compute_volatility(daily_returns: pd.Series) -> float:
    return daily_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)


def compute_sharpe(daily_returns: pd.Series, risk_free_rate: float) -> float:
    ann_return = compute_annualized_return(daily_returns)
    vol = compute_volatility(daily_returns)
    if vol == 0 or np.isnan(vol):
        return np.nan
    return (ann_return - risk_free_rate) / vol


def compute_sortino(daily_returns: pd.Series, risk_free_rate: float) -> float:
    ann_return = compute_annualized_return(daily_returns)
    downside = daily_returns[daily_returns < 0]
    if downside.empty:
        return np.nan
    downside_dev = downside.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    if downside_dev == 0 or np.isnan(downside_dev):
        return np.nan
    return (ann_return - risk_free_rate) / downside_dev


def compute_max_drawdown(nav_series: pd.Series) -> float:
    cumulative_max = nav_series.cummax()
    drawdown = (nav_series - cumulative_max) / cumulative_max
    return drawdown.min()


def compute_var_cvar(daily_returns: pd.Series, confidence: float = VAR_CONFIDENCE):
    """Historical VaR/CVaR at the given confidence level (returned as positive loss %)."""
    if daily_returns.empty:
        return np.nan, np.nan
    alpha = 1 - confidence
    var_threshold = daily_returns.quantile(alpha)
    tail_losses = daily_returns[daily_returns <= var_threshold]
    cvar = tail_losses.mean() if not tail_losses.empty else var_threshold
    return -var_threshold, -cvar  # express as positive loss magnitudes


def compute_beta_alpha_tracking_error(fund_returns: pd.Series, benchmark_returns: pd.Series,
                                       risk_free_rate: float):
    """Align fund and benchmark returns by date and compute CAPM beta/alpha + tracking error."""
    aligned = pd.concat([fund_returns, benchmark_returns], axis=1, join="inner").dropna()
    if len(aligned) < MIN_OBSERVATIONS:
        return np.nan, np.nan, np.nan

    fund_r = aligned.iloc[:, 0]
    bench_r = aligned.iloc[:, 1]

    covariance = np.cov(fund_r, bench_r)[0, 1]
    variance = np.var(bench_r, ddof=1)
    beta = covariance / variance if variance != 0 else np.nan

    ann_fund_return = compute_annualized_return(fund_r)
    ann_bench_return = compute_annualized_return(bench_r)
    alpha = ann_fund_return - (risk_free_rate + beta * (ann_bench_return - risk_free_rate)) \
        if not np.isnan(beta) else np.nan

    tracking_error = (fund_r - bench_r).std() * np.sqrt(TRADING_DAYS_PER_YEAR)

    return beta, alpha, tracking_error


# --------------------------------------------------------------------------
# Per-scheme computation
# --------------------------------------------------------------------------
def compute_scheme_metrics(scheme_code: str, scheme_df: pd.DataFrame,
                            benchmark_returns: Optional[pd.Series],
                            risk_free_rate: float) -> Optional[dict]:
    scheme_df = scheme_df.sort_values("date").drop_duplicates(subset="date")
    if len(scheme_df) < MIN_OBSERVATIONS:
        log.warning("Scheme %s skipped — only %d NAV observations (need >= %d).",
                    scheme_code, len(scheme_df), MIN_OBSERVATIONS)
        return None

    nav = scheme_df.set_index("date")["nav"]
    daily_returns = nav.pct_change().dropna()

    cagr = compute_cagr(nav, scheme_df["date"])
    volatility = compute_volatility(daily_returns)
    sharpe = compute_sharpe(daily_returns, risk_free_rate)
    sortino = compute_sortino(daily_returns, risk_free_rate)
    max_dd = compute_max_drawdown(nav)
    var_95, cvar_95 = compute_var_cvar(daily_returns)

    beta = alpha = tracking_error = np.nan
    if benchmark_returns is not None:
        beta, alpha, tracking_error = compute_beta_alpha_tracking_error(
            daily_returns, benchmark_returns, risk_free_rate
        )

    return {
        "scheme_code": scheme_code,
        "as_of_date": scheme_df["date"].max().strftime("%Y-%m-%d"),
        "cagr": round(cagr, 6) if pd.notna(cagr) else None,
        "volatility": round(volatility, 6) if pd.notna(volatility) else None,
        "sharpe_ratio": round(sharpe, 6) if pd.notna(sharpe) else None,
        "sortino_ratio": round(sortino, 6) if pd.notna(sortino) else None,
        "beta": round(beta, 6) if pd.notna(beta) else None,
        "alpha": round(alpha, 6) if pd.notna(alpha) else None,
        "tracking_error": round(tracking_error, 6) if pd.notna(tracking_error) else None,
        "max_drawdown": round(max_dd, 6) if pd.notna(max_dd) else None,
        "var_95": round(var_95, 6) if pd.notna(var_95) else None,
        "cvar_95": round(cvar_95, 6) if pd.notna(cvar_95) else None,
    }


# --------------------------------------------------------------------------
# Persist results
# --------------------------------------------------------------------------
def save_scheme_performance(conn: sqlite3.Connection, records: list) -> None:
    if not records:
        log.warning("No scheme performance records to save.")
        return
    df = pd.DataFrame(records)
    df.to_sql("scheme_performance", conn, if_exists="replace", index=False)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_perf_scheme ON scheme_performance(scheme_code)"
    )
    conn.commit()
    log.info("Saved performance metrics for %d schemes into 'scheme_performance'.", len(df))


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def run(db_path: Path, benchmark_path: Optional[Path], risk_free_rate: float) -> None:
    with sqlite3.connect(db_path) as conn:
        nav_df = load_nav_history(conn)
        if nav_df.empty:
            log.error("nav_history table is empty or missing. Run etl_pipeline.py / "
                      "live_nav_fetch.py first.")
            return

        benchmark_returns = load_benchmark(benchmark_path)

        records = []
        scheme_codes = nav_df["scheme_code"].unique()
        log.info("Computing performance metrics for %d schemes...", len(scheme_codes))

        for i, code in enumerate(scheme_codes, start=1):
            scheme_df = nav_df[nav_df["scheme_code"] == code]
            result = compute_scheme_metrics(code, scheme_df, benchmark_returns, risk_free_rate)
            if result:
                records.append(result)
            if i % 50 == 0:
                log.info("  ... processed %d/%d schemes", i, len(scheme_codes))

        save_scheme_performance(conn, records)
        log.info("Metric computation complete.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute mutual fund performance & risk metrics")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH,
                         help="Path to the SQLite database file")
    parser.add_argument("--benchmark", type=Path, default=None,
                         help="CSV file with 'date,close' columns for benchmark (e.g. Nifty 50)")
    parser.add_argument("--risk-free-rate", type=float, default=0.07,
                         help="Annual risk-free rate used in Sharpe/Sortino/Alpha (default 0.07 = 7%%)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args.db, args.benchmark, args.risk_free_rate)


if __name__ == "__main__":
    main()
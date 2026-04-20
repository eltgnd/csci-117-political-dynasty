"""
precompute_indicators.py
========================

Iterates over every (province, year) combination present in political_dynasty.csv
and computes all four dynastic indicators:

    HHI  — Herfindahl-Hirschman Index (seat concentration)
    CGC  — Clan Gini Coefficient (inequality of network influence)
    CCD  — Clan Connectivity Density (network cohesion)
    ACC  — Aggregate Clan Connectivity (internal clan resilience)

Output
------
Writes a single CSV to data/precomputed_indicators.csv with columns:
    Province, Year, HHI_Score, CGC_Score, CCD_Score, ACC_Score

The Streamlit app reads this file directly.

Options (edit the constants below)
-----------------------------------
DATA_PATH      — path to the raw dataset
OUTPUT_PATH    — where to write the precomputed CSV
ELECTION_YEARS — restrict computation to these years only (set to None to use all)
N_WORKERS      — number of parallel processes (set to 1 to disable parallelism)
"""

import os
import time
import logging
import argparse
import multiprocessing
from functools import partial
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from backend_math import (
    get_hhi_index_per_province,
    get_cgc_per_province,
    get_ccd_per_province,
    get_acc_per_province,
)

# ── Configuration ────────────────────────────────────────────────────────────────

DATA_PATH      = "political_dynasty.csv"
OUTPUT_DIR     = "data"
OUTPUT_PATH    = os.path.join(OUTPUT_DIR, "precomputed_indicators.csv")
ELECTION_YEARS = [2004, 2007, 2010, 2013, 2016, 2019, 2022, 2025]  # set to None for all
N_WORKERS      = max(1, multiprocessing.cpu_count() - 1)

# ── Logging ──────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Data Loading ─────────────────────────────────────────────────────────────────

def load_and_normalize(path: str) -> pd.DataFrame:
    log.info(f"Loading dataset from '{path}' …")
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.title()

    if "Full Name" not in df.columns:
        df["Full Name"] = (
            df["First Name"].fillna("").str.strip() + " "
            + df["Middle Name"].fillna("").str.strip() + " "
            + df["Last Name"].fillna("").str.strip()
        ).str.strip()

    df["Year"]            = pd.to_numeric(df["Year"],            errors="coerce").astype("Int64")
    df["Community"]       = pd.to_numeric(df["Community"],       errors="coerce").fillna(-1).astype(int)
    df["Position Weight"] = pd.to_numeric(df["Position Weight"], errors="coerce").fillna(0)
    df["Middle Name"]     = df["Middle Name"].fillna("")

    log.info(f"  {len(df):,} records | {df['Province'].nunique()} provinces | years: {sorted(df['Year'].dropna().unique().tolist())}")
    return df


# ── Per-year computation ─────────────────────────────────────────────────────────

def compute_year(year: int, df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all four indicators for every province for a single year.
    Returns a DataFrame with columns: Province, Year, HHI_Score, CGC_Score, CCD_Score, ACC_Score
    """
    try:
        hhi = get_hhi_index_per_province(df, year).rename(columns={"HHI_Score": "HHI_Score"})
        cgc = get_cgc_per_province(df, year)
        ccd = get_ccd_per_province(df, year)
        acc = get_acc_per_province(df, year)

        merged = (
            hhi
            .merge(cgc, on="Province", how="outer")
            .merge(ccd, on="Province", how="outer")
            .merge(acc, on="Province", how="outer")
        )
        merged["Year"] = year
        return merged[["Province", "Year", "HHI_Score", "CGC_Score", "CCD_Score", "ACC_Score"]]

    except Exception as exc:
        log.warning(f"  [year={year}] computation failed: {exc}")
        return pd.DataFrame(columns=["Province", "Year", "HHI_Score", "CGC_Score", "CCD_Score", "ACC_Score"])


# ── Main ─────────────────────────────────────────────────────────────────────────

def main(args):
    t_start = time.time()

    # Load data
    df = load_and_normalize(args.data_path)

    # Determine which years to process
    data_years = sorted(df["Year"].dropna().unique().tolist())
    if ELECTION_YEARS is not None:
        years = [y for y in ELECTION_YEARS if y in data_years]
    else:
        years = data_years

    if not years:
        log.error("No valid election years found. Check ELECTION_YEARS and your dataset.")
        return

    log.info(f"Computing indicators for {len(years)} year(s): {years}")
    log.info(f"Using {args.workers} worker(s).")

    # Compute — parallel or sequential
    frames = []
    if args.workers > 1:
        worker_fn = partial(compute_year, df=df)
        with multiprocessing.Pool(processes=args.workers) as pool:
            results = list(tqdm(
                pool.imap(worker_fn, years),
                total=len(years),
                desc="Years processed",
                unit="year",
            ))
        frames = results
    else:
        for year in tqdm(years, desc="Years processed", unit="year"):
            log.info(f"  Processing {year} …")
            frames.append(compute_year(year, df))

    # Combine and sort
    result_df = pd.concat([f for f in frames if not f.empty], ignore_index=True)
    result_df = result_df.sort_values(["Province", "Year"]).reset_index(drop=True)

    # Round scores for readability
    for col in ["HHI_Score", "CGC_Score", "CCD_Score", "ACC_Score"]:
        result_df[col] = result_df[col].round(6)

    # Write output
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    result_df.to_csv(args.output_path, index=False)

    elapsed = time.time() - t_start
    log.info(f"✓ Done in {elapsed:.1f}s — {len(result_df):,} rows written to '{args.output_path}'")
    log.info(f"  Provinces: {result_df['Province'].nunique()} | Years: {sorted(result_df['Year'].unique().tolist())}")


# ── CLI ──────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Precompute dynastic indicators for the Philippine Clan Watch Dashboard."
    )
    parser.add_argument(
        "--data-path",   default=DATA_PATH,   help=f"Path to raw CSV (default: {DATA_PATH})"
    )
    parser.add_argument(
        "--output-path", default=OUTPUT_PATH,  help=f"Output CSV path (default: {OUTPUT_PATH})"
    )
    parser.add_argument(
        "--output-dir",  default=OUTPUT_DIR,   help=f"Output directory (default: {OUTPUT_DIR})"
    )
    parser.add_argument(
        "--workers",     default=N_WORKERS, type=int,
        help=f"Parallel workers (default: {N_WORKERS}, set 1 to disable)"
    )
    args = parser.parse_args()
    main(args)
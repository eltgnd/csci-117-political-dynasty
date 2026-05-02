"""
precompute_community_labels.py
==============================
Run once (or after every data update) to generate the clan label lookup CSV:

    python precompute_community_labels.py

Output
------
data/community_labels.csv  with columns:
    Province, Community, Label

The Streamlit app reads this file directly instead of recomputing labels
at startup, which eliminates the groupby + string-frequency computation
from the critical path.
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path

import pandas as pd

# ── Configuration ────────────────────────────────────────────────────────────────

DATA_PATH   = "data/political_dynasty.csv"
OUTPUT_DIR  = "data"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "community_labels.csv")

# ── Logging ──────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Data loading ─────────────────────────────────────────────────────────────────

def load_and_normalize(path: str) -> pd.DataFrame:
    log.info(f"Loading dataset from '{path}' …")
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.title()

    df["Year"]        = pd.to_numeric(df["Year"],        errors="coerce")
    df["Community"]   = pd.to_numeric(df["Community"],   errors="coerce").fillna(-1).astype(int)
    df["Last Name"]   = df["Last Name"].fillna("").astype(str).str.strip()
    df["Middle Name"] = df["Middle Name"].fillna("").astype(str).str.strip()

    log.info(
        f"  {len(df):,} records | "
        f"{df['Province'].nunique()} provinces | "
        f"{df['Community'].nunique()} unique community IDs"
    )
    return df


def compute_label(group: pd.DataFrame) -> str:
    """
    Reproduce the exact label logic from data_loader.get_community_label_map
    for a single (province, community) group.
    """
    last_names   = group["Last Name"].replace("", pd.NA).dropna().astype(str)
    middle_names = group["Middle Name"].replace("", pd.NA).dropna().astype(str)
    middle_names = middle_names[middle_names.str.strip() != ""]

    combined = pd.concat([last_names, middle_names], ignore_index=True)

    if combined.empty:
        return str(group["Community"].iloc[0])

    freq  = combined.value_counts()
    mode1 = freq.index[0]

    mode2_candidates = freq.index[freq.index != mode1]
    if len(mode2_candidates) > 0:
        return f"{mode1}-{mode2_candidates[0]}"
    return mode1


def compute_all_labels(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Computing clan labels for all (Province, Community) groups …")
    t0 = time.time()

    rows = []
    groups = list(df.groupby(["Province", "Community"]))
    total  = len(groups)

    for i, ((province, community), group) in enumerate(groups, 1):
        label = compute_label(group)
        rows.append({"Province": province, "Community": community, "Label": label})
        if i % 500 == 0 or i == total:
            log.info(f"  {i:,} / {total:,} groups processed …")

    result = pd.DataFrame(rows).sort_values(["Province", "Community"]).reset_index(drop=True)
    elapsed = time.time() - t0
    log.info(f"  Done — {len(result):,} labels computed in {elapsed:.1f}s")
    return result


# ── Main ─────────────────────────────────────────────────────────────────────────

def main(args):
    t_start = time.time()

    df     = load_and_normalize(args.data_path)
    labels = compute_all_labels(df)

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    labels.to_csv(args.output_path, index=False)

    elapsed = time.time() - t_start
    log.info(f"✓ Written {len(labels):,} rows → '{args.output_path}'  ({elapsed:.1f}s total)")

    # Quick sanity preview
    log.info("Sample output:")
    print(labels.head(10).to_string(index=False))


# ── CLI ──────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Precompute clan (community) labels for the Philippine Clan Watch Dashboard."
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
    args = parser.parse_args()
    main(args)
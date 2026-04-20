"""
data_loader.py
All @st.cache_data helpers for loading and aggregating data.

Precomputed-first pattern:
  - If data/precomputed_indicators.csv exists → read instantly from it.
  - If missing → fall back to live computation and show a warning banner.
"""

import os

import pandas as pd
import streamlit as st

from config import DATA_PATH, PRECOMPUTED_PATH, ELECTION_YEARS, ISLAND_GROUPS
from backend_math import (
    get_hhi_index_per_province,
    get_cgc_per_province,
    get_ccd_per_province,
    get_acc_per_province,
    get_provincial_indicator_trend,
)


# ── Primary data load ────────────────────────────────────────────────────────────

@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
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
    return df


@st.cache_data
def load_precomputed() -> pd.DataFrame | None:
    if not os.path.exists(PRECOMPUTED_PATH):
        st.warning(
            f"⚠️ Precomputed indicators not found at `{PRECOMPUTED_PATH}`. "
            "Run `python precompute_indicators.py` once to generate it. "
            "The app will fall back to on-demand computation (slower).",
            icon="⚠️",
        )
        return None
    df = pd.read_csv(PRECOMPUTED_PATH)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    return df


# ── Lookup helpers ───────────────────────────────────────────────────────────────

@st.cache_data
def get_community_label_map(df: pd.DataFrame) -> dict:
    """
    Map (province, community_int) → "{mode1}-{mode2}" label.

    mode1 = most frequent value across the union of Last Name + Middle Name
            for that (province, community) group.
    mode2 = second most frequent value (different from mode1).

    Middle names that are empty/NaN are excluded before counting.
    Falls back to a single name if there is no second mode.
    """
    result = {}
    for (province, community), group in df.groupby(["Province", "Community"]):
        # Combine Last Name and Middle Name into one frequency series,
        # filtering out empty/null strings from Middle Name.
        last_names   = group["Last Name"].dropna().astype(str)
        middle_names = (
            group["Middle Name"]
            .dropna()
            .astype(str)
            .pipe(lambda s: s[s.str.strip() != ""])
        )
        combined = pd.concat([last_names, middle_names], ignore_index=True)

        if combined.empty:
            result[(province, community)] = str(community)
            continue

        freq = combined.value_counts()

        mode1 = freq.index[0]
        # mode2: next most frequent value that is different from mode1
        mode2_candidates = freq.index[freq.index != mode1]
        if len(mode2_candidates) > 0:
            label = f"{mode1}-{mode2_candidates[0]}"
        else:
            label = mode1

        result[(province, community)] = label

    return result


@st.cache_data
def get_available_years(df: pd.DataFrame) -> list:
    return sorted(df["Year"].dropna().unique().tolist())


@st.cache_data
def get_election_years_in_data(df: pd.DataFrame) -> list:
    avail = set(get_available_years(df))
    return [y for y in ELECTION_YEARS if y in avail]


# ── Province-level indicators ────────────────────────────────────────────────────

@st.cache_data
def get_indicators_for_province(
    precomp: pd.DataFrame | None,
    df: pd.DataFrame,
    province: str,
    years: tuple,
) -> pd.DataFrame:
    """
    [Year, HHI, CGC, CCD, ACC] for one province across requested years.
    Source: precomputed CSV if available, else live computation.
    """
    if precomp is not None:
        prov_df = precomp[precomp["Province"] == province].copy()
        prov_df = prov_df[prov_df["Year"].isin(years)].sort_values("Year")
        if not prov_df.empty:
            return prov_df.rename(columns={
                "HHI_Score": "HHI", "CGC_Score": "CGC",
                "CCD_Score": "CCD", "ACC_Score": "ACC",
            })[["Year", "HHI", "CGC", "CCD", "ACC"]].reset_index(drop=True)

    return get_provincial_indicator_trend(df, province, list(years))


@st.cache_data
def get_indicators_single_year(
    precomp: pd.DataFrame | None,
    df: pd.DataFrame,
    province: str,
    year: int,
) -> dict:
    """
    Return {HHI, CGC, CCD, ACC} for one province/year as a plain dict.
    Used for the KPI metric row.
    """
    trend = get_indicators_for_province(precomp, df, province, (year,))
    if trend.empty:
        return {"HHI": 0.0, "CGC": 0.0, "CCD": 0.0, "ACC": 0.0}
    row = trend.iloc[0]
    return {k: float(row.get(k, 0.0)) for k in ["HHI", "CGC", "CCD", "ACC"]}
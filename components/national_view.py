"""
components/national_view.py

Map approach: the GeoJSON is municipality-level. Plotly's choropleth does
one-to-one feature matching, so matching on province name only renders ONE
municipality per province. The fix: inject a unique _fid on every feature,
build a municipality-row DataFrame with each municipality's province score,
then match on _fid. Every municipality gets colored by its province's score.
"""

import copy
import json
import os
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import (
    GEOJSON_PATH,
    INDICATOR_COLORS,
    INDICATOR_LABELS,
    INDICATOR_HELP,
    INDICATOR_SCORE_COL,
    DF_TO_GEOJSON,
    DF_TO_GEOJSON_FALLBACK,
)
from data_loader import (
    get_national_indicators,
    get_election_years_in_data,
    get_island_group_trend,
    get_hhi_for_year,
)


# ── Normaliser (shared) ───────────────────────────────────────────────────────────

def _normalize(name: str) -> str:
    """Strip everything except lowercase letters and digits."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


# ── GeoJSON load + preparation ────────────────────────────────────────────────────

@st.cache_data
def _load_and_prep_geojson() -> tuple[dict | None, str | None, str | None]:
    """
    Load the GeoJSON once, inject a unique _fid property into every feature,
    and auto-detect:
      prov_key  — property holding the province name  (e.g. ADM2_EN)
      muni_key  — property holding the municipality name (e.g. ADM3_EN / name)

    Returns (geojson_with_fids, prov_key, muni_key).
    All three can be None if the file is missing.
    """
    if not os.path.exists(GEOJSON_PATH):
        return None, None, None

    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    features = geojson.get("features", [])
    if not features:
        return geojson, None, None

    # ── Detect province key ───────────────────────────────────────────────────────
    # Strategy: count unique values per string property across all features.
    # The province key has ~70-85 unique values; municipality key has ~1 500+.
    props_sample = [f["properties"] for f in features]
    all_str_keys = [
        k for k, v in props_sample[0].items() if isinstance(v, str)
    ]

    cardinality: dict[str, int] = {}
    for k in all_str_keys:
        cardinality[k] = len({f["properties"].get(k, "") for f in features if f["properties"].get(k)})

    # Named candidates take priority over cardinality guessing
    PROV_CANDIDATES = ["ADM2_EN", "adm1_en", "NAME_1", "PROVINCE", "province",
                        "Province", "PROV_NAME", "prov_name"]
    MUNI_CANDIDATES = ["ADM3_EN", "adm2_en", "NAME_2", "name", "MUNICIPALITY",
                        "municipality", "MUN_NAME", "mun_name"]

    prov_key = next((k for k in PROV_CANDIDATES if k in cardinality), None)
    muni_key = next((k for k in MUNI_CANDIDATES if k in cardinality), None)

    # Cardinality fallback if named keys not found
    if not prov_key:
        # Province: lowest cardinality that plausibly covers ≥30 distinct values
        candidates = sorted(
            [(k, n) for k, n in cardinality.items() if 30 <= n <= 200],
            key=lambda x: x[1],
        )
        prov_key = candidates[0][0] if candidates else None

    if not muni_key:
        # Municipality: highest cardinality
        candidates = sorted(cardinality.items(), key=lambda x: x[1], reverse=True)
        # Exclude prov_key from consideration
        candidates = [(k, n) for k, n in candidates if k != prov_key]
        muni_key = candidates[0][0] if candidates else None

    # ── Inject _fid into every feature ───────────────────────────────────────────
    for i, feat in enumerate(features):
        feat["properties"]["_fid"] = str(i)

    return geojson, prov_key, muni_key


# ── Score lookup builder ──────────────────────────────────────────────────────────

def _build_norm_score_map(nat_df: pd.DataFrame, score_col: str) -> dict[str, float]:
    """
    Build {normalized_province_name: score} from the national indicator DataFrame.

    Both the DF province name (after DF_TO_GEOJSON mapping) and the raw DF
    province name are stored under their normalized forms so fuzzy matching
    from GeoJSON province values always finds the right score.
    """
    norm_score: dict[str, float] = {}

    for _, row in nat_df.iterrows():
        prov = row["Province"].strip()
        score = row[score_col]
        upper = prov.upper()

        # Normalised DF province name as-is
        norm_score[_normalize(prov)] = score

        # Normalised GeoJSON-mapped name (handles COTABATO→NorthCotabato, etc.)
        geo_name = DF_TO_GEOJSON.get(upper) or DF_TO_GEOJSON_FALLBACK.get(upper)
        if geo_name:
            norm_score[_normalize(geo_name)] = score

    return norm_score


# ── Municipality-level DataFrame builder ──────────────────────────────────────────

def _build_muni_df(
    geojson: dict,
    prov_key: str,
    muni_key: str | None,
    norm_score: dict[str, float],
    score_col: str,
) -> pd.DataFrame:
    """
    One row per GeoJSON feature (municipality).
    Columns: _fid, Province, Municipality, <score_col>

    Each municipality inherits the indicator score of its province.
    Features whose province cannot be matched to a score are omitted
    (they appear transparent on the map rather than crashing Plotly).
    """
    rows = []
    for feat in geojson["features"]:
        fid       = feat["properties"]["_fid"]
        prov_raw  = feat["properties"].get(prov_key, "") if prov_key else ""
        muni_name = feat["properties"].get(muni_key, fid) if muni_key else fid

        norm_prov = _normalize(prov_raw)
        score     = norm_score.get(norm_prov)

        rows.append({
            "_fid":         fid,
            "Province":     prov_raw,
            "Municipality": muni_name,
            score_col:      score,
        })

    df = pd.DataFrame(rows)
    return df[df[score_col].notna()].copy()


# ── 1. Interactive Indicator Choropleth ──────────────────────────────────────────
def _render_region_bar(
    df: pd.DataFrame,
    precomp: pd.DataFrame | None,
    nat_df: pd.DataFrame,
    score_col: str,
    indicator: str,
    year: int,
) -> None:
    """Bar chart of mean indicator score per region, sorted descending."""
    # Join region from the main df (which has a Region column per province)
    prov_region = (
        df[["Province", "Region"]]
        .drop_duplicates(subset=["Province"])
        .copy()
    )
    # Normalise province names to match nat_df
    merged = nat_df.merge(prov_region, on="Province", how="left")

    if "Region" not in merged.columns or merged["Region"].isna().all():
        st.info("No Region column found in the dataset. Cannot render region bar chart.")
        return

    region_df = (
        merged.groupby("Region")[score_col]
        .mean()
        .reset_index()
        .rename(columns={score_col: f"Mean {indicator}"})
        .sort_values(f"Mean {indicator}", ascending=False)
    )

    fig = px.bar(
        region_df,
        x=f"Mean {indicator}",
        y="Region",
        orientation="h",
        title=f"Mean {INDICATOR_LABELS[indicator]} by Region ({year})",
        color=f"Mean {indicator}",
        color_continuous_scale="Reds",
        labels={f"Mean {indicator}": indicator},
    )
    fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
    st.plotly_chart(fig, width='stretch')

def _render_choropleth(
    df: pd.DataFrame, precomp: pd.DataFrame | None, year: int
) -> None:
    st.subheader("Dynastic Concentration Map")

    # ── View mode selector ────────────────────────────────────────────────────────
    view_mode = st.radio(
        "View mode",
        options=["🗺️ Map", "📊 Bar Chart by Region"],
        horizontal=True,
        key="nat_view_mode_radio",
    )

    # ── Indicator selector ────────────────────────────────────────────────────────
    indicator = st.radio(
        "Select indicator",
        options=list(INDICATOR_LABELS.keys()),
        format_func=lambda k: INDICATOR_LABELS[k],
        horizontal=True,
        key="nat_choro_radio",
    )
    st.caption(INDICATOR_HELP[indicator])

    nat_df    = get_national_indicators(precomp, df, year)
    score_col = INDICATOR_SCORE_COL[indicator]

    # ── Bar chart mode ────────────────────────────────────────────────────────────
    if view_mode == "📊 Bar Chart by Region":
        _render_region_bar(df, precomp, nat_df, score_col, indicator, year)
        return

    # ── Map mode ──────────────────────────────────────────────────────────────────
    geojson, prov_key, muni_key = _load_and_prep_geojson()

    if geojson is None:
        st.info(
            f"`{GEOJSON_PATH}` not found. "
            "Place your Philippine province GeoJSON in the `data/` folder. "
            "Showing a ranked bar chart instead."
        )
        _render_bar_fallback(nat_df, score_col, indicator, year)
        return

    if not prov_key:
        st.warning(
            "Could not detect a province property in the GeoJSON. "
            "Check that the file has a property named `ADM2_EN`, `NAME_2`, or `PROVINCE`."
        )
        _render_bar_fallback(nat_df, score_col, indicator, year)
        return

    norm_score = _build_norm_score_map(nat_df, score_col)
    muni_df    = _build_muni_df(geojson, prov_key, muni_key, norm_score, score_col)

    if muni_df.empty:
        st.warning(
            "No municipalities could be matched to province scores. "
            f"Detected province key: `{prov_key}`. "
            "Update `DF_TO_GEOJSON` in `config.py` if province names differ."
        )
        _render_bar_fallback(nat_df, score_col, indicator, year)
        return

    # ── Debug expander ────────────────────────────────────────────────────────────
    all_prov_vals = {
        feat["properties"].get(prov_key, "")
        for feat in geojson["features"]
        if feat["properties"].get(prov_key)
    }
    unmatched = [p for p in sorted(all_prov_vals) if _normalize(p) not in norm_score]
    if unmatched:
        with st.expander(f"⚠️ {len(unmatched)} GeoJSON province value(s) not matched — click to see"):
            st.write(unmatched)
            st.caption("Add these to `DF_TO_GEOJSON` in `config.py`.")

    coverage = len(muni_df) / max(len(geojson["features"]), 1) * 100
    st.caption(f"Map coverage: {len(muni_df):,} / {len(geojson['features']):,} municipalities matched ({coverage:.0f}%)")

    # ── Build province-level score lookup for the hover tooltip ──────────────────
    # Map each GeoJSON province string → DF province name (for clean display)
    geo_to_df_prov: dict[str, str] = {}
    for _, row in nat_df.iterrows():
        p     = row["Province"].strip()
        norm  = _normalize(p)
        geo_to_df_prov[norm] = p
        upper = p.upper()
        geo_name = DF_TO_GEOJSON.get(upper) or DF_TO_GEOJSON_FALLBACK.get(upper)
        if geo_name:
            geo_to_df_prov[_normalize(geo_name)] = p

    muni_df = muni_df.copy()
    muni_df["Province (DF)"] = muni_df["Province"].apply(
        lambda p: geo_to_df_prov.get(_normalize(p), p)
    )
    # Round score for cleaner tooltip
    muni_df[score_col] = muni_df[score_col].round(4)

    # ── Choropleth: municipality geometry, province-level hover ───────────────────
    # hover_name="Province (DF)"  → province name as bold tooltip header
    # hover_data excludes Municipality and _fid → hover shows province info only
    # marker_line_width=0         → no borders between municipalities within a province
    fig = px.choropleth(
        muni_df,
        geojson=geojson,
        locations="_fid",
        featureidkey="properties._fid",
        color=score_col,
        color_continuous_scale="Reds",
        title=f"{INDICATOR_LABELS[indicator]} by Province ({year})",
        labels={score_col: indicator, "_fid": ""},
        hover_name="Province (DF)",
        hover_data={
            score_col:      True,
            "Province":     False,   # raw GeoJSON name — hide
            "Province (DF)": False,  # already in hover_name
            "Municipality": False,   # suppress — province-level hover only
            "_fid":         False,
        },
    )
    fig.update_traces(marker_line_width=0)   # remove inter-municipality borders
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, width='stretch')



def _render_bar_fallback(nat_df, score_col, indicator, year):
    fig = px.bar(
        nat_df.sort_values(score_col, ascending=False),
        x="Province", y=score_col,
        title=f"{INDICATOR_LABELS[indicator]} by Province ({year})",
        color=score_col, color_continuous_scale="Reds",
        labels={score_col: indicator},
    )
    fig.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False)
    st.plotly_chart(fig, width='stretch')


# ── 2. Democracy Scatterplot ─────────────────────────────────────────────────────

def _render_democracy_scatter(
    df: pd.DataFrame, precomp: pd.DataFrame | None, year: int
) -> None:
    st.subheader("Democracy Scatterplot")

    yr_df = df[df["Year"] == year].copy()
    if yr_df.empty:
        st.info("No data for this year.")
        return

    hhi_df = get_hhi_for_year(precomp, df, year)

    rows = []
    for prov, grp in yr_df.groupby("Province"):
        vc = grp["Community"].value_counts()
        if vc.empty:
            continue
        rows.append({
            "Province":               prov,
            "Unique Clans":           grp["Community"].nunique(),
            "Largest Clan Share (%)": vc.iloc[0] / len(grp) * 100,
        })

    scatter_df = pd.DataFrame(rows).merge(
        hhi_df[["Province", "HHI_Score"]], on="Province", how="left"
    )

    fig = px.scatter(
        scatter_df,
        x="Unique Clans",
        y="Largest Clan Share (%)",
        text="Province",
        size="HHI_Score",
        color="HHI_Score",
        color_continuous_scale="Reds",
        title=f"Political Pluralism vs. Clan Dominance — {year}",
        labels={
            "Unique Clans":           "No. of Unique Clans in Power",
            "Largest Clan Share (%)": "Seats Held by Largest Clan (%)",
        },
    )
    fig.update_traces(textposition="top center", textfont_size=8)
    st.plotly_chart(fig, width='stretch')


# ── 3. Island-Group Aggregated Trend ─────────────────────────────────────────────

def _render_island_trend(
    df: pd.DataFrame,
    precomp: pd.DataFrame | None,
    year: int,
) -> None:
    st.subheader("Dynastic Indicator Trends by Island Group")

    indicator = st.radio(
        "Select indicator",
        options=list(INDICATOR_LABELS.keys()),
        format_func=lambda k: INDICATOR_LABELS[k],
        horizontal=True,
        key="nat_island_radio",
    )
    st.caption(INDICATOR_HELP[indicator])

    avail_years = tuple(get_election_years_in_data(df))
    if not avail_years:
        st.info("No election year data available.")
        return

    with st.spinner("Aggregating island-group trends…"):
        try:
            trend_df = get_island_group_trend(precomp, df, indicator, avail_years)
            if trend_df.empty:
                st.info("No trend data available.")
                return

            group_colors = {
                "Philippines": "#c084fc",
                "Luzon":       "#f87171",
                "Visayas":     "#60a5fa",
                "Mindanao":    "#34d399",
            }

            fig = go.Figure()
            for group in ["Philippines", "Luzon", "Visayas", "Mindanao"]:
                if group not in trend_df.columns:
                    continue
                fig.add_trace(go.Scatter(
                    x=trend_df["Year"],
                    y=trend_df[group],
                    mode="lines+markers",
                    name=group,
                    line=dict(
                        color=group_colors.get(group, "#999"),
                        width=3 if group == "Philippines" else 1.8,
                        dash="dot" if group == "Philippines" else "solid",
                    ),
                    marker=dict(size=6),
                ))

            if year in trend_df["Year"].values:
                fig.add_vline(
                    x=year, line_dash="dot", line_color="#555566",
                    annotation_text=str(year), annotation_position="top right",
                )

            fig.update_layout(
                title=f"{INDICATOR_LABELS[indicator]} — Island Groups vs. Philippines",
                xaxis_title="Election Year",
                yaxis_title=f"Mean {indicator} Score",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(fig, width='stretch')

        except Exception as exc:
            st.error(f"Could not compute island-group trend: {exc}")


# ── 4. Deep Root League Table ─────────────────────────────────────────────────────

def _longest_streak(years_held: list, reference: list) -> int:
    if not years_held:
        return 0
    in_power = set(years_held)
    best = cur = 0
    for y in sorted(reference):
        if y in in_power:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def _render_deep_root_table(df: pd.DataFrame, label_map: dict) -> None:
    st.subheader("Deep Root League Table — Clans with Longest Consecutive Years in Power")

    avail = get_election_years_in_data(df)
    rows  = []
    for comm, grp in df.groupby("Community"):
        years_held   = grp["Year"].dropna().unique().tolist()
        dom_province = grp["Province"].value_counts().index[0] if not grp.empty else ""
        clan_label   = label_map.get((dom_province, comm), str(comm))
        rows.append({
            "Clan":                  f"{clan_label} ({comm})",
            "Consecutive Cycles":    _longest_streak(years_held, avail),
            "Total Position Weight": round(grp["Position Weight"].sum(), 2),
            "Provinces":             ", ".join(sorted(grp["Province"].unique().tolist())[:3]),
        })

    deep_df = (
        pd.DataFrame(rows)
        .sort_values("Consecutive Cycles", ascending=False)
        .head(20)
    )

    fig = px.bar(
        deep_df,
        x="Consecutive Cycles", y="Clan",
        orientation="h",
        color="Total Position Weight",
        color_continuous_scale="Reds",
        title="Top 20 Clans by Consecutive Election Cycles in Power (Nationwide)",
        hover_data=["Provinces"],
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, width='stretch')


# ── Public entry-point ───────────────────────────────────────────────────────────

def render(
    df: pd.DataFrame,
    precomp: pd.DataFrame | None,
    year: int,
    label_map: dict,
) -> None:
    st.header(f"National-Level Analysis — {year}")

    _render_choropleth(df, precomp, year)
    st.markdown("---")

    _render_democracy_scatter(df, precomp, year)
    st.markdown("---")

    _render_island_trend(df, precomp, year)
    st.markdown("---")

    # _render_deep_root_table(df, label_map)
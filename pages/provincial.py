"""
pages/provincial.py
Streamlit page script — Provincial Analysis.

This file is intentionally thin: it only handles sidebar controls
and delegates all rendering to components/provincial_view.py.
"""

import streamlit as st

from data_loader import (
    load_data,
    load_precomputed,
    get_community_label_map,
    get_available_years,
)
from config import ELECTION_YEARS, PROVINCES_TO_EXCLUDE
from components import provincial_view

st.set_page_config(
    page_title="Provincial Analysis — PH Clan Watch",
    page_icon="🏛️",
    layout="wide",
)

# ── Load shared data ──────────────────────────────────────────────────────────────

df      = load_data()
precomp = load_precomputed()

label_map   = get_community_label_map(df)
avail_years = get_available_years(df)

# ── Sidebar filters ───────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Filters")

    year = st.select_slider(
        "Election Year",
        options=avail_years if avail_years else ELECTION_YEARS,
        value=avail_years[-1] if avail_years else 2022,
    )


    provinces = sorted(df["Province"].dropna().unique().tolist())
    provinces = [p for p in provinces if p not in PROVINCES_TO_EXCLUDE]
    province  = st.selectbox("Province", provinces)

    st.markdown("---")
    st.caption('**Data Visualization** by Val Eltagonde.')
    st.caption('**Data and methodology** from Acuña, Alejandro, and Leung (2025) and Garcia & Montemayor (2026), Ateneo de Manila University.')

# ── Render ────────────────────────────────────────────────────────────────────────

provincial_view.render(df, precomp, province, year, label_map)

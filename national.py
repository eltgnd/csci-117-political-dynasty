"""
pages/national.py
Streamlit page script — National-Level Analysis.
"""

import streamlit as st

from data_loader import (
    load_data,
    load_precomputed,
    get_community_label_map,
    get_available_years,
)
from config import ELECTION_YEARS
from components import national_view

st.set_page_config(
    page_title="National Analysis — PH Clan Watch",
    page_icon="🗺️",
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

    st.markdown("---")
    st.caption(
        f"**{len(df):,}** records · "
        f"**{df['Province'].nunique()}** provinces · "
        f"{df['Year'].min()}–{df['Year'].max()}"
    )
    st.write('Test')

# ── Render ────────────────────────────────────────────────────────────────────────

national_view.render(df, precomp, year, label_map)

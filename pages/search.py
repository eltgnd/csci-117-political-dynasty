"""
pages/search.py
Streamlit page script — Politician Search.
"""

import streamlit as st

from data_loader import load_data, get_community_label_map
from components import search_view

st.set_page_config(
    page_title="Politician Search — PH Clan Watch",
    page_icon="🔍",
    layout="wide",
)

# ── Load shared data ──────────────────────────────────────────────────────────────

df        = load_data()
label_map = get_community_label_map(df)

# ── Sidebar info ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.caption(
        f"**{len(df):,}** records · "
        f"**{df['Province'].nunique()}** provinces · "
        f"{df['Year'].min()}–{df['Year'].max()}"
    )

# ── Render ────────────────────────────────────────────────────────────────────────

search_view.render(df, label_map)

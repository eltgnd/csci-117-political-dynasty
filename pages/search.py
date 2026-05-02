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
    st.caption('**Data Visualization** by Val Eltagonde')
    st.caption('**Data and methodology** from Acuña, Alejandro, and Leung (2025) and Garcia & Montemayor (2026), Ateneo de Manila University.')

# ── Render ────────────────────────────────────────────────────────────────────────

search_view.render(df, label_map)

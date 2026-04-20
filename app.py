"""
app.py
Philippine Clan Watch Dashboard — navigation entry point only.

Run with:
    streamlit run app.py
"""

import streamlit as st

home_page       = st.Page("pages/landing.py",    title="About the Project",     icon="🏠")
provincial_page = st.Page("pages/provincial.py", title="Provincial Analysis",   icon="🏛️")
national_page   = st.Page("pages/national.py",   title="National Analysis",     icon="🗺️")
search_page     = st.Page("pages/search.py",     title="Politician Search",     icon="🔍")

pg = st.navigation(
    {
        "Overview":  [home_page],
        "Analysis":  [provincial_page, national_page],
        "Tools":     [search_page],
    },
    position="sidebar",
    expanded=True,
)

pg.run()

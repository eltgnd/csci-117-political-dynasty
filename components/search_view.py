"""
components/search_view.py
All rendering logic for the Politician Search page.

New flow:
  1. Province selector
  2. Name text input (filtered to selected province)
  3. Name+context dropdown if multiple matches
  4. Year selection panel (radio: all years that politician appears in that province)
  5. Graph renders only after year is confirmed
"""

import pandas as pd
import networkx as nx
import streamlit as st
import streamlit.components.v1 as components

from backend_math import generate_graph
from network_renderer import pyvis_network_html


# ─── cached graph builder ─────────────────────────────────────────────────────────

@st.cache_data
def _build_graph_data(df: pd.DataFrame, province: str, year: int):
    """Build and cache the full provincial graph for a given province+year."""
    df_upper = df.copy()
    df_upper.columns = [c.upper() for c in df_upper.columns]
    return generate_graph(df_upper, province, year)


# ─── helpers ──────────────────────────────────────────────────────────────────────

def _resolve_node(G: nx.Graph, full_name: str) -> str | None:
    if full_name in G.nodes():
        return full_name
    lower = full_name.lower()
    for node in G.nodes():
        if node.lower() == lower:
            return node
    return None


def _render_ego_graph(G_full: nx.Graph, full_name: str, label_map: dict) -> None:
    node = _resolve_node(G_full, full_name)
    if node is None:
        st.warning(f"'{full_name}' was not found as a network node for this province/year.")
        return

    ego = nx.ego_graph(G_full, node, radius=2, undirected=True)
    if len(ego.nodes()) <= 1:
        st.info("This politician has no direct clan connections in the network for this year.")
        return

    html = pyvis_network_html(ego, label_map)
    components.html(html, height=600, scrolling=False)
    st.caption(
        f"{ego.number_of_nodes()} connected politicians · "
        f"{ego.number_of_edges()} consanguinity links (radius 2)"
    )


def _render_connections_table(G_full: nx.Graph, full_name: str, label_map: dict, province: str) -> None:
    node = _resolve_node(G_full, full_name)
    if node is None:
        return

    neighbours = list(nx.neighbors(G_full, node))
    if not neighbours:
        return

    st.subheader("Direct Connections (Radius 1)")
    rows = [
        {
            "Name":        nb,
            "Clan": label_map.get((province, G_full.nodes[nb].get("community", -1)), "—"),
            "Edge Weight": round(float(G_full[node][nb].get("weight", 0)), 3),
        }
        for nb in neighbours
    ]
    st.dataframe(
        pd.DataFrame(rows).sort_values("Edge Weight", ascending=False),
        width='stretch',
    )


# ─── Public entry-point ───────────────────────────────────────────────────────────

def render(df: pd.DataFrame, label_map: dict) -> None:
    st.header("Politician Search")

    # ── Step 1: Province selector ─────────────────────────────────────────────────
    provinces = sorted(df["Province"].dropna().unique().tolist())
    province  = st.selectbox("Select province", provinces, key="search_province")

    # Filter data to selected province up front
    prov_df = df[df["Province"] == province]

    st.markdown("---")

    # ── Step 2: Name search (within selected province) ────────────────────────────
    query = st.text_input(
        f"Search politician name in {province}",
        placeholder="e.g. Santos, Maria",
        key="search_query",
    )

    if not query.strip():
        st.info("Type a name to search.")
        return

    mask    = prov_df["Full Name"].str.contains(query.strip(), case=False, na=False)
    results = prov_df[mask].copy()

    if results.empty:
        st.warning(f"No politicians matching **'{query}'** found in {province}.")
        return

    # ── Step 3: Name disambiguation dropdown ──────────────────────────────────────
    # Show unique names (without year yet — year is chosen separately below)
    unique_names = sorted(results["Full Name"].unique().tolist())

    full_name = (
        unique_names[0]
        if len(unique_names) == 1
        else st.selectbox(
            f"{len(unique_names)} matches found — select a politician:",
            unique_names,
            key="search_name_select",
        )
    )

    # Metadata for the chosen politician (position, community — use most recent record)
    person_records = results[results["Full Name"] == full_name].sort_values("Year", ascending=False)
    sample         = person_records.iloc[0]
    community      = sample.get("Community", -1)


    st.markdown("---")

    # ── Step 4: Year selection panel ──────────────────────────────────────────────
    available_years = sorted(person_records["Year"].dropna().unique().tolist())

    if not available_years:
        st.warning("No election year data found for this politician.")
        return

    st.subheader("Select Election Year")
    st.caption(
        f"**{full_name}** appears in the dataset for **{len(available_years)}** "
        f"election year(s) in {province}."
    )

    year = st.radio(
        "Choose a year to view the clan network:",
        options=available_years,
        format_func=lambda y: (
            f"{y}  —  {person_records[person_records['Year'] == y]['Position'].iloc[0]}"
            if not person_records[person_records["Year"] == y].empty else str(y)
        ),
        horizontal=True,
        key="search_year_radio",
    )

    st.markdown("---")

    # ── Step 5: Ego-graph (only after year confirmed) ─────────────────────────────
    st.subheader(f"Clan Network: {full_name} · {province} · {year}")

    with st.spinner("Building clan network…"):
        try:
            G_full = _build_graph_data(df, province, int(year))
            _render_ego_graph(G_full, full_name, label_map)
            st.markdown("---")
            _render_connections_table(G_full, full_name, label_map, province)
        except Exception as exc:
            st.error(f"Could not build network: {exc}")

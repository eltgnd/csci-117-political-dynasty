"""
components/provincial_view.py
All rendering logic for the Provincial Analysis page.

Changes vs previous version:
  - _render_kpis: also shows the 4 dynastic indicator scores for selected year
  - _render_heatmap / _render_positions_over_time / _render_weighted_degree_bar:
      cache keys explicitly include (province, year) so they always refresh on change
  - _render_indicator_trend: single-indicator view with radio selector above the chart
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from backend_math import generate_graph, get_provincial_kpis
from config import INDICATOR_COLORS, INDICATOR_LABELS, INDICATOR_HELP, INDICATOR_SCORE_COL
from data_loader import (
    get_indicators_for_province,
    get_indicators_single_year,
    get_election_years_in_data,
)
from network_renderer import pyvis_network_html


# ─── cached data-prep helpers ─────────────────────────────────────────────────────
# These wrap pure-pandas logic so Streamlit caches on (df hash, province, year).

@st.cache_data
def _heatmap_data(df: pd.DataFrame, province: str, year: int) -> pd.DataFrame:
    """Return pivot table for clan × position heatmap."""
    prov_yr = df[(df["Province"] == province) & (df["Year"] == year)].copy()
    if prov_yr.empty:
        return pd.DataFrame()
    top_clans = prov_yr["Community"].value_counts().head(12).index.tolist()
    sub = prov_yr[prov_yr["Community"].isin(top_clans)].copy()
    pivot = (
        sub.groupby(["Position", "Community"])
        .size()
        .reset_index(name="Count")
    )
    return pivot


@st.cache_data
def _positions_over_time_data(df: pd.DataFrame, province: str) -> pd.DataFrame:
    """Return (Year, Community, Count) for the stacked area chart."""
    prov_all  = df[df["Province"] == province].copy()
    if prov_all.empty:
        return pd.DataFrame()
    top_clans = prov_all["Community"].value_counts().head(8).index.tolist()
    prov_top  = prov_all[prov_all["Community"].isin(top_clans)].copy()
    return (
        prov_top.groupby(["Year", "Community"])
        .size()
        .reset_index(name="Count")
    )


@st.cache_data
def _weighted_degree_data(df: pd.DataFrame, province: str, year: int) -> pd.DataFrame:
    """Return top-15 politicians by weighted degree for selected province/year."""
    df_upper = df.copy()
    df_upper.columns = [c.upper() for c in df_upper.columns]
    G = generate_graph(df_upper, province, year)
    if not G.nodes():
        return pd.DataFrame()
    return (
        pd.DataFrame(
            list(dict(G.degree(weight="weight")).items()),
            columns=["Politician", "Weighted Degree"],
        )
        .sort_values("Weighted Degree", ascending=False)
        .head(15)
    )


# ── 1. Political Health KPIs + Dynastic Indicators ───────────────────────────────

def _render_kpis(
    df: pd.DataFrame,
    precomp: pd.DataFrame | None,
    province: str,
    year: int,
) -> None:
    # --- row 1: original three KPIs ---
    kpis = get_provincial_kpis(df, province, year)
    st.caption('AT A GLANCE')
    with st.container(border=True):
        st.write(f"In {year}, clans with >1 member simultaneously hold **{kpis['clan_concentration_pct']}%** of positions in office. The maximum number of members from a single clan holding office at the same time is **{kpis['simultaneous_counter']}**. The newcomer rate, the percent of officials with no prior record of holding office in this province, is **{kpis['newcomer_rate_pct']}%**.")

    # c1.metric(
    #     "Clan Concentration",
    #     f"{kpis['clan_concentration_pct']}%",
    #     help="% of positions held by members of dynastic clans (clans with >1 member simultaneously in office)",
    # )
    # c2.metric(
    #     "Simultaneous Counter",
    #     kpis["simultaneous_counter"],
    #     help="Maximum number of members from a single clan holding office at the same time",
    # )
    # c3.metric(
    #     "Newcomer Rate",
    #     f"{kpis['newcomer_rate_pct']}%",
    #     help="% of officials with no prior record of holding office in this province",
    # )

    # --- row 2: four dynastic indicator scores ---
    scores = get_indicators_single_year(precomp, df, province, year)
    st.caption("DYNASTIC INDICATOR SCORES")
    d1, d2, d3, d4 = st.columns(4, border=True)
    d1.metric(INDICATOR_LABELS['HHI'], f" {scores['HHI']:.2f}", help=INDICATOR_HELP["HHI"])
    d2.metric(INDICATOR_LABELS['CGC'], f" {scores['CGC']:.4f}", help=INDICATOR_HELP["CGC"])
    d3.metric(INDICATOR_LABELS['CCD'], f" {scores['CCD']:.4f}", help=INDICATOR_HELP["CCD"])
    d4.metric(INDICATOR_LABELS['ACC'], f" {scores['ACC']:.4f}", help=INDICATOR_HELP["ACC"])


# ── 2. Dynasty Network Graph ─────────────────────────────────────────────────────

def _render_network_graph(
    df: pd.DataFrame, province: str, year: int, label_map: dict
) -> None:
    st.subheader("Dynasty Network Graph")
    df_upper = df.copy()
    df_upper.columns = [c.upper() for c in df_upper.columns]

    with st.spinner("Building network graph…"):
        try:
            G = generate_graph(df_upper, province, year)
            if not G.nodes():
                st.info("No network data available for this province and year.")
                return

            # ── Build legend data from graph node attributes ──────────────────────
            import networkx as nx
            from network_renderer import make_color_map

            communities = nx.get_node_attributes(G, "community")
            color_map   = make_color_map(communities.values())

            # One legend entry per unique community in this graph
            legend_entries = {}
            for node, comm in communities.items():
                if comm not in legend_entries:
                    legend_entries[comm] = {
                        "color": color_map.get(comm, "#888888"),
                        "label": label_map.get((province, comm), str(comm)),
                        "count": 0,
                    }
                legend_entries[comm]["count"] += 1

            # Sort legend by number of members descending
            sorted_legend = sorted(
                legend_entries.items(), key=lambda x: x[1]["count"], reverse=True
            )

            # ── Two-column layout: graph left, legend right ───────────────────────
            col_graph, col_legend = st.columns([3, 1])

            with col_graph:
                html = pyvis_network_html(G, label_map, province)
                components.html(html, height=600, scrolling=False)

            with col_legend:
                with st.container(border=True, height=590):
                    st.markdown("**Clan Legend by Size**")
                    st.caption(f"{len(sorted_legend)} clan(s) · {G.number_of_nodes()} politicians")
                    for comm, info in sorted_legend:
                        # Colored swatch + label using HTML in st.markdown
                        hex_color = info["color"]
                        label     = info["label"]
                        count     = info["count"]
                        st.markdown(
                            f"<div style='display:flex; align-items:center; "
                            f"margin-bottom:6px; gap:8px;'>"
                            f"<div style='width:14px; height:14px; border-radius:50%; "
                            f"background:{hex_color}; flex-shrink:0;'></div>"
                            f"<span style='font-size:13px; line-height:1.3;'>"
                            f"<b>{label}</b><br>"
                            f"<span style='color:#888; font-size:11px;'>{count} member(s)</span>"
                            f"</span></div>",
                            unsafe_allow_html=True,
                        )

        except Exception as exc:
            st.error(f"Network graph error: {exc}")

# ── 3. Clan × Position Heatmap ───────────────────────────────────────────────────

def _render_heatmap(
    df: pd.DataFrame, province: str, year: int, label_map: dict
) -> None:
    
    st.subheader("Clan-Position Heatmap")

    pivot_raw = _heatmap_data(df, province, year)
    if pivot_raw.empty:
        st.info("No data for this selection.")
        return

    # Apply clan labels after fetching cached raw data
    pivot_raw = pivot_raw.copy()
    pivot_raw["Clan Label"] = pivot_raw["Community"].map(
        lambda c: f"{label_map.get((province, c), c)} ({c})"
    )
    hm_pivot = pivot_raw.pivot_table(
        index="Position", columns="Clan Label", values="Count", fill_value=0
    )

    fig = px.imshow(
        hm_pivot,
        color_continuous_scale="Reds",
        aspect="auto",
        # title=f"Positions Held by Top Clans — {province} {year}",
        labels=dict(color="Count"),
    )
    fig.update_layout(xaxis_title="Clan (Last Name Mode)", yaxis_title="Position")
    st.plotly_chart(fig, width='stretch')


# ── 4. Dynastic Indicator Trend (single indicator, user-selectable) ──────────────

def _render_indicator_trend(
    df: pd.DataFrame,
    precomp: pd.DataFrame | None,
    province: str,
    year: int,
) -> None:
    st.subheader("Dynastic Indicator Trend")

    # Selector sits directly above the chart — not in the sidebar
    with st.container(border=True):
        indicator = st.radio(
            "Select indicator to display",
            options=list(INDICATOR_LABELS.keys()),
            format_func=lambda k: INDICATOR_LABELS[k],
            horizontal=True,
            key="prov_indicator_radio",
        )

        avail_years = tuple(get_election_years_in_data(df))
        if not avail_years:
            st.info("No election year data available.")
            return

    if indicator == 'HHI':        
        with st.expander("📊 HHI — Herfindahl-Hirschman Index"):
            st.markdown(r"""
            **What it measures:** Seat concentration across clans in a given province and year.

            $$
            HHI = \sum_{k} \left( 100 \times s_k \right)^2
            $$

            where $s_k$ is the share of total **Position Weight** held by clan $k$.

            - **Range:** 0 – 10,000  
            - **Higher** = power is monopolised by one or few clans  
            - **Lower** = positions are spread across many clans  
            - A score above **2,500** is conventionally considered highly concentrated.
            """)
    if indicator == 'CGC': 
        with st.expander("📈 CGC — Clan Gini Coefficient"):
            st.markdown(r"""
            **What it measures:** Inequality in *network influence* (weighted degree centrality) across politicians.

            $$
            G = \frac{\sum_{i} \sum_{j} |d_i - d_j|}{2 n \sum_{i} d_i}
            $$

            where $d_i$ is the weighted degree (sum of edge weights) of node $i$ in the provincial network.

            - **Range:** 0 – 1  
            - **Higher** = a small number of politicians concentrate almost all network connections  
            - **Lower** = influence is spread more evenly
            """)
    if indicator == 'CCD':        
        with st.expander("🔗 CCD — Clan Connectivity Density"):
            st.markdown(r"""
            **What it measures:** How tightly the dynasty network is woven together.

            $$
            CCD = 1 - \frac{\text{Connected Components}}{|\text{Nodes}|}
            $$

            - **Range:** approaches 0 – 1  
            - **Higher** = the network has few isolated components; clans are heavily interconnected  
            - **Lower** = many politicians stand in separate, unconnected clusters
            """)
    if indicator == 'ACC':        
        with st.expander("🏛️ ACC — Aggregate Clan Connectivity"):
            st.markdown(r"""
            **What it measures:** Internal resilience of each clan — how hard it is to disconnect a clan's internal network.

            For each community $c$ with $n_c$ members:

            $$
            ACC = \sum_{c} \frac{\kappa(G_c)}{n_c}
            $$

            where $\kappa(G_c)$ is the **node connectivity** of the subgraph induced by community $c$
            (the minimum number of nodes whose removal disconnects the subgraph).

            - **Range:** 0 and above  
            - **Higher** = clans have robust internal structures that can survive the removal of individual members  
            - **Lower** = clans are loosely connected internally
            """)


    with st.spinner("Loading trend data…"):
        try:
            trend_df = get_indicators_for_province(precomp, df, province, avail_years)
            if trend_df.empty:
                st.info("No indicator data for this province.")
                return

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=trend_df["Year"],
                y=trend_df[indicator],
                mode="lines+markers",
                name=indicator,
                line=dict(color=INDICATOR_COLORS[indicator], width=2),
                marker=dict(size=7),
            ))
            if year in trend_df["Year"].values:
                fig.add_vline(
                    x=year, line_dash="dot", line_color="gray",
                    annotation_text=str(year), annotation_position="top right",
                )
            fig.update_layout(
                # title=f"{INDICATOR_LABELS[indicator]} — {province}",
                xaxis_title="Election Year",
                yaxis_title="Score",
                hovermode="x unified",
                showlegend=False,
            )
            st.plotly_chart(fig, width='stretch')

        except Exception as exc:
            st.error(f"Could not load indicator trend: {exc}")


# ── 5. Total Positions Held Over Time (stacked area) ────────────────────────────

def _render_positions_over_time(
    df: pd.DataFrame, province: str, label_map: dict
) -> None:
    st.subheader("Total Positions Held Over Time by Top Clans")

    raw = _positions_over_time_data(df, province)
    if raw.empty:
        st.info("No historical data for this province.")
        return

    # Apply clan labels to the cached raw data
    raw = raw.copy()
    raw["Clan Label"] = raw["Community"].map(
        lambda c: f"{label_map.get((province, c), c)} ({c})"
    )

    fig = px.area(
        raw,
        x="Year", y="Count", color="Clan Label",
        # title=f"Positions Held by Top Clans — {province}",
        labels={"Count": "Positions Held", "Year": "Election Year"},
    )
    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01),
    )
    st.plotly_chart(fig, width='stretch')


# ── 6. Top 15 Nodes by Weighted Degree ──────────────────────────────────────────

def _render_weighted_degree_bar(
    df: pd.DataFrame, province: str, year: int
) -> None:
    st.subheader("Top 15 Politicians by Weighted Degree (Network Influence)")

    with st.spinner("Computing weighted degrees…"):
        try:
            wdeg_df = _weighted_degree_data(df, province, year)
            if wdeg_df.empty:
                st.info("No graph data available.")
                return

            fig = px.bar(
                wdeg_df,
                x="Weighted Degree", y="Politician",
                orientation="h",
                # title=f"Top 15 by Weighted Degree — {province} {year}",
                color="Weighted Degree",
                color_continuous_scale="Reds",
            )
            fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
            st.plotly_chart(fig, width='stretch')

        except Exception as exc:
            st.error(f"Degree calculation error: {exc}")


# ── Public entry-point ───────────────────────────────────────────────────────────

def render(
    df: pd.DataFrame,
    precomp: pd.DataFrame | None,
    province: str,
    year: int,
    label_map: dict,
) -> None:
    st.header(f"{province}")

    _render_kpis(df, precomp, province, year)
    # st.markdown("---")

    _render_network_graph(df, province, year, label_map)
    # st.markdown("---")

    _render_heatmap(df, province, year, label_map)
    # st.markdown("---")

    _render_indicator_trend(df, precomp, province, year)
    # st.markdown("---")

    _render_positions_over_time(df, province, label_map)
    # st.markdown("---")

    _render_weighted_degree_bar(df, province, year)





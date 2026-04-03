"""
╔═══════════════════════════════════════════════════════════════════╗
║         THE PHILIPPINE CLAN WATCH DASHBOARD — app.py              ║
║  Streamlit + Plotly political dynasty visualization tool          ║
╚═══════════════════════════════════════════════════════════════════╝

Run with:  streamlit run app.py
Requires:  streamlit, plotly, pandas, numpy, networkx, pyvis
           (pip install streamlit plotly pandas numpy networkx pyvis)
"""

# ─────────────────────────────────────────────────────────────────
#  IMPORTS
# ─────────────────────────────────────────────────────────────────
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import networkx as nx
import os

from backend_math import get_adjacency_matrix, get_provincial_kpis, get_hhi_index_per_province, generate_graph


# ─────────────────────────────────────────────────────────────────
#  PAGE CONFIG & THEME CONSTANTS
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PH Clan Watch",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dashboard-wide CSS ──────────────────────────────────────────
st.markdown(
    """
    <style>
        /* ── Global font & background ── */
        @import url('https://fonts.googleapis.com/css2?family=Gotham:wght@400;700;800&family=IBM+Plex+Mono:wght@400;600&display=swap');

        html, body, [class*="css"]  { font-family: 'Gotham', sans-serif; }

        /* Dark government-data aesthetic */
        .stApp { background-color: #0d1117; color: #e6edf3; }
        section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }

        /* Metric cards */
        [data-testid="metric-container"] {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 16px 20px;
        }
        [data-testid="metric-container"] label { color: #8b949e !important; font-size: 0.75rem; letter-spacing: 0.1em; text-transform: uppercase; }
        [data-testid="metric-container"] [data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace; font-size: 2rem; color: #f0f6fc; }

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #30363d; }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 6px 6px 0 0;
            color: #8b949e;
            font-weight: 700;
            letter-spacing: 0.05em;
            padding: 10px 22px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1f2937;
            color: #58a6ff;
            border-bottom: 2px solid #58a6ff;
        }

        /* Section headers */
        .section-header {
            font-family: 'Gotham', sans-serif;
            font-weight: 800;
            font-size: 0.7rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: #58a6ff;
            margin-bottom: 6px;
        }

        /* Dividers */
        hr { border-color: #30363d; margin: 24px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Plotly base template (dark) ──────────────────────────────────
PLOTLY_TEMPLATE = "plotly_dark"
CLAN_PALETTE    = px.colors.qualitative.Bold   # up to 10 distinct colours
BG_COLOR        = "#0d1117"
PAPER_COLOR     = "#161b22"
GRID_COLOR      = "#21262d"

def _base_layout(**kwargs):
    """Returns a consistent dark layout dict for all Plotly figures."""
    base = dict(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=PAPER_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(family="IBM Plex Mono, monospace", color="#c9d1d9"),
        margin=dict(l=40, r=20, t=50, b=40),
        xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
    )
    base.update(kwargs)
    return base


# ─────────────────────────────────────────────────────────────────
#  DATA LOADER  (cached)
# ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading dataset…")
def load_data() -> pd.DataFrame:
    """
    Loads the main 140 000-row DataFrame.
    """
    df = pd.read_csv('political_dynasty.csv')
    df.columns = [c.title() for c in df.columns] # Title-case column names
    return df


# ─────────────────────────────────────────────────────────────────
#  SIDEBAR — GLOBAL CONTROLS
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏛️ PH Clan Watch")
    st.caption("Political dynasty tracker · 2004-2025")
    st.divider()

    view_mode = st.radio(
        "Dashboard Mode",
        options=["Provincial View", "National View"],
        index=0,
        help="Provincial: deep-dive into one province.  "
             "National: compare dynasties across all 80 provinces.",
    )

    # Load data once (cached) so sidebar Province list is real
    df = load_data()
    all_provinces = sorted(df["Province"].unique().tolist())

    selected_province = None
    if view_mode == "Provincial View":
        selected_province = st.selectbox(
            "Province",
            options=all_provinces,
            index=0,
        )

    selected_year = st.select_slider(
        "Election Year",
        options=sorted(df["Year"].unique().tolist()),
        value=sorted(df["Year"].unique().tolist())[-1],
    )

    st.divider()
    st.caption("Data as of the selected election cycle. "
               "HHI = Herfindahl-Hirschman Index.")


# ─────────────────────────────────────────────────────────────────
#  HEADER BANNER
# ─────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="
        padding: 28px 32px 20px;
        background: linear-gradient(135deg, #161b22 0%, #0d1f3c 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        margin-bottom: 24px;
    ">
        <div style="font-size:0.65rem;letter-spacing:0.25em;color:#58a6ff;
                    text-transform:uppercase;font-weight:700;margin-bottom:6px;">
            Philippine Political Data Project
        </div>
        <h1 style="margin:0;font-size:2.2rem;font-weight:800;color:#f0f6fc;
                   font-family:'Gotham',sans-serif;line-height:1.1;">
            Clan Watch Dashboard
        </h1>
        <p style="margin:8px 0 0;color:#8b949e;font-size:0.9rem;">
            Tracking dynastic power across <b style="color:#e6edf3">80 provinces</b> ·
            <b style="color:#e6edf3">8 election cycles</b> ·
            Leiden community detection
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────
#  TAB ROUTING
# ─────────────────────────────────────────────────────────────────
tab_prov, tab_nat = st.tabs(["🗺️  Provincial View", "🌐  National View"])


# ═══════════════════════════════════════════════════════════════════
#  TAB 1 — PROVINCIAL VIEW
# ═══════════════════════════════════════════════════════════════════
with tab_prov:

    if view_mode != "Provincial View":
        st.info("Switch the sidebar to **Provincial View** to explore this tab.")
        st.stop()

    # ── Filter dataframe ─────────────────────────────────────────
    df_prov = df[
        (df["Province"] == selected_province) &
        (df["Year"] == selected_year)
    ]
    df_prov_all_years = df[df["Province"] == selected_province]

    st.markdown(
        f"<div class='section-header'>Province: {selected_province} · "
        f"Election cycle: {selected_year}</div>",
        unsafe_allow_html=True,
    )

    # ── 1. POLITICAL HEALTH KPIs ─────────────────────────────────
    kpis = get_provincial_kpis(df, selected_province, selected_year)

    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        st.metric(
            label="🏴 Clan Concentration",
            value=f"{kpis['clan_concentration_pct']}%",
            help="% of all positions held by the single largest political clan.",
        )
    with col_k2:
        st.metric(
            label="⚡ Simultaneous Officeholders",
            value=kpis["simultaneous_counter"],
            help="Number of individuals holding more than one elected position "
                 "concurrently (directly or through immediate family).",
        )
    with col_k3:
        st.metric(
            label="🌱 Political Newcomer Rate",
            value=f"{kpis['newcomer_rate_pct']}%",
            help="% of elected officials appearing for the first time in any "
                 "office in this province.",
        )

    st.divider()

    # ── 2. DYNASTY NETWORK GRAPH ─────────────────────────────────
    st.markdown("<div class='section-header'>Dynasty Network Graph</div>",
                unsafe_allow_html=True)

    # ── View controls ─────────────────────────────────────────
    show_names = st.toggle(
        "Show politician names",
        value=True,
        help="When off, names move to the hover tooltip to reduce visual clutter.",
    )

    G = generate_graph(df, selected_province, selected_year)

    if len(G.nodes) == 0:
        st.info(f"No network data available for {selected_province} · {selected_year}.")
    else:
        pos = nx.spring_layout(G, seed=42, weight="weight", k=1.8)

        communities   = nx.get_node_attributes(G, "community")
        unique_clans  = sorted(set(communities.values()))
        clan_color    = {cid: CLAN_PALETTE[i % len(CLAN_PALETTE)]
                        for i, cid in enumerate(unique_clans)}

        degrees       = dict(G.degree(weight="weight"))
        max_deg       = max(degrees.values()) if degrees else 1

        edge_x, edge_y, edge_widths = [], [], []
        for u, v, data_e in G.edges(data=True):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]
            edge_widths.append(data_e.get("weight", 1))

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=0.8, color="#30363d"),
            hoverinfo="none",
            showlegend=False,
        )

        node_traces = []
        for cid in unique_clans:
            clan_nodes = [n for n in G.nodes() if communities.get(n) == cid]
            if not clan_nodes:
                continue

            node_x = [pos[n][0] for n in clan_nodes]
            node_y = [pos[n][1] for n in clan_nodes]
            sizes  = [
                10 + 30 * (degrees.get(n, 0) / max_deg)
                for n in clan_nodes
            ]
            labels = [
                n if len(n) <= 22 else n[:20] + "…"
                for n in clan_nodes
            ]

            # ── Toggle: names on graph vs. names only in hover ───
            if show_names:
                trace_mode      = "markers+text"
                hover_template  = (
                    "<b>%{customdata[0]}</b><br>"
                    "Clan: %{customdata[1]}<br>"
                    "Weighted degree: %{customdata[2]:.2f}"
                    "<extra></extra>"
                )
            else:
                trace_mode      = "markers"
                # Richer hover since the label is no longer visible on canvas
                hover_template  = (
                    "<b>%{customdata[0]}</b><br>"
                    "Clan: %{customdata[1]}<br>"
                    "Weighted degree: %{customdata[2]:.2f}<br>"
                )

            node_traces.append(
                go.Scatter(
                    x=node_x,
                    y=node_y,
                    mode=trace_mode,
                    name=f"Clan {cid}",
                    text=labels,
                    textposition="top center",
                    textfont=dict(size=7, color="#8b949e"),
                    hovertemplate=hover_template,
                    customdata=[
                        [n, cid, round(degrees.get(n, 0), 2)]
                        for n in clan_nodes
                    ],
                    marker=dict(
                        size=sizes,
                        color=clan_color[cid],
                        line=dict(width=1, color="#0d1117"),
                        opacity=0.92,
                    ),
                )
            )

        fig_net = go.Figure(data=[edge_trace] + node_traces)
        fig_net.update_layout(
            **_base_layout(
                title=dict(
                    text=(
                        f"Political Clan Network — "
                        f"{selected_province} · {selected_year}  "
                        f"<span style='font-size:12px;color:#8b949e'>"
                        f"({G.number_of_nodes()} politicians, "
                        f"{G.number_of_edges()} connections)</span>"
                    ),
                    font=dict(size=14),
                ),
                showlegend=True,
                legend=dict(
                    title=dict(text="Community", font=dict(size=11)),
                    font=dict(size=10),
                    bgcolor="#161b22",
                    bordercolor="#30363d",
                    borderwidth=1,
                    itemsizing="constant",
                ),
                xaxis=dict(showgrid=False, zeroline=False, visible=False),
                yaxis=dict(showgrid=False, zeroline=False, visible=False),
                height=520,
            )
        )

        st.plotly_chart(fig_net, use_container_width=True)

        with st.expander("Network statistics"):
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            col_s1.metric("Politicians (nodes)", G.number_of_nodes())
            col_s2.metric("Connections (edges)", G.number_of_edges())
            col_s3.metric("Distinct clans", len(unique_clans))
            col_s4.metric(
                "Network density",
                f"{nx.density(G):.3f}",
                help="0 = no connections, 1 = everyone connected to everyone.",
            )

    # ── 3. POWER MARKET SHARE — Stacked Area ─────────────────────
    st.markdown("<div class='section-header'>Power Market Share · Stacked Area</div>",
                unsafe_allow_html=True)

    # Aggregate: count positions per Year × Community
    area_data = (
        df_prov_all_years
        .groupby(["Year", "Community"])
        .size()
        .reset_index(name="Count")
    )

    # Keep only Top 5 communities (by total seats) + "Others"
    top5_communities = (
        area_data.groupby("Community")["Count"].sum()
        .nlargest(5).index.tolist()
    )
    area_data["Group"] = area_data["Community"].apply(
        lambda c: f"Clan {c}" if c in top5_communities else "Others"
    )
    area_agg = (
        area_data.groupby(["Year", "Group"])["Count"].sum()
        .reset_index()
    )

    # Pivot so Plotly can build a proper stacked area
    area_pivot = area_agg.pivot(index="Year", columns="Group", values="Count").fillna(0).reset_index()
    clan_cols  = [c for c in area_pivot.columns if c.startswith("Clan")]
    other_cols = [c for c in area_pivot.columns if c == "Others"]
    ordered_cols = sorted(clan_cols) + other_cols

    # -- Instantiate stacked area chart
    fig_area = go.Figure()
    for i, col in enumerate(ordered_cols):
        color = "#555555" if col == "Others" else CLAN_PALETTE[i % len(CLAN_PALETTE)]
        fig_area.add_trace(
            go.Scatter(
                x=area_pivot["Year"],
                y=area_pivot[col],
                mode="lines",
                name=col,
                stackgroup="one",       # ← enables stacking
                line=dict(width=0.5),
                fillcolor=color,
                line_color=color,
                hovertemplate=f"<b>{col}</b><br>Year: %{{x}}<br>Seats: %{{y}}<extra></extra>",
            )
        )

    fig_area.update_layout(
        **_base_layout(
            title="Total Positions Held by Top Clans Over Time",
            height=360,
            legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
        )
    )
    fig_area.update_xaxes(title_text="Election Year", dtick=3)
    fig_area.update_yaxes(title_text="Positions Held")
    st.plotly_chart(fig_area, use_container_width=True)

    st.divider()

    # ── 4. CHECKS & BALANCES HEATMAP ─────────────────────────────
    st.markdown("<div class='section-header'>Checks & Balances Matrix · Heatmap</div>",
                unsafe_allow_html=True)

    hm_data = df_prov.copy()
    top5_cids = (
        hm_data.groupby("Community").size().nlargest(5).index.tolist()
    )
    hm_data = hm_data[hm_data["Community"].isin(top5_cids)]
    hm_pivot = (
        hm_data.groupby(["Position", "Community"])
        .size()
        .reset_index(name="Seats")
        .pivot(index="Position", columns="Community", values="Seats")
        .fillna(0)
    )
    hm_pivot.columns = [f"Clan {c}" for c in hm_pivot.columns]

    # -- Instantiate heatmap
    fig_hm = go.Figure(
        data=go.Heatmap(
            z=hm_pivot.values,
            x=hm_pivot.columns.tolist(),
            y=hm_pivot.index.tolist(),
            colorscale="YlOrRd",
            hoverongaps=False,
            hovertemplate="Clan: <b>%{x}</b><br>Position: <b>%{y}</b><br>Seats: %{z}<extra></extra>",
            colorbar=dict(title="Seats", tickfont=dict(size=10)),
        )
    )
    fig_hm.update_layout(
        **_base_layout(
            title="Seats Held by Top 5 Clans per Position Type",
            height=360,
        )
    )
    st.plotly_chart(fig_hm, use_container_width=True)

    st.divider()

    # ── 5. PIE OF POWER — Waffle Chart ───────────────────────────
    st.markdown("<div class='section-header'>The Pie of Power · 10×10 Waffle Chart</div>",
                unsafe_allow_html=True)

    # Compute seat share per community
    waffle_data = (
        df_prov.groupby("Community").size()
        .reset_index(name="Seats")
        .sort_values("Seats", ascending=False)
    )
    total_seats = waffle_data["Seats"].sum()
    waffle_data["Pct"] = waffle_data["Seats"] / total_seats

    # Convert to 100 cells
    waffle_data["Cells"] = (waffle_data["Pct"] * 100).round().astype(int)
    # Correct rounding drift
    while waffle_data["Cells"].sum() > 100:
        waffle_data.loc[waffle_data["Cells"].idxmax(), "Cells"] -= 1
    while waffle_data["Cells"].sum() < 100:
        waffle_data.loc[waffle_data["Cells"].idxmin(), "Cells"] += 1

    # Build 10×10 grid as scatter
    grid_x, grid_y, grid_color, grid_text = [], [], [], []
    cell_idx = 0
    rows, cols_w = 10, 10
    for clan_i, row_d in waffle_data.iterrows():
        cid = row_d["Community"]
        color = CLAN_PALETTE[int(clan_i) % len(CLAN_PALETTE)]
        for _ in range(int(row_d["Cells"])):
            r = cell_idx // cols_w
            c = cell_idx % cols_w
            grid_x.append(c)
            grid_y.append(rows - 1 - r)
            grid_color.append(color)
            grid_text.append(f"Clan {cid}<br>{row_d['Pct']*100:.1f}%")
            cell_idx += 1

    # -- Instantiate waffle chart (square scatter markers)
    fig_waffle = go.Figure(
        go.Scatter(
            x=grid_x,
            y=grid_y,
            mode="markers",
            marker=dict(
                symbol="square",
                size=28,
                color=grid_color,
                line=dict(color=BG_COLOR, width=2),
            ),
            text=grid_text,
            hovertemplate="%{text}<extra></extra>",
        )
    )
    fig_waffle.update_layout(
        **_base_layout(
            title=f"Seat Distribution Among Clans · {selected_province} {selected_year}",
            height=420,
        )
    )
    fig_waffle.update_xaxes(range=[-0.6, 9.6], showgrid=False, visible=False)
    fig_waffle.update_yaxes(range=[-0.6, 9.6], showgrid=False, visible=False,
                             scaleanchor="x", scaleratio=1)

    # Add custom legend as annotations
    legend_clans = waffle_data.head(8)
    for li, (_, lrow) in enumerate(legend_clans.iterrows()):
        color = CLAN_PALETTE[int(li) % len(CLAN_PALETTE)]
        fig_waffle.add_annotation(
            x=10.4, y=9 - li * 1.2,
            text=f"<span style='color:{color}'>■</span>  Clan {lrow['Community']} "
                 f"({lrow['Pct']*100:.0f}%)",
            showarrow=False,
            xanchor="left",
            font=dict(size=11, color="#c9d1d9"),
        )

    st.plotly_chart(fig_waffle, use_container_width=True)


# # ═══════════════════════════════════════════════════════════════════
# #  TAB 2 — NATIONAL VIEW
# # ═══════════════════════════════════════════════════════════════════
# with tab_nat:

#     if view_mode != "National View":
#         st.info("Switch the sidebar to **National View** to explore this tab.")
#         st.stop()

#     st.markdown(
#         f"<div class='section-header'>National Overview · {selected_year}</div>",
#         unsafe_allow_html=True,
#     )

#     df_year = df[df["Year"] == selected_year]


#     # ── 1. DYNASTIC CONCENTRATION MAP ────────────────────────────
#     st.markdown("<div class='section-header'>Dynastic Concentration · Choropleth</div>",
#                 unsafe_allow_html=True)

#     hhi_df = get_hhi_index_per_province(df, selected_year)

#     # ── Load GeoJSON (cached so it's only read once) ─────────────
#     @st.cache_data
#     def load_geojson(path) -> dict:
#         """
#         Loads the Philippine provinces GeoJSON from disk.
#         """
#         import json
#         with open(path, "r", encoding="utf-8") as f:
#             return json.load(f)

#     geojson = load_geojson("provinces.json")

#     FEATURE_KEY = "properties.NAME_2"   # e.g. "properties.PROVINCE"

#     # ── Normalize province names so they join cleanly ────────────────
#     # GeoJSON names and your DataFrame names may differ in casing,
#     # accents, or abbreviations (e.g. "Davao Del Sur" vs "Davao del Sur").
#     # This lowercase strip pass catches the most common mismatches.
#     import unicodedata

#     def _normalize(name: str) -> str:
#         """Lowercase, strip, remove accents."""
#         name = str(name).strip().lower()
#         name = unicodedata.normalize("NFD", name)
#         name = "".join(c for c in name if unicodedata.category(c) != "Mn")
#         return name

#     # Build a lookup: normalized GeoJSON name → original GeoJSON name
#     geojson_names = {
#         _normalize(feat["properties"][FEATURE_KEY.split(".")[-1]]): feat["properties"][FEATURE_KEY.split(".")[-1]]
#         for feat in geojson["features"]
#     }

#     # Map HHI province names to their GeoJSON equivalents
#     hhi_df["Province_GeoJSON"] = hhi_df["Province"].apply(
#         lambda p: geojson_names.get(_normalize(p), p)   # fall back to original if no match
#     )

#     # ── Flag unmatched provinces so you can fix them ─────────────────
#     unmatched = hhi_df[hhi_df["Province_GeoJSON"] == hhi_df["Province"]].copy()
#     unmatched = unmatched[
#         ~unmatched["Province"].apply(_normalize).isin(geojson_names)
#     ]
#     if not unmatched.empty:
#         with st.expander(f"⚠️ {len(unmatched)} province(s) not matched to GeoJSON — click to review"):
#             st.dataframe(unmatched[["Province", "HHI_Score"]], use_container_width=True)
#             st.caption(
#                 "These provinces appear in your dataset but have no matching feature "
#                 "in the GeoJSON. Check for spelling differences or adjust `FEATURE_KEY`."
#             )

#     # ── Instantiate px.choropleth ─────────────────────────────────────
#     fig_map = px.choropleth(
#         hhi_df,
#         geojson=geojson,

#         # featureidkey must point to the GeoJSON property that holds
#         # the province name — must match what Province_GeoJSON contains.
#         featureidkey=FEATURE_KEY,

#         # The DataFrame column that joins to featureidkey
#         locations="Province_GeoJSON",

#         # The column that drives the fill colour
#         color="HHI_Score",

#         hover_name="Province",
#         hover_data={
#             "HHI_Score": True,
#             "Province_GeoJSON": False,   # hide the internal join column
#         },

#         # YlOrRd: yellow (low HHI / competitive) → dark red (high HHI / monopoly)
#         color_continuous_scale="YlOrRd",
#         range_color=(0, 10_000),         # standard HHI scale

#         title=f"Dynastic Concentration by Province (HHI) · {selected_year}",
#         template=PLOTLY_TEMPLATE,

#         # Restrict the map frame to the Philippines bounding box
#         fitbounds="locations",
#         basemap_visible=False,
#     )

#     fig_map.update_geos(
#         visible=False,          # hide the default world basemap tiles
#         bgcolor=BG_COLOR,
#         framecolor="#30363d",
#         showland=True,          landcolor="#1c2128",
#         showocean=True,         oceancolor="#0d1117",
#         showcoastlines=True,    coastlinecolor="#30363d",
#         showlakes=False,
#         projection_type="mercator",
#     )

#     fig_map.update_traces(
#         marker_line_color="#30363d",    # province border colour
#         marker_line_width=0.6,
#     )

#     fig_map.update_layout(
#         paper_bgcolor=PAPER_COLOR,
#         font=dict(family="IBM Plex Mono, monospace", color="#c9d1d9"),
#         height=620,
#         margin=dict(l=0, r=0, t=50, b=10),
#         coloraxis_colorbar=dict(
#             title=dict(text="HHI Score", font=dict(size=11)),
#             tickvals=[0, 2500, 5000, 7500, 10_000],
#             ticktext=["0<br>(Competitive)", "2,500", "5,000", "7,500", "10,000<br>(Monopoly)"],
#             tickfont=dict(size=10),
#             len=0.75,
#             thickness=14,
#             bgcolor=PAPER_COLOR,
#             bordercolor="#30363d",
#             borderwidth=1,
#         ),
#     )

#     st.plotly_chart(fig_map, use_container_width=True)




#     # ── 2. DEMOCRACY SCATTERPLOT ──────────────────────────────────
#     st.markdown("<div class='section-header'>Democracy Scatterplot · Province Bubbles</div>",
#                 unsafe_allow_html=True)

#     scatter_data = (
#         df_year.groupby("Province")
#         .agg(
#             unique_communities=("Community", "nunique"),
#             total_seats=("Community", "count"),
#         )
#         .reset_index()
#     )
#     dominant = (
#         df_year.groupby(["Province", "Community"])
#         .size()
#         .reset_index(name="cnt")
#     )
#     dominant_pct = dominant.loc[
#         dominant.groupby("Province")["cnt"].idxmax()
#     ][["Province", "cnt"]].rename(columns={"cnt": "dominant_cnt"})
#     scatter_data = scatter_data.merge(dominant_pct, on="Province")
#     scatter_data["dominant_pct"] = (
#         scatter_data["dominant_cnt"] / scatter_data["total_seats"] * 100
#     ).round(1)

#     # -- Instantiate scatterplot
#     fig_scatter = px.scatter(
#         scatter_data,
#         x="unique_communities",
#         y="dominant_pct",
#         size="total_seats",
#         color="dominant_pct",
#         color_continuous_scale="RdYlGn_r",
#         hover_name="Province",
#         hover_data={"unique_communities": True,
#                     "dominant_pct": True,
#                     "total_seats": True},
#         labels={
#             "unique_communities": "Distinct Clans in Power",
#             "dominant_pct": "% Seats by Largest Clan",
#             "total_seats": "Total Seats",
#         },
#         title=f"Political Diversity vs. Clan Dominance · {selected_year}",
#         template=PLOTLY_TEMPLATE,
#     )
#     fig_scatter.update_layout(
#         **_base_layout(
#             height=420,
#             coloraxis_colorbar=dict(
#                 title="Dominant %", tickfont=dict(size=10)
#             ),
#         )
#     )
#     fig_scatter.update_traces(
#         marker=dict(line=dict(width=1, color="#0d1117")),
#         textposition="top center",
#     )
#     # Reference lines: quadrant guides
#     fig_scatter.add_hline(y=50, line_dash="dot", line_color="#30363d",
#                            annotation_text="50% dominance",
#                            annotation_font_color="#8b949e",
#                            annotation_font_size=10)
#     st.plotly_chart(fig_scatter, use_container_width=True)

#     st.divider()

#     # ── 3. TURNCOATISM TRACKER — Sankey ──────────────────────────
#     st.markdown("<div class='section-header'>Turncoatism Tracker · Sankey Diagram</div>",
#                 unsafe_allow_html=True)

#     # Top 10 largest national clans
#     top10_national = (
#         df.groupby("Community").size().nlargest(10).index.tolist()
#     )

#     # Build party transitions between the two most recent consecutive years
#     available_years = sorted(df["Year"].unique())
#     if len(available_years) >= 2:
#         y_prev, y_curr = available_years[-2], available_years[-1]
#     else:
#         y_prev, y_curr = available_years[0], available_years[0]

#     df_prev = df[(df["Year"] == y_prev) & (df["Community"].isin(top10_national))]
#     df_curr = df[(df["Year"] == y_curr) & (df["Community"].isin(top10_national))]

#     # Aggregate: Community × Party → count
#     sankey_prev = (
#         df_prev.groupby(["Community", "Party"])
#         .size().reset_index(name="n")
#     )
#     sankey_curr = (
#         df_curr.groupby(["Community", "Party"])
#         .size().reset_index(name="n")
#     )

#     # Build Sankey node list: source = "Clan X | Party A | 2019"
#     #                         target = "Clan X | Party B | 2022"
#     all_src_labels = [
#         f"Clan {r['Community']} · {r['Party']} ({y_prev})"
#         for _, r in sankey_prev.iterrows()
#     ]
#     all_tgt_labels = [
#         f"Clan {r['Community']} · {r['Party']} ({y_curr})"
#         for _, r in sankey_curr.iterrows()
#     ]
#     all_labels = list(dict.fromkeys(all_src_labels + all_tgt_labels))
#     label_idx  = {lbl: i for i, lbl in enumerate(all_labels)}

#     # Match on (Community) — transitions between party affiliations
#     sankey_source, sankey_target, sankey_value = [], [], []
#     for _, r_prev in sankey_prev.iterrows():
#         matches = sankey_curr[sankey_curr["Community"] == r_prev["Community"]]
#         for _, r_curr in matches.iterrows():
#             src_lbl = f"Clan {r_prev['Community']} · {r_prev['Party']} ({y_prev})"
#             tgt_lbl = f"Clan {r_curr['Community']} · {r_curr['Party']} ({y_curr})"
#             if src_lbl in label_idx and tgt_lbl in label_idx:
#                 sankey_source.append(label_idx[src_lbl])
#                 sankey_target.append(label_idx[tgt_lbl])
#                 sankey_value.append(int(r_prev["n"]))

#     # -- Instantiate Sankey diagram
#     fig_sankey = go.Figure(
#         go.Sankey(
#             arrangement="snap",
#             node=dict(
#                 label=all_labels,
#                 pad=12,
#                 thickness=16,
#                 color="#58a6ff",
#                 line=dict(color="#0d1117", width=0.5),
#                 hovertemplate="%{label}<br>Total: %{value}<extra></extra>",
#             ),
#             link=dict(
#                 source=sankey_source,
#                 target=sankey_target,
#                 value=sankey_value,
#                 color="rgba(88,166,255,0.18)",
#                 hovertemplate=(
#                     "%{source.label} → %{target.label}<br>"
#                     "Officeholders: %{value}<extra></extra>"
#                 ),
#             ),
#         )
#     )
#     fig_sankey.update_layout(
#         **_base_layout(
#             title=f"Clan Party Shifts · {y_prev} → {y_curr} (Top 10 Clans)",
#             height=520,
#             font=dict(size=10),
#         )
#     )
#     st.plotly_chart(fig_sankey, use_container_width=True)

#     st.divider()

#     # ── 4. DEEP ROOT LEAGUE TABLE ─────────────────────────────────
#     st.markdown("<div class='section-header'>Deep Root League Table · Horizontal Bar</div>",
#                 unsafe_allow_html=True)

#     # Proxy for "consecutive years in power": count distinct years per community
#     deep_root = (
#         df.groupby("Community")["Year"]
#         .nunique()
#         .reset_index(name="Cycles in Power")
#         .sort_values("Cycles in Power", ascending=False)
#         .head(20)
#         .reset_index(drop=True)
#     )
#     deep_root["Clan"] = "Clan " + deep_root["Community"].astype(str)

#     # Seat volume (bubble size proxy → bar opacity or secondary bar)
#     seat_vol = df.groupby("Community").size().reset_index(name="Total Seats")
#     deep_root = deep_root.merge(seat_vol, on="Community")

#     # -- Instantiate horizontal bar chart
#     fig_bar = go.Figure(
#         go.Bar(
#             x=deep_root["Cycles in Power"],
#             y=deep_root["Clan"],
#             orientation="h",
#             marker=dict(
#                 color=deep_root["Cycles in Power"],
#                 colorscale="Blues",
#                 line=dict(color="#0d1117", width=0.5),
#                 colorbar=dict(title="Cycles", tickfont=dict(size=10)),
#             ),
#             customdata=deep_root[["Total Seats", "Community"]].values,
#             hovertemplate=(
#                 "<b>%{y}</b><br>"
#                 "Election cycles present: %{x}<br>"
#                 "Total seats (all years): %{customdata[0]}<extra></extra>"
#             ),
#             text=deep_root["Cycles in Power"],
#             textposition="outside",
#             textfont=dict(size=11, color="#8b949e"),
#         )
#     )
#     fig_bar.update_layout(
#         **_base_layout(
#             title="Top 20 Most Deeply Rooted Clans (by Election Cycles Present Nationally)",
#             height=540,
#             yaxis=dict(autorange="reversed", gridcolor=GRID_COLOR),
#         )
#     )
#     fig_bar.update_xaxes(title_text="Distinct Election Cycles")
#     fig_bar.update_yaxes(title_text="")
#     st.plotly_chart(fig_bar, use_container_width=True)


# ─────────────────────────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <hr>
    <div style="text-align:center;color:#30363d;font-size:0.75rem;
                font-family:'IBM Plex Mono',monospace;padding:12px 0 24px;">
        Philippine Clan Watch Dashboard · Leiden community detection ·
        Data: COMELEC public records ·
        Built with Streamlit + Plotly
    </div>
    """,
    unsafe_allow_html=True,
)
"""
pages/landing.py
Landing page — project overview, methodology, mathematics, and acknowledgements.
"""

import streamlit as st
import plotly.graph_objects as go
import math

st.set_page_config(page_title="About — PH Clan Watch", page_icon="🇵🇭", layout="wide")

# ── Hero ─────────────────────────────────────────────────────────────────────────

st.title("🇵🇭 Philippine Dynasty Network Dashboard")


# ── About the Project ─────────────────────────────────────────────────────────────

st.subheader("About the Project")

tab1,tab2,tab3,tab4 = st.tabs(['Rationale', 'Goal', 'Acknowledgements', 'Disclaimer'])

with tab1:
    st.caption('WHY DO POLITICAL DYNASTIES MATTER IN THE PHILIPPINES')

    st.markdown("""Political power in the Philippines has long been concentrated within families, making the nation one of the most dynastic democracies in the world—and the highest-ranking in Asia **[1]**. From 2004 to 2022, the proportion of elected positions held by dynastic politicians increased from around 40% to over 50%. By the 2025 elections, dynasties controlled an overwhelming 87% of provincial governments **[2]**. Despite constitutional provisions intended to prevent the monopolization of power, political families continuously circumvent term limits by rotating positions among relatives, acting as an institutional mechanism that reproduces power across generations **[3]**.""")

with tab2:
    st.caption('MOTIVATION AND GOAL')

    st.markdown('''Traditionally, dynasties were simply categorized as "thin" (single-office succession) or "fat" (multiple relatives in office) **[4]**. However, these simple labels fail to capture the complex, evolving web of alliances and power distribution. This project shifts this approach by applying  **Graph Theory** and **Network Analysis**, fields in mathematics that can show provincial political environments as complex, interconnected networks. The hope is that this will allow voters and the general public to visually explore how political clans are structured, how power concentrates, and how deeply entrenched these networks are across the nation.''')

with tab3:       
    st.caption('ACKNOWLEDGEMENTS')

    st.markdown("""
    This dashboard was developed as a final project for a Data Visualization class. The focus is visualizating the structure of political dynasties. To do this, I heavily rely on the meticulous data gathering, cleaning, and processing by the authors below. Without them, this project is not possible at all.""")

    st.caption('DATA AND METHODOLOGY SOURCES')
    st.markdown("""
    The data, network definitions, and graph theory methodology powering this visualization are heavily adapted from independent academic research:

    * **Primary Data & Methodology Reference:** 
        * R. Acuña, A. Alejandro, and R. Leung. The families that stay together: A network analysis of dynastic power in Philippine politics. arXiv. Undergraduate thesis, Ateneo de Manila University. 2025. url: https://arxiv.org/abs/2505.21280.
            * The 2004–2022 historical dataset and the foundational methodology for measuring dynastic networks—including the graph theory principles, the Leiden community detection application, and the use of the HHI, CGC, CCD, and ACC metrics—are directly borrowed from their work.
        * A. Garcia and L. Montemayor. Power in the Network: Dynastic Persistence, Network Structure, and Economic Development in Philippine Local Politics. Undergraduate thesis, Ateneo de Manila University. 2026.
            * **Supplemental 2025 Data:** Department of the Interior and Local Government (DILG) Masterlist and the Commission on Elections (COMELEC).""")

with tab4:
    st.caption('DISCLAIMER')

    st.markdown("""*The creator of this dashboard is not affiliated with the original thesis research team. This project strictly utilizes their published datasets and methodological framework for educational and public data visualization purposes.*""")

st.markdown("---")

# ── Dataset & Scope ───────────────────────────────────────────────────────────────

st.header("Dataset & Scope")

st.markdown("The data powering this dashboard spans eight election cycles over two decades, analyzing the inferred relationships of over 140,000 local officials.")

col1, col2, col3 = st.columns(3, border=True)
col1.metric("📅 Election Years", "2004 – 2025")
col2.metric("🔎 Positions Tracked", "7 Local Offices")
col3.metric("🏠 Provinces Covered", "80")

tab_sources, tab_scope, tab_positions = st.tabs(["Data Sources", "Geographical Scope", "Elected Positions"])

with tab_sources:
    st.markdown("The historical data (2004–2022) is adapted from the comprehensive dataset compiled by Acuña et al. (2025). The most recent 2025 election data was integrated using the Department of the Interior and Local Government (DILG) Masterlist and verified against Commission on Elections (COMELEC) records.")

with tab_scope:
    st.markdown("We map the networks of 80 provinces. *(Note: Sulu, Tawi-tawi, Compostela Valley, North Cotabato, Davao de Oro, Dinagat Islands, and Davao Occidental are excluded due to insufficient or incomplete data).*")

with tab_positions:
    st.markdown("""
    * Congressional District Representative
    * Provincial Governor & Vice Governor
    * Provincial Board Member
    * City/Municipal Mayor & Vice Mayor
    * City/Municipal Councilor
    """)

st.markdown("---")

# ── Methodology ──────────────────────────────────────────────────────────────────

st.header("Methodology")

tab1, tab2, tab3, tab4, = st.tabs([
    "What is a graph?",
    "How are dynasty networks constructed?",
    "How are dynasties determined?",
    "Dynastic indicators",
    # "How to read the dashboard",
])

# ── Tab 1: Network fundamentals + annotated example ──────────────────────────────
with tab1:
    st.subheader("Network Fundamentals")
    st.markdown("""
    To map political dynasties, we model each province's political landscape as a
    **network (graph)**. A network is a structure made of two things:

    - **Nodes (vertices)** — each node is one elected politician.
    - **Edges (links)** — each edge is a line connecting two politicians who share
      family ties inferred from their names.

    Networks let us move beyond looking at politicians as isolated individuals and
    instead reveal the hidden family structures that bind them together.
    """)

    st.markdown("#### Anatomy of a dynasty network")
    with st.container(border=True):
        st.caption(
            "Hover over any element below. Node size reflects position weight; "
            "edge thickness reflects relationship strength; color identifies the clan."
        )

        # ── Node positions (two clusters = two clans) ─────────────────────────────
        nodes = [
            # Clan A (red-orange) — 3 members
            dict(id=0, x=0.18, y=0.72, label="Gov. Reyes",    pw=4.0, clan="Reyes Clan",    color="#e63946", pos="Governor"),
            dict(id=1, x=0.10, y=0.38, label="Rep. Reyes",    pw=2.0, clan="Reyes Clan",    color="#e63946", pos="Representative"),
            dict(id=2, x=0.34, y=0.38, label="Mayor Reyes",   pw=1.5, clan="Reyes Clan",    color="#e63946", pos="Mayor"),
            # Clan B (blue) — 3 members
            dict(id=3, x=0.72, y=0.72, label="Gov. Santos",   pw=4.0, clan="Santos Clan",   color="#457b9d", pos="Governor"),
            dict(id=4, x=0.60, y=0.38, label="Rep. Santos",   pw=2.0, clan="Santos Clan",   color="#457b9d", pos="Representative"),
            dict(id=5, x=0.85, y=0.38, label="Mayor Santos",  pw=1.5, clan="Santos Clan",   color="#457b9d", pos="Mayor"),
        ]

        # ── Edge definitions (within-clan only) ───────────────────────────────────
        edges = [
            # Clan A
            dict(src=0, tgt=1, w=6.0, label="Same surname + middle name\nConsanguinity = 0.75"),
            dict(src=0, tgt=2, w=6.0, label="Same surname + middle name\nConsanguinity = 0.75"),
            dict(src=1, tgt=2, w=2.25, label="Same surname\nConsanguinity = 0.75"),
            # Clan B
            dict(src=3, tgt=4, w=6.0,  label="Same surname + middle name\nConsanguinity = 0.75"),
            dict(src=3, tgt=5, w=6.0,  label="Same surname + middle name\nConsanguinity = 0.75"),
            dict(src=4, tgt=5, w=2.25, label="Same surname\nConsanguinity = 0.75"),
        ]

        node_x = [n["x"] for n in nodes]
        node_y = [n["y"] for n in nodes]

        fig_net = go.Figure()

        # Draw edges first (so nodes sit on top)
        for e in edges:
            s, t = nodes[e["src"]], nodes[e["tgt"]]
            # Width scaled between 1 and 8 for visual clarity
            lw = max(1, min(8, e["w"] / 1.2))
            fig_net.add_trace(go.Scatter(
                x=[s["x"], t["x"], None],
                y=[s["y"], t["y"], None],
                mode="lines",
                line=dict(width=lw, color=s["color"]),
                opacity=0.55,
                hoverinfo="skip",
                showlegend=False,
            ))

        # Draw invisible wide lines for easier edge hover
        for e in edges:
            s, t = nodes[e["src"]], nodes[e["tgt"]]
            mx, my = (s["x"] + t["x"]) / 2, (s["y"] + t["y"]) / 2
            fig_net.add_trace(go.Scatter(
                x=[mx], y=[my],
                mode="markers",
                marker=dict(size=14, color="rgba(0,0,0,0)", opacity=0),
                customdata=[[e["label"]]],
                hovertemplate="<b>Edge</b><br>%{customdata[0]}<extra></extra>",
                showlegend=False,
            ))

        # Draw nodes
        for n in nodes:
            sz = 20 + n["pw"] * 10
            fig_net.add_trace(go.Scatter(
                x=[n["x"]], y=[n["y"]],
                mode="markers",
                marker=dict(size=sz, color=n["color"], line=dict(width=2, color="#ffffff")),
                customdata=[[n["label"], n["clan"], n["pos"], n["pw"]]],
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Clan: %{customdata[1]}<br>"
                    "Position: %{customdata[2]}<br>"
                    "Position Weight: %{customdata[3]}<extra></extra>"
                ),
                showlegend=False,
            ))

        # Node labels (permanent, small)
        for n in nodes:
            fig_net.add_annotation(
                x=n["x"], y=n["y"] - 0.11,
                text=n["label"],
                showarrow=False,
                font=dict(size=11, color="#cccccc"),
                align="center",
            )

        # ── Callout annotations ───────────────────────────────────────────────────

        # Callout: NODE
        fig_net.add_annotation(
            x=nodes[0]["x"], y=nodes[0]["y"],
            ax=-120, ay=-30,
            axref="pixel", ayref="pixel",
            arrowhead=2, arrowwidth=1.5, arrowcolor="#aaaaaa",
            bgcolor="#1e2030", bordercolor="#555", borderwidth=1,
            font=dict(size=11, color="#eeeeee"),
            text="<b>Node</b><br>One politician.<br>Size = position weight.<br>Color = clan.",
            align="left",
        )

        # Callout: EDGE (point to midpoint of Gov→Rep edge in Clan A)
        emid_x = (nodes[0]["x"] + nodes[1]["x"]) / 2
        emid_y = (nodes[0]["y"] + nodes[1]["y"]) / 2
        fig_net.add_annotation(
            x=emid_x, y=emid_y,
            ax=-140, ay=40,
            axref="pixel", ayref="pixel",
            arrowhead=2, arrowwidth=1.5, arrowcolor="#aaaaaa",
            bgcolor="#1e2030", bordercolor="#555", borderwidth=1,
            font=dict(size=11, color="#eeeeee"),
            text="<b>Edge</b><br>Inferred family tie.<br>Thickness = strength<br>(consanguinity × power).",
            align="left",
        )

        # Callout: CLUSTER
        fig_net.add_annotation(
            x=0.22, y=0.95,
            showarrow=False,
            bgcolor="#1e2030", bordercolor="#e63946", borderwidth=1.5,
            font=dict(size=11, color="#eeeeee"),
            text="<b>Cluster A — Reyes Clan</b><br>Tightly grouped nodes<br>= one political dynasty.",
            align="left",
        )
        fig_net.add_annotation(
            x=0.73, y=0.95,
            showarrow=False,
            bgcolor="#1e2030", bordercolor="#457b9d", borderwidth=1.5,
            font=dict(size=11, color="#eeeeee"),
            text="<b>Cluster B — Santos Clan</b><br>Separate color = different<br>political dynasty.",
            align="left",
        )

        fig_net.update_layout(
            height=420,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(visible=False, range=[-0.05, 1.05]),
            yaxis=dict(visible=False, range=[0.15, 1.08]),
            hovermode="closest",
        )

        st.plotly_chart(fig_net, use_container_width=True)

    st.markdown("""
    | Visual element | What it encodes |
    |---|---|
    | Node **color** | Clan / community membership |
    | Node **size** | Position weight (Governor > Mayor > Councilor) |
    | Edge **thickness** | Relationship strength: consanguinity score × both positions' weights |
    | Cluster **density** | How entrenched a dynasty is — more edges = more interconnected family |""")

    st.info('Nodes with no edges are independent politicians with no detectable family ties to others in the same province and year.')


# ── Tab 2: Consanguinity scoring ──────────────────────────────────────────────────
with tab2:
    st.subheader("Consanguinity Scoring")
    st.info(
        "**Key assumption:** Philippine naming conventions carry genealogical information. "
        "A person's middle name is typically their mother's maiden surname, and their last name "
        "is their father's. Shared surnames and middle names are used as a"
        "proxy for biological and affinal (marriage-based) family ties."
    )

    st.markdown("#### Step 1 — Pairwise relationship scoring")
    st.markdown("""
    For every pair of politicians *(i, j)* in the same province and year,
    we assign a **consanguinity score** based on how their names overlap:
    """)

    col_table, col_example = st.columns([1.2, 1])
    with col_table:
        st.markdown("""
        | Condition | Score | Interpretation |
        |---|:---:|---|
        | Same last name **and** same middle name | **1.00** | Identical branch — likely siblings or same person across roles |
        | Same last name only | **0.75** | Paternal line — likely siblings, cousins, or parent–child |
        | Cross-match: one's last name = other's middle name | **0.50** | Maternal link — in-law or intermarriage |
        | Same middle name only | **0.25** | Shared maternal grandmother — distant common ancestor |
        | No match | **0.00** | No detectable family tie |
        """)
    with col_example:
        st.markdown("**Example: Gov. Maria Santos-Reyes vs. Rep. Juan Santos-Cruz**")
        st.markdown("""
        - Last name: `SANTOS` = `SANTOS` ✓  
        - Middle name: `REYES` ≠ `CRUZ` ✗  
        - → **Score = 0.75** (same last name only)
        """)
        st.markdown("**Example: Gov. Ana Reyes-Santos vs. Rep. Juan Santos-Cruz**")
        st.markdown("""
        - Last name: `REYES` ≠ `SANTOS`  
        - Gov's last `REYES` ≠ Rep's middle `CRUZ`  
        - Gov's middle `SANTOS` = Rep's last `SANTOS` ✓  
        - → **Score = 0.50** (cross-surname middle-name match)
        """)

    st.markdown("#### Step 2 — Edge weight calculation")
    st.markdown("""
    Raw consanguinity scores alone ignore *how powerful* the politicians are.
    A family tie between two governors is structurally more significant than
    one between two barangay councilors. We weight each edge accordingly:
    """)
    st.latex(r"w(i,\,j) = \text{PositionWeight}(i) \times \text{PositionWeight}(j) \times \text{Consanguinity}(i,\,j)")

    c1, c2, c3 = st.columns(3, border=True)
    c1.metric('Member, House of Representatives', '5.0')
    c2.metric('Governor', '5.0')
    c3.metric('Mayor', '5.0')

    c1b, c2b, c3b, c4b = st.columns(4, border=True)
    c1b.metric("Vice Governor", "3.0")
    c2b.metric("Vice Mayor", "3.0")
    c3b.metric("Councilor", "2.0")
    c4b.metric("Provincial Board Member", "2.0")

    st.markdown("""
    **Worked example:** Governor Reyes (PW = 5) and Mayor Reyes (PW = 5) share the same
    last name only → consanguinity = 0.75.

    $$w = 5 \\times 5 \\times 0.75 = 18.75$$

    This edge gets weight **18.75** — a thick line in the network graph.
    """)


# ── Tab 3: Community detection ────────────────────────────────────────────────────
with tab3:
    st.subheader("Community Detection — The Leiden Algorithm")

    col_left, col_right = st.columns([1.6, 1])
    with col_left:
        st.markdown("""
        Once the weighted network is built, we face a core question:
        **which politicians form a single political dynasty?**

        Surnames alone are insufficient — intermarriages and distant relatives
        can link families across many degrees of separation, creating sprawling
        networks that are hard to cut cleanly by hand.

        We use the **Leiden algorithm**, a state-of-the-art community detection
        method that identifies groups of nodes that are:

        - **Densely connected internally** (many strong edges within the group), and
        - **Sparsely connected externally** (few or weak edges to other groups).

        Each resulting **Community ID** is our structural proxy for one political
        dynasty. Politicians in the same community form a clan.
        """)
    with col_right:
        st.info(
            "**Why Leiden and not Louvain?**\n\n"
            "The older Louvain algorithm can produce poorly connected or even "
            "disconnected communities. Leiden guarantees that every detected "
            "community is internally connected, making clan boundaries more "
            "meaningful and stable."
        )
        st.success(
            "**Resolution parameter:** Controls how finely the algorithm slices "
            "the network. A higher value produces smaller, more granular clans; "
            "a lower value merges related families into broader dynasties."
        )

    st.markdown("#### From network to dynasty: step by step")

    steps = [
        ("1. Build the provincial network",
         "All politicians in a province for a given election year become nodes. "
         "Edges are added for every pair with consanguinity > 0, weighted by the formula above."),
        ("2. Run Leiden community detection",
         "The algorithm partitions the network into communities by maximising modularity — "
         "a measure of how much more densely connected communities are internally "
         "versus what would be expected by chance."),
        ("3. Assign Community IDs",
         "Each node receives a Community ID integer. Politicians with the same ID "
         "belong to the same detected dynasty. IDs are local to each province — "
         "Community 1 in Batangas is unrelated to Community 1 in Cebu."),
        ("4. Label clans",
         "Each community is labelled using the two most frequent surnames/middle names "
         "among its members (e.g. 'Reyes-Santos'), giving a human-readable clan identifier."),
    ]
    for title, body in steps:
        with st.expander(title):
            st.markdown(body)

    st.markdown("""
    > **Important limitation:** The consanguinity heuristic can produce false positives
    > for very common Filipino surnames (e.g. *Santos*, *Reyes*, *Garcia*). Two unrelated
    > politicians sharing a common surname may be placed in the same community even without
    > a real family tie. Results should be interpreted alongside qualitative knowledge of
    > local political families.
    """)


# ── Tab 4: Dynastic indicators ────────────────────────────────────────────────────
with tab4:
    st.subheader("Dynastic Indicators — Measuring Dynasty Strength")
    st.markdown("""
    Four composite scores quantify different **dimensions** of political dynasty power
    in a province. They are computed from the weighted network and the position data,
    and are available for every province–year pair in the dataset.
    """)

    ind1, ind2, ind3, ind4 = st.tabs(["HHI", "CGC", "CCD", "ACC"])

    with ind1:
        st.markdown("#### HHI — Herfindahl-Hirschman Index")
        st.markdown("""
        Borrowed from economics (where it measures market concentration), HHI here
        measures how monopolised political power is across clans in a province.
        """)
        st.latex(r"\text{HHI} = \sum_{k=1}^{K} \left(100 \times s_k\right)^2")
        st.markdown("""
        where $s_k$ is clan $k$'s share of total **position weight** held in that year.

        | Score range | Interpretation |
        |---|---|
        | < 1,500 | Competitive — power spread across many clans |
        | 1,500 – 2,500 | Moderately concentrated |
        | > 2,500 | Highly concentrated — one or two dominant clans |
        | 10,000 | Theoretical maximum (one clan holds all positions) |

        **Higher HHI = more dynasty-dominated province.**
        """)

    with ind2:
        st.markdown("#### CGC — Clan Gini Coefficient")
        st.markdown("""
        Measures *inequality* in **network influence** across individual politicians,
        using each politician's weighted degree (sum of all edge weights connected to them)
        as a proxy for influence.
        """)
        st.latex(r"G = \frac{\displaystyle\sum_i \sum_j |d_i - d_j|}{2n \displaystyle\sum_i d_i}")
        st.markdown("""
        where $d_i$ is the weighted degree of politician $i$ in the provincial network.

        - **Range:** 0 – 1
        - **G = 0:** Every politician has identical network influence (perfectly equal).
        - **G = 1:** One politician concentrates all network connections (maximum inequality).

        A province where one family patriarch connects to dozens of officials scores
        near 1; a province where all officials have similar connectivity scores near 0.
        """)

    with ind3:
        st.markdown("#### CCD — Clan Connectivity Density")
        st.markdown("""
        Measures how tightly **woven together** the overall dynasty network is —
        i.e., how few isolated political actors exist.
        """)
        st.latex(r"\text{CCD} = 1 - \frac{\text{Connected components}}{|\text{Nodes}|}")
        st.markdown("""
        - **Range:** approaches 0 to 1
        - If every politician is linked to at least one other, the network has few
          components and CCD is high.
        - A province full of independent single-person "dynasties" (many components,
          each of size 1) scores low.

        **Higher CCD = more interconnected dynasty ecosystem.**
        """)

    with ind4:
        st.markdown("#### ACC — Aggregate Clan Connectivity")
        st.markdown("""
        Measures the **internal resilience** of each clan — how structurally robust
        the clan is to losing individual members.
        """)
        st.latex(
            r"\text{ACC} = \sum_{c} \frac{\kappa(G_c)}{|V(G_c)|}"
        )
        st.markdown("""
        where $\\kappa(G_c)$ is the **node connectivity** of clan $c$'s subgraph —
        the minimum number of nodes whose removal would disconnect the clan's network.
        Summed and normalised across all clans in the province.

        - **ACC = 0:** Every clan is a tree — removing one person breaks it.
        - **Higher ACC:** Clans have redundant connections and can withstand member turnover.

        This captures whether dynastic power is **institutionalised** (many internal
        connections, high ACC) or **personalised** (dependent on a single patriarch, low ACC).
        """)

    st.markdown("---")
    st.markdown("""
    **Interpreting the four indicators together:**

    | Scenario | HHI | CGC | CCD | ACC |
    |---|:---:|:---:|:---:|:---:|
    | Single dominant patriarch-led dynasty | High | High | Low | Low |
    | One powerful but internally connected clan | High | Med | Med | High |
    | Many intermarried clans forming one network | Med | Low | High | Med |
    | Competitive province, many small clans | Low | Low | Low | Low |
    """)


# # ── Tab 5: How to read the dashboard ─────────────────────────────────────────────
# with tab5:
#     st.subheader("How to Read the Dashboard")

#     st.markdown("#### Provincial Analysis page")
#     charts_prov = {
#         "Dynasty Network Graph": (
#             "Each dot is a politician; dot size = position weight. "
#             "Dots of the same color belong to the same clan. "
#             "Lines between dots = inferred family ties; thicker = stronger relationship. "
#             "**Hover over any node** to see the politician's name, clan, and position weight. "
#             "Look for dense, large-node clusters — those are entrenched dynasties."
#         ),
#         "Clan × Position Heatmap": (
#             "Rows = position types (Governor, Mayor, etc.). "
#             "Columns = top clans (labeled by surname mode). "
#             "**Dark red cells** = that clan dominates that office type. "
#             "A clan with a dark cell in 'Governor' and 'Mayor' simultaneously holds executive power at multiple levels."
#         ),
#         "Dynastic Indicator Trend": (
#             "One line chart per indicator (selectable via radio button). "
#             "X-axis = election year; Y-axis = indicator score. "
#             "A **rising trend** = dynasty power consolidating over time. "
#             "The dotted vertical line marks the currently selected year."
#         ),
#         "Total Positions Over Time": (
#             "Stacked area chart showing how many positions each top clan held across all election years. "
#             "A clan that grows its area over time is expanding. "
#             "A clan that shrinks or disappears lost power — by electoral loss, death, or fragmentation."
#         ),
#         "Top 15 by Weighted Degree": (
#             "Horizontal bar chart of the most *connected* politicians in the network. "
#             "Weighted degree = sum of all edge weights attached to a node. "
#             "High weighted degree = politically powerful AND deeply embedded in a large family network. "
#             "This is different from merely holding a high-weight position — a lone Governor with no family ties ranks low here."
#         ),
#     }
#     for chart, desc in charts_prov.items():
#         with st.expander(chart):
#             st.markdown(desc)

#     st.markdown("#### National Analysis page")
#     charts_nat = {
#         "Dynastic Concentration Map": (
#             "Choropleth map of the Philippines colored by the selected indicator score. "
#             "**Darker red = higher score** (more concentrated / more dynastic). "
#             "Hover over any province to see the exact score. "
#             "Switch between Map and Bar Chart modes using the radio button above."
#         ),
#         "Democracy Scatterplot": (
#             "Each bubble is a province. "
#             "X-axis = number of unique clans in power (more = more pluralistic). "
#             "Y-axis = % of seats held by the single largest clan (higher = more dominated). "
#             "**Ideal democratic position: bottom-right** (many clans, none dominant). "
#             "**Danger zone: top-left** (few clans, one dominant). "
#             "Bubble size = HHI score."
#         ),
#         "Island Group Trend": (
#             "Line chart comparing mean indicator scores for Luzon, Visayas, Mindanao, and the Philippines overall. "
#             "The dotted purple line is the national average. "
#             "Use this to compare whether dynasty entrenchment is geographically concentrated."
#         ),
#         "Deep Root League Table": (
#             "Ranks clans by the longest consecutive streak of election cycles in which "
#             "they held at least one position, anywhere in the Philippines. "
#             "Bar length = cycles; color intensity = total position weight accumulated. "
#             "Hover to see which provinces the clan operates in."
#         ),
#     }
#     for chart, desc in charts_nat.items():
#         with st.expander(chart):
#             st.markdown(desc)

#     st.markdown("#### Politician Search page")
#     st.markdown("""
#     1. **Select a province** from the dropdown.
#     2. **Type a name** (partial match is fine — try just a surname).
#     3. If multiple matches appear, **select the exact politician** from the dropdown.
#     4. **Choose an election year** — the radio shows only years where that politician
#        appears in the dataset, along with the position they held that year.
#     5. The **ego-graph** renders: the politician is in the center, all their
#        family-network connections radiate outward to radius 2.
#        Direct connections (radius 1) are listed in the table below.
#     """)
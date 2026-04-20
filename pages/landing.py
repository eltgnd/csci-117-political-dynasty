"""
pages/landing.py
Landing page — project overview, methodology, mathematics, and acknowledgements.
"""

import streamlit as st

st.set_page_config(page_title="About — PH Clan Watch", page_icon="🇵🇭", layout="wide")

# ── Hero ─────────────────────────────────────────────────────────────────────────

st.title("🇵🇭 Philippine Clan Watch Dashboard")


# ── About the Project ─────────────────────────────────────────────────────────────

st.header("About the Project")

st.caption('WHY DO POLITICAL DYNASTIES MATTER IN THE PHILIPPINES')
st.markdown("""
Political power in the Philippines has long been concentrated within families, making the nation one of the most dynastic democracies in the world—and the highest-ranking in Asia. From 2004 to 2022, the proportion of elected positions held by dynastic politicians increased from around 40% to over 50%. By the 2025 elections, dynasties controlled an overwhelming 87% of provincial governments. Despite constitutional provisions intended to prevent the monopolization of power, political families continuously circumvent term limits by rotating positions among relatives, acting as an institutional mechanism that reproduces power across generations.""")

st.caption('MOTIVATION AND GOAL')
st.markdown('''Traditionally, dynasties were simply categorized as "thin" (single-office succession) or "fat" (multiple relatives in office). However, these simple labels fail to capture the complex, evolving web of alliances and power distribution. Built as a project for a Data Visualization class, this platform shifts the paradigm by applying **Graph Theory** and **Network Analysis**. We model provincial political environments as complex, interconnected networks, allowing voters and the general public to visually explore how political clans are structured, how power concentrates, and how deeply entrenched these networks are across the nation.''')

st.markdown("---")

# ── Dataset & Scope ───────────────────────────────────────────────────────────────

st.header("Dataset & Scope")

st.markdown("""
The data powering this dashboard spans eight election cycles over two decades, analyzing the inferred relationships of over 140,000 local officials.

* **Data Sources:** The historical data (2004–2022) is adapted from the comprehensive dataset compiled by Acuña et al. (2025). The most recent 2025 election data was integrated using the Department of the Interior and Local Government (DILG) Masterlist and verified against Commission on Elections (COMELEC) records.
* **Geographical Scope:** We map the networks of 80 provinces. *(Note: Sulu, Tawi-tawi, Compostela Valley, North Cotabato, Davao de Oro, Dinagat Islands, and Davao Occidental are excluded due to insufficient or incomplete data).*
* **Elected Positions Included:**
    * Congressional District Representative
    * Provincial Governor & Vice Governor
    * Provincial Board Member
    * City/Municipal Mayor & Vice Mayor
    * City/Municipal Councilor
""")

col1, col2, col3 = st.columns(3, border=True)
col1.metric("📅 Election Years", "2004 – 2025")
col2.metric("🔎 Positions Tracked", "7 Local Offices")
col3.metric("🏠 Provinces Covered", "80")

st.markdown("---")

# ── Methodology ──────────────────────────────────────────────────────────────────

st.header("Methodology")

st.subheader("Consanguinity Scoring")
st.markdown("""
The platform infers kinship between politicians using a **consanguinity heuristic** based on
shared surnames and middle names — a proxy for biological and affinal family ties common in
Philippine naming conventions.

| Condition | Consanguinity Score |
|---|---|
| Same Last Name **and** Same Middle Name | 1.00 (identical / same branch) |
| Same Last Name only | 0.75 (likely siblings / cousins) |
| Cross-surname middle-name match | 0.50 (in-law / maternal link) |
| Same Middle Name only | 0.25 (distant common ancestor) |
| No match | 0.00 (unrelated) |

Edge weights in the network are computed as:""")

st.latex(r"w(i, j) = \text{PositionWeight}(i) \times \text{PositionWeight}(j) \times \text{Consanguinity}(i, j)")
st.markdown("""This means connections between more powerful politicians in tighter family relationships
carry higher weight in the graph.
""")

st.subheader("Community Detection (The Leiden Algorithm)")
st.markdown("""
To identify distinct political families from thousands of elected officials, we rely on the **Leiden community detection algorithm**. 

Because familial relationships can be vast and tangled (e.g., intermarriages or distant relatives sharing common surnames), identifying a "clan" is not always straightforward. The Leiden algorithm solves this by analyzing the connections and isolating highly cohesive, densely connected groups of politicians. In our platform, every generated **Community ID** serves as a structural proxy for a definitive political dynasty, clustering together allied politicians who heavily dominate their local electoral networks.
""")

st.markdown("---")

# ── Dynastic Indicators ───────────────────────────────────────────────────────────

st.header("Dynastic Indicators")
st.markdown("Four composite scores quantify different facets of political dynasty strength.")

with st.expander("📊 HHI — Herfindahl-Hirschman Index", expanded=True):
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

st.markdown("---")

# ── Acknowledgements & Citations ──────────────────────────────────────────────────

st.header("Acknowledgements & Citations")

st.markdown("""
This dashboard was developed as a final project for a Data Visualization class. It aims to bring critical academic research regarding the structure of political dynasties to voters and the broader public.

### Data & Methodology Sources
The data, network definitions, and graph theory methodology powering this visualization are heavily adapted from independent academic research:

* **Primary Data & Methodology Reference:** 
    * R. Acuña, A. Alejandro, and R. Leung. The families that stay together: A network analysis of dynastic power in Philippine politics. arXiv. Undergraduate thesis, Ateneo de Manila University. 2025. url: https://arxiv.org/abs/2505.21280.
        * The 2004–2022 historical dataset and the foundational methodology for measuring dynastic networks—including the graph theory principles, the Leiden community detection application, and the use of the HHI, CGC, CCD, and ACC metrics—are directly borrowed from their work.
    * A. Garcia and L. Montemayor. Power in the Network: Dynastic Persistence, Network Structure, and Economic Development in Philippine Local Politics. Undergraduate thesis, Ateneo de Manila University. 2026.
        * **Supplemental 2025 Data:** Department of the Interior and Local Government (DILG) Masterlist and the Commission on Elections (COMELEC).

### Disclaimer
*The creator of this dashboard is not affiliated with the original thesis research team. This project strictly utilizes their published datasets and methodological framework for educational and public data visualization purposes.*
""")
"""
network_renderer.py
NetworkX → visual graph rendering.
"""

import os
import re
import tempfile

import networkx as nx
import plotly.graph_objects as go
from pyvis.network import Network

from config import PALETTE, DARK_BG


# ── Color utilities ──────────────────────────────────────────────────────────────

def make_color_map(communities) -> dict:
    return {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(sorted(set(communities)))}


# ── Tooltip injection ────────────────────────────────────────────────────────────

def _build_tooltip_js(node_data: list[dict]) -> str:
    """
    Build a JavaScript snippet that replaces every node's plain-text title
    with a real DOM element so vis.js renders it as styled HTML.

    node_data: list of dicts with keys: id, name, clan, pw
    """
    lines = ["(function() {", "  var tooltips = {"]
    for nd in node_data:
        # Escape single quotes in values
        name = nd["name"].replace("'", "\\'")
        clan = nd["clan"].replace("'", "\\'")
        pw   = nd["pw"]
        # Key is the node id (also the name string in our graph)
        lines.append(
            f"    '{name}': '<div style=\""
            f"font-family:sans-serif;font-size:13px;line-height:1.5;"
            f"background:#1e2030;color:#e0e0e0;border:1px solid #444;"
            f"border-radius:8px;padding:8px 12px;min-width:160px;"
            f"box-shadow:0 4px 12px rgba(0,0,0,0.5)\">"
            f"<span style=\"font-weight:700;font-size:14px;color:#ffffff\">{name}</span><br>"
            f"<span style=\"color:#aaaaaa\">Clan:</span> {clan}<br>"
            f"<span style=\"color:#aaaaaa\">Position Weight:</span> {pw}"
            f"</div>',"
        )
    lines += [
        "  };",
        "  function patchNodes() {",
        "    if (typeof network === 'undefined') { setTimeout(patchNodes, 200); return; }",
        "    var ids = network.body.data.nodes.getIds();",
        "    ids.forEach(function(id) {",
        "      if (tooltips[id]) {",
        "        var el = document.createElement('div');",
        "        el.innerHTML = tooltips[id];",
        "        network.body.data.nodes.update({id: id, title: el.firstChild});",
        "      }",
        "    });",
        "  }",
        "  setTimeout(patchNodes, 600);",
        "})();",
    ]
    return "\n".join(lines)


# ── pyvis renderer ───────────────────────────────────────────────────────────────

def pyvis_network_html(G: nx.Graph, label_map: dict, province: str = "") -> str:
    """
    Build a pyvis Network. Returns a self-contained HTML string for
    st.components.v1.html().

    - Dark background (#0e1117) matching Streamlit dark theme
    - No permanent node labels — name appears only on hover
    - Hover tooltip is a styled card injected as a real DOM element
    - Only intra-community edges rendered
    """
    net = Network(height="580px", width="100%", bgcolor=DARK_BG, font_color="#cccccc")
    net.set_options("""{
      "physics": {
        "enabled": true,
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100
        },
        "minVelocity": 0.75,
        "solver": "forceAtlas2Based"
      },
      "nodes": {
        "shape": "dot",
        "font": { "size": 0, "color": "rgba(0,0,0,0)" }
      },
      "edges": {
        "smooth": { "type": "continuous" },
        "color": { "color": "#333344", "highlight": "#aaaaaa", "hover": "#888888" },
        "width": 1
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 80,
        "hideEdgesOnDrag": true
      }
    }""")

    communities = nx.get_node_attributes(G, "community")
    pw_attrs    = nx.get_node_attributes(G, "position_weight")
    color_map   = make_color_map(communities.values())

    node_data = []  # collected for tooltip JS injection

    for node in G.nodes():
        comm  = communities.get(node, -1)
        color = color_map.get(comm, "#888888")
        pw    = float(pw_attrs.get(node, 1))
        size  = max(8, min(40, pw * 8))

        # Label map key is (province, community) tuple when province is known
        if province:
            clan_label = label_map.get((province, comm), label_map.get(comm, str(comm)))
        else:
            clan_label = label_map.get(comm, str(comm))

        # Placeholder plain-text title — will be replaced by injected DOM element
        net.add_node(
            node,
            label="",          # no permanent text label
            title=f"{node}",   # placeholder; overwritten by JS below
            color={
                "background": color,
                "border":     color,
                "highlight":  {"background": "#ffffff", "border": "#ffffff"},
                "hover":      {"background": "#dddddd", "border": "#ffffff"},
            },
            size=size,
        )
        node_data.append({"name": node, "clan": clan_label, "pw": pw})

    # Intra-community edges only
    for u, v, data in G.edges(data=True):
        if communities.get(u, -1) == communities.get(v, -1):
            net.add_edge(u, v, value=float(data.get("weight", 1)))

    # Write pyvis HTML to temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        net.save_graph(f.name)
        fname = f.name

    with open(fname, "r", encoding="utf-8") as f:
        html = f.read()
    os.unlink(fname)

    # ── Patch 1: dark background on the body ─────────────────────────────────────
    html = re.sub(
        r"<body[^>]*>",
        f"<body style='background-color:{DARK_BG};margin:0;padding:0;'>",
        html,
        count=1,
    )

    # ── Patch 2: inject tooltip DOM-element script just before </body> ────────────
    tooltip_js = _build_tooltip_js(node_data)
    inject = f"<script>\n{tooltip_js}\n</script>\n</body>"
    html = html.replace("</body>", inject, 1)

    return html


# ── Plotly fallback ──────────────────────────────────────────────────────────────

def plotly_network_figure(G: nx.Graph, label_map: dict, province: str = "") -> go.Figure:
    """Plotly spring-layout fallback. Supports dark mode."""
    import networkx as nx
    pos         = nx.spring_layout(G, seed=42)
    communities = nx.get_node_attributes(G, "community")
    pw_attrs    = nx.get_node_attributes(G, "position_weight")
    color_map   = make_color_map(communities.values())

    edge_x, edge_y = [], []
    for u, v, data in G.edges(data=True):
        if communities.get(u) == communities.get(v):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=0.8, color="#333344"), hoverinfo="none",
    ))

    for node in G.nodes():
        x, y  = pos[node]
        comm  = communities.get(node, -1)
        pw    = float(pw_attrs.get(node, 1))
        clan  = (label_map.get((province, comm), label_map.get(comm, str(comm)))
                 if province else label_map.get(comm, str(comm)))
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode="markers",
            marker=dict(size=max(8, pw * 8), color=color_map.get(comm, "#888888")),
            hovertemplate=f"<b>{node}</b><br>Clan: {clan}<br>PW: {pw}<extra></extra>",
            showlegend=False,
        ))

    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
        height=580,
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
    )
    return fig
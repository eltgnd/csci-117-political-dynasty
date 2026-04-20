"""
config.py
Shared constants for the Philippine Clan Watch Dashboard.
"""

import plotly.express as px

# ── Dataset paths ────────────────────────────────────────────────────────────────
DATA_PATH        = "data/political_dynasty.csv"
PRECOMPUTED_PATH = "data/precomputed_indicators.csv"

# ── Election years present in the dataset ───────────────────────────────────────
ELECTION_YEARS = [2004, 2007, 2010, 2013, 2016, 2019, 2022, 2025]

# ── Color palette for community/clan coloring ────────────────────────────────────
PALETTE = (
    px.colors.qualitative.Plotly
    + px.colors.qualitative.D3
    + px.colors.qualitative.G10
)

# ── Dynastic indicator display config ────────────────────────────────────────────
INDICATOR_COLORS = {
    "HHI": "#e63946",
    "CGC": "#457b9d",
    "CCD": "#2a9d8f",
    "ACC": "#e9c46a",
}

INDICATOR_LABELS = {
    "HHI": "Herfindahl-Hirschman Index",
    "CGC": "Clan Gini Coefficient",
    "CCD": "Clan Connectivity Density",
    "ACC": "Aggregate Clan Connectivity",
}

INDICATOR_HELP = {
    "HHI": "Seat concentration (higher = more monopolized by one clan)",
    "CGC": "Inequality of network influence (higher = more unequal)",
    "CCD": "Network cohesion (higher = more interconnected)",
    "ACC": "Internal clan resilience (higher = more robust clans)",
}

# score column name in precomputed CSV
INDICATOR_SCORE_COL = {
    "HHI": "HHI_Score",
    "CGC": "CGC_Score",
    "CCD": "CCD_Score",
    "ACC": "ACC_Score",
}

PROVINCES_TO_EXCLUDE = ['SULU', 'TAWI-TAWI', 'DAVAO DE ORO', 'COMPOSTELLA VALLEY', 'DINAGAT ISLANDS', 'DAVAO OCCIDENTAL']

DARK_BG = "#0e1117"
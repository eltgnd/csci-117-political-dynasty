"""
config.py
Shared constants for the Philippine Clan Watch Dashboard.
"""

import plotly.express as px

# ── Dataset paths ────────────────────────────────────────────────────────────────
DATA_PATH        = "data/political_dynasty.csv"
PRECOMPUTED_PATH = "data/precomputed_indicators.csv"
GEOJSON_PATH     = "data/gadm41_PHL_2.json"

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

# ── Philippine island group → province mapping ───────────────────────────────────
# Used for the national aggregated trend chart.
ISLAND_GROUPS: dict[str, list[str]] = {
    "Luzon": [
        # CAR
        "Abra", "Apayao", "Benguet", "Ifugao", "Kalinga", "Mountain Province",
        # Ilocos Region
        "Ilocos Norte", "Ilocos Sur", "La Union", "Pangasinan",
        # Cagayan Valley
        "Batanes", "Cagayan", "Isabela", "Nueva Vizcaya", "Quirino",
        # Central Luzon
        "Aurora", "Bataan", "Bulacan", "Nueva Ecija", "Pampanga", "Tarlac", "Zambales",
        # NCR
        "Metro Manila", "NCR",
        # CALABARZON
        "Batangas", "Cavite", "Laguna", "Quezon", "Rizal",
        # MIMAROPA
        "Marinduque", "Occidental Mindoro", "Oriental Mindoro", "Palawan", "Romblon",
        # Bicol
        "Albay", "Camarines Norte", "Camarines Sur", "Catanduanes", "Masbate", "Sorsogon",
    ],
    "Visayas": [
        # Western Visayas
        "Aklan", "Antique", "Capiz", "Guimaras", "Iloilo", "Negros Occidental",
        # Central Visayas
        "Bohol", "Cebu", "Negros Oriental", "Siquijor",
        # Eastern Visayas
        "Biliran", "Eastern Samar", "Leyte", "Northern Samar", "Samar", "Southern Leyte",
    ],
    "Mindanao": [
        # Zamboanga Peninsula
        "Zamboanga del Norte", "Zamboanga del Sur", "Zamboanga Sibugay",
        # Northern Mindanao
        "Bukidnon", "Camiguin", "Lanao del Norte", "Misamis Occidental", "Misamis Oriental",
        # Davao Region
        "Davao de Oro", "Davao del Norte", "Davao del Sur",
        "Davao Occidental", "Davao Oriental",
        # SOCCSKSARGEN
        "Cotabato", "Sarangani", "South Cotabato", "Sultan Kudarat",
        # Caraga
        "Agusan del Norte", "Agusan del Sur", "Dinagat Islands",
        "Surigao del Norte", "Surigao del Sur",
        # BARMM
        "Basilan", "Lanao del Sur", "Maguindanao",
        "Maguindanao del Norte", "Maguindanao del Sur",
        "Sulu", "Tawi-Tawi",
    ],
}


# ── GeoJSON province name mapping ────────────────────────────────────────────────
# Maps DataFrame province names (uppercase, spaces) → GeoJSON property values (CamelCase)
# GeoJSON featureidkey is assumed to be "properties.ADM2_EN" or similar CamelCase field.

DF_TO_GEOJSON: dict[str, str] = {
    # A
    "ABRA":                              "Abra",
    "AGUSAN DEL NORTE":                  "AgusandelNorte",
    "AGUSAN DEL SUR":                    "AgusandelSur",
    "AKLAN":                             "Aklan",
    "ALBAY":                             "Albay",
    "ANTIQUE":                           "Antique",
    "APAYAO":                            "Apayao",
    "AURORA":                            "Aurora",
    # B
    "BASILAN":                           "Basilan",
    "BATAAN":                            "Bataan",
    "BATANES":                           "Batanes",
    "BATANGAS":                          "Batangas",
    "BENGUET":                           "Benguet",
    "BILIRAN":                           "Biliran",
    "BOHOL":                             "Bohol",
    "BUKIDNON":                          "Bukidnon",
    "BULACAN":                           "Bulacan",
    # C
    "CAGAYAN":                           "Cagayan",
    "CAMARINES NORTE":                   "CamarinesNorte",
    "CAMARINES SUR":                     "CamarinesSur",
    "CAMIGUIN":                          "Camiguin",
    "CAPIZ":                             "Capiz",
    "CATANDUANES":                       "Catanduanes",
    "CAVITE":                            "Cavite",
    "CEBU":                              "Cebu",
    "COTABATO":                          "NorthCotabato",   # "Cotabato" in DF = North Cotabato province
    # D
    "DAVAO DE ORO":                      "DavaoDeOro",      # renamed from Compostela Valley 2019
    "DAVAO DEL NORTE":                   "DavaodelNorte",
    "DAVAO DEL SUR":                     "DavaodelSur",
    "DAVAO OCCIDENTAL":                  "DavaoOccidental",
    "DAVAO ORIENTAL":                    "DavaoOriental",
    "DINAGAT ISLANDS":                   "DinagatIslands",
    # E
    "EASTERN SAMAR":                     "EasternSamar",
    # G
    "GUIMARAS":                          "Guimaras",
    # I
    "IFUGAO":                            "Ifugao",
    "ILOCOS NORTE":                      "IlocosNorte",
    "ILOCOS SUR":                        "IlocosSur",
    "ILOILO":                            "Iloilo",
    "ISABELA":                           "Isabela",
    # K
    "KALINGA":                           "Kalinga",
    # L
    "LA UNION":                          "LaUnion",
    "LAGUNA":                            "Laguna",
    "LANAO DEL NORTE":                   "LanaodelNorte",
    "LANAO DEL SUR":                     "LanaodelSur",
    "LEYTE":                             "Leyte",
    # M
    "MAGUINDANAO":                       "Maguindanao",
    "MARINDUQUE":                        "Marinduque",
    "MASBATE":                           "Masbate",
    "MISAMIS OCCIDENTAL":                "MisamisOccidental",
    "MISAMIS ORIENTAL":                  "MisamisOriental",
    "MOUNTAIN PROVINCE":                 "MountainProvince",
    # N
    "NEGROS OCCIDENTAL":                 "NegrosOccidental",
    "NEGROS ORIENTAL":                   "NegrosOriental",
    "NORTHERN SAMAR":                    "NorthernSamar",
    "NUEVA ECIJA":                       "NuevaEcija",
    "NUEVA VIZCAYA":                     "NuevaVizcaya",
    # NCR districts — all map to MetropolitanManila in GeoJSON
    "NCR, SECOND DISTRICT":             "MetropolitanManila",
    "NCR, THIRD DISTRICT":              "MetropolitanManila",
    "NCR, FOURTH DISTRICT":             "MetropolitanManila",
    "NCR, CITY OF MANILA, FIRST DISTRICT": "MetropolitanManila",
    "NCR, FIRST DISTRICT":              "MetropolitanManila",
    # O
    "OCCIDENTAL MINDORO":                "OccidentalMindoro",
    "ORIENTAL MINDORO":                  "OrientalMindoro",
    # P
    "PALAWAN":                           "Palawan",
    "PAMPANGA":                          "Pampanga",
    "PANGASINAN":                        "Pangasinan",
    # Q
    "QUEZON":                            "Quezon",
    "QUIRINO":                           "Quirino",
    # R
    "RIZAL":                             "Rizal",
    "ROMBLON":                           "Romblon",
    # S
    "SAMAR":                             "Samar",
    "SARANGANI":                         "Sarangani",
    "SIQUIJOR":                          "Siquijor",
    "SORSOGON":                          "Sorsogon",
    "SOUTH COTABATO":                    "SouthCotabato",
    "SOUTHERN LEYTE":                    "SouthernLeyte",
    "SULTAN KUDARAT":                    "SultanKudarat",
    "SULU":                              "Sulu",
    "SURIGAO DEL NORTE":                 "SurigaodelNorte",
    "SURIGAO DEL SUR":                   "SurigaodelSur",
    # T
    "TARLAC":                            "Tarlac",
    "TAWI-TAWI":                         "Tawi-Tawi",
    # Z
    "ZAMBALES":                          "Zambales",
    "ZAMBOANGA DEL NORTE":               "ZamboangadelNorte",
    "ZAMBOANGA DEL SUR":                 "ZamboangadelSur",
    "ZAMBOANGA SIBUGAY":                 "ZamboangaSibugay",
}

# Fallback: if DAVAO DE ORO not found in GeoJSON, try the old name
DF_TO_GEOJSON_FALLBACK: dict[str, str] = {
    "DAVAO DE ORO": "CompostelaValley",
}

# Dark mode background color (matches Streamlit's default dark theme)
DARK_BG = "#0e1117"
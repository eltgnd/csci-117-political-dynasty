### IMPORTS ###

import pandas as pd
import numpy as np
import networkx as nx


### ADJACENCY MATRIX ###

def consanguinity(ln_i, mn_i, ln_j, mn_j):
    if ln_i == ln_j and mn_i == mn_j:
        return 1
    elif ln_i == ln_j:
        return 3/4
    elif mn_i and (ln_i == mn_j or mn_i == ln_j):
        return 1/2
    elif mn_i == mn_j and mn_i:
        return 1/4
    return 0

def get_adjacency_matrix(data, province, year):
    r = data[(data["PROVINCE"] == province) & (data["YEAR"] == year)]
    rnew = r[["FIRST NAME", "MIDDLE NAME", "LAST NAME", "YEAR", "POSITION WEIGHT"]].fillna("")

    rnew = rnew.copy()
    rnew["FULL NAME"] = rnew["FIRST NAME"] + " " + rnew["MIDDLE NAME"] + " " + rnew["LAST NAME"]

    # Keep all unique entries
    df_unique = rnew.drop_duplicates(subset=["FULL NAME", "MIDDLE NAME", "LAST NAME"])

    unique_names = df_unique["FULL NAME"].values
    cnt = len(unique_names)

    # Convert to NumPy arrays for fast access
    col_lns = df_unique["LAST NAME"].values
    col_mns = df_unique["MIDDLE NAME"].values
    col_pws = df_unique["POSITION WEIGHT"].values

    # Initialize adjacency matrix
    am = np.zeros((cnt, cnt))

    # Compute adjacency matrix using vectorized operations where possible
    for i in range(cnt):
        ln_i, mn_i, pw_i = col_lns[i], col_mns[i], col_pws[i]
        for j in range(i + 1, cnt):  # Only compute the upper triangle
            ln_j, mn_j, pw_j = col_lns[j], col_mns[j], col_pws[j]
            c = consanguinity(ln_i, mn_i, ln_j, mn_j)
            weight = pw_i * pw_j * c
            am[i, j] = weight
            am[j, i] = weight  # Fill the symmetric part

    return pd.DataFrame(am, index=unique_names, columns=unique_names)

### GENERATE GRAPH ###
def generate_graph(data, province, year):
    data = data.copy()
    data.columns = [c.upper() for c in data.columns]

    # Ensure FULL NAME column exists
    if "FULL NAME" not in data.columns:
        data["FULL NAME"] = (
            data["FIRST NAME"].fillna("") + " " +
            data["MIDDLE NAME"].fillna("") + " " +
            data["LAST NAME"].fillna("")
        ).str.strip()

    # Generate adjacency matrix
    am = get_adjacency_matrix(data, province, year)

    # Create NetworkX graph
    G = nx.from_pandas_adjacency(am)

    # Add node attributes from the merged data
    subset = data[(data["PROVINCE"] == province) & (data["YEAR"] == year)]
    community_attrs = subset.set_index("FULL NAME")["COMMUNITY"].to_dict()
    nx.set_node_attributes(G, community_attrs, "community")

    # Add position weight as node attribute
    pw_attrs = subset.set_index("FULL NAME")["POSITION WEIGHT"].to_dict()
    nx.set_node_attributes(G, pw_attrs, "position_weight")

    # Remove edges with zero weight to clean up the network
    zero_weight_edges = [(u, v) for u, v, w in G.edges(data="weight") if w == 0]
    G.remove_edges_from(zero_weight_edges)

    return G


##################


def get_provincial_kpis(df, province, year):
    """
    Calculates political health KPIs for a specific province and year.
    """
    # Normalize columns
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    # Try to find the correct column names regardless of case
    col_map = {c.upper(): c for c in df.columns}
    province_col = col_map.get("PROVINCE", "Province")
    year_col = col_map.get("YEAR", "Year")
    community_col = col_map.get("COMMUNITY", "Community")
    first_col = col_map.get("FIRST NAME", "First Name")
    mid_col = col_map.get("MIDDLE NAME", "Middle Name")
    last_col = col_map.get("LAST NAME", "Last Name")

    current_df = df[(df[province_col] == province) & (df[year_col] == year)]

    if current_df.empty:
        return {
            "clan_concentration_pct": 0.0,
            "simultaneous_counter": 0,
            "newcomer_rate_pct": 0.0
        }

    total_positions = len(current_df)
    community_counts = current_df[community_col].value_counts()

    # 1. Simultaneous Counter
    simultaneous_counter = int(community_counts.max()) if not community_counts.empty else 0

    # 2. Clan Concentration Percentage
    dynastic_communities = community_counts[community_counts > 1].index
    dynasty_members = current_df[current_df[community_col].isin(dynastic_communities)]
    clan_concentration_pct = float(round((len(dynasty_members) / total_positions) * 100, 2))

    # 3. Newcomer Rate Percentage
    current_names = (
        current_df[first_col].astype(str) + " " +
        current_df[mid_col].astype(str) + " " +
        current_df[last_col].astype(str)
    ).str.lower()

    historical_df = df[(df[province_col] == province) & (df[year_col] < year)]
    historical_names = (
        historical_df[first_col].astype(str) + " " +
        historical_df[mid_col].astype(str) + " " +
        historical_df[last_col].astype(str)
    ).str.lower()

    newcomers = current_names[~current_names.isin(historical_names)]
    newcomer_rate_pct = float(round((len(newcomers) / total_positions) * 100, 2))

    return {
        "clan_concentration_pct": clan_concentration_pct,
        "simultaneous_counter": simultaneous_counter,
        "newcomer_rate_pct": newcomer_rate_pct
    }


##############


def get_hhi_index_per_province(data, year):
    data = data.copy()
    data.columns = [c.upper() for c in data.columns]

    provinces = data['PROVINCE'].unique()
    hhi_values = []

    for province in provinces:
        dfX = data[(data['YEAR'] == year) & (data['PROVINCE'] == province)]

        cols = list(dfX['COMMUNITY'].unique())
        communities = sorted(set(cols))

        hhi = pd.DataFrame(communities, columns=['COMMUNITY'])

        total = dfX['POSITION WEIGHT'].sum()
        if total == 0:
            hhi_values.append(0.0)
            continue

        scores = [dfX[dfX['COMMUNITY'] == c]['POSITION WEIGHT'].sum() for c in communities]
        hhi['SEATS'] = scores
        hhi['SEAT SHARES'] = hhi['SEATS'] / total
        hh_index = np.square(100 * hhi['SEAT SHARES']).sum()
        hhi_values.append(hh_index)

    return pd.DataFrame({"Province": provinces, "HHI_Score": hhi_values})


##############  NEW INDICES  ##############


def _gini(array: np.ndarray) -> float:
    """Compute the Gini coefficient of a 1-D array."""
    array = array.flatten().astype(float)
    if array.size == 0:
        return 0.0
    if np.amin(array) < 0:
        array -= np.amin(array)
    array += 1e-7  # avoid zeros
    array = np.sort(array)
    n = array.shape[0]
    index = np.arange(1, n + 1)
    return float(np.sum((2 * index - n - 1) * array) / (n * np.sum(array)))


def get_cgc_per_province(data, year):
    """
    Clan Gini Coefficient (CGC): Gini coefficient of weighted degree centrality
    per province for a given year. Higher = more centralized power.

    Returns:
        pd.DataFrame with columns ['Province', 'CGC_Score']
    """
    data = data.copy()
    data.columns = [c.upper() for c in data.columns]
    provinces = data['PROVINCE'].unique()
    results = []
    for province in provinces:
        subset = data[(data['PROVINCE'] == province) & (data['YEAR'] == year)]
        if subset.empty:
            results.append({'Province': province, 'CGC_Score': 0.0})
            continue
        am = get_adjacency_matrix(data, province, year)
        G = nx.from_pandas_adjacency(am)
        degrees = np.array([d for _, d in G.degree(weight='weight')], dtype=float)
        results.append({'Province': province, 'CGC_Score': _gini(degrees)})
    return pd.DataFrame(results)


def get_ccd_per_province(data, year):
    """
    Clan Connectivity Density (CCD): 1 - (number of connected components / total positions).
    Higher = more interconnected dynasty network.

    Returns:
        pd.DataFrame with columns ['Province', 'CCD_Score']
    """
    data = data.copy()
    data.columns = [c.upper() for c in data.columns]
    provinces = data['PROVINCE'].unique()
    results = []
    for province in provinces:
        subset = data[(data['PROVINCE'] == province) & (data['YEAR'] == year)]
        total = len(subset)
        if total == 0:
            results.append({'Province': province, 'CCD_Score': 0.0})
            continue
        am = get_adjacency_matrix(data, province, year)
        G = nx.from_pandas_adjacency(am)
        n_components = nx.number_connected_components(G)
        ccd = float(1 - n_components / total)
        results.append({'Province': province, 'CCD_Score': ccd})
    return pd.DataFrame(results)


def get_acc_per_province(data, year):
    """
    Aggregate Clan Connectivity (ACC): For each community in a province, compute
    node_connectivity(G_community) / |V(G_community)| and sum across all communities.
    Higher = more internally resilient clan structures.

    Returns:
        pd.DataFrame with columns ['Province', 'ACC_Score']
    """
    data = data.copy()
    data.columns = [c.upper() for c in data.columns]
    data['MIDDLE NAME'] = data['MIDDLE NAME'].fillna('')
    provinces = data['PROVINCE'].unique()
    results = []
    for province in provinces:
        prov_df = data[(data['PROVINCE'] == province) & (data['YEAR'] == year)]
        acc_sum = 0.0
        for comm_id in prov_df['COMMUNITY'].unique():
            sample = prov_df[prov_df['COMMUNITY'] == comm_id]
            n = len(sample)
            if n <= 1:
                continue
            surnames = sample['LAST NAME'].tolist()
            mns = sample['MIDDLE NAME'].tolist()
            adj = np.zeros((n, n), dtype=int)
            for i in range(n):
                for j in range(i + 1, n):
                    if (surnames[i] == surnames[j] or
                            (mns[i] and mns[i] == mns[j]) or
                            surnames[i] == mns[j] or
                            mns[i] == surnames[j]):
                        adj[i, j] = adj[j, i] = 1
            G_comm = nx.from_numpy_array(adj)
            nc = nx.node_connectivity(G_comm)
            acc_sum += nc / n
        results.append({'Province': province, 'ACC_Score': acc_sum})
    return pd.DataFrame(results)


def get_provincial_indicator_trend(data, province, years):
    """
    Returns a DataFrame with all four dynastic indicators for a given province
    across the specified list of election years.

    Columns: ['Year', 'HHI', 'CGC', 'CCD', 'ACC']
    """
    rows = []
    for year in years:
        # HHI
        hhi_df = get_hhi_index_per_province(data, year)
        hhi_row = hhi_df[hhi_df['Province'] == province]
        hhi_val = float(hhi_row['HHI_Score'].iloc[0]) if not hhi_row.empty else 0.0

        # CGC
        cgc_df = get_cgc_per_province(data, year)
        cgc_row = cgc_df[cgc_df['Province'] == province]
        cgc_val = float(cgc_row['CGC_Score'].iloc[0]) if not cgc_row.empty else 0.0

        # CCD
        ccd_df = get_ccd_per_province(data, year)
        ccd_row = ccd_df[ccd_df['Province'] == province]
        ccd_val = float(ccd_row['CCD_Score'].iloc[0]) if not ccd_row.empty else 0.0

        # ACC
        acc_df = get_acc_per_province(data, year)
        acc_row = acc_df[acc_df['Province'] == province]
        acc_val = float(acc_row['ACC_Score'].iloc[0]) if not acc_row.empty else 0.0

        rows.append({'Year': year, 'HHI': hhi_val, 'CGC': cgc_val, 'CCD': ccd_val, 'ACC': acc_val})

    return pd.DataFrame(rows)

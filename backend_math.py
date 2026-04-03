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
    data.columns = [c.upper() for c in data.columns]
    # Generate adjacency matrix
    am = get_adjacency_matrix(data, province, year)

    # Create NetworkX graph
    G = nx.from_pandas_adjacency(am)

    # Add node attributes from the merged data
    subset = data[(data["PROVINCE"] == province) & (data["YEAR"] == year)]
    node_attrs = subset.set_index("FULL NAME")["COMMUNITY"].to_dict()
    nx.set_node_attributes(G, node_attrs, "community")

    # Remove edges with zero weight to clean up the network
    zero_weight_edges = [(u, v) for u, v, w in G.edges(data="weight") if w == 0]
    G.remove_edges_from(zero_weight_edges)

    return G


##################


def get_provincial_kpis(df, province, year):
    """
    Calculates political health KPIs for a specific province and year.
    
    Args:
        df (pd.DataFrame): The main dataset containing all election records.
        province (str): The province to analyze.
        year (int): The election year to analyze.
        
    Returns:
        dict: A dictionary containing clan_concentration_pct, simultaneous_counter, 
              and newcomer_rate_pct.
    """

    # Filter dataset for the selected province and year
    current_df = df[(df['Province'] == province) & (df['Year'] == year)]
    
    if current_df.empty:
        return {
            "clan_concentration_pct": 0.0,
            "simultaneous_counter": 0,
            "newcomer_rate_pct": 0.0
        }
        
    total_positions = len(current_df)
    
    # Calculate Community sizes for the current year
    community_counts = current_df['Community'].value_counts()
    
    # 1. Simultaneous Counter
    # The maximum number of individuals belonging to the exact same clan (Community) 
    # holding office at the same time in this specific year.
    simultaneous_counter = int(community_counts.max()) if not community_counts.empty else 0
    
    # 2. Clan Concentration Percentage
    # Defined as the percentage of total positions held by individuals who are part 
    # of a clan (where a clan is a Community with more than 1 member in office).
    dynastic_communities = community_counts[community_counts > 1].index
    dynasty_members = current_df[current_df['Community'].isin(dynastic_communities)]
    clan_concentration_pct = float(round((len(dynasty_members) / total_positions) * 100, 2))
    
    # 3. Newcomer Rate Percentage
    # Percentage of politicians in the current year who have no prior record of 
    # holding office in this province in any previous year.
    current_names = (current_df['First Name'].astype(str) + " " + 
                     current_df['Middle Name'].astype(str) + " " + 
                     current_df['Last Name'].astype(str)).str.lower()
                     
    historical_df = df[(df['Province'] == province) & (df['Year'] < year)]
    historical_names = (historical_df['First Name'].astype(str) + " " + 
                        historical_df['Middle Name'].astype(str) + " " + 
                        historical_df['Last Name'].astype(str)).str.lower()
                        
    newcomers = current_names[~current_names.isin(historical_names)]
    newcomer_rate_pct = float(round((len(newcomers) / total_positions) * 100, 2))
    
    return {
        "clan_concentration_pct": clan_concentration_pct,
        "simultaneous_counter": simultaneous_counter,
        "newcomer_rate_pct": newcomer_rate_pct
    }


##############


def get_hhi_index_per_province(data, year):
    data.columns = [c.upper() for c in data.columns]

    provinces = data['PROVINCE'].unique()
    hhi_values = []
    
    for province in provinces:
        # Get all positions in the province in the selected year
        dfX = data[(data['YEAR'] == year) & (data['PROVINCE'] == province)]

        # Get list of all unique community IDs
        cols = list(dfX['COMMUNITY'].unique())
        communities = []
        for community in cols:
            if community not in communities:
                communities.append(community)
        communities = sorted(communities)

        # Convert to DataFrame
        hhi = pd.DataFrame(communities, columns=['COMMUNITY'])

        # Get position score per community
        total = dfX['POSITION WEIGHT'].sum()
        scores = []
        for community in communities:
            score = dfX[dfX['COMMUNITY'] == community]['POSITION WEIGHT'].sum()
            scores.append(score)

        hhi['SEATS'] = scores
        hhi['SEAT SHARES'] = hhi['SEATS'] / total

        hh_index = np.square(100 * hhi['SEAT SHARES']).sum()
        hhi_values.append(hh_index)
    
    return pd.DataFrame({"Province": provinces, "HHI_Score": hhi_values})
        
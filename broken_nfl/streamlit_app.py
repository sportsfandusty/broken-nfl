import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm, multivariate_normal
from scipy.optimize import least_squares
from pulp import LpProblem, LpVariable, LpMaximize, lpSum, LpStatus, PULP_CBC_CMD

# Load your data into a DataFrame 'df'
# Ensure 'df' has columns: 'Name', 'Pos', 'Team', 'Opp', 'Salary', 'Roster%', '25th', '50th', 'Proj', '75th', '85th'
df = pd.read_csv('your_player_projections.csv')
df.reset_index(drop=True, inplace=True)

# Fit log-normal parameters for each player
def fit_log_normal_with_projection(player_data):
    percentiles = [25, 50, 75, 85]
    p_values = [p / 100 for p in percentiles]
    z_scores = norm.ppf(p_values)
    P_values = [
        player_data['25th'],
        player_data['50th'],
        player_data['75th'],
        player_data['85th'],
    ]
    ln_P_values = np.log(P_values)
    projection = player_data['Proj']  # Using 'Proj' as the mean projection

    # Define the residual function
    def residuals(params):
        mu, sigma = params
        res = []
        for ln_P, z in zip(ln_P_values, z_scores):
            res.append(ln_P - (mu + sigma * z))
        # Add the mean equation
        res.append(np.exp(mu + 0.5 * sigma**2) - projection)
        return res

    # Initial guesses
    mu_init = np.log(player_data['50th'])
    sigma_init = 0.1  # Start with a small sigma

    result = least_squares(
        residuals, x0=[mu_init, sigma_init], bounds=([-np.inf, 1e-6], [np.inf, np.inf])
    )

    mu_est, sigma_est = result.x
    return mu_est, sigma_est

# Fit the distribution for all players
mu_list = []
sigma_list = []

for idx, row in df.iterrows():
    player_data = {
        '25th': row['25th'],
        '50th': row['50th'],
        '75th': row['75th'],
        '85th': row['85th'],
        'Proj': row['Proj']
    }
    mu, sigma = fit_log_normal_with_projection(player_data)
    mu_list.append(mu)
    sigma_list.append(sigma)

# Define the correlation matrix
num_players = len(df)
correlation_matrix = np.identity(num_players)

position_correlations = {
    ('QB', 'WR'): 0.5,
    ('QB', 'TE'): 0.4,
    ('WR', 'WR'): 0.3,
    # Add other correlations as needed
}

# Build the correlation matrix
for i in range(num_players):
    for j in range(i + 1, num_players):
        pos_i = df.loc[i, 'Pos']
        pos_j = df.loc[j, 'Pos']
        team_i = df.loc[i, 'Team']
        team_j = df.loc[j, 'Team']

        corr_key = (pos_i, pos_j)
        corr = position_correlations.get(corr_key)
        if corr is None:
            corr_key = (pos_j, pos_i)
            corr = position_correlations.get(corr_key)

        if corr is not None and team_i == team_j:
            correlation_matrix[i, j] = corr
            correlation_matrix[j, i] = corr

# Ensure the correlation matrix is positive definite
from numpy.linalg import eigh

def nearest_positive_definite(corr_mat):
    eigvals, eigvecs = eigh(corr_mat)
    eigvals[eigvals < 0] = 1e-6
    return eigvecs @ np.diag(eigvals) @ eigvecs.T

correlation_matrix = nearest_positive_definite(correlation_matrix)

# Streamlit Interface
st.title("DraftKings NFL Showdown Lineup Optimizer")

# Sidebar Controls
with st.sidebar:
    st.header("Optimizer Settings")
    variance_level = st.slider('Variance Level (%)', min_value=0, max_value=100, value=15)
    num_lineups = st.number_input('Number of Lineups', min_value=1, max_value=150, value=20, step=1)
    min_unique_players = st.number_input('Minimum Unique Players Between Lineups', min_value=1, max_value=6, value=2, step=1)
    optimize_button = st.button('Optimize Lineups')

# Generate correlated projections
def generate_correlated_projections(mu_list, sigma_list, correlation_matrix, variance_level):
    num_players = len(mu_list)
    # Adjust sigma based on variance level
    adjusted_sigma_list = np.array(sigma_list) * (variance_level / 15)  # Assuming 15% is the base variance level
    # Generate correlated standard normal samples
    z_samples = multivariate_normal.rvs(mean=np.zeros(num_players), cov=correlation_matrix)
    # Transform to log-normal projections
    projections = np.exp(np.array(mu_list) + adjusted_sigma_list * z_samples)
    return projections

# Optimizer function
def generate_lineup(projections, existing_lineups=None, min_unique_players=1):
    prob = LpProblem("DraftKings_NFL_Showdown", LpMaximize)

    # Create variables
    C = LpVariable.dicts("Captain", df.index, cat='Binary')
    F = LpVariable.dicts("Flex", df.index, cat='Binary')

    # Objective function
    prob += lpSum([
        1.5 * projections[i] * C[i] + projections[i] * F[i]
        for i in df.index
    ])

    # Salary cap constraint
    prob += lpSum([
        1.5 * df.loc[i, 'Salary'] * C[i] + df.loc[i, 'Salary'] * F[i]
        for i in df.index
    ]) <= 50000

    # Lineup composition constraints
    prob += lpSum([C[i] for i in df.index]) == 1
    prob += lpSum([F[i] for i in df.index]) == 5

    # Ensure a player is not both Captain and Flex
    for i in df.index:
        prob += C[i] + F[i] <= 1

    # Enforce minimum unique players between lineups
    if existing_lineups:
        for lineup in existing_lineups:
            prob += lpSum([
                C[i] + F[i] for i in df.index
                if (df.loc[i, 'Name'] in lineup)
            ]) <= 6 - min_unique_players

    # Solve the optimization problem
    solver = PULP_CBC_CMD(msg=0)
    prob.solve(solver)

    if LpStatus[prob.status] != 'Optimal':
        return None

    lineup_players = []
    lineup = {
        'Captain': [],
        'Flex': [],
        'Total Salary': 0,
        'Total Projection': 0,
        'Total 85th Percentile Outcome': 0,
        'Total Roster%': 0,
    }
    for i in df.index:
        if C[i].varValue == 1:
            player = df.loc[i].to_dict()
            lineup['Captain'].append(player)
            lineup['Total Salary'] += 1.5 * player['Salary']
            lineup['Total Projection'] += 1.5 * projections[i]
            lineup['Total 85th Percentile Outcome'] += 1.5 * player['85th']
            lineup['Total Roster%'] += player['Roster%']
            lineup_players.append(player['Name'])
        elif F[i].varValue == 1:
            player = df.loc[i].to_dict()
            lineup['Flex'].append(player)
            lineup['Total Salary'] += player['Salary']
            lineup['Total Projection'] += projections[i]
            lineup['Total 85th Percentile Outcome'] += player['85th']
            lineup['Total Roster%'] += player['Roster%']
            lineup_players.append(player['Name'])
    return lineup, lineup_players

# Main Logic
if optimize_button:
    lineups = []
    lineup_players_list = []
    attempts = 0
    max_attempts = num_lineups * 5  # Prevent infinite loop

    while len(lineups) < num_lineups and attempts < max_attempts:
        attempts += 1

        # Generate projections with variance
        projections = generate_correlated_projections(mu_list, sigma_list, correlation_matrix, variance_level)
        # Ensure projections are non-negative
        projections = np.maximum(0, projections)

        # Generate lineup with adjusted projections
        lineup_result = generate_lineup(projections, lineup_players_list, min_unique_players)
        if lineup_result is not None:
            lineup, lineup_players = lineup_result
            # Check for duplicates
            lineup_players_set = frozenset(lineup_players)
            if lineup_players_set not in [frozenset(lp) for lp in lineup_players_list]:
                lineup_players_list.append(lineup_players)
                lineups.append(lineup)

    if lineups:
        for idx, lineup in enumerate(lineups, start=1):
            st.write(f"### Lineup {idx}")
            st.write(f"**Total Salary Used:** ${lineup['Total Salary']:.0f}")
            st.write(f"**Total Projection:** {lineup['Total Projection']:.2f}")
            st.write(f"**Total 85th Percentile Outcome:** {lineup['Total 85th Percentile Outcome']:.2f}")
            st.write(f"**Total Roster%:** {lineup['Total Roster%']:.2f}%")
            st.write("**Captain:**")
            for player in lineup['Captain']:
                st.write(f"- {player['Name']} ({player['Pos']}, {player['Team']}) - Salary: ${1.5 * player['Salary']:.0f}")
            st.write("**Flex Players:**")
            for player in lineup['Flex']:
                st.write(f"- {player['Name']} ({player['Pos']}, {player['Team']}) - Salary: ${player['Salary']}")
            st.write("---")
    else:
        st.write("No valid lineups could be generated with the given settings.")

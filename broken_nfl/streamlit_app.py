import streamlit as st
import pandas as pd
import os
import logging

# Set up the file directory for CSV files
csv_dir = "opto/prepped"
st.set_page_config(page_title="Showdown Optimizer", layout="wide")
st.title("Showdown Optimizer")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# List CSV files ending with '_captain.csv' or '_flex.csv'
csv_files = [f for f in os.listdir(csv_dir) if f.endswith('_captain.csv') or f.endswith('_flex.csv')]

# Extract game identifiers by removing prefixes and suffixes
game_identifiers = set()
for f in csv_files:
    if f.startswith('SD_'):
        game_id = f.replace('SD_', '').replace('_captain.csv', '').replace('_flex.csv', '')
        game_identifiers.add(game_id)

# Sort game identifiers for consistent display
sorted_game_ids = sorted(game_identifiers)

# Sidebar for selecting the game and updating projections
with st.sidebar:
    selected_game = st.selectbox('Select game', sorted_game_ids)

# Displaying the selected game in the title, cleaned up
st.write(f"Displaying data for game: **{selected_game.replace('-@-', ' @ ')}**")

# Paths to the captain and flex CSV files
captain_file = os.path.join(csv_dir, f"SD_{selected_game}_captain.csv")
flex_file = os.path.join(csv_dir, f"SD_{selected_game}_flex.csv")

# Load the dataframes into session state if not already loaded or if the selected game has changed
if 'selected_game' not in st.session_state or st.session_state['selected_game'] != selected_game:
    # Try to load captain data
    if os.path.exists(captain_file):
        captain_df = pd.read_csv(captain_file)
        # Initialize 'Original_Proj' if not already in columns
        if 'Original_Proj' not in captain_df.columns:
            captain_df['Original_Proj'] = captain_df['Proj']
    else:
        captain_df = None
        st.warning(f"Captain file not found for game {selected_game}.")

    # Try to load flex data
    if os.path.exists(flex_file):
        flex_df = pd.read_csv(flex_file)
        # Initialize 'Original_Proj' if not already in columns
        if 'Original_Proj' not in flex_df.columns:
            flex_df['Original_Proj'] = flex_df['Proj']
    else:
        flex_df = None
        st.warning(f"Flex file not found for game {selected_game}.")

    # Store dataframes in session state
    st.session_state['captain_df'] = captain_df
    st.session_state['flex_df'] = flex_df
    st.session_state['selected_game'] = selected_game

# Universal styling for both tables
st.markdown("""
    <style>
    .main {
        max-width: 90%;
    }
    .block-container {
        padding-top: 2rem;
    }
    .stTabs [role="tablist"] button {
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

# Function to recalculate dependent metrics
def recalculate_metrics(df):
    df = df.copy()
    # Recalculate PPD columns
    df['25th/$'] = (df['25th'] / df['Salary']) * 1000
    df['50th/$'] = (df['50th'] / df['Salary']) * 1000
    df['Proj/$'] = (df['Proj'] / df['Salary']) * 1000
    df['75th/$'] = (df['75th'] / df['Salary']) * 1000
    df['85th/$'] = (df['85th'] / df['Salary']) * 1000
    return df

# Function to adjust percentiles
def adjust_percentiles(df, adjustment_factor=1.0):
    logging.info("Adjusting percentile outcome values...")
    df = df.copy()
    try:
        # Filter rows where 'Proj' is different from 'Original_Proj'
        adjustment_needed = df[df['Proj'] != df['Original_Proj']]

        # Iterate over rows where adjustment is needed
        for idx, row in adjustment_needed.iterrows():
            # Calculate the shift factor based on 'Proj' and 'Original_Proj'
            shift_factor = (row['Proj'] / row['Original_Proj']) * adjustment_factor

            # Adjust the percentiles
            df.at[idx, '25th'] = max(0, row['25th'] * shift_factor)
            df.at[idx, '50th'] = max(0, row['50th'] * shift_factor)
            df.at[idx, '75th'] = row['75th'] * shift_factor
            df.at[idx, '85th'] = row['85th'] * shift_factor

        logging.info("Percentiles adjusted successfully")
        return df

    except Exception as e:
        logging.error(f"function call: adjust_percentiles failed due to error - {str(e)}")
        raise

# Function to update projection
def update_projection(player_name, new_proj):
    if 'flex_df' in st.session_state and st.session_state['flex_df'] is not None:
        # Update projection in flex_df
        player_mask = st.session_state['flex_df']['Name'] == player_name
        # Store Original_Proj if not already stored
        if 'Original_Proj' not in st.session_state['flex_df'].columns:
            st.session_state['flex_df']['Original_Proj'] = st.session_state['flex_df']['Proj']
        st.session_state['flex_df'].loc[player_mask, 'Proj'] = new_proj
        # Recalculate percentiles
        st.session_state['flex_df'] = adjust_percentiles(st.session_state['flex_df'])
        # Recalculate dependent columns in flex_df
        st.session_state['flex_df'] = recalculate_metrics(st.session_state['flex_df'])
    if 'captain_df' in st.session_state and st.session_state['captain_df'] is not None:
        # Update projection in captain_df
        player_mask = st.session_state['captain_df']['Name'] == player_name
        # Store Original_Proj if not already stored
        if 'Original_Proj' not in st.session_state['captain_df'].columns:
            st.session_state['captain_df']['Original_Proj'] = st.session_state['captain_df']['Proj']
        # Update 'Proj' in captain_df (1.5x flex projection)
        new_captain_proj = new_proj * 1.5
        st.session_state['captain_df'].loc[player_mask, 'Proj'] = new_captain_proj
        # Recalculate percentiles
        st.session_state['captain_df'] = adjust_percentiles(st.session_state['captain_df'])
        # Recalculate dependent columns in captain_df
        st.session_state['captain_df'] = recalculate_metrics(st.session_state['captain_df'])

# Sidebar for updating player projections
if 'flex_df' in st.session_state and st.session_state['flex_df'] is not None:
    with st.sidebar:
        st.write("## Update Player Projection")
        player_names = st.session_state['flex_df']['Name'].unique()
        selected_player = st.selectbox('Select player', player_names)
        current_proj = st.session_state['flex_df'].loc[st.session_state['flex_df']['Name'] == selected_player, 'Proj'].values[0]
        new_proj = st.number_input('New Projection', value=float(current_proj))
        if st.button('Update Projection'):
            update_projection(selected_player, new_proj)
            st.success(f'Projection updated for {selected_player}')

# Retrieve dataframes from session state after updates
captain_df = st.session_state.get('captain_df', None)
flex_df = st.session_state.get('flex_df', None)

def style_dataframe(df):
    # Format numeric columns to display two decimal places
    numeric_cols = df.select_dtypes(include=['float', 'float64']).columns
    styled_df = df.style.format({col: "{:.2f}" for col in numeric_cols})

    # Center all data
    styled_df = styled_df.set_properties(**{
        'text-align': 'center',
        'background-color': '#f7f7f7',
        'color': '#4d4d4d'
    })

    # Center the column headers and adjust background and font colors
    styled_df = styled_df.set_table_styles([
        {'selector': 'th', 'props': [
            ('text-align', 'center'),
            ('background-color', '#e0e0e0'),
            ('color', '#4d4d4d')
        ]}
    ])

    # Style the 'Proj' column
    if 'Proj' in df.columns:
        # Create a CSS style for the 'Proj' column
        proj_style = [
            {'selector': f'th.col{df.columns.get_loc("Proj")}', 'props': [
                ('font-weight', 'bold'),
                ('font-size', '16px'),
                ('background-color', '#d9d9d9'),
                ('color', '#4d4d4d')
            ]},
            {'selector': f'td.col{df.columns.get_loc("Proj")}', 'props': [
                ('font-weight', 'bold'),
                ('font-size', '16px'),
                ('background-color', '#d9d9d9'),
                ('color', '#4d4d4d')
            ]}
        ]
        styled_df = styled_df.set_table_styles(proj_style, overwrite=False)

    return styled_df


# Tabs for Captain and Flex
if captain_df is not None or flex_df is not None:
    tab_capt, tab_flex = st.tabs(["Capt", "Flex"])

    if captain_df is not None:
        with tab_capt:
            st.write("Captain Table")
            styled_captain_df = style_dataframe(captain_df)
            st.write(styled_captain_df)
    else:
        with tab_capt:
            st.warning("Captain data not available.")

    if flex_df is not None:
        with tab_flex:
            st.write("Flex Table")
            styled_flex_df = style_dataframe(flex_df)
            st.write(styled_flex_df)
    else:
        with tab_flex:
            st.warning("Flex data not available.")
else:
    st.error("No data available for the selected game.")

st.write("Select different games from the sidebar to display.")


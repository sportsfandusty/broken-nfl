import streamlit as st
import pandas as pd
import os

# Set the path for the CSV files directory
csv_dir = "projections/prepped"

# Streamlit app configuration
st.set_page_config(page_title="CSV Viewer", layout="wide")

# Title of the app
st.title("CSV Viewer")

# List available CSV files in the directory
csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]

# Sidebar setup for dropdown selection
with st.sidebar:
    st.header("File Selection")
    selected_file = st.selectbox("Select a CSV file to view:", csv_files)

# Full path to the selected file
file_path = os.path.join(csv_dir, selected_file)

# Disable page scrolling, and allow the table itself to scroll
st.markdown("""
    <style>
    .main {
        max-width: 100%;
    }
    .block-container {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Load the selected CSV file
if selected_file:
    st.write(f"Displaying data from: **{selected_file}**")
    try:
        df = pd.read_csv(file_path)

        # Create two tabs: Flex and Capt
        tabs = st.tabs(["Flex", "Capt"])

        # Flex tab shows the original data
        with tabs[0]:
            st.write("Flex Table")
            st.dataframe(df, height=500)

        # Capt tab shows the data with adjustments (Salary, Proj, Adj Proj, and percentiles multiplied by 1.5)
        with tabs[1]:
            st.write("Capt Table")

            # Ensure the required columns exist before performing operations
            required_columns = ['Salary', 'Proj', 'Adj Proj', '25th', '50th', '75th', '85th', '95th']
            if all(col in df.columns for col in required_columns):
                df_capt = df.copy()

                # Multiply Salary, Proj, Adj Proj, and percentile columns by 1.5
                df_capt['Salary'] = df_capt['Salary'] * 1.5
                df_capt['Proj'] = df_capt['Proj'] * 1.5
                df_capt['Adj Proj'] = df_capt['Adj Proj'] * 1.5
                df_capt['25th'] = df_capt['25th'] * 1.5
                df_capt['50th'] = df_capt['50th'] * 1.5
                df_capt['75th'] = df_capt['75th'] * 1.5
                df_capt['85th'] = df_capt['85th'] * 1.5
                df_capt['95th'] = df_capt['95th'] * 1.5

                # Display the updated dataframe
                st.dataframe(df_capt, height=500)
            else:
                st.error(f"Some of the required columns are missing: {required_columns}")

    except Exception as e:
        st.error(f"Error loading {selected_file}: {e}")

# Footer
st.write("Select different CSV files from the sidebar to display.")


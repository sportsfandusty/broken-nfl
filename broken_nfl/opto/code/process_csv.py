import pandas as pd
import os
import settings
import functions as fn
import logging

# Configure logging to print to terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Read the CSV file
csv_files = [f for f in os.listdir(settings.RAW_CSV_DIR) if f.endswith('.csv')]
if not csv_files:
    logging.error("No CSV files found in the raw CSV directory.")
    exit(1)
raw_csv_file = os.path.join(settings.RAW_CSV_DIR, csv_files[0])
df = pd.read_csv(raw_csv_file)

# Rename columns first
df.rename(columns=settings.RENAME_RULES, inplace=True)

# Filter out unwanted rows based on projection threshold
df = df[df['Proj'] > settings.MY_PROJ_THRESHOLD]

# Keep only the desired columns
df_filtered = df[settings.COLUMNS_TO_KEEP].copy()

# Reset index
df_filtered = df_filtered.reset_index(drop=True)

# Adjust 'Roster%' percentage
if 'Roster%' in df_filtered.columns:
    df_filtered = fn.adjust_roster_percentage(df_filtered)

# Proceed with separating captains and flex players as before...

# Identify duplicated names in the 'Name' column
duplicated_names = df_filtered['Name'].duplicated(keep=False)

# Separate duplicated and non-duplicated rows
duplicates_df = df_filtered[duplicated_names].copy()
non_duplicates_df = df_filtered[~duplicated_names].copy()

# For duplicated names, separate captain and flex rows based on salary
# Captains have higher salaries
captain_rows = duplicates_df.loc[duplicates_df.groupby('Name')['Salary'].idxmax()].reset_index(drop=True)

# Flex players from duplicates have lower salaries
flex_rows_from_duplicates = duplicates_df.loc[duplicates_df.groupby('Name')['Salary'].idxmin()].reset_index(drop=True)

# Combine flex_rows_from_duplicates with non_duplicated rows to get the full flex DataFrame
flex_df_cleaned = pd.concat([flex_rows_from_duplicates, non_duplicates_df], ignore_index=True)

# Continue with your calculations for both DataFrames
# Adjust percentiles
captain_df_cleaned = fn.adjust_percentiles(captain_rows, adjustment_factor=1.0)
flex_df_cleaned = fn.adjust_percentiles(flex_df_cleaned, adjustment_factor=1.0)

# Calculate PPD (Points Per Dollar or similar metric)
captain_df_cleaned = fn.calculate_ppd(captain_df_cleaned)
flex_df_cleaned = fn.calculate_ppd(flex_df_cleaned)

# Select columns to display
captain_df_cleaned = captain_df_cleaned[settings.COLUMNS_TO_DISPLAY]
flex_df_cleaned = flex_df_cleaned[settings.COLUMNS_TO_DISPLAY]

# Standardize numeric columns
captain_df_cleaned = fn.standardize_numeric_columns(captain_df_cleaned)
flex_df_cleaned = fn.standardize_numeric_columns(flex_df_cleaned)

# Sort DataFrames by 'Salary' in descending order
captain_df_cleaned = captain_df_cleaned.sort_values(by='Salary', ascending=False)
flex_df_cleaned = flex_df_cleaned.sort_values(by='Salary', ascending=False)

# Save the processed CSV files
file_base_name = os.path.basename(raw_csv_file)
game_identifier = file_base_name.split('_')[-1].replace('.csv', '')

# Ensure the output directory exists
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

# Save flex data
flex_output_path = os.path.join(settings.OUTPUT_DIR, f'SD_{game_identifier}_flex.csv')
flex_df_cleaned.to_csv(flex_output_path, index=False)

# Save captain data
captain_output_path = os.path.join(settings.OUTPUT_DIR, f'SD_{game_identifier}_captain.csv')
captain_df_cleaned.to_csv(captain_output_path, index=False)

print(f"{game_identifier} showdown CSV prepped for flex and captain")


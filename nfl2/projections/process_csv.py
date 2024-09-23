import pandas as pd
import os
import settings
import functions as fn  
import logging

# Configure logging to print to terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#finding the raw csv
csv_files = [f for f in os.listdir(settings.RAW_CSV_DIR) if f.endswith('.csv')]
raw_csv_file = os.path.join(settings.RAW_CSV_DIR, csv_files[0])
df = pd.read_csv(raw_csv_file)

#filter out unwanted columns and rows
df_filtered = df[settings.COLUMNS_TO_KEEP]
df_filtered = df_filtered.rename(columns=settings.RENAME_RULES)
df_filtered = df_filtered[df_filtered['Proj'] > settings.MY_PROJ_THRESHOLD]
df_cleaned = df_filtered.loc[df_filtered.groupby('Name')['Salary'].idxmin()]
df_cleaned = df_cleaned.sort_values(by='Salary', ascending=False)

#calculates new percentile outcomes if event of projection adjustment
df_cleaned = fn.adjust_percentiles(df_cleaned, adjustment_factor=1.0)
#calculates percentile outcome value columns
df_cleaned = fn.calculate_ppd(df_cleaned)
#standardize numeric columns 
df_cleaned = fn.standardize_numeric_columns(df_cleaned)

#file saving
file_base_name = os.path.basename(raw_csv_file)
game_identifier = file_base_name.split('_')[-1].replace('.csv', '')
flex_output_path = os.path.join(settings.OUTPUT_DIR, f'SD_{game_identifier}.csv')
df_cleaned.to_csv(flex_output_path, index=False)

print(f"{game_identifier} showdown CSV prepped")



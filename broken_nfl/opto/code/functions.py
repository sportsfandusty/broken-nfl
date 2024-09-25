import pandas as pd
import logging

# Configure logging if not already configured in the main script
# Uncomment the following line if logging is not configured elsewhere
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def adjust_percentiles(df, adjustment_factor=1.0):

    logging.info("adjusting percentile outcome values..")

    try:
        # Filter rows where 'proj' is different from 'adj_proj'
        adjustment_needed = df[df['Proj'] != df['Adj_Proj']]
        
        # Iterate over rows where adjustment is needed
        for idx, row in adjustment_needed.iterrows():
            # Calculate the shift factor based on 'proj' and 'adj_proj'
            shift_factor = (row['Adj_Proj'] / row['Proj']) * adjustment_factor

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

def calculate_ppd(df):
    logging.info("Calculating value range of outcomes...")
    df = df.copy()
    df.loc[:, '25th/$'] = (df['25th'] / df['Salary']) * 1000
    df.loc[:, '50th/$'] = (df['50th'] / df['Salary']) * 1000
    df.loc[:, 'Proj/$'] = (df['Proj'] / df['Salary']) * 1000
    df.loc[:, '75th/$'] = (df['75th'] / df['Salary']) * 1000
    df.loc[:, '85th/$'] = (df['85th'] / df['Salary']) * 1000
    return df


def standardize_numeric_columns(df):
    logging.info("Standardizing numeric columns")
    df = df.copy()
    # Removed the 'Roster%' adjustment here
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
    numeric_columns = numeric_columns.drop('Salary', errors='ignore')  # Exclude 'Salary' column
    df.loc[:, numeric_columns] = df[numeric_columns].round(2)
    return df

def adjust_roster_percentage(df):
    logging.info("Adjusting 'Roster%' percentages")
    df = df.copy()
    df.loc[:, 'Roster%'] = df['Roster%'] / 100
    return df


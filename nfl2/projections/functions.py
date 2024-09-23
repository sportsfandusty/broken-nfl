import logging

def adjust_percentiles(df, adjustment_factor=1.0):
    """
    Adjust the percentile values if necessary by comparing 'proj' and 'adj_proj'.
    This function modifies the '25th%', '50th%', '75th%', '85th%', '95th%', and '99th%' columns.
    The adjustment_factor allows for flexible scaling.
    """
    logging.info("function call: adjust_percentiles started")

    try:
        # Filter rows where 'proj' is different from 'adj_proj'
        adjustment_needed = df[df['Proj'] != df['Adj Proj']]
        
        # Iterate over rows where adjustment is needed
        for idx, row in adjustment_needed.iterrows():
            # Calculate the shift factor based on 'proj' and 'adj_proj'
            shift_factor = (row['Adj Proj'] / row['Proj']) * adjustment_factor

            # Adjust the percentiles
            df.at[idx, '25th'] = max(0, row['25th'] * shift_factor)
            df.at[idx, '50th'] = max(0, row['50th'] * shift_factor)
            df.at[idx, '75th'] = row['75th'] * shift_factor
            df.at[idx, '85th'] = row['85th'] * shift_factor
            df.at[idx, '95th'] = row['95th'] * shift_factor
            

        logging.info("Percentiles adjusted successfully")
        return df

    except Exception as e:
        logging.error(f"function call: adjust_percentiles failed due to error - {str(e)}")
        raise


def calculate_ppd(df):
    """
    Calculate Points Per Dollar (PPD) for each percentile and projection column.
    Adds columns at the end of the DataFrame for:
    - '25th PPD', '50th PPD', 'Proj PPD', '75th PPD', '85th PPD', '95th PPD'

    Parameters:
    df (pd.DataFrame): DataFrame containing salary and percentiles.

    Returns:
    pd.DataFrame: DataFrame with PPD columns added.
    """
    df['25th PPD'] = (df['25th'] / df['Salary'])*1000
    df['50th PPD'] = (df['50th'] / df['Salary'])*1000
    df['Proj PPD'] = (df['Proj'] / df['Salary'])*1000
    df['75th PPD'] = (df['75th'] / df['Salary'])*1000
    df['85th PPD'] = (df['85th'] / df['Salary'])*1000
    df['95th PPD'] = (df['95th'] / df['Salary'])*1000

    return df


def standardize_numeric_columns(df):
    """
    Standardizes all numeric columns, except 'Salary', to display 2 decimal places.
    Also divides the 'Roster%' column by 1000 to convert it to a more readable percentage format.

    Parameters:
    df (pd.DataFrame): DataFrame with numeric columns.

    Returns:
    pd.DataFrame: DataFrame with standardized numeric columns.
    """
    # Divide 'Roster%' column by 1000
    if 'Roster%' in df.columns:
        df['Roster%'] = df['Roster%'] / 100

    # Round all numeric columns to 2 decimal places, except 'Salary'
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
    numeric_columns = numeric_columns.drop('Salary', errors='ignore')  # Exclude 'Salary' column
    df[numeric_columns] = df[numeric_columns].round(2)

    return df


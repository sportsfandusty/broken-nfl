import os

# Define the base directory relative to the location of this settings.py file
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'opto'))

# Set up the raw CSV input directory
RAW_CSV_DIR = os.path.join(BASE_DIR,'csvs')

# Set up the output directory for prepped files
OUTPUT_DIR = os.path.join(BASE_DIR, 'prepped')


#Removes players that have no projection
MY_PROJ_THRESHOLD = 0  

#Standardize Column Names
RENAME_RULES = {
    'SS Proj': 'Proj',
    'My Own': 'Roster%',
    'My Proj': 'Adj_Proj',
    'dk_25_percentile': '25th',
    'dk_50_percentile': '50th',
    'dk_75_percentile': '75th',
    'dk_85_percentile': '85th',
    'dk_std': 'Std'
}

#Columns to keep for the initial csv processing
COLUMNS_TO_KEEP = ['Name', 'Pos', 'Team', 'Opp', 'Salary', 'Proj', 'Adj_Proj','Roster%', '25th',
                   '50th', '75th', '85th', 'Std']
#Columns to display on webapp 
COLUMNS_TO_DISPLAY = ['Name', 'Pos', 'Team', 'Opp', 'Salary', 'Roster%', '25th',
                   '50th','Proj', '75th', '85th', '25th/$', '50th/$', 'Proj/$', '75th/$', '85th/$']



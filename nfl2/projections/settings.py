import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CSV_DIR = os.path.join(BASE_DIR, 'csvs')
OUTPUT_DIR = os.path.join(BASE_DIR, 'prepped')

COLUMNS_TO_KEEP = ['Name', 'Pos', 'Team', 'Opp', 'Salary', 'SS Proj', 'My Own', 'dk_25_percentile',
                   'dk_50_percentile', 'My Proj', 'dk_75_percentile', 'dk_85_percentile', 'dk_95_percentile', 'dk_std']

RENAME_RULES = {
    'SS Proj': 'Proj',
    'My Own': 'Roster%',
    'My Proj': 'Adj Proj',
    'dk_25_percentile': '25th',
    'dk_50_percentile': '50th',
    'dk_75_percentile': '75th',
    'dk_85_percentile': '85th',
    'dk_95_percentile': '95th',
    'dk_std': 'Std Dev'
}

MY_PROJ_THRESHOLD = 0  
 


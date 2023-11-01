"""
Config file containing constants for data processing.

INPUT_FILES: List of strings
    Contains file names of Excel data files to load.

COLUMNS_TO_DROP: List of integers  
    Contains column indexes from loaded data to drop.

SHIP_RANGE_LIMITS: Dictionary 
    Keys are ship type strings, values are tuples of (min, max) distance ranges.
    Used to validate distance traveled for a ship type.

    Example:
    "Bulk carrier": (30000, 150000)

This provides a single place to configure file names, dropped columns, 
and data validation ranges. Helps avoid hard-coding these values in main code.
"""


INPUT_FILES = [
    'data/2018-v270-11102023-EU MRV Publication of information.xlsx',
    'data/2019-v217-11102023-EU MRV Publication of information.xlsx',
    'data/2020-v194-11102023-EU MRV Publication of information.xlsx',
    'data/2021-v176-13102023-EU MRV Publication of information.xlsx'
    # '2022-v98-28102023-EU MRV Publication of information.xlsx'
]

COLUMNS_TO_DROP = [ 
    4,5,6,8,9,10,11,
    13,15,17,18,19,20,
    24,25,26,27,28,29,
    34,36,37,40,41,42,
    43,49,50,51,52,55,
    56,57,58,59,60
]

# Ranges obtained from the internet - might be useful to cross-validate somehow
SHIP_RANGE_LIMITS = {
    "Passenger ship": (20000, 100000),
    "Ro-pax ship": (15000, 75000),
    "Other ship types": (10000, 200000),
    "Ro-ro ship": (10000, 50000),
    "Gas carrier": (20000, 100000),
    "Bulk carrier": (30000, 150000),
    "General cargo ship": (20000, 100000),
    "Vehicle carrier": (15000, 75000),
    "Chemical tanker": (20000, 100000),
    "Container ship": (30000, 150000),
    "Refrigerated cargo carrier": (20000, 100000),
    "Container/ro-ro cargo ship": (15000, 75000),
    "Oil tanker": (30000, 150000),
    "Combination carrier": (20000, 100000),
    "LNG carrier": (20000, 100000)
}
import pandas as pd
import numpy as np
import re
from pathlib import Path
import sys

from Platforms_Cleaner import Platforms_Cleaner
from shared.PlatformNames import PlatformNames
from shared.PlatformType import PlatformType
from shared.PlatformCategory import PlatformCategory

src_root = Path(__file__).resolve().parents[1]
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from shared.paths import RAW_DIR

class Care_com_Cleaner(Platforms_Cleaner):
    def __init__(self):
        super().__init__()
        self.name = PlatformNames.CARE_COM

class Care_com_Babysitting_Workers_Cleaner(Care_com_Cleaner):
    def __init__(self):
        super().__init__()
        self.type = PlatformType.WORKER
        self.category = PlatformCategory.BABYSITTING
        self.raw_directory = str(RAW_DIR) + '/'

    def clean(self, df):
        df['Location'] = (
            df['Location']
            .astype(str)        # make sure it's a string
            .str.strip()        # trim whitespace
            .str.replace('|', '', regex=False)  # remove literal |
            .str.strip()        # clean again
        )
        # Split location into PLZ, city and canton (example: from "1004 Lausanne, Waadt" to "1004", "Lausanne", "Waadt")
        # First, try the "normal" case with comma
        extracted = df['Location'].str.extract(r'(\d{4})\s+([^,]+),\s+(.+)')
        # Fallback: PLZ + first word as City (ignore the rest), no Canton
        fallback = df['Location'].str.extract(r'(\d{4})\s+(\S+)')
        # Fill PLZ and City from fallback when missing
        extracted[0] = extracted[0].fillna(fallback[0])  # PLZ
        extracted[1] = extracted[1].fillna(fallback[1])  # City
        # Rename columns
        extracted.columns = ['PLZ', 'City', 'Canton']
        df[['PLZ', 'City', 'Canton']] = extracted
        
        # Get the profile ID from the 'URL' column
        df['ID'] = df['URL'].str.extract(r'/(\d+)\?')[0]
        df['Full Name'] = df['Name']
        df['Name'] = df['Name'].apply(lambda x: ' '.join(x.split()[:-1]))
        # Remove the "Alter: " from the "Age" column
        df['Age'] = df['Age'].str.replace('Alter: ', '', regex=False)
        # Convert the 'Age' column to numeric, forcing errors to NaN
        df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
        # Remove the "Erfahrung: " from the "Experience" column
        df['Experience'] = df['Experience'].str.replace('Erfahrung: ', '', regex=False)
        # Convert the 'Experience' column to numeric, forcing errors to NaN
        # cleaned_df['Experience'] = pd.to_numeric(cleaned_df['Experience'], errors='coerce')
        # Change the "Ab Fr.X pro Stunde" to "X" in "Salary" column
        df['Salary'] = df['Salary'].str.replace('Ab Fr.', '', regex=False)
        df['Salary'] = df['Salary'].str.replace('pro Stunde', '', regex=False)
        # Convert the 'Salary' column to numeric, forcing errors to NaN
        df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
        # Extract the number of gigs from the 'Number of gigs' column (e.g., '2-mal eingestellt'), keep 0 if it's 0
        df['Bookings'] = df['Number of gigs'].apply(self.extract_bookings)
        df['Bookings'] = pd.to_numeric(df['Bookings'], errors='coerce')
        # Dedup based on ID
        df = df.drop_duplicates(subset=['ID'])
        return df
    
    def extract_bookings(self, value):
        if value == '0':
            return 0
        match = re.search(r'(\d+)', str(value))
        return int(match.group(1)) if match else 0
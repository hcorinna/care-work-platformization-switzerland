import pandas as pd
import numpy as np
import re
from pathlib import Path
import sys

from Platforms_Cleaner import Platforms_Cleaner
from shared.PlatformNames import PlatformNames
from shared.PlatformType import PlatformType
from Location_Cleaner import Location_Cleaner

src_root = Path(__file__).resolve().parents[1]
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from shared.paths import RAW_DIR, COMBINED_DIR, CLEAN_DIR

class Platform24_Cleaner(Platforms_Cleaner):
    def __init__(self):
        super().__init__()

    experience_map = {
            '0-1 Jahre Erfahrung': 0.5,
            '1-3 Jahre Erfahrung': 2,
            '3-5 Jahre Erfahrung': 4,
            'Über 5 Jahre Erfahrung': 6
        }

    last_online_map = {
                'Zuletzt eingeloggt: Vor mehr als 1 Monat': 'Inactive (1+ month)',
                'Zuletzt eingeloggt: Letzten Monat': 'Active (last month)',
                'Zuletzt eingeloggt: Letzte Woche': 'Active (last week)',
                'Zuletzt eingeloggt: Gestern': 'Active (yesterday)',
                'Zuletzt eingeloggt: Heute': 'Active (today)',
            }
    last_online_order = ['Inactive (1+ month)', 'Active (last month)', 'Active (last week)', 'Active (yesterday)', 'Active (today)']

    def convert_member_since(self, value):
        # Check for missing values (NaN)
        if pd.isna(value):
            return np.nan
        # Handle specific cases (like 'Heute' or 'Gestern')
        if 'Heute' in value:
            return 0  # Heute = 0 years
        if 'Gestern' in value:
            return 1 / 365  # Gestern = 1 day, approximate as 1/365 of a year
        
        # Handle "fast", "etwa", "mehr als" cases
        summand = 0
        if 'fast' in value:
            summand = -0.1  # Assume "fast" means approximately 90% of the value
        elif 'mehr als' in value:
            summand = 0.1  # Assume "etwa" or "mehr als" means 10% more than the value

        # Match "...ein Jahr"
        number_pattern = r"\b.*\bein Jahr\b"
        match = re.match(number_pattern, value)
        if match:
            return 1 + summand
        
        # Match "...ein Monat"
        number_pattern = r"\b.*\bein Monat\b"
        match = re.match(number_pattern, value)
        if match:
            return 1/12  # 1 month = 1/12 year

        # Extract number and unit (e.g., "2 Jahre", "5 Monate")
        number_pattern = r".*?(\d+)\s*(Jahre|Monate|Tage)"
        match = re.match(number_pattern, value)
        
        if match:
            number = int(match.group(1))
            unit = match.group(2)
            
            # Convert the unit to years
            if unit == "Jahre":
                return number + summand
            elif unit == "Monate":
                return (number / 12)  # Convert months to years
            elif unit == "Tage":
                return (number / 365)  # Convert days to years
        return np.nan  # If no match is found, return NaN
    
    def clean(self, df):
        location_split = df['Location'].str.split(' ')
        df['PLZ'] = location_split.str[0].astype(int)
        df['City'] = location_split.str[1:].str.join(' ')
        
        # Clean Reply Rate (extract percentages)
        df['Reply rate'] = df['Reply rate'].str.extract(r'(\d+)').astype(float)
        
        # Standardize 'Last online' column
        df['Last online'] = df['Last online'].map(self.last_online_map)
        # Convert 'Last online' to a categorical variable with the specific order
        df['Last online'] = pd.Categorical(df['Last online'], categories=self.last_online_order, ordered=True)
        
        # Standardize 'Member since' column (convert to float)
        df['Member since'] = df['Member since'].str.replace('Mitglied seit: ', '', regex=False)
        df['Membership length'] = df['Member since'].apply(self.convert_member_since)

        # Remove duplicates
        df = df.drop_duplicates(subset=['ID'])

        cleaner = Location_Cleaner()
        df = cleaner.clean(df)
        df.drop(df[df["CountryCode"] != "ch"].index, inplace=True)

        return df

class Platform24_Workers_Cleaner(Platform24_Cleaner):
    def __init__(self):
        super().__init__()
        self.type = PlatformType.WORKER

    def clean(self, df):
        # Clean Age (extract numbers)
        df['Age'] = df['Age'].str.extract(r'(\d+)').astype(float)
        
        # Clean Salary (extract numbers)
        df['Salary'] = df['Salary'].str.extract(r'(\d+)').astype(float)
        
        # Clean Experience (convert to numeric categories)
        df['Experience_int'] = df['Experience'].map(self.experience_map)
        
        df = super().clean(df)
        return df
    
class Babysitting24_Workers_Cleaner(Platform24_Workers_Cleaner):
    def __init__(self):
        super().__init__()
        self.name = PlatformNames.BABYSITTING24
        self.raw_directory = str(RAW_DIR) + '/'

class Seniorservice24_Workers_Cleaner(Platform24_Workers_Cleaner):
    def __init__(self):
        super().__init__()
        self.name = PlatformNames.SENIORSERVICE24
        self.raw_directory = str(RAW_DIR) + '/'

class Babysitting24_Jobs_Cleaner(Platform24_Cleaner):
    def __init__(self):
        super().__init__()
        self.name = PlatformNames.BABYSITTING24
        self.type = PlatformType.JOB
        self.raw_directory = str(RAW_DIR) + '/'

class Seniorservice24_Jobs_Cleaner(Platform24_Cleaner):
    def __init__(self):
        super().__init__()
        self.name = PlatformNames.SENIORSERVICE24
        self.type = PlatformType.JOB
        self.raw_directory = str(RAW_DIR) + '/'

    def clean(self, df):
         # Clean Tasks column: replace line breaks with [NL]
        if 'Tasks' in df.columns:
            df['Tasks'] = df['Tasks'].str.replace('\n', '[NL]', regex=False)

        df = super().clean(df)
        return df
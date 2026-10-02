import pandas as pd
import numpy as np
from pathlib import Path
import sys

from Platforms_Cleaner import Platforms_Cleaner
from shared.PlatformNames import PlatformNames
from shared.PlatformType import PlatformType

src_root = Path(__file__).resolve().parents[1]
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from shared.paths import RAW_DIR

class GreatAuPair_Cleaner(Platforms_Cleaner):
    def __init__(self):
        super().__init__()
        self.name = PlatformNames.GREATAUPAIR
    
    def clean_location(self, location):
        # Location format: "Niederlenz, Switzerland"
        # Exract the city and country
        parts = location.split(', ')
        if len(parts) == 2:
            city = parts[0].strip()
            country = parts[1].strip()
            return pd.Series([city, country])
        else:
            return pd.Series([location, np.nan])
        
    def clean(self, df):
        df['Full Name'] = df['Name']
        df['Name'] = df['Name'].apply(lambda x: ' '.join(x.split()[:-1]))
        df[['City', 'Country']] = df['Location'].apply(self.clean_location)
        # Keep only rows where Country is Switzerland
        df = df[df['Country'] == 'Switzerland']
        df['Last online (delta in days)'] = df['Last Logged In'].str.replace('Last logged in', '', regex=False)
        df['Last online (delta in days)'] = df['Last online (delta in days)'].str.replace(' days ago', '', regex=False)
        # If what remains is "Today", set it to 0, otherwise convert to numeric
        df['Last online (delta in days)'] = df['Last online (delta in days)'].replace('Today', '0')
        df['Last online (delta in days)'] = df['Last online (delta in days)'].replace('Yesterday', '1')
        # Convert to numeric, forcing errors to NaN
        df['Last online (delta in days)'] = pd.to_numeric(df['Last online (delta in days)'], errors='coerce')
        return df

class GreatAuPair_Workers_Cleaner(GreatAuPair_Cleaner):
    def __init__(self):
        super().__init__()
        self.type = PlatformType.WORKER
        self.raw_directory = str(RAW_DIR) + '/'

    def clean(self, df):
        df = super().clean(df)
        df['Age'] = df['Age'].str.replace(' years old', '', regex=False)
        df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
        return df

class GreatAuPair_Jobs_Cleaner(GreatAuPair_Cleaner):
    def __init__(self):
        super().__init__()
        self.type = PlatformType.JOB
        self.raw_directory = str(RAW_DIR) + '/'

    def clean(self, df):
        df = super().clean(df)
        return df
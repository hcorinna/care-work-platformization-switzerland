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

class MisGrosi_Cleaner(Platforms_Cleaner):
    def __init__(self):
        super().__init__()
        self.name = PlatformNames.MISGROSI

class MisGrosi_Workers_Cleaner(MisGrosi_Cleaner):
    def __init__(self):
        super().__init__()
        self.type = PlatformType.WORKER
        self.raw_directory = str(RAW_DIR) + '/'

    def clean(self, df):
        df[['PLZ', 'City', 'Country']] = df['Location'].str.extract(r'(\d{4,5})\s+([^,]+),\s*(.+)')
        # Keep only rows where Country is Switzerland, Schweiz, or blank
        df = df[df['Country'].isin(['Switzerland', 'Schweiz', ''])]
        return df

class MisGrosi_Jobs_Cleaner(MisGrosi_Cleaner):
    def __init__(self):
        super().__init__()
        self.type = PlatformType.JOB
        self.raw_directory = str(RAW_DIR) + '/'

    def clean(self, df):
        # Assuming df is your DataFrame and 'Date posted' is the column to clean
        df['Posted x months ago'] = df['Date posted'].apply(self.convert_date_posted)
        df[['PLZ', 'City', 'Country']] = df['Location'].str.extract(r'(\d{4,5})\s+([^,]+),\s*(.+)')
        # Keep only rows where Country is Switzerland, Schweiz, or blank
        df = df[df['Country'].isin(['Switzerland', 'Schweiz', ''])]
        return df
    
    # Function to convert 'Date posted' to months ago
    def convert_date_posted(self, date_str):
        if pd.isna(date_str):
            return date_str
        elif 'Monat' in date_str:
            return int(date_str.split()[1])
        elif 'Jahr' in date_str:
            return int(date_str.split()[1]) * 12
        else:
            return np.nan
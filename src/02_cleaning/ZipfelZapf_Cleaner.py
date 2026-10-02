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

class ZipfelZapf_Jobs_Cleaner(Platforms_Cleaner):
    def __init__(self):
        super().__init__()
        self.name = PlatformNames.ZIPFELZAPF
        self.type = PlatformType.JOB
        self.raw_directory = str(RAW_DIR) + '/'

    def clean(self, df):
        df[['City', 'Canton']] = df['Location'].str.split(' - ', expand=True)
        df['Raw salary'] = df['Salary']
        df['Salary'] = df['Salary'].apply(self.parse_salary)
        return df
    
    def parse_salary(self, value):
        if isinstance(value, str) and 'CHF' in value:
            parts = value.replace('CHF', '').strip().split('-')
            if len(parts) == 2:
                try:
                    low = float(parts[0])
                    high = float(parts[1])
                    return (low + high) / 2
                except ValueError:
                    return None
        return None  # e.g., "Marktüblich" or malformed

import pandas as pd
import numpy as np
import re
from pathlib import Path
import sys

from Platforms_Cleaner import Platforms_Cleaner
from shared.PlatformNames import PlatformNames
from shared.PlatformType import PlatformType

src_root = Path(__file__).resolve().parents[1]
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from shared.paths import RAW_DIR

class Tagesmutterverein_Workers_Cleaner(Platforms_Cleaner):
    def __init__(self):
        super().__init__()
        self.name = PlatformNames.TAGESMUTTERVEREIN
        self.type = PlatformType.WORKER
        self.raw_directory = str(RAW_DIR) + '/'

    def clean(self, df):
        df['Salary'] = df['Description'].apply(self.extract_hourly_rate)
        df = df.rename(columns={'Location': 'City'})
        return df
    
    def extract_hourly_rate(self, description):
        if pd.isna(description):
            return None
        match = re.search(r'Preis:\s*([\d.]+)\s*Fr\.?\s*/\s*Stunde', description)
        if match:
            return float(match.group(1))
        return None

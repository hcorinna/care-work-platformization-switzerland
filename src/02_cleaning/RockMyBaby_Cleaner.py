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

class RockMyBaby_Jobs_Cleaner(Platforms_Cleaner):
    def __init__(self):
        super().__init__()
        self.type = PlatformType.JOB
        self.name = PlatformNames.ROCKMYBABY
        self.raw_directory = str(RAW_DIR) + '/'

    def clean(self, df):
        df[['Canton', 'City']] = df['Location'].str.split(' - ', expand=True)
        # If City is "Switzerland", set it to the Canton value
        df.loc[df['City'] == 'Switzerland', 'City'] = df['Canton']
        return df
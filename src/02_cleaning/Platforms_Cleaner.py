from abc import ABC, abstractmethod
from os import listdir
from os.path import isfile, join
from pathlib import Path
import sys

import pandas as pd

src_root = Path(__file__).resolve().parents[1]
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from shared.paths import RAW_DIR, COMBINED_DIR, CLEAN_DIR

class Platforms_Cleaner(ABC):
    def __init__(self):
        self.raw_directory = str(RAW_DIR) + '/'
        self.combined_directory = str(COMBINED_DIR) + '/'
        self.clean_directory = str(CLEAN_DIR) + '/'
        self.name = ""
        self.type = None
        self.category = None

    def get_filename(self):
        return self.name.value + "_" + self.type.value + (("_" + self.category.value) if self.category else "")

    def __get_raw_files_from_dir(self):
        raw_files = [join(self.raw_directory, f) for f in listdir(self.raw_directory) if isfile(join(self.raw_directory, f))]
        return raw_files
    
    def __get_combined_raw_data(self):
        return pd.read_csv(self.combined_directory + '_' + self.get_filename() + '.csv')
    
    def get_clean_data(self):
        return pd.read_csv(self.clean_directory + '_' + self.get_filename() + '.csv')

    def __combine_raw_data(self):
        csv_files = self.__get_raw_files_from_dir()
        combined_df = pd.concat([pd.read_csv(file) for file in csv_files])
        return combined_df
    
    def __export_combined_raw_data(self):
        combined_df = self.__combine_raw_data()
        Path(self.combined_directory).mkdir(parents=True, exist_ok=True)
        combined_df.to_csv(self.combined_directory + self.get_filename() + '.csv', index=False)
        return combined_df

    def export_clean_data(self):
        combined_df = self.__export_combined_raw_data()
        cleaned_df = self.clean(combined_df)
        Path(self.clean_directory).mkdir(parents=True, exist_ok=True)
        cleaned_df.to_csv(self.clean_directory + self.get_filename() + '.csv', index=False)
        return cleaned_df

    @abstractmethod
    def clean(self, raw_data):
        pass
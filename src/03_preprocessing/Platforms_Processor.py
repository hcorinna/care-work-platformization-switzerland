from os import listdir, path
from os.path import isfile, join
from pathlib import Path
import sys

import yaml
import pandas as pd
from gender_processing import process_dataset as gender_process_dataset
from location_processing import process_dataset as location_process_dataset
from plz_processing import add_user_counts_to_population_density
from active_processing import process_dataset as active_process_dataset

src_root = Path(__file__).resolve().parents[1]
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from shared.paths import CLEAN_DIR, PROCESSED_DIR

class Platforms_Processor:
    def __init__(
        self,
        from_clean_data=True,
        gender=True,
        gender_use_api=False,
        location=True,
        location_count=True,
        active=True,
    ):
        self.clean_directory = str(CLEAN_DIR) + '/'
        self.processed_directory = str(PROCESSED_DIR) + '/'
        self.from_clean_data = from_clean_data
        self.gender = gender
        self.gender_use_api = gender_use_api
        self.location = location
        self.location_count = location_count
        self.active = active
        config_path = Path(__file__).resolve().parent / 'config' / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            self.MIN_ACCURACY = config.get('min_accuracy', 80)
            self.IS_ACTIVE_DAYS = config.get('is_active_days', 31)

    def __get_clean_files_from_dir(self):
        clean_files = [join(self.clean_directory, f) for f in listdir(self.clean_directory) if isfile(join(self.clean_directory, f))]
        return clean_files
    
    def __get_processed_files_from_dir(self):
        processed_files = [join(self.processed_directory, f) for f in listdir(self.processed_directory) if isfile(join(self.processed_directory, f))]
        return processed_files
    
    def __process(self, df, filename):
        print('Processing file:', filename)
        if self.gender:
            df = gender_process_dataset(
                df,
                filename,
                self.MIN_ACCURACY,
                use_api=self.gender_use_api,
            )
        if self.location:
            df, not_standardized_count = location_process_dataset(df, filename)
        if self.active:
            df = active_process_dataset(df, filename, self.IS_ACTIVE_DAYS)
        return (df, not_standardized_count) if self.location else (df, 0)

    def export_clean_data(self):
        Path(self.processed_directory).mkdir(parents=True, exist_ok=True)
        data_files = self.__get_clean_files_from_dir() if self.from_clean_data else self.__get_processed_files_from_dir()
        population_density_df = pd.read_csv('./plz_data/population_density_clean.csv')
        not_standardized_count = 0
        total_rows = 0
        for file in data_files:
            df = pd.read_csv(file)
            total_rows += len(df)
            filename = path.basename(file)
            processed_df, not_standardized_count_file = self.__process(df, filename)
            not_standardized_count += not_standardized_count_file
            processed_df.to_csv(join(self.processed_directory, filename), index=False)
            if self.location_count:
                # Add user counts to population density
                if 'Gemeindename' in processed_df.columns:
                    population_density_df = add_user_counts_to_population_density(processed_df, population_density_df, platform_name=filename.split('.')[0])
                else:
                    print(f"'Gemeindename' column not found in {filename}, skipping user counts addition.")
        population_density_df.to_csv(join(self.processed_directory, 'population_density_with_user_numbers.csv'), index=False)
        
        if self.location:
            print(f"Total rows with non-standardized 'Gemeindename' across all files: {not_standardized_count} out of {total_rows}, that's {not_standardized_count / total_rows * 100:.2f}%")

        return processed_df
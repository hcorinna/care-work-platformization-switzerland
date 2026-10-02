from pathlib import Path

import pandas as pd

_this_dir = Path(__file__).resolve().parent
base_dir = _this_dir.parent
plz_df = pd.read_csv(base_dir / "01_data_collection" / "resources" / "postal_codes" / "PLZ.csv", sep=';', comment='#')
translation_df = pd.read_csv(_this_dir / 'plz_data' / 'transformed_translations.csv')
population_density_df = pd.read_csv(_this_dir / 'plz_data' / 'population_density_new.csv')

def process_dataset(df, filename):
    # Check if 'City' names exist in translation_df['Translation'], if so replace them with the corresponding 'Original' from translation_df
    if 'City' in df.columns:
        df = df.merge(translation_df, left_on='City', right_on='Translation', how='left')
        df['Gemeindename'] = df['Gemeindename'].fillna(df['City'])
    if 'ResolvedCity' in df.columns:
        df = df.merge(translation_df, left_on='ResolvedCity', right_on='Translation', how='left', suffixes=(None, '_rc'))
        df['Gemeindename'] = df['Gemeindename_rc'] if 'City' not in df.columns else df['Gemeindename'].fillna(df['ResolvedCity'])
    if 'Gemeindename' not in df.columns:
        df['Gemeindename'] = ""
    # For every row in df, check if the value of 'Gemeindename' is in population_density_df['City'], otherwise try it with other data
    not_standardized_count = 0
    for index, row in df.iterrows():
        if row['Gemeindename'] not in population_density_df['Bezeichnung'].values:
            gemeindename = ""
            deriving_functions = [derive_gemeindename_from_village_name, derive_gemeindename_from_PLZ, derive_gemeindename_from_resolved_city_name]
            # While we still haven't found a gemeindename and we still have functions to try, go through the functions
            for func in deriving_functions:
                if not gemeindename:
                    gemeindename = func(row, df.columns)
            if gemeindename:
                df.at[index, 'Gemeindename'] = gemeindename
            else:
                # print(f"'Gemeindename' not found in population density data for row {index} with PLZ {row.get('PLZ', 'N/A')} and City {row['City']}")
                # print(row['City'])
                not_standardized_count += 1
    print(f"Total rows with non-standardized 'Gemeindename': {not_standardized_count} out of {len(df)} in {filename}, that's {not_standardized_count / len(df) * 100:.2f}%")
    return df, not_standardized_count


def derive_gemeindename_from_PLZ(row, columns=None):
    """
    Derives 'Gemeindename' from 'PLZ' in the given DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame containing 'PLZ' column.
        plz_df (pd.DataFrame): DataFrame containing 'PLZ' and 'Gemeindename'.
        
    Returns:
        pd.DataFrame: DataFrame with 'Gemeindename' column added.
    """
    if 'PLZ' in row and row['PLZ'] != -1:
        plz_value = row['PLZ']
        derived_cities = plz_df[plz_df['PLZ'] == plz_value]['Gemeindename'].tolist()
        for derived_city in derived_cities:
            if derived_city in population_density_df['Bezeichnung'].values:
                return derived_city
    return ""

def derive_gemeindename_from_village_name(row, columns=None):
    """
    Derives 'Gemeindename' from 'PLZ' in the given DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame containing 'City' column.
        plz_df (pd.DataFrame): DataFrame containing 'Ortsname' and 'Gemeindename'.
        
    Returns:
        pd.DataFrame: DataFrame with 'Gemeindename' column added.
    """
    if 'City' in row:
        ortsname = row['City']
        derived_cities = plz_df[plz_df['Ortschaftsname'] == ortsname]['Gemeindename'].tolist()
        for derived_city in derived_cities:
            if derived_city in population_density_df['Bezeichnung'].values:
                return derived_city
    return ""

def derive_gemeindename_from_resolved_city_name(row, columns=None):
    """
    Derives 'Gemeindename' from 'PLZ' in the given DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame containing 'City' column.
        plz_df (pd.DataFrame): DataFrame containing 'Ortsname' and 'Gemeindename'.
        
    Returns:
        pd.DataFrame: DataFrame with 'Gemeindename' column added.
    """
    if 'ResolvedCity' in row:
        resolved_city = row['ResolvedCity']
        if resolved_city in population_density_df['Bezeichnung'].values:
            return resolved_city
        derived_cities = plz_df[plz_df['Ortschaftsname'] == resolved_city]['Gemeindename'].tolist()
        for derived_city in derived_cities:
            if derived_city in population_density_df['Bezeichnung'].values:
                return derived_city
    return ""
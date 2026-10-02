from pathlib import Path

import pandas as pd

def compare_files():
    # Read the CSV file
    population_density_df = pd.read_csv('./population_density.csv', sep=';', encoding='utf-8')
    population_density_new_df = pd.read_csv('./population_density_new.csv', sep=',', encoding='utf-8')
    base_dir = Path(__file__).resolve().parents[2]
    plz_df = pd.read_csv(base_dir / "01_data_collection" / "resources" / "postal_codes" / "PLZ.csv", sep=';', encoding='utf-8', comment='#')

    population_density_cities = set(population_density_df['GEO_NAME'].unique())
    population_density_new_cities = set(population_density_new_df['Bezeichnung'].unique())
    plz_cities = set(plz_df['Gemeindename'].unique())
    
    missing_cities_in_PLZ = population_density_cities - plz_cities
    print(f"Cities in population density data but not in PLZ data: {missing_cities_in_PLZ}")

    missing_cities_in_population_density = plz_cities - population_density_cities
    print(f"Cities in PLZ data but not in population density data: {missing_cities_in_population_density}")

    missing_cities_in_population_density_new = plz_cities - population_density_new_cities
    print(f"Cities in PLZ data but not in new population density data: {missing_cities_in_population_density_new}")

    missing_cities_in_population_density_new_reverse = population_density_new_cities - plz_cities
    print(f"Cities in new population density data but not in PLZ data: {missing_cities_in_population_density_new_reverse}")

    missing_cities_in_population_density = population_density_new_cities - population_density_cities
    print(f"Cities in new population density data but not in old population density data: {missing_cities_in_population_density}")

    missing_cities_in_population_density_reverse = population_density_cities - population_density_new_cities
    print(f"Cities in old population density data but not in new population density data: {missing_cities_in_population_density_reverse}")

def main():
    compare_files()

if __name__ == "__main__":
    main()
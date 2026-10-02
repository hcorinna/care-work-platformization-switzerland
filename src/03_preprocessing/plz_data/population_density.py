# Extract only what we need from the population density data.
# Data format:
# "GEO_ID";"GEO_NAME";"VARIABLE";VALUE;"UNIT";"STATUS";"STATUS_DESC";"DESC_VAL";"PERIOD_REF";"SOURCE";"LAST_UPDATE";"GEOM_CODE";"GEOM";"GEOM_PERIOD";"MAP_ID";"MAP_URL"
# "1";"Aeugst am Albis";"Anzahl Einwohner/-innen";1998;"Einwohner/Innen";"A";"Normaler Wert";"";"2023-12-31";"BFS – Statistik der Bevölkerung und der Haushalte (STATPOP)";"2024-08-08";"polg";"Politische Gemeinden";"2023-01-01";"27876";"https://www.atlas.bfs.admin.ch/maps/13/map/mapIdOnly/27876_de.html"
# "1";"Aeugst am Albis";"Einwohner/-innen pro km² Gesamtfläche";252.6;"Einwohner pro km²";"A";"Normaler Wert";"";"2023-12-31";"BFS – Arealstatistik der Schweiz (AREA), Statistik der Bevölkerung und der Haushalte (STATPOP)";"2024-08-08";"polg";"Politische Gemeinden";"2023-01-01";"27876";"https://www.atlas.bfs.admin.ch/maps/13/map/mapIdOnly/27876_de.html"
# "2";"Affoltern am Albis";"Anzahl Einwohner/-innen";12859;"Einwohner/Innen";"A";"Normaler Wert";"";"2023-12-31";"BFS – Statistik der Bevölkerung und der Haushalte (STATPOP)";"2024-08-08";"polg";"Politische Gemeinden";"2023-01-01";"27876";"https://www.atlas.bfs.admin.ch/maps/13/map/mapIdOnly/27876_de.html"

# Extract "GEO_NAME" and "VALUE" for rows where "VARIABLE" is "Einwohner/-innen pro km² Gesamtfläche"
# Add "VALUE" as "EinwohnerInnenzahl" when "VARIABLE" is "Anzahl Einwohner/-innen" and add 
import pandas as pd

def extract_population_density() -> pd.DataFrame:
    # Read the CSV file
    df = pd.read_csv('./population_density.csv', sep=';', encoding='utf-8')
    
    # Pivot the data based on VARIABLE
    pivot_df = df.pivot(index='GEO_NAME', columns='VARIABLE', values='VALUE').reset_index()

    # Rename columns
    pivot_df = pivot_df.rename(columns={
        'GEO_NAME': 'City',
        'Anzahl Einwohner/-innen': 'Population',
        'Einwohner/-innen pro km² Gesamtfläche': 'Density'
    })
    pivot_df['City'] = pivot_df['City']

    pivot_df.to_csv('./population_density_clean.csv', index=False)

def main():
    extract_population_density()

if __name__ == "__main__":
    main()
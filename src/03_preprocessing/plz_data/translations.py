# For every language column (Deutsch,Französisch,Italienisch,Rätoromanisch,Englisch) entry, create a new row in the new dataframe.
# The new row should have the following columns:
# - Translation: the value from the language column
# - Original: the value from the Gemeindename column
import pandas as pd

def transform_translations(input_file, output_file):
    # Read the translations CSV file
    df = pd.read_csv(input_file, comment='#')

    # Create a new DataFrame to hold the transformed data
    transformed_data = []

    # Iterate over each row in the original DataFrame
    for index, row in df.iterrows():
        original = row['Gemeindename']
        # Iterate over each language column
        for lang in ['Deutsch', 'Französisch', 'Italienisch', 'Rätoromanisch', 'Englisch']:
            translation = row[lang]
            if pd.notna(translation):  # Check if translation is not NaN
                transformed_data.append({'Translation': translation, 'Gemeindename': original})

    # Create a new DataFrame from the transformed data
    transformed_df = pd.DataFrame(transformed_data)
    # Save the transformed DataFrame to a new CSV file
    transformed_df.to_csv(output_file, index=False)

def main():
    # Define input and output file paths
    input_file = './translations.csv'
    output_file = './transformed_translations.csv'
    # Transform the translations
    transform_translations(input_file, output_file)

if __name__ == "__main__":
    main()
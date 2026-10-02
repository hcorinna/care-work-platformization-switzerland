from pathlib import Path

import pandas as pd
import requests

def process_dataset(df, filename, min_accuracy=70, use_api=False, api_key=None):
    if 'Name' not in df.columns:
        print(f"'Name' column not found in {filename}")
        return df
    cache_path = Path(__file__).resolve().parent / 'gender_data.csv'
    if cache_path.exists():
        gender_df = pd.read_csv(cache_path)
    else:
        gender_df = pd.DataFrame(
            columns=["name", "name_sanitized", "gender", "samples", "accuracy"]
        )
    if use_api and api_key is None:
        credentials_path = Path(__file__).resolve().parents[1] / 'credentials.json'
        if not credentials_path.exists():
            raise FileNotFoundError(
                "credentials.json not found. Provide api_key or place credentials.json at repo root."
            )
        credentials = pd.read_json(credentials_path)
        if "GENDER_API_KEY" not in credentials:
            raise KeyError("GENDER_API_KEY missing in credentials.json")
        api_key = credentials["GENDER_API_KEY"]
    # Find unique names not in gender_df
    all_names = df['Name'].dropna().apply(split_names, filename=filename).explode().unique()
    unique_names = set([n for n in all_names if n])
    known_names = set(gender_df['name'].values)
    new_names = list(unique_names - known_names)
    new_rows = get_missing_names(new_names, api_key) if use_api else []
    if new_rows:
        pd.DataFrame(new_rows).to_csv(cache_path, mode='a', header=not cache_path.exists(), index=False)
        gender_df = pd.concat([gender_df, pd.DataFrame(new_rows)], ignore_index=True)
    df['Gender'] = df['Name'].apply(lambda x: '+'.join(split_names_and_lookup(x, gender_df, min_accuracy, filename)))
    return df

def split_names_and_lookup(name, gender_df, min_accuracy=70, filename=None):
    names = split_names(name, filename)
    genders = []
    for n in names:
        genders.append(lookup_gender(n, gender_df, min_accuracy))
    return genders

def get_missing_names(new_names, api_key):
    new_rows = []
    errors = 0
    for name in new_names:
        url = 'https://gender-api.com/get'
        params = {'key': api_key, 'name': name}
        try:
            response = requests.get(url, params=params)
            data = response.json()
            new_rows.append({
                'name': name.lower(),
                'name_sanitized': data.get('name_sanitized', name.lower()),
                'gender': data.get('gender', 'unknown'),
                'samples': data.get('samples', 0),
                'accuracy': data.get('accuracy', 0)
            })
        except Exception as e:
            print(f"Error with API call for name {name}: {e}")
            errors += 1
            if errors > 3:
                print("Too many errors, stopping API calls.")
                return new_rows
    return new_rows

def lookup_gender(name, gender_df, min_accuracy=70):
    name = str(name).lower()
    match = gender_df[gender_df['name_sanitized'] == name]
    # print(f"Looking up name: {name}, found matches: {len(match)}")
    if match.empty:
        match = gender_df[gender_df['name'] == name]
        # print(f"Fallback lookup for name: {name}, found matches: {len(match)}")
    elif match.empty:
        conjunctions = [' und ', ' et ', ' e ', ' and ']
        for conj in conjunctions:
            if conj in name:
                return 'unknown'
    if not match.empty:
        match = match.iloc[0]
        if match['accuracy'] >= min_accuracy:
            return match['gender']
    return 'unknown'

def split_names(name, filename):
    if "job" in filename.lower():
        conjunctions = [' und ', ' et ', ' e ', ' and ']
        name = str(name).lower().strip()
        for conj in conjunctions:
            if conj in name:
                return [n.strip() for n in name.split(conj) if n.strip()]
    return [name.lower().strip()] if isinstance(name, str) else []
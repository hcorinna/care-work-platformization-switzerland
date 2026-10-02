import pandas as pd

def process_dataset(df, filename, is_active_days=31):
    """
    Processes the dataset to ensure it has a 'Is active' and 'Joined recently' column derived from membership length and last online.

    Args:
        df (pd.DataFrame): The DataFrame to process.

    Returns:
        pd.DataFrame: The processed DataFrame with a 'Activity Status' column.
    """
    if "24" in filename:
        df['Recently active'] = [v != 'Inactive (1+ month)' and not pd.isna(v) for v in df['Last online']]
        df['Recently joined'] = df['Membership length'] < is_active_days / 365
    elif "babysits" in filename:
        df['Recently active'] = df['Last online (delta in days)'] < is_active_days
        df["Recently joined"] = df.apply(lambda x: babysits_recently_joined(x["Scraping date"], x["Joined"]), axis=1)
    elif "care" in filename:
        df['Recently active'] = ~df['Last online'].isna()
    elif "greataupair" in filename:
        df['Recently active'] = df['Last online (delta in days)'] < is_active_days
    if 'Recently active' in df.columns and 'Recently joined' in df.columns:
        df['Is active'] = df['Recently active'] & ~df['Recently joined']
    return df

def babysits_recently_joined(scraping_date, joined):
    scraping_date = pd.to_datetime(scraping_date, errors='coerce')
    joined = pd.to_datetime(joined, errors='coerce')
    two_months_mark = (scraping_date.replace(day=1) - pd.DateOffset(months=1)).to_pydatetime()
    return joined >= two_months_mark
import ast
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pathlib import Path
import sys

from Platforms_Cleaner import Platforms_Cleaner
from shared.PlatformNames import PlatformNames
from shared.PlatformType import PlatformType

src_root = Path(__file__).resolve().parents[1]
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from shared.paths import RAW_DIR

class Babysits_Cleaner(Platforms_Cleaner):
    def __init__(self):
        super().__init__()
        self.name = PlatformNames.BABYSITS
        self.german_months = {
            "Januar": "January",
            "Februar": "February",
            "März": "March",
            "April": "April",
            "Mai": "May",
            "Juni": "June",
            "Juli": "July",
            "August": "August",
            "September": "September",
            "Oktober": "October",
            "November": "November",
            "Dezember": "December"
        }

    def extract_ID(self, url):
        match = re.search(r'/(babysitter|nanny|tagesmutter)/[^/]+/(\d+)/?', url)
        return match.group(2) if match else ""
    
    def extract_review_count(self, value):
        if value == '0':
            return 0
        match = re.match(r'(\d+)', str(value))
        return int(match.group(1)) if match else 0
    
    def count_reviews(self, review_str):
        if not isinstance(review_str, str) or review_str.strip() == "":
            return 0
        try:
            reviews = ast.literal_eval(review_str)
            if isinstance(reviews, list):
                return len(reviews)
            else:
                return 0
        except (ValueError, SyntaxError):
            return 0
        
    def convert_member_since(self, date_str):
        for de, en in self.german_months.items():
            date_str = date_str.replace(de, en)
        return datetime.strptime(date_str, "%B %Y")


class Babysits_Workers_Cleaner(Babysits_Cleaner):
    def __init__(self):
        super().__init__()
        self.type = PlatformType.WORKER
        self.raw_directory = str(RAW_DIR) + '/'

    def clean(self, df):
        df['ID'] = df['URL'].apply(lambda x: self.extract_ID(x))
        df = df.drop_duplicates(subset=['ID'])
        df = df.rename(columns={'Location': 'City'})
        df['Experience'] = df['Experience'].str.replace('Erfahrung: ', '', regex=False)
        df['Bookings'] = df['Bookings'].str.replace('Buchungen: ', '', regex=False)
        df['Bookings'] = df['Bookings'].fillna('0')
        df['Bookings'] = pd.to_numeric(df['Bookings'], errors='coerce')
        df['Salary'] = df['Salary'].str.replace('/Stunde', '', regex=False)
        df['Salary'] = df['Salary'].str.replace('CHF', '', regex=False)
        df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
        df['Number of reviews'] = df['Reviews'].apply(self.count_reviews)
        df['Number of reviews'] = pd.to_numeric(df['Number of reviews'], errors='coerce')
        df['Favorised count'] = df['Favorised count'].fillna('0')
        df['Number of references'] = df['Number of references'].fillna('0')
        df = df[~df['URL'].str.contains(r'--(?:Italien|Deutschland|Frankreich|%C3%96sterreich|Liechtenstein|Finnland)', na=False)]
        return df
    
class Babysits_Workers_Cleaner_Full(Babysits_Cleaner):
    def __init__(self):
        super().__init__()
        self.type = PlatformType.WORKER
        self.raw_directory = str(RAW_DIR) + '/'

    def clean(self, df):
        df = df.drop_duplicates(subset=['ID'])

        # Fix misplaced URLs for "PRIVAT"
        mask = df['Name'] == "PRIVAT"
        df.loc[mask, 'URL'] = df.loc[mask, 'Reviews']
        df.loc[mask, 'Reviews'] = None
        # df['ID'] = df['URL'].apply(lambda x: self.extract_ID(x))
        df = df.rename(columns={'Location': 'City'})
        df['Bookings'] = df['Bookings'].fillna('0')
        df['Bookings'] = pd.to_numeric(df['Bookings'], errors='coerce')
        df['Salary'] = df['Salary'].str.replace('/Stunde', '', regex=False)
        df['Salary'] = df['Salary'].str.replace('CHF', '', regex=False)
        df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
        df['Number of reviews'] = df['Reviews'].apply(self.count_reviews)
        df['Number of reviews'] = pd.to_numeric(df['Number of reviews'], errors='coerce')
        df['Favorised count'] = df['Favorised count'].fillna('0')
        df['Number of references'] = df['Number of references'].fillna('0')
        df["Joined"] = df["Member since"].apply(lambda x: self.convert_member_since(x) if isinstance(x, str) else np.nan)
        df = df[~df['URL'].str.contains(r'--(?:Italien|Deutschland|Frankreich|%C3%96sterreich|Liechtenstein|Finnland)', na=False)]
        return df

class Babysits_Jobs_Cleaner(Babysits_Cleaner):
    def __init__(self):
        super().__init__()
        self.type = PlatformType.JOB
        self.raw_directory = str(RAW_DIR) + '/'

    def clean(self, df):
        # Rename the column 'Favorised countURL' to 'Favorised count' and add the column 'URL'
        new_columns = list(df.columns[1:]) + ['Extra']
        df.columns = new_columns
        df.rename(columns={'Favorised countURL': 'Favorised count', 'Additionals': 'URL', 'Extra': 'Additionals'}, inplace=True)
        df['Number of kids'] = df['Number of kids'].str.replace('Anzahl der Kinder: ', '', regex=False)
        df['Number of kids'] = pd.to_numeric(df['Number of kids'], errors='coerce')
        df['Age of kids'] = df['Age of kids'].str.replace('Alter der Kinder: ', '', regex=False)
        df = df.rename(columns={'Location': 'City'})
        # Fill NaN values in 'Favorised count' with 0
        df['Favorised count'] = df['Favorised count'].fillna('0')
        df = df.drop_duplicates(subset=['ID'])
        df = df[~df['URL'].str.contains(r'--(?:Italien|Deutschland|Frankreich|%C3%96sterreich|Liechtenstein|Finnland)', na=False)]
        return df
    
class Babysits_Jobs_Cleaner_Full(Babysits_Cleaner):
    def __init__(self):
        super().__init__()
        self.type = PlatformType.JOB
        self.raw_directory = str(RAW_DIR) + '/'

    def clean(self, df):
        df['Number of kids'] = pd.to_numeric(df['Number of kids'], errors='coerce')
        df = df.rename(columns={'Number of kids': 'Number of children'})
        df = df.rename(columns={'Location': 'City'})
        # Fill NaN values in 'Favorised count' with 0
        df['Favorised count'] = df['Favorised count'].fillna('0')
        df['Salary'] = df['Salary'].str.replace('/Stunde', '', regex=False)
        df['Salary'] = df['Salary'].str.replace('CHF', '', regex=False)
        df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
        df["Joined"] = df["Member since"].apply(lambda x: self.convert_member_since(x) if isinstance(x, str) else np.nan)
        df = df.drop_duplicates(subset=['ID'])
        df = df[~df['URL'].str.contains(r'--(?:Italien|Deutschland|Frankreich|%C3%96sterreich|Liechtenstein|Finnland)', na=False)]
        return df
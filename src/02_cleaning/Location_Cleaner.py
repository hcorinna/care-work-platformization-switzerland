from pathlib import Path

import requests
import re
import time
import json
import os

class Location_Cleaner:
    def __init__(self, cache_file=None, pause=1.0, save_every=30):
        if cache_file is None:
            cache_file = Path(__file__).resolve().parents[1] / "shared" / "cache" / "nominatim_cache.json"
        self.cache_file = Path(cache_file)
        self.pause = pause
        self.save_every = save_every
        self.cache = self.load_cache()
        self.COUNTRIES = {
            "switzerland": "ch",
            "greece": "gr",
            "italia": "it",
            "italy": "it",
            "spain": "es",
            "austria": "at",
            "germany": "de",
            "france": "fr",
            "portugal": "pt",
            "usa": "us",
            "united states": "us",
        }
        # Short/truncated Swiss city prefixes
        self.SWISS_SHORT_CITY_PREFIXES = [
            "st",       # abbreviation
            "sankt",    # German full
            "saint",    # French/English
            "san",      # Italian
            "sanct",    # historical
            "sant",     # Romansh
            "la"        # La Chaux-de-Fonds
        ]

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_cache(self):
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def detect_country_in_text(self, text):
        text_lower = text.lower()
        for name, code in self.COUNTRIES.items():
            if name in text_lower:
                return name.capitalize(), code
        return None, None

    def clean_query(self, location_text):
        """
        Returns:
            postal_code: str or None
            city_part: str or None (used only if >2 letters and not Swiss short prefix)
        """
        location_text = str(location_text).strip()
        match = re.match(r"^(\d{4})\s*(.*)", location_text)
        if match:
            postal_code = match.group(1)
            city_part = match.group(2).strip() or None
            if city_part and (len(city_part) <= 2 or city_part.lower() in self.SWISS_SHORT_CITY_PREFIXES):
                city_part = None
            return postal_code, city_part
        return None, location_text

    def get_country_from_nominatim(self, postal_code, city_part, fallback_query):
        """Query Nominatim restricted to Switzerland and return country + resolved city."""
        cache_key = fallback_query
        if cache_key in self.cache:
            return self.cache[cache_key]

        params = {"format": "json", "addressdetails": 1, "limit": 1, "country": "Switzerland"}
        if postal_code:
            params["postalcode"] = postal_code
        if city_part:
            params["city"] = city_part

        try:
            r = requests.get("https://nominatim.openstreetmap.org/search", params=params,
                             headers={"User-Agent": "SwissLocationCleaner"})
            r.raise_for_status()
            results = r.json()
            if results:
                address = results[0].get("address", {})
                country = address.get("country")
                country_code = address.get("country_code")
                # get city, fallback to town or village
                city = address.get("city") or address.get("town") or address.get("village")
            else:
                country, country_code, city = None, None, None
        except Exception:
            country, country_code, city = None, None, None

        self.cache[cache_key] = (country, country_code, city)
        return country, country_code, city

    def clean(self, df, location_column="Location"):
        """Process the DataFrame and return cleaned version with Country + ResolvedCity info."""
        df = df.copy()  # <- important: ensures no chained assignment warnings
        
        countries = []
        cities = []
        for idx, loc in enumerate(df[location_column], 1):
            postal_code, city_part = self.clean_query(loc)
            country, country_code, resolved_city = self.get_country_from_nominatim(
                postal_code, city_part, fallback_query=loc
            )
            countries.append((country, country_code))
            cities.append(resolved_city)

            if idx % self.save_every == 0:
                print(f"Saving cache after {idx} rows...")
                self.save_cache()
                time.sleep(self.pause)

        self.save_cache()
        df["Country"], df["CountryCode"] = zip(*countries)
        df["ResolvedCity"] = cities
        return df
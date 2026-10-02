import csv
import time
from pathlib import Path
import sys

from selenium import webdriver
import json
import pandas as pd
from datetime import datetime
import re

import MisGrosi
from ZipfelZapf import ZipfelZapf
from RockMyBaby import RockMyBaby
from TagesmutterVerein import TagesmutterVerein
import GreatAuPair
import Babysits
import Platform24
import Care_com

src_root = Path(__file__).resolve().parents[2]
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from shared.paths import scraper_runs_dir

class Scraper:
    def __init__(self, platform, filename, plz_counter=0, profile_counter=0):
        self.platform = platform
        self.profile_counter = profile_counter
        self.filename = filename
        self.plz_counter = plz_counter
        self.logger = platform.logger
        
        self.__setup()

    def __setup(self):
        self.__open_browser()
        # Only open new file if PLZ counter == 0 as this should trigger a fresh start. A PLZ counter > 0 indicates that we want to add to the existing CSV file.
        if self.plz_counter == 0:
            self.__open_new_file()
    
    def __open_browser(self):
        """
        Opens a new automated browser window with all tell-tales of automated browser disabled
        """
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        if self.platform.get_name().name != "BABYSITS" and self.platform.get_name().name != "TAGESMUTTERVEREIN" and self.platform.get_name().name != "GREATAUPAIR" and self.platform.get_name().name != "BABYSITTING24" and self.platform.get_name().name != "SENIORSERVICE24" and self.platform.get_name().name != "CARE_COM" and self.platform.get_name().name != "MISGROSI":
            options.add_argument("--headless=new")

        # remove all signs of this being an automated browser
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # open the browser with the new options
        self.driver = webdriver.Chrome(options=options)

    def __transfer_session(self, headless_driver):
        headless_driver.get(self.driver.current_url)
        # Transfer cookies
        for cookie in self.driver.get_cookies():
            headless_driver.add_cookie(cookie)
        # Transfer local storage
        local_storage = self.driver.execute_script("return window.localStorage;")
        for key, value in local_storage.items():
            headless_driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")

    def __switch_to_headless(self):
        self.logger.debug("Switching to headless mode...")
        # Start headless browser
        headless_options = webdriver.ChromeOptions()
        headless_options.add_argument("--headless=new")
        headless_driver = webdriver.Chrome(options=headless_options)
        # Transfer session data to headless browser
        self.__transfer_session(headless_driver)
        # Close the normal browser
        self.driver.quit()
        self.driver = headless_driver
        self.logger.debug("Switched to headless mode.")

    def __open_new_file(self):
        Path(self.filename).parent.mkdir(parents=True, exist_ok=True)
        with open(self.filename,'w') as fd:
            writer = csv.writer(fd)
            writer.writerow(self.platform.attributes)

    def get_scraper_results_filename(self, chunk=None):
        filename = datetime.today().strftime('%Y-%m-%d') + "_scraper_results" + (("_chunk-" + str(chunk)) if chunk != None else "") + ".json"
        return str(scraper_runs_dir() / filename)

    def get_scraper_run_data(self, chunk):
        filename = self.get_scraper_results_filename(chunk)
        try:
            with open(filename, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        return data
    
    def write_results_to_json(self, success, chunk):
        data = self.get_scraper_run_data(chunk)

        data[self.platform.get_name().value + "_" + self.platform.get_type().value] = {
            "plz_count": self.plz_counter,
            "profile_count": self.profile_counter,
            "success": success
        }

        results_path = Path(self.get_scraper_results_filename(chunk))
        results_path.parent.mkdir(parents=True, exist_ok=True)
        with results_path.open('w') as file:
            json.dump(data, file, indent=4)

    def preload_plz_profile_counter(self, chunk=None):
        data = self.get_scraper_run_data(chunk)
        key = self.platform.get_name().value + "_" + self.platform.get_type().value
        self.logger.debug("Attempting to preload with the following data:")
        self.logger.debug(f"chunk: {chunk}")
        self.logger.debug(f"filename: {self.get_scraper_results_filename(chunk)}")
        self.logger.debug(f"data: {data}")
        if key in data:
            self.logger.info(f"Found previous run data for {self.platform.get_name().value} {self.platform.get_type().value}, preloading")
            self.plz_counter = data[key]["plz_count"]
            self.plz_counter = self.plz_counter
            self.profile_counter = data[key]["profile_count"]
            self.logger.info("Preloading completed")
        else:
            self.logger.info(f"No previous run data found for {self.platform.get_name().value} {self.platform.get_type().value}, scraping from scratch")

    def get_plz_counter(self):
        return self.plz_counter
    
    def get_profile_counter(self):
        return self.profile_counter
    
    def teardown(self):
        self.driver.quit()

    def login(self):
        self.platform.login(self.driver)

    def get_plz_list(self, chunk=None, plz_list=None):
        if plz_list is not None:
            self.logger.info("Using override PLZ list")
            return plz_list

        plz_dir = Path(__file__).resolve().parents[1] / "resources" / "postal_codes"
        if chunk != None and isinstance(chunk, int):
            self.logger.info(f"Using chunk {chunk} for PLZ list")
            plz_data = pd.read_csv(plz_dir / "split_population_data.csv", delimiter=",")
            plz_list = plz_data[plz_data["chunk"] == chunk]["PLZ"].tolist()
        else:
            self.logger.info("Using entire PLZ list")
            plz_data = pd.read_csv(plz_dir / "population_by_plz.csv", delimiter=",")
            plz_list = list(set(plz_data["PLZ"]))
        return plz_list
    
    def loop_through_profiles(self):
        # Iterate through search results
        more_profiles_available = True
        while more_profiles_available:
            profiles = self.platform.find_profiles(self.driver)
            with open(self.filename,'a') as fd:
                writer = csv.writer(fd)
                for profile in profiles:
                    try:
                        attributes = self.platform.get_profile_data(profile, self.driver)
                        if len(attributes) > 0:
                            writer.writerow(attributes)
                            self.profile_counter += 1
                            self.logger.info(f"attributes: {attributes}")
                            self.logger.info(f"Number of scraped profiles: {self.profile_counter}")
                    except Exception as e:
                        self.logger.exception(f"Error while scraping profile data of PLZ # {self.plz_counter} and profile # {self.profile_counter}")
            time.sleep(2)
            more_profiles_available = self.platform.load_more_profiles(self.driver)

    def run(self, chunk=None, plz_list=None):
        self.logger.info(f"Start scraping {self.platform.get_name()} {self.platform.get_type().value}")
        self.login()
        self.logger.info("Login successful")
        if self.platform.get_name().name == "BABYSITS" or self.platform.get_name().name == "CARE_COM":
            self.logger.info("Switching to headless mode for Babysits, Seniorservice24 or Care.com")
            self.__switch_to_headless()
        self.driver.get(self.platform.website)
        # Check if platform requires PLZ search
        # Careful: Whenever a PLZ search is required, you will likely get duplicates between PLZs, so make sure to dedup' your dataset after scraping
        if self.platform.requires_plz_search:
            plz_dir = Path(__file__).resolve().parents[1] / "resources" / "postal_codes"
            plz_list = self.get_plz_list(chunk, plz_list=plz_list)
            plz_names_list = pd.read_csv(plz_dir / "PLZ.csv", delimiter=";", comment='#')
            # Only iterate over PLZ's we haven't scraped
            plz_iterate = plz_list[self.plz_counter:]
            first_plz_index = self.plz_counter
            # Search for PLZ
            for plz in plz_iterate:
                if self.platform.requires_plz_name:
                    plz_names = plz_names_list[plz_names_list["PLZ"] == plz]["Ortschaftsname"]
                    plz_names = [re.sub(r'[0-9]+', '', name).strip() for name in plz_names]
                    plz_names = list(set(plz_names))
                    for plz_name in plz_names:
                        self.logger.info(f'Search PLZ # {str(self.plz_counter)}: {str(plz)}, {plz_name}')
                        if self.platform.navigate_to_plz(self.driver, plz, plz_name):
                            if self.plz_counter == first_plz_index and self.platform.requires_distance_sorting:
                                self.platform.sort_by_distance(self.driver)
                            self.loop_through_profiles()
                        else:
                            # Write PLZ to csv to remember which PLZs failed
                            with open("../../failed_plz/" + datetime.today().strftime('%Y-%m-%d') + "_failed_plz" + (("_chunk-" + str(chunk)) if chunk != None else "") + ".csv", 'a') as fd:
                                writer = csv.writer(fd)
                                writer.writerow([plz, plz_name])
                else:
                    self.logger.info(f'Search PLZ # {str(self.plz_counter)}: {str(plz)}')
                    # Added the if for Babysits.ch
                    if self.platform.navigate_to_plz(self.driver, plz):
                        if self.plz_counter == first_plz_index and self.platform.requires_distance_sorting:
                            self.platform.sort_by_distance(self.driver)
                        self.loop_through_profiles()
                    else:
                        # Write PLZ to csv to remember which PLZs failed
                        with open("../../failed_plz/" + datetime.today().strftime('%Y-%m-%d') + "_failed_plz" + (("_chunk-" + str(chunk)) if chunk != None else "") + ".csv", 'a') as fd:
                            writer = csv.writer(fd)
                            writer.writerow([plz])
                self.plz_counter += 1
        else:
            self.loop_through_profiles()
        self.teardown()
        self.logger.info(f"Finished scraping {self.platform.get_name()} {self.platform.get_type().value}")
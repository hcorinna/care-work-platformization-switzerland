from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Platforms import Platforms
from shared.PlatformNames import PlatformNames
from shared.PlatformType import PlatformType

import time

class TagesmutterVerein(Platforms):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.name = PlatformNames.TAGESMUTTERVEREIN
        self.website = "https://www.xn--tagesmutter-verein-zrich-ftc.ch/"
        self.type = PlatformType.WORKER
        self.attributes = ["Name", "Location", "Description"]

    def load_more_profiles(self, driver):
        """
        No dynamic loading is required as all profiles are visible on the page.
        """
        return False

    def find_profiles(self, driver):
        """
        Wait for the table rows to load and return them as profiles.
        """
        try:
            time.sleep(10)
            iframe = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "nKphmK")))
            driver.switch_to.frame(iframe)
            self.logger.info("Switched to iframe")
            time.sleep(20)
            last_profile = None
            WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "card-body")))
            profiles = driver.find_elements(By.CLASS_NAME, "card-body")
            scroll_to = profiles[-1]
            while last_profile != scroll_to:
                driver.execute_script("arguments[0].scrollIntoView(true);", scroll_to)
                last_profile = scroll_to
                WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "card-body")))
                profiles = driver.find_elements(By.CLASS_NAME, "card-body")
                scroll_to = profiles[-1]
            
            # Now find the profiles inside the iframe
            profiles = driver.find_elements(By.CLASS_NAME, "card-body")
            self.logger.info(f"Found {len(profiles)} profiles.")
            return profiles
        except Exception as e:
            self.logger.exception("Error finding profiles")
            return []

    def get_profile_data(self, profile, driver):
        """
        Extract name, location, and description from a single profile element.
        """
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", profile)
            time.sleep(1)
            # Wait for the elements to be present in the profile
            WebDriverWait(driver, 10).until(
                lambda p: p.find_element(By.CLASS_NAME, "card-title") and p.find_elements(By.TAG_NAME, "div")
            )
            name_location = profile.find_element(By.CLASS_NAME, "card-title").text
            description = ""

            self.logger.debug('name_location', name_location)

            # Ensure rows and columns exist before accessing
            description_rows = profile.find_elements(By.CLASS_NAME, "row")
            description_columns = []
            if len(description_rows) > 1:
                description_columns = description_rows[1].find_elements(By.TAG_NAME, "div")
            elif len(description_rows) == 1:
                description_columns = description_rows[0].find_elements(By.TAG_NAME, "div")
            if len(description_columns) > 1:
                description = description_columns[1].text

            # Assume name and location are separated by a comma (e.g., "Name, Location")
            if "," in name_location:
                name, location = name_location.split(", ", 1)
            else:
                name, location = name_location, ""
            return [name.strip(), location.strip(), description.strip()]
        except Exception as e:
            self.logger.exception("Error extracting profile data")
            return []
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Platforms import Platforms
from shared.PlatformNames import PlatformNames
from shared.PlatformType import PlatformType

class RockMyBaby(Platforms):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.name = PlatformNames.ROCKMYBABY
        self.loginpage = "https://www.rockmybaby.ch/users/login"
        self.website = "https://www.rockmybaby.ch/nannyrequests"
        self.type = PlatformType.JOB
        self.attributes = ["Location", "Days/Hours", "Job Type", "Live In", "Wages", "Start Date", "URL"]

    def load_more_profiles(self, driver):
        """
        RockMyBaby does not have a 'Load More' button or pagination for jobs.
        Simply return False as there are no additional profiles to load.
        """
        return False

    def find_profiles(self, driver):
        """
        Wait for the table rows to load and return them as profiles.
        """
        try:
            X_seconds = 20
            wait = WebDriverWait(driver, timeout = X_seconds)
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "old-tr")))

            rows = driver.find_elements(By.CLASS_NAME, "new-tr")
            rows.extend(driver.find_elements(By.CLASS_NAME, "old-tr"))
            return rows
        except Exception as e:
            self.logger.exception("Error finding profiles")
            return []

    def get_profile_data(self, profile, driver):
        """
        Extract data for a single row in the table.
        """
        try:
            cells = profile.find_elements(By.TAG_NAME, "td")
            url = profile.find_element(By.CSS_SELECTOR, "div.content-td > a").get_attribute("href")
            if len(cells) == 6:  # Ensure there are 6 columns
                data = [cell.text.strip() for cell in cells]
                cleaned_data = data[1].split('\n')
                cleaned_data.extend(data[2:])
                cleaned_data.append(url)
                self.logger.debug('locdays', cleaned_data)
                return cleaned_data
            else:
                self.logger.error("Unexpected number of columns in row:", len(cells))
                return []
        except Exception as e:
            self.logger.exception("Error extracting profile data")
            return []
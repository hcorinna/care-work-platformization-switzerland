from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Platforms import Platforms
from shared.PlatformNames import PlatformNames
from shared.PlatformType import PlatformType

class ZipfelZapf(Platforms):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.name = PlatformNames.ZIPFELZAPF
        self.loginpage = "https://www.zipfelzapf.ch/einloggen"
        self.website = "https://zipfelzapf.ch/home"
        self.type = PlatformType.JOB
        self.attributes = ['Date', 'Location', 'Days', 'Position', 'Frequency', 'Salary', 'StartDate', 'URL']

    def load_more_profiles(self, driver):
        """
        Handle loading more profiles if a "Load More" button exists in the future.
        Currently returns False since there's no such feature.
        """
        return False

    def find_profiles(self, driver):
        """
        Locate all profile rows on the current page.
        """
        try:
            # Wait until the table rows are loaded
            X_seconds = 20
            wait = WebDriverWait(driver, timeout = X_seconds)
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "tbody tr")))

            # Find rows explicitly, excluding the last row
            job_table = driver.find_element(By.CLASS_NAME, "table-area")
            jobs = job_table.find_elements(By.CSS_SELECTOR, "tbody tr")
            jobs.pop()
            return jobs
        except Exception as e:
            self.logger.exception("Error finding profiles")
            return []

    def get_profile_data(self, profile, driver):
        """
        Extract relevant job details from a single profile row.
        """
        try:
            # Attempt to find all text elements in the row
            cells = profile.find_elements(By.TAG_NAME, 'td')
            url = profile.find_element(By.CSS_SELECTOR, 'td > a').get_attribute('href')
            if len(cells) == 6:  # Ensure there are 6 columns
                data = [cell.text.strip() for cell in cells]
                date = data[0].replace("NEW", "").strip()
                cleaned_data = [date]
                location_days = data[1].split('\n')
                cleaned_data.extend(location_days)
                cleaned_data.extend(data[2:])
                cleaned_data.append(url)
                self.logger.debug(cleaned_data)
                return cleaned_data
            else:
                self.logger.error("Unexpected number of columns in row:", len(cells))
                return []
        except Exception as e:
            self.logger.exception("Error extracting profile data")
            return []
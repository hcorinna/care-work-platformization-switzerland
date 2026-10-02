from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Platforms import Platforms
from shared.PlatformNames import PlatformNames
from shared.PlatformType import PlatformType

class GreatAuPair(Platforms):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)
        self.name = PlatformNames.GREATAUPAIR
        self.loginpage = "https://www.greataupair.com/myaccount.cfm"
        self.website = ""

    def load_more_profiles(self, driver):
        """
        Handle loading more profiles if pagination exists.
        """
        try:
            results_pagination = driver.find_element(By.CLASS_NAME, "resultsPagination")
            next_page_number = self.pagination + 1
            next_page = results_pagination.find_elements(By.XPATH, "//td/a[@rel=" + str(next_page_number) + "]")
            if len(next_page) == 0:
                next_page = results_pagination.find_elements(By.CLASS_NAME, "nextResults")
            if not len(next_page) == 0:
                next_page[0].click()
                self.pagination += 1
                self.logger.info(f"Went to page {self.pagination}")
                return True
            return False
        except Exception as e:
            self.logger.exception("Error loading the next page")
            return False

    def find_profiles(self, driver):
        """
        Locate all job profile cards on the current page.
        """
        try:
            X_seconds = 20
            wait = WebDriverWait(driver, timeout=X_seconds)
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "searchResult")))
            profiles = driver.find_elements(By.CLASS_NAME, "searchResult")
            return profiles
        except Exception as e:
            self.logger.exception(f"Error finding profiles")
            return []

    def get_profile_data(self, profile, driver):
        """
        Extract relevant job details from a single profile card.
        """
        try:
            data = []
            # Extract text elements
            name_element = profile.find_element(By.CLASS_NAME, "name-txt")
            name = name_element.text.strip()
            url = name_element.get_attribute("href")
            job_title = profile.find_element(By.CLASS_NAME, "headline").text.strip()
            data.extend([name, job_title])

            info_row = profile.find_element(By.CLASS_NAME, "searchResultInfo")
            cells = info_row.find_elements(By.TAG_NAME, "p")
            if len(cells) == 4:
                details = [cell.text.strip() for cell in cells] # location, salary, hours, experience
                data.extend(details)
            
            info_bottom = profile.find_element(By.CLASS_NAME, "searchResultMetadata")
            cells_bottom = info_bottom.find_elements(By.TAG_NAME, "p")
            if len(cells_bottom) == 5:
                details_bottom = [cell.text.strip() for cell in cells_bottom[:-1]]
                data.extend(details_bottom[:2])
                cell = details_bottom[3]
                if ", " in cell:
                    job_type, accommodation = cell.split(", ")
                else:
                    job_type = accommodation = ""
                    self.logger.info(f"Unexpected format in job type and accommodation: {cell}")
                data.extend([job_type, accommodation])

            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(url)
            availability_block = driver.find_element(By.CLASS_NAME, "availability-block")
            last_logged_in_date = availability_block.find_element(By.XPATH, ".//dd[contains(text(), 'Last logged in')]").text
            member_since = availability_block.find_element(By.XPATH, ".//dd[contains(text(), 'Member since')]").text
            data.extend([last_logged_in_date, member_since])
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            
            data.append(url)

            return data
        except Exception as e:
            self.logger.exception("Error extracting profile data")
            return []

class Workers(GreatAuPair):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)
        self.website = "https://www.greataupair.com/fastfind.cfm/caretype/babysitter/countrylist/223/page/1/displayRows/45"
        self.type = PlatformType.WORKER
        self.attributes = [
            'Name', 'Job Title', 'Location', 'Age', 'Salary',
            'Experience', 'Last Logged In', 'Availability', 'Job Type',
            'Accommodation', 'Last Logged In (Date)', 'Member Since', 'URL'
        ]


class Jobs(GreatAuPair):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)
        self.website = "https://greataupair.com/fastfind.cfm/search/family/caretype/babysitter/countrylist/223/page/1/displayRows/45"
        self.type = PlatformType.JOB
        self.attributes = [
            'Name', 'Job Title', 'Location', 'Salary', 'Hours',
            'Experience Required', 'Last Logged In', 'Availability',
            'Job Type', 'Accommodation', 'Last Logged In (Date)', 'Member Since', 'URL'
        ]
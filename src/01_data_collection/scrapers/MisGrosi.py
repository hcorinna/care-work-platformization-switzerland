from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from abc import abstractmethod
import re

from Platforms import Platforms
from shared.PlatformNames import PlatformNames
from shared.PlatformType import PlatformType

class MisGrosi(Platforms):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.name = PlatformNames.MISGROSI
        self.loginpage = "https://www.misgrosi.ch/login/"
        self.load_button_class = ""
        self.profile_class = ""
        self._last_profile_count = 0
    
    def load_more_profiles(self, driver):
        # this line will only execute whenever the element was found (or after 20 seconds if it wasn't)
        load_button = driver.find_element(By.CLASS_NAME, self.load_button_class)
        if load_button:
            if load_button.is_displayed():
                load_button.click()
                self.pagination += 1
                return True
        return False
    
    def find_profiles(self, driver):
        X_seconds = 20
        wait = WebDriverWait(driver, timeout = X_seconds)
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, self.profile_class)))

        expected_count = self._last_profile_count + 1
        try:
            wait.until(
                lambda d: len(d.find_elements(By.CLASS_NAME, self.profile_class)) >= expected_count
            )
        except TimeoutException:
            pass

        profiles = driver.find_elements(By.CLASS_NAME, self.profile_class)
        if profiles:
            self._last_profile_count = len(profiles)
            starter = (self.pagination-1) * 6 # 6 profiles per page
            return profiles[starter:]
        
    def is_logged_in(self, driver):
        return False

    def fill_in_log_in(self, driver):
        username_field = driver.find_element(By.CLASS_NAME, "cleanlogin-field-username")
        username_field.clear()
        username_field.send_keys(self.username)

        password_field = driver.find_element(By.CLASS_NAME, "cleanlogin-field-password")
        password_field.send_keys(self.password)

        btn_submit = driver.find_element(By.XPATH, '//input[@value="Anmelden"]')

        if btn_submit:
            btn_submit.click()
        
    @abstractmethod
    def get_profile_data(self, profile, driver):
        pass

class Workers(MisGrosi):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.website = "https://www.misgrosi.ch/wunsch-grosi-suchen/listegrosis/"
        self.type = PlatformType.WORKER
        self.attributes = ["User", "Location", "Category", "Is active", "Salary", "URL"]
        self.load_button_class = 'load_more_resumes'
        self.profile_class = "resume"
        self._salary_pattern = re.compile(r"Stundenlohn:\s*([^\n]+)", re.IGNORECASE)

    def _extract_salary(self, driver):
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
        except NoSuchElementException:
            return ""
        match = self._salary_pattern.search(body_text)
        return match.group(1).strip() if match else ""

    def get_profile_data(self, profile, driver):
        name = profile.find_element(By.TAG_NAME, 'h3').text
        location = profile.find_element(By.CLASS_NAME, 'candidate-location-column').text
        category = profile.find_element(By.CLASS_NAME, 'resume-category').text
        url = profile.find_element(By.CSS_SELECTOR, 'li.resume > a').get_attribute('href')
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(url)
        active = driver.find_elements(By.XPATH, '//div[text()="Profil aktiv"]')
        is_active = True if len(active) == 1 else False
        salary = self._extract_salary(driver)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return [name, location, category, is_active, salary, url]
    
class Jobs(MisGrosi):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.website = "https://www.misgrosi.ch/betreuungsgesuche/"
        self.type = PlatformType.JOB
        self.attributes = ["Title", "User", "Location", "Category", "Date posted", "URL"]
        self.load_button_class = 'load_more_jobs'
        self.profile_class = "job_listing"
        self.requires_login = True

    def find_profiles(self, driver):
        profiles = super().find_profiles(driver)
        # Return all but the last item due to a bug with the MisGrosi job search
        return profiles[:-1]

    def get_profile_data(self, profile, driver):
        title = profile.find_element(By.TAG_NAME, 'h3').text
        try:
            user = profile.find_element(By.CLASS_NAME, 'company').text
        except NoSuchElementException:
            user = ""
        location = profile.find_element(By.CLASS_NAME, 'location').text
        category = profile.find_element(By.CLASS_NAME, 'job-type').text
        url = profile.find_element(By.CSS_SELECTOR, 'li.job_listing > a').get_attribute('href')
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(url)
        try:
            date_posted = driver.find_element(By.CLASS_NAME, "date-posted").text
        except NoSuchElementException:
            date_posted = ""
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return [title, user, location, category, date_posted, url]
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.relative_locator import locate_with
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException

import re

from abc import abstractmethod

from Platforms import Platforms
from shared.PlatformNames import PlatformNames
from shared.PlatformType import PlatformType

from datetime import date, datetime

import time

class Platform24(Platforms):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.current_plz = 0
        self.requires_login = True
        self.requires_plz_search = True
        self.requires_distance_sorting = True
        self.max_distance_still_zero = True
        self.requires_plz_name = True

    def is_logged_in(self, driver):
        return False

    def fill_in_log_in(self, driver):
        WebDriverWait(driver, timeout = 20).until(EC.presence_of_element_located((By.ID, "CybotCookiebotDialogBodyButtonDecline")))
        btn_cookies = driver.find_element(By.ID, "CybotCookiebotDialogBodyButtonDecline")
        btn_cookies.click()

        time.sleep(2)
        
        email_field = driver.find_element(By.ID, "user_login")
        email_field.clear()
        email_field.send_keys(self.username)

        time.sleep(2)

        password_field = driver.find_element(By.ID, "user_password")
        password_field.send_keys(self.password)

        time.sleep(2)

        btn_submit = driver.find_element(By.XPATH, '//input[@value="Login"]')

        if btn_submit:
            btn_submit.click()

    def sort_by_distance(self, driver):
        try:
            dropdown = driver.find_elements(By.CLASS_NAME, "dropdown")
            dropdown = dropdown[2]
            # distance_option = dropdown.find_element(By.XPATH, ".//ul/div[contains(@class, 'sort-by__option')]")
            ul_dropdown = dropdown.find_element(By.CLASS_NAME, "dropdown-menu")
            distance_option = ul_dropdown.find_element(By.XPATH, ".//span[text()='Entfernung']")
            if "sort-by__option--selected" not in distance_option.get_attribute("class"):
                dropdown.click() # and @data-value='distance'
                time.sleep(2)
                distance_option.click()
                time.sleep(3)
        except Exception as e:
                self.logger.exception(f"Error while trying to sort by distance for PLZ {self.current_plz}. This PLZ has to be rescraped.")

    def navigate_to_plz(self, driver, plz, name=""):
        self.max_distance_still_zero = True
        self.pagination = 1
        try:
            WebDriverWait(driver, timeout = 20).until(EC.presence_of_element_located((By.ID, "search_form_q_place")))
            input_plz = driver.find_element(By.ID, "search_form_q_place")
            input_plz.clear()
            search_string = f"{str(plz)}, {name}" if name != "" else str(plz)
            input_plz.send_keys(search_string)
            input_plz.send_keys(Keys.ENTER)

            self.current_plz = plz

            time.sleep(2)
            return True
        except Exception as e:
            self.logger.exception(f"Error while navigating to PLZ {plz}")
            return False

    def load_more_profiles(self, driver):
        try:
            if not self.max_distance_still_zero:
                return False
            results_pagination = driver.find_elements(By.CLASS_NAME, "page-btns")
            if not len(results_pagination) == 0:
                results_pagination = results_pagination[0]
                next_page_number = self.pagination + 1
                next_page = results_pagination.find_elements(By.XPATH, ".//a[contains(@class, 'pagination__btn') and text()=" + str(next_page_number) + "]")
                # next_page = results_pagination.find_elements(By.XPATH, ".//a[contains(@class, 'btn-next') and text()='Vorwärts')]")
                if not len(next_page) == 0:
                    next_link = next_page[0].get_attribute('href')
                    driver.get(next_link)
                    self.pagination += 1
                    return True
            return False
        except Exception as e:
            self.logger.exception("Error loading the next page")
            return False
    
    def find_profiles(self, driver):
        # let's wait up to 20 seconds
        X_seconds = 20
        wait = WebDriverWait(driver, timeout = X_seconds)

        try:
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "search-results")))
            profiles = driver.find_elements(By.CLASS_NAME, "search-card")
            return profiles
        except TimeoutException:
            # Log an error and return an empty list if search-results not found
            self.logger.error("'search-results' element not found within timeout. It could be that the PLZ does not exist.")
            driver.get(self.website)
            self.max_distance_still_zero = False
            return []
    
    def scrape_activity(self, url, driver):
        # Open profile in new tab and scrape more data
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(url)
        activities = driver.find_elements(By.CLASS_NAME, 'activities__text')
        last_online = member_since = reply_rate = ""
        if len(activities) >= 3:
            last_online = activities[0].text
            member_since = activities[1].text
            reply_rate = activities[2].text
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return last_online, member_since, reply_rate
    
    def get_location_and_distance(self, location):
        km_match = re.search(r"\(([\d.]+)\s+km\s+entfernt\)", location)
        distance = float(km_match.group(1)) if km_match else None
        zip_city_match = re.match(r"^(\d{4}\s+\w+)", location)
        clean_location = zip_city_match.group(1) if zip_city_match else location
        self.logger.info(f"Location: {location}, distance: {distance}, clean location: {clean_location}")
        return clean_location, distance
        
    @abstractmethod
    def get_profile_data(self, profile, driver):
        pass

class Babysitting24(Platform24):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)
        
        self.name = PlatformNames.BABYSITTING24
        self.loginpage = "https://babysitting24.ch/de/sign_in"
    
    @abstractmethod
    def get_profile_data(self, profile, driver):
        pass

class Babysitting24Workers(Babysitting24):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.website = "https://babysitting24.ch/de/providers/search"
        self.type = PlatformType.WORKER
        self.attributes = ["ID", "Name", "Location", "Experience", "Age", "Salary", "Number of reviews", "Last online", "Member since", "Reply rate", "URL", "Additionals"]

    def get_profile_data(self, profile, driver):
        id = profile.get_attribute("id")
        featured_fields = profile.find_elements(By.CSS_SELECTOR, 'span.profile__featured-field')
        fields = [field.text.strip() for field in featured_fields]
        fields = list(filter(None, fields))
        location = fields[0]
        clean_location, distance = self.get_location_and_distance(location)
        if distance != None and distance > 0:
            self.max_distance_still_zero = False
            self.logger.info(f"Skipping profile {id} because distance is greater than 0")
            return []
        experience = next((field for field in fields if "Jahre Erfahrung" in field), "")
        age = next((field for field in fields if re.match(r"^\d+\s+Jahre$", field)), "")
        filled_variables = sum(i != "" for i in [location, experience, age])
        additionals = ('; ').join(fields[filled_variables:]) if len(fields) > filled_variables else ""

        name = profile.find_element(By.TAG_NAME, 'h4').text
        salary = profile.find_elements(By.XPATH, ".//span[contains(text(), 'CHF ')]")
        salary = salary[0].text if len(salary) > 0 else ""
        stars_container = profile.find_elements(By.CLASS_NAME, "stars-container")
        if len(stars_container) == 1:
            number_of_reviews_locator = locate_with(By.TAG_NAME, "span").to_right_of(stars_container[0])
            number_of_reviews = driver.find_element(number_of_reviews_locator).text
            number_of_reviews = int(number_of_reviews.strip("()"))
        else:
            number_of_reviews = 0
        url = profile.find_element(By.CSS_SELECTOR, 'a.search-card__link').get_attribute('href')
        last_online, member_since, reply_rate = self.scrape_activity(url, driver)
        return [id, name, clean_location, experience, age, salary, number_of_reviews, last_online, member_since, reply_rate, url, additionals]
    
class Babysitting24Jobs(Babysitting24):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.website = "https://babysitting24.ch/de/jobs/search"
        self.type = PlatformType.JOB
        self.attributes = ["ID", "Title", "Location", "Type", "Last online", "Publishing date", "Member since", "Reply rate", "Starting date", "Care type", "Number of children", "Children's age", "Special care wishes", "Caregiver requirements", "Frequency", "URL", "Additionals"]

    def scrape_activity(self, url, driver):
        # Open profile in new tab and scrape more data
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(url)
        
        detail_data = {}
        
        # Original activity data extraction
        activities = driver.find_elements(By.CLASS_NAME, 'activities__text')
        if len(activities) >= 3:
            detail_data['last_online'] = activities[0].text
            detail_data['member_since'] = activities[1].text
            detail_data['reply_rate'] = activities[2].text
        else:
            detail_data['last_online'] = detail_data['member_since'] = detail_data['reply_rate'] = ""
        
        # Extract profile data using XPath
        profile_fields = {
            'starting_date': "//div[contains(text(), 'Gewünschter Arbeitsbeginn')]/following-sibling::div",
            'care_type': "//div[contains(@class, 'profile-values-group-default-field__label') and contains(text(), 'Art der gesuchten Betreuung')]/following-sibling::div",
            'number_of_children': "//div[contains(@class, 'profile-values-group-default-field__label') and contains(text(), 'Anzahl zu betreuender Kinder')]/following-sibling::div",
            'child_age': "//div[contains(@class, 'profile-values-group-default-field__label') and contains(text(), 'Kindesalter')]/following-sibling::div",
            'special_care_wishes': "//div[contains(@class, 'profile-values-group-default-field__label') and contains(text(), 'Spezielle Betreuungswünsche')]/following-sibling::div",
            'caregiver_requirements': "//div[contains(@class, 'profile-values-group-default-field__label') and contains(text(), 'Anforderungen an die Betreuungsperson')]/following-sibling::div",
            'frequency': "//div[contains(@class, 'profile-values-group-default-field__label') and contains(text(), 'Häufigkeit')]/following-sibling::div"
        }
        
        for field_name, xpath in profile_fields.items():
            try:
                detail_data[field_name] = driver.find_element(By.XPATH, xpath).text.strip()
            except:
                detail_data[field_name] = ""
        
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        
        return detail_data

    def get_profile_data(self, profile, driver):
        featured_fields = profile.find_elements(By.CSS_SELECTOR, 'span.profile__featured-field')
        fields = [field.text.strip() for field in featured_fields]
        fields = list(filter(None, fields))
        location = fields[0]
        clean_location, distance = self.get_location_and_distance(location)
        if distance != None and distance > 0:
            self.max_distance_still_zero = False
            self.logger.info("Skipping profile because distance is greater than 0")
            return []
        job_type = fields[1] if len(fields) >= 2 else ""
        additionals = ('; ').join(fields[2:]) if len(fields) > 2 else ""

        id = profile.get_attribute("id")
        title = profile.find_element(By.TAG_NAME, 'h4').text
        try:
            publishing_date = profile.find_element(By.XPATH, ".//p[contains(text(), 'Veröffentlicht am:')]").text.split(": ")[1]
        except NoSuchElementException:
            publishing_date = None
            self.logger.warning(f"Publishing date not found for profile {id}")
        url = profile.find_element(By.CSS_SELECTOR, 'a.search-card__link').get_attribute('href')
        detail_data = self.scrape_activity(url, driver)
        return [id, title, clean_location, job_type, detail_data['last_online'], publishing_date, detail_data['member_since'], detail_data['reply_rate'], detail_data['starting_date'], detail_data['care_type'], detail_data['number_of_children'], detail_data['child_age'], detail_data['special_care_wishes'], detail_data['caregiver_requirements'], detail_data['frequency'], url, additionals]

class Seniorservice24(Platform24):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.name = PlatformNames.SENIORSERVICE24
        self.loginpage = "https://seniorservice24.ch/de/sign_in"

class Seniorservice24Workers(Seniorservice24):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.website = "https://seniorservice24.ch/de/providers/search"
        self.type = PlatformType.WORKER
        self.attributes = ["ID", "Name", "Location", "Experience", "Age", "Part/full time", "Salary", "Number of reviews", "Last online", "Member since", "Reply rate", "URL", "Additionals"]

    def get_profile_data(self, profile, driver):
        id = profile.get_attribute("id")
        featured_fields = profile.find_elements(By.CSS_SELECTOR, 'span.profile__featured-field')
        fields = [field.text.strip() for field in featured_fields]
        fields = list(filter(None, fields))
        location = fields[0]
        clean_location, distance = self.get_location_and_distance(location)
        if distance != None and distance > 0:
            self.max_distance_still_zero = False
            self.logger.info(f"Skipping profile {id} because distance is greater than 0")
            return []
        experience = next((field for field in fields if "Jahre Erfahrung" in field), "")
        age = next((field for field in fields if re.match(r"^\d+\s+Jahre$", field)), "")
        part_full_time = next((field for field in fields if "zeit" in field), "")
        filled_variables = sum(i != "" for i in [location, experience, age, part_full_time])
        additionals = ('; ').join(fields[filled_variables:]) if len(fields) > filled_variables else ""

        name = profile.find_element(By.TAG_NAME, 'h4').text
        salary = profile.find_elements(By.XPATH, ".//span[contains(text(), 'CHF ')]")
        salary = salary[0].text if len(salary) > 0 else ""
        stars_container = profile.find_elements(By.CLASS_NAME, "stars-container")
        if len(stars_container) == 1:
            number_of_reviews_locator = locate_with(By.TAG_NAME, "span").to_right_of(stars_container[0])
            number_of_reviews = driver.find_element(number_of_reviews_locator).text
            number_of_reviews = int(number_of_reviews.strip("()"))
        else:
            number_of_reviews = 0
        url = profile.find_element(By.CSS_SELECTOR, 'a.search-card__link').get_attribute('href')
        last_online, member_since, reply_rate = self.scrape_activity(url, driver)
        return [id, name, clean_location, experience, age, part_full_time, salary, number_of_reviews, last_online, member_since, reply_rate, url, additionals]
    
class Seniorservice24Jobs(Seniorservice24):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.website = "https://seniorservice24.ch/de/jobs/search"
        self.type = PlatformType.JOB
        self.attributes = ["ID", "Title", "Location", "Last online", "Publishing date", "Member since", "Reply rate", "Starting date", "Tasks", "Frequency", "URL", "Additionals"]

    def scrape_activity(self, url, driver):
        # Open profile in new tab and scrape more data
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(url)
        
        detail_data = {}
        
        # Original activity data extraction
        activities = driver.find_elements(By.CLASS_NAME, 'activities__text')
        if len(activities) >= 3:
            detail_data['last_online'] = activities[0].text
            detail_data['member_since'] = activities[1].text
            detail_data['reply_rate'] = activities[2].text
        else:
            detail_data['last_online'] = detail_data['member_since'] = detail_data['reply_rate'] = ""
        
        # Extract profile data using XPath
        profile_fields = {
            'starting_date': "//div[contains(text(), 'Gewünschter Arbeitsbeginn')]/following-sibling::div",
            'tasks': "//div[contains(@class, 'profile-values-group-default-field__label') and contains(text(), 'Aufgaben')]/following-sibling::div",
            'frequency': "//div[contains(@class, 'profile-values-group-default-field__label') and contains(text(), 'Häufigkeit')]/following-sibling::div"
        }
        
        for field_name, xpath in profile_fields.items():
            try:
                detail_data[field_name] = driver.find_element(By.XPATH, xpath).text.strip()
            except:
                detail_data[field_name] = ""
        
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        
        return detail_data
    
    def get_profile_data(self, profile, driver):
        featured_fields = profile.find_elements(By.CSS_SELECTOR, 'span.profile__featured-field')
        fields = [field.text.strip() for field in featured_fields]
        fields = list(filter(None, fields))
        location = fields[0]
        clean_location, distance = self.get_location_and_distance(location)
        if distance != None and distance > 0:
            self.max_distance_still_zero = False
            self.logger.info("Skipping profile because distance is greater than 0")
            return []
        additionals = ('; ').join(fields[1:]) if len(fields) > 1 else ""

        id = profile.get_attribute("id")
        title = profile.find_element(By.TAG_NAME, 'h4').text
        try:
            publishing_date = profile.find_element(By.XPATH, ".//p[contains(text(), 'Veröffentlicht am')]").text
        except NoSuchElementException:
            publishing_date = ""
        url = profile.find_element(By.CSS_SELECTOR, 'a.search-card__link').get_attribute('href')
        detail_data = self.scrape_activity(url, driver)
        return [id, title, clean_location, detail_data['last_online'], publishing_date, detail_data['member_since'], detail_data['reply_rate'], detail_data['starting_date'], detail_data['tasks'], detail_data['frequency'], url, additionals]
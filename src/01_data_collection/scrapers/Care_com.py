from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException

from abc import abstractmethod

import re
from datetime import date

from Platforms import Platforms
from shared.PlatformNames import PlatformNames
from shared.PlatformType import PlatformType
from shared.PlatformCategory import PlatformCategory

import time

class Care_com(Platforms):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.name = PlatformNames.CARE_COM
        self.loginpage = "https://www.care.com/de-ch/login"
        self.current_plz = 0
        self.requires_login = True
        self.requires_plz_search = True
        self.requires_distance_sorting = True
        self.requires_plz_name = True
        self.snippet_name = ""

    def is_logged_in(self, driver):
        return False
    
    def fill_in_log_in(self, driver):
        WebDriverWait(driver, timeout = 20).until(EC.presence_of_element_located((By.ID, "onetrust-reject-all-handler")))
        btn_cookies = driver.find_element(By.ID, "onetrust-reject-all-handler")
        btn_cookies.click()

        time.sleep(2)
        
        email_field = driver.find_element(By.ID, "j_username")
        email_field.clear()
        email_field.send_keys(self.username)

        time.sleep(2)

        password_field = driver.find_element(By.ID, "j_password")
        password_field.send_keys(self.password)

        time.sleep(2)

        btn_submit = driver.find_element(By.XPATH, '//button[@name="login"]')

        if btn_submit:
            btn_submit.click()

        time.sleep(3)

        x = input("Waiting for solving of captcha. Enter OK when done.")

        if x == 'OK':
            pass
        else:
            print("You must solve the captcha to proceed.")

    @abstractmethod
    def get_profile_data(self, profile, driver):
        pass

class Workers(Care_com):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.type = PlatformType.WORKER
        self.attributes = ["Scraping date", "Name", "Location", "Number of reviews", "Number of gigs", "Salary", "Experience", "Age", "Last online", "Reply rate", "URL"]
        self.snippet_name = "providerSnippet"

    def sort_by_distance(self, driver):
        distance_dropdown = driver.find_element(By.ID, 'radius')
        distance_dropdown = Select(distance_dropdown)
        distance_dropdown.select_by_value('5')
        
        sort_by_distance_element = driver.find_element(By.XPATH, '//input[@name="distance"]')
        sort_by_distance_element.click()

    def navigate_to_plz(self, driver, plz, name=""):
        self.pagination = 1
        try:
            input_plz = WebDriverWait(driver, timeout=20).until(
                EC.element_to_be_clickable((By.ID, "searchText"))
            )
            time.sleep(3)
            input_plz.click()
            input_plz.clear()
            time.sleep(3)
            input_plz = WebDriverWait(driver, timeout=20).until(
                EC.element_to_be_clickable((By.ID, "searchText"))
            )
            search_string = f"{str(plz)} {name}" if name != "" else str(plz)
            input_plz.send_keys(search_string)
            time.sleep(1)
            input_plz.send_keys(Keys.ENTER)

            self.current_plz = plz

            time.sleep(2)

            return True
        except Exception as e:
            self.logger.exception(f"Error while navigating to PLZ {plz}")
            return False
    
    def load_more_profiles(self, driver):
        try:
            next_page = driver.find_elements(By.CLASS_NAME, "nextLink")
            if not len(next_page) == 0:
                next_page = next_page[0]
                next_page.click()
                self.pagination += 1
                return True
            return False
        except Exception as e:
            self.logger.exception("Error loading the next page")
            return False
    
    def find_profiles(self, driver):
        WebDriverWait(driver, timeout = 20).until(EC.visibility_of_element_located((By.CLASS_NAME, "grid7")))
        profiles = driver.find_elements(By.CLASS_NAME, self.snippet_name)
        
        return profiles

    def get_profile_data(self, profile, driver):
        name = profile.find_element(By.CLASS_NAME, "name").text
        location = profile.find_element(By.CLASS_NAME, "hidden-xs").text
        stars = profile.find_elements(By.CLASS_NAME, "stars-text")
        number_of_reviews = stars[0].text if len(stars) > 0 else 0
        hire_counts = profile.find_elements(By.CLASS_NAME, "hireCount")
        number_of_gigs = hire_counts[0].text if len(hire_counts) > 0 else 0
        row_containers = profile.find_element(By.CLASS_NAME, "info-row-bottom")
        containers = row_containers.find_elements(By.CLASS_NAME, "badge-container")
        salary = containers[0].text
        experience_badge = profile.find_elements(By.CLASS_NAME, "badge-experience")
        experience = experience_badge[0].text if len(experience_badge) > 0 else ""
        try:
            age = profile.find_element(By.CLASS_NAME, "badge-age").text
        except NoSuchElementException:
            self.logger.warning("Age not found")
            age = ""
        url = profile.find_element(By.CLASS_NAME, "profileLink").get_attribute("href")
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(url)
        time.sleep(2)
        last_online = reply_rate = ""
        try:
            last_online = driver.find_element(By.CSS_SELECTOR, "span.jss22").text.strip()
        except NoSuchElementException:
            self.logger.warning("Last online not found")
        try:
            reply_element = driver.find_element(By.XPATH, "//span[contains(text(), '%')]/following-sibling::span[contains(text(), 'Antwort')]/../span[1]")
            value = reply_element.text.strip()
            rate_match = re.search(r'(\d+)%', value)
            reply_rate = int(rate_match.group(1)) if rate_match else value
        except NoSuchElementException:
            self.logger.warning("Reply rate not found")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        scraping_date = date.today()
        return [scraping_date.strftime('%Y-%m-%d'), name, location, number_of_reviews, number_of_gigs, salary, experience, age, last_online, reply_rate, url]

class BabysittingWorkers(Workers):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.website = "https://www.care.com/de-ch/profile/kinderbetreuung"
        self.category = PlatformCategory.BABYSITTING
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.relative_locator import locate_with

import pandas as pd
import re

from selenium import webdriver

from datetime import date, datetime

from abc import ABC
import logging
import csv
import json

from shared.PlatformNames import PlatformNames
from shared.PlatformType import PlatformType

import time

class BabysitsDetails(ABC):
    def __init__(self, profile_range_start=0, profile_range_end=1):
        self.name = PlatformNames.BABYSITS
        self.type = None
        self.loginpage = "https://www.babysits.ch/einloggen/"
        self.profile_range_start = profile_range_start
        self.profile_range_end = profile_range_end
        self.clean_file_path = ""
        self.today = datetime.now().strftime("%Y-%m-%d")

        self.initialise_platform_credentials()

    def __setup(self):
        self.__open_browser()
        self.__open_new_file()

    def __teardown(self):
        self.driver.quit()

    def __open_new_file(self):
        with open(self.__get_filename_in_folder(),'w') as fd:
            writer = csv.writer(fd)
            writer.writerow(self.attributes)

    def __get_filename(self):
        return f"f_{self.today}_{self.name.value}_{self.type.value}_{self.profile_range_start}-{self.profile_range_end}"

    def __get_filename_in_folder(self):
        """
        Returns the filename for the scraped data
        """
        return f"../../../data/raw/2025-04-03/{self.name.value.capitalize()} {self.type.value.capitalize()}s/{self.__get_filename()}.csv"
    
    def __open_browser(self):
        """
        Opens a new automated browser window with all tell-tales of automated browser disabled
        """
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        # options.add_argument("--headless=new")  # Uncomment this line to run in headless mode

        # remove all signs of this being an automated browser
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # open the browser with the new options
        self.driver = webdriver.Chrome(options=options)

    def __switch_to_headless(self):
        # Start headless browser
        headless_options = webdriver.ChromeOptions()
        headless_options.add_argument("--headless=new")
        headless_driver = webdriver.Chrome(options=headless_options)
        # Transfer session data to headless browser
        self.__transfer_session(headless_driver)
        # Close the normal browser
        self.driver.quit()
        self.driver = headless_driver

    def __transfer_session(self, headless_driver):
        headless_driver.get(self.driver.current_url)
        # Transfer cookies
        for cookie in self.driver.get_cookies():
            headless_driver.add_cookie(cookie)
        # Transfer local storage
        local_storage = self.driver.execute_script("return window.localStorage;")
        for key, value in local_storage.items():
            headless_driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")

    def scrape(self):
        main_log = "../../../loggers/" + self.__get_filename() + '.log'
        logging.basicConfig(filename=main_log, level=logging.INFO, filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)
        self.logger = logger
        print("Starting Babysits Details Scraper, setting up...")
        self.__setup()
        print("Setup complete, opening Babysits login page...")
        self.log_in(self.driver)
        print("Logged in, switching to headless mode...")
        self.__switch_to_headless()
        print("Headless mode activated, scraping full profiles...")
        self.scrape_full_profiles()
        print("Scraping complete, closing browser and cleaning up...")
        self.__teardown()
        print("Finished")

    def initialise_platform_credentials(self):
        with open('../../../credentials.json', 'r') as file:
            credentials = json.load(file)
        platform_credentials = credentials[self.name.name]

        if "username" in platform_credentials:
            self.username = platform_credentials["username"]
        else:
            self.username = platform_credentials["email"]
        self.password = platform_credentials["password"]
        
    def log_in(self, driver):
        driver.get(self.loginpage)
        WebDriverWait(driver, timeout = 20).until(EC.presence_of_element_located((By.CLASS_NAME, "show-email-form")))
        
        btn_email_login = driver.find_element(By.CLASS_NAME, "show-email-form")
        btn_email_login.click()

        time.sleep(1)
        
        email_field = driver.find_element(By.ID, "continueEmail")
        email_field.send_keys(self.username)

        password_field = driver.find_element(By.ID, "loginPassword")
        password_field.send_keys(self.password)

        btn_continue = driver.find_element(By.CSS_SELECTOR, "button.continue")
        btn_submit = driver.find_element(By.XPATH, '//button[normalize-space()="Einloggen"]')

        if btn_continue:
            btn_continue.click()

        time.sleep(5)

        if btn_submit:
            btn_submit.click()

        x = input("Waiting for solving of captcha. Enter OK when done.")

        if x == 'OK':
            WebDriverWait(driver, timeout = 20).until(EC.presence_of_element_located((By.CLASS_NAME, "close-dialog")))
            driver.find_element(By.CLASS_NAME, "close-dialog").click()
        else:
            print("You must solve the captcha to proceed.")

    def scrape_full_profiles(self):
        user_df = pd.read_csv(self.clean_file_path)
        to_scrape_df = user_df.iloc[self.profile_range_start:self.profile_range_end]
        with open(self.__get_filename_in_folder(),'a') as fd:
            writer = csv.writer(fd)
            for index, row in to_scrape_df.iterrows():
                try:
                    # Open profile in new tab and scrape more data
                    self.driver.get(row['URL'])
                    time.sleep(2)
                    self.logger.info(f"Scraping profile {index + 1}: {row['URL']}")
                    attributes = self.scrape_babysits_details(self.driver, row['URL'], row['PLZ'], row['ID']) if 'PLZ' in to_scrape_df.columns else self.scrape_babysits_details(self.driver, row['URL'], -1, row['ID'])
                    writer.writerow(attributes)
                    self.logger.info(f"attributes: {attributes}")
                except Exception:
                    self.logger.exception(f"Error while scraping profile {index + 1}: {row['URL']}")

    def get_characteristics(self, driver):
        characteristics_div = driver.find_elements(By.XPATH, "//div[@class='summary mt-4']//div[@class='content']//div[@class='status']")
        if len(characteristics_div) != 0:
            characteristics_div = characteristics_div[0]
            characteristics = characteristics_div.find_elements(By.TAG_NAME, "li")
            characteristics = [charac.text.strip() for charac in characteristics]
        else:
            characteristics = []
        return characteristics
    
    def parse_summary(self, driver):
        summary = {
            'experience': "",
            'experience_age': "",
            'experience_special_needs': "",
            'supersitter': False,
            'ID': False,
            'first_aid': False,
            'babysitter_certificate': False,
            'sexual_offenses_record_extract': False,
            'criminal_record_extract': False,
            'other_certificates': [],
            'number_of_kids': None,
            'kids_ages': "",
            'kids_special_needs': "",
        }

        try:
            summary_elements = driver.find_elements(By.CSS_SELECTOR, "div.summary .summary-item")
            for el in summary_elements:
                try:
                    title = el.find_element(By.CSS_SELECTOR, ".title").text.strip()
                    content_div = el.find_element(By.CSS_SELECTOR, ".status")
                    
                    if title == "Erfahrung":
                        summary['experience'] = content_div.text.strip()
                    elif title == "Erfahrung mit dem Alter":
                        summary['experience_age'] = content_div.text.strip()
                    elif title == "Erfahrung mit Kindern mit besonderen Bedürfnissen":
                        summary['experience_special_needs'] = el.find_element(By.TAG_NAME, "ul").text.strip()
                    elif title.endswith("Supersitter"):
                        summary['supersitter'] = True
                    elif title == "Lichtbildausweis":
                        summary['ID'] = True
                    elif title == "Erste-Hilfe-Zertifikat":
                        summary['first_aid'] = True
                    elif title == "Babysitter Zertifikat":
                        summary['babysitter_certificate'] = True
                    elif title == "Certificado de Delitos de Naturaleza Sexual":
                        summary['sexual_offenses_record_extract'] = True
                    elif title == "Extraits du casier judiciaire" or title == "Strafregisterauszüge" or title == "Criminal records excerpts" or title == "Criminal Record Certificate - Model 2" or title == "Bulletin n°3 du Casier Judiciaire" or title == "Auszug aus dem Strafregister - Modell 2" or title=="Extrait de casier judiciaire – Modèle 2": 
                        summary['criminal_record_extract'] = True
                    elif title == "Anzahl der Kinder":
                        summary['number_of_kids'] = content_div.text.strip()
                    elif title == "Alter der Kinder":
                        summary['kids_ages'] = content_div.text.strip()
                    elif title == "Kinder mit besonderen Bedürfnissen":
                        summary['kids_special_needs'] = el.find_element(By.TAG_NAME, "ul").text.strip()
                    elif title == "Stundenlohn" or title == "Eigenschaften" or title == "Eigenschaften der Kinder":
                        continue
                    else:
                        self.logger.warning(f"Unknown summary title: {title}")
                        summary['other_certificates'].append(title)
                except NoSuchElementException:
                    continue
        except NoSuchElementException:
            self.logger.info("No summary found")
            return summary
        return summary
    
    def parse_credentials(self, driver):
        credentials = {
            'driver_license': "",
            'car': "",
            'has_kids': "",
            'smoker': "",
            'preferred_location': "",
            'languages_spoken': [],
            'favorite_count': 0,
            'highest_degree': "",
            'highest_degree_details': "",
            'certificates_children': "",
            'certificates_medical': "",
            'searching_for': "",
            'preferred_location': "",
        }

        try:
            credential_elements = driver.find_elements(By.CSS_SELECTOR, "div.credentials-list .credential")
            for cred in credential_elements:
                try:
                    title = cred.find_element(By.CSS_SELECTOR, ".title").text.strip()
                    content_div = cred.find_element(By.CSS_SELECTOR, ".text-end")
                    
                    if title == "Führerschein":
                        credentials['driver_license'] = content_div.text.strip().lower() == "ja"
                    elif title == "Auto":
                        credentials['car'] = content_div.text.strip().lower() == "ja"
                    elif title == "Hat Kinder":
                        credentials['has_kids'] = content_div.text.strip().lower() == "ja"
                    elif title == "Raucher":
                        credentials['smoker'] = content_div.text.strip().lower() == "ja"
                    elif title.startswith("Bevorzugter Ort"):
                        credentials['preferred_location'] = content_div.text.strip()
                    elif title.startswith("Sprachen"):
                        languages = content_div.find_elements(By.TAG_NAME, "li")
                        credentials['languages_spoken'] = [lang.text.strip() for lang in languages]
                    elif title == "Favorisiert":
                        match = re.search(r'\d+', content_div.text)
                        credentials['favorite_count'] = int(match.group()) if match else 0
                    elif title.startswith("Bildungsniveau"):
                        credentials['highest_degree'] = content_div.text.strip()
                    elif title.startswith("Ausbildungsdetails"):
                        credentials['highest_degree_details'] = content_div.text.strip()
                    elif title.startswith("Lehr- oder Kinderbetreuungszertifikate"):
                        credentials['certificates_children'] = content_div.text.strip()
                    elif title.startswith("Professionelle medizinische Zertifizierungen"):
                        credentials['certificates_medical'] = content_div.text.strip()
                    elif title == "Auf der Suche nach":
                        credentials['searching_for'] = content_div.text.strip().replace('\n', '|')
                    elif title == "Bevorzugter Ort fürs Babysitting":
                        credentials['preferred_location'] = content_div.text.strip()
                    else:
                        self.logger.warning(f"Unknown credential title: {title}")
                except NoSuchElementException:
                    continue
        except NoSuchElementException:
            self.logger.info("No credentials found")
            return credentials
        return credentials
    
    def parse_reviews(self, driver):
        reviews = []
        try:
            reviews_div = driver.find_element(By.ID, "reviews-block-ref")
            header = reviews_div.find_element(By.TAG_NAME, "h2").text.strip()
            num_reviews = int(header.split()[0])
            cards = reviews_div.find_elements(By.CLASS_NAME, "slider-item")
            for card in cards:
                review = {"author_name": "", "author_id": "", "date": "", "stars": None, "title": "", "text": ""}
                try:
                    review["author_name"] = card.find_element(By.CSS_SELECTOR, ".author").text.strip()
                    links = card.find_elements(By.CSS_SELECTOR, ".stretched-link")
                    review["author_id"] = links[0].get_attribute("href") if len(links) > 0 else ""
                    # stars_span = card.find_element(By.CSS_SELECTOR, ".stars").get_attribute("title")
                    stars_span = card.find_element(By.XPATH, "//span[contains(@title, 'Sterne')]").get_attribute("title")
                    match = re.search(r"\b(\d+)\s+(von|van)\b", stars_span)
                    if match:
                        number = match.group(1)
                        review["stars"] = number
                    else:
                        self.logger.exception(f"Error while parsing stars in reviews: {stars_span}")
                    date_div = card.find_elements(By.CLASS_NAME, "text-body-secondary")
                    if len(date_div) == 2:
                        date_div = date_div[1]
                    elif len(date_div) == 1:
                        date_div = date_div[0]
                    else:
                        date_div = card
                    review["date"] = date_div.find_element(By.CSS_SELECTOR, "small").text.strip()
                    review["text"] = card.find_element(By.CSS_SELECTOR, "p.mb-0").text.strip()
                    title = card.find_elements(By.CSS_SELECTOR, "h4.mb-2")
                    review["title"] = title[0].text.strip() if len(title) > 0 else ""
                    reviews.append(review)
                except NoSuchElementException:
                    self.logger.exception(f"Error while parsing review")
                    reviews.append(review)
                    continue
        except NoSuchElementException:
            self.logger.info("No reviews found")
            return reviews
        if len(reviews) != num_reviews:
            self.logger.warning(f"Number of reviews found ({len(reviews)}) does not match expected number ({num_reviews})")
        return reviews
    
    def parse_references(self, driver):
        references = []
        try:
            references_div = driver.find_element(By.ID, "references-wrapper")
            header = references_div.find_element(By.TAG_NAME, "h2").text.strip()
            num_references = int(header.split()[0])
            cards = references_div.find_elements(By.CLASS_NAME, "slider-item")
            for card in cards:
                reference = {"author_name": "", "author_id": "", "date": "", "relationship": "", "title": "", "text": ""}
                try:
                    reference["author_name"] = card.find_element(By.CSS_SELECTOR, ".author").text.strip()
                    links = card.find_elements(By.CSS_SELECTOR, ".stretched-link")
                    reference["author_id"] = links[0].get_attribute("href") if len(links) > 0 else ""
                    secondary_div = card.find_elements(By.CLASS_NAME, "text-body-secondary")
                    reference["relationship"] = secondary_div[0].text.strip()
                    reference["date"] = secondary_div[1].find_element(By.CSS_SELECTOR, "small").text.strip() if len(secondary_div) > 1 else card.find_element(By.CSS_SELECTOR, "small").text.strip()
                    reference["text"] = card.find_element(By.CSS_SELECTOR, "p.mb-0").text.strip()
                    title = card.find_elements(By.CSS_SELECTOR, "h4.mb-2")
                    reference["title"] = title[0].text.strip() if len(title) > 0 else ""
                    references.append(reference)
                except (NoSuchElementException, IndexError):
                    self.logger.warning(f"Error while parsing reference")
                    references.append(reference)
                    continue
        except NoSuchElementException:
            self.logger.info("No references found")
            return references
        if len(references) != num_references:
            self.logger.warning(f"Number of references found ({len(references)}) does not match expected number ({num_references})")
        return references


    def parse_activities(self, driver):
        activities = {
            'member_since': "",
            'reply_rate': "",
            'average_reply_speed': "",
            'bookings': "",
            'recurring_bookings': "",
            'last_activity': ""
        }

        try:
            activity_elements = driver.find_elements(By.CSS_SELECTOR, "div.activities .activity")
            for activity in activity_elements:
                try:
                    title = activity.find_element(By.CSS_SELECTOR, ".title").text.strip()
                    status = activity.find_element(By.CSS_SELECTOR, ".status")
                    
                    # Normalize title and assign accordingly
                    if title == "Mitglied seit":
                        activities['member_since'] = status.text.strip()
                    elif title == "Beantwortete Nachrichten":
                        activities['reply_rate'] = status.text.strip()
                    elif title == "Durchschnittliche Antwortzeit":
                        activities['average_reply_speed'] = status.text.strip()
                    elif title == "Buchungen":
                        activities['bookings'] = status.text.strip()
                    elif title == "Buchungen wiederholen":
                        activities['recurring_bookings'] = status.text.strip()
                    elif title == "Letzte Aktivität":
                        activities['last_activity'] = status.text.strip()
                    else:
                        self.logger.warning(f"Unknown credential title: {title}")
                except NoSuchElementException:
                    continue
        except NoSuchElementException:
            pass
        return activities
    
class BabysitsDetailsWorkers(BabysitsDetails):
    def __init__(self, profile_range_start=0, profile_range_end=1):
        super().__init__(profile_range_start, profile_range_end)
        self.type = PlatformType.WORKER
        self.clean_file_path = "../../../data/clean/babysits_worker.csv"
        self.attributes = ["PLZ", "Scraping date", "ID", "Name", "Age", "Type", "Location", "Experience", "Experience age", "Experience special needs", "Supersitter", "Verified ID", "First aid certificate", "Babysitter certificate", "Sexual offenses record extract", "Criminal record extract", "Other certificates", "Driver license", "Has car", "Has kids", "Smoker", "Peferred working location", "Languages spoken", "Favorised count", "Highest degree", "Highest degree details", "Certificates (working with kids)", "Medical certificates", "Characteristics", "Superpowers", "Open to", "Salary", "Last online", "Last online (delta in days)", "Member since", "Reply rate", "Average reply speed", "Bookings", "Recurring bookings", "Number of reviews", "Reviews", "Number of references", "References", "URL"]

    def scrape_babysits_details(self, driver, url, plz, id):
        try:
            d1 = date.today()
            name = driver.find_element(By.TAG_NAME, 'h1').text.strip()
            job_type_location = driver.find_element(
                By.XPATH,
                "//div[contains(@class, 'mb-3') and .//a[contains(text(), 'in')]]"
            ).text
            job_type, location = job_type_location.split(' in ')
            salary = driver.find_element(
                By.XPATH,
                "//div[div[text()[normalize-space()='Stundenlohn']]]/div[contains(@class, 'fw-bold')]"
            ).text.strip()
            # Scrape age
            summary_div = driver.find_element(By.CLASS_NAME, 'details-summary')
            age = summary_div.find_elements(By.CLASS_NAME, 'me-4')[0].find_element(By.CLASS_NAME, 'fw-bold').text.strip()
            # Calculate difference in days comapred to scraping day
            last_online = driver.find_element(By.TAG_NAME, 'time').get_attribute('datetime')
            d2 = date.fromisoformat(last_online)
            last_online_delta = (d1 - d2).days
            characteristics = self.get_characteristics(driver)
            summary = self.parse_summary(driver)
            # Credentials
            credentials = self.parse_credentials(driver)
            # Superpowers
            superpowers = self.parse_superpowers(driver)
            # Open to
            open_to = self.parse_open_to(driver)
            # Scrape bewertungen (name, userID/url, text, date, stars, date)
            reviews = self.parse_reviews(driver)
            # Scrape referenz (name, userID/url, beziehung, descrption, date)
            references = self.parse_references(driver)
            # Scrape activity levels
            activities = self.parse_activities(driver)
        except NoSuchElementException as e:
            try:
                alert = driver.find_element(By.CLASS_NAME, 'alert').text.strip()
                self.logger.warning(f"Alert found on profile {url}: {alert}")
                return [plz, d1.strftime('%Y-%m-%d'), id, "PRIVAT", None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, "", None, None, None, None, None, None, None, None, None, None, url]
            except NoSuchElementException:
                self.logger.exception(f"No alert found on profile {url}")
                return [plz, d1.strftime('%Y-%m-%d'), id, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, "", None, None, None, None, None, None, None, None, None, None, url]
        return [plz, d1.strftime('%Y-%m-%d'), id, name, age, job_type, location, summary['experience'], summary['experience_age'], summary['experience_special_needs'], summary['supersitter'], summary['ID'], summary['first_aid'], summary['babysitter_certificate'], summary['sexual_offenses_record_extract'], summary['criminal_record_extract'], ';'.join(summary['other_certificates']), credentials['driver_license'], credentials['car'], credentials['has_kids'], credentials['smoker'], credentials['preferred_location'], credentials['languages_spoken'], credentials['favorite_count'], credentials['highest_degree'], credentials['highest_degree_details'], credentials['certificates_children'], credentials['certificates_medical'], characteristics, superpowers, open_to, salary, last_online, last_online_delta, activities["member_since"], activities["reply_rate"], activities["average_reply_speed"], activities["bookings"], activities["recurring_bookings"], len(reviews), reviews, len(references), references, url]
    
    def parse_superpowers(self, driver):
        superpowers = []
        try:
            header = driver.find_element(By.XPATH, "//h2[contains(text(), 'Superkräfte')]")
            superpowers_locator = locate_with(By.CSS_SELECTOR, "div.credentials-list .credential").below(header)
            superpower_elements = driver.find_elements(superpowers_locator)
            for superpower in superpower_elements:
                try:
                    content = superpower.find_element(By.CSS_SELECTOR, ".content").text.strip()
                    superpowers.append(content)
                except NoSuchElementException:
                    self.logger.exception(f"Error while parsing superpowers, skipping {superpower}")
                    continue
        except NoSuchElementException:
            self.logger.info("No superpowers found")
            return superpowers
        return superpowers
    
    def parse_open_to(self, driver):
        open_to = []
        try:
            header = driver.find_element(By.XPATH, "//h2[contains(text(), 'Ich bin offen')]")
            open_to_locator = locate_with(By.CSS_SELECTOR, "div.credentials-list .credential").below(header)
            open_to_elements = driver.find_elements(open_to_locator)
            for ot in open_to_elements:
                try:
                    content = ot.find_element(By.CSS_SELECTOR, ".content").text.strip()
                    open_to.append(content)
                except NoSuchElementException:
                    self.logger.exception(f"Error while parsing open to, skipping {ot}")
                    continue
        except NoSuchElementException:
            self.logger.info("No open to found")
            return open_to
        return open_to
    
class BabysitsDetailsJobs(BabysitsDetails):
    def __init__(self, profile_range_start=0, profile_range_end=1):
        super().__init__(profile_range_start, profile_range_end)
        self.type = PlatformType.JOB
        self.clean_file_path = "../../../data/clean/babysits_job.csv"
        self.attributes = ["PLZ", "Scraping date", "ID", "Name", "Type", "Location", "Characteristics of the kids", "Number of kids", "Age of kids", "Kids with special needs", "Verified ID", "Tasks", "Looking for", "Preferred location", "Languages spoken", "Favorised count", "Member since", "Reply rate", "Average reply speed", "Bookings", "Recurring bookings", "Salary", "Last online", "Last online (delta in days)", "Number of reviews", "Reviews", "Number of references", "References", "URL"]

    def scrape_babysits_details(self, driver, url, plz, id):
        try:
            d1 = date.today()
            name = driver.find_element(By.TAG_NAME, 'h1').text.strip()
            job_type_location = driver.find_element(
                By.XPATH,
                "//div[contains(@class, 'mb-3') and .//a[contains(text(), 'in')]]"
            ).text
            job_type, location = job_type_location.split(' in ')
            salary = driver.find_element(
                By.XPATH,
                "//div[div[text()[normalize-space()='Stundenlohn']]]/div[contains(@class, 'fw-bold')]"
            ).text.strip()
            last_online = driver.find_element(By.TAG_NAME, 'time').get_attribute('datetime')
            d2 = date.fromisoformat(last_online)
            last_online_delta = (d1 - d2).days
            characteristics = self.get_characteristics(driver)
            summary = self.parse_summary(driver)
            # Credentials
            credentials = self.parse_credentials(driver)
            # Open to
            open_to = self.parse_open_to(driver)
            # Scrape bewertungen (name, userID/url, text, date, stars, date)
            reviews = self.parse_reviews(driver)
            # Scrape referenz (name, userID/url, beziehung, descrption, date)
            references = self.parse_references(driver)
            # Scrape activity levels
            activities = self.parse_activities(driver)
        except NoSuchElementException as e:
            try:
                alert = driver.find_element(By.CLASS_NAME, 'alert').text.strip()
                self.logger.warning(f"Alert found on profile {url}: {alert}")
                return [plz, d1.strftime('%Y-%m-%d'), id, "PRIVAT", None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, url]
            except NoSuchElementException:
                self.logger.exception(f"No alert found on profile {url}")
                return [plz, d1.strftime('%Y-%m-%d'), id, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, url]
        return [plz, d1.strftime('%Y-%m-%d'), id, name, job_type, location, characteristics, summary['number_of_kids'], summary['kids_ages'], summary['kids_special_needs'], summary['ID'], open_to, credentials['searching_for'], credentials['preferred_location'], credentials['languages_spoken'], credentials['favorite_count'], activities['member_since'], activities['reply_rate'], activities['average_reply_speed'], activities["bookings"], activities["recurring_bookings"], salary, last_online, last_online_delta, len(reviews), reviews, len(references), references, url]
    
    def parse_open_to(self, driver):
        open_to = []
        try:
            header = driver.find_element(By.XPATH, "//h2[contains(text(), 'Wir brauchen')]")
            open_to_locator = locate_with(By.CSS_SELECTOR, "div.credentials-list .credential").below(header)
            open_to_elements = driver.find_elements(open_to_locator)
            for ot in open_to_elements:
                try:
                    content = ot.find_element(By.CSS_SELECTOR, ".content").text.strip()
                    open_to.append(content)
                except NoSuchElementException:
                    self.logger.exception(f"Error while parsing open to, skipping {ot}")
                    continue
        except NoSuchElementException:
            self.logger.info("No open to found")
            return open_to
        return open_to

# Run the scraper
BabysitsDetailsJobs(profile_range_start=0, profile_range_end=1199).scrape()
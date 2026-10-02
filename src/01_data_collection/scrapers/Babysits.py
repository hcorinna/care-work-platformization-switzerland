from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.relative_locator import locate_with

import re
from datetime import date, datetime

from abc import abstractmethod

from Platforms import Platforms
from shared.PlatformNames import PlatformNames
from shared.PlatformType import PlatformType

import time

class Babysits(Platforms):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.name = PlatformNames.BABYSITS
        self.loginpage = "https://www.babysits.ch/einloggen/"
        self.current_plz = 0
        self.requires_login = True
        self.requires_plz_search = True

    def is_logged_in(self, driver):
        WebDriverWait(driver, timeout = 20).until(EC.presence_of_element_located((By.CLASS_NAME, "show-email-form")))
        btn_email_login = driver.find_element(By.CLASS_NAME, "show-email-form")
        if btn_email_login:
            self.logger.info('User is not logged in')
            return False
        self.logger.info('User is logged in')
        return True

    def fill_in_log_in(self, driver):
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

    def navigate_to_plz(self, driver, plz, name=""):
        self.pagination = 1
        max_retries = 4
        
        for attempt in range(max_retries):
            try:
                # Step 1: Find and click search button (only on first attempt)
                if attempt == 0:
                    WebDriverWait(driver, timeout=30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button.search-expand-button"))
                    )
                    search_button = driver.find_element(By.CSS_SELECTOR, "button.search-expand-button")
                    search_button.click()
                
                # Step 2: Wait for search input to be clickable
                WebDriverWait(driver, timeout=180).until(
                    EC.element_to_be_clickable((By.ID, "autocomplete-header-1"))
                )
                
                # Step 3: Enter ZIP code
                input_plz = driver.find_element(By.ID, "autocomplete-header-1")
                input_plz.clear()
                time.sleep(0.5)  # Brief pause after clearing
                input_plz.send_keys(str(plz) + ', Schweiz')
                input_plz.send_keys(Keys.ENTER)
                
                self.current_plz = plz
                time.sleep(2)  # Wait for results to load
                
                self.logger.info(f"Successfully navigated to PLZ {plz}")
                return True  # Success!
                
            except TimeoutException as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for PLZ {plz}: Timeout waiting for elements")
                
                if attempt < max_retries - 1:  # Not the last attempt
                    self.logger.info(f"Refreshing page and retrying PLZ {plz}")
                    driver.refresh()
                    time.sleep(5)  # Wait for page to reload
                else:
                    self.logger.error(f"Failed to navigate to PLZ {plz} after {max_retries} attempts")
                    return False
                    
            except Exception as e:
                self.logger.exception(f"Unexpected error while navigating to PLZ {plz}: {str(e)}")
                
                if attempt < max_retries - 1:
                    self.logger.info(f"Refreshing page and retrying PLZ {plz} after unexpected error")
                    driver.refresh() 
                    time.sleep(5)
                else:
                    self.logger.error(f"Failed to navigate to PLZ {plz} after unexpected errors")
                    return False
        
        return False  # Should never reach here, but just in case
    
    def load_more_profiles(self, driver):
        try:
            time.sleep(1)
            results_pagination = driver.find_elements(By.CLASS_NAME, "pagination")
            if not len(results_pagination) == 0:
                results_pagination = results_pagination[0]
                next_page_number = self.pagination + 1
                next_page = results_pagination.find_elements(By.XPATH, "//li/a[contains(@class, 'page-link') and text()=" + str(next_page_number) + "]")
                if not len(next_page) == 0:
                    next_link = next_page[0].get_attribute('href')
                    driver.get(next_link)
                    self.pagination += 1
                    time.sleep(1)
                    return True
            return False
        except Exception as e:
            self.logger.exception("Error while loading the next page")
            return False
    
    def find_profiles(self, driver):
        WebDriverWait(driver, timeout = 20).until(EC.presence_of_element_located((By.CLASS_NAME, "result-list")))
        profiles = driver.find_elements(By.CLASS_NAME, "profile-card")
        return profiles
    
    @abstractmethod
    def get_profile_data(self, profile, driver):
        pass

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
                        summary['number_of_kids'] = int(content_div.text.strip())
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
                        credentials['searching_for'] = content_div.text.strip()
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
                    stars_span = card.find_element(By.CSS_SELECTOR, ".stars").get_attribute("title")
                    match = re.search(r"review:\s*(\d+)\s*van", stars_span)
                    if match:
                        number = match.group(1)
                        review["stars"] = number
                    else:
                        self.logger.exception(f"Error while parsing stars: {stars_span}")
                    date_div = card.find_elements(By.CLASS_NAME, "text-body-secondary")
                    date_div = date_div[1] if len(date_div) == 2 else date_div[0]
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
                    reference["date"] = secondary_div[1].find_element(By.CSS_SELECTOR, "small").text.strip()
                    reference["text"] = card.find_element(By.CSS_SELECTOR, "p.mb-0").text.strip()
                    title = card.find_elements(By.CSS_SELECTOR, "h4.mb-2")
                    reference["title"] = title[0].text.strip() if len(title) > 0 else ""
                    references.append(reference)
                except NoSuchElementException:
                    self.logger.exception(f"Error while parsing reference")
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

class Workers(Babysits):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.website = "https://www.babysits.ch/babysitter/"
        self.type = PlatformType.WORKER
        self.attributes = ["PLZ", "Scraping date", "ID", "Name", "Type", "Location", "Experience", "Bookings", "Favorised count", "Reviews", "Number of references", "Salary", "URL"]

    def get_profile_data(self, profile, driver):
        scraping_date = date.today()
        name = profile.find_element(By.CLASS_NAME, 'name').text
        job_type_location = profile.find_element(By.CLASS_NAME, 'city').text
        job_type, location = job_type_location.split(' in ')
        # badge-experience
        try:
            experience = profile.find_element(By.CLASS_NAME, 'badge-experience').text
        except NoSuchElementException:
            self.logger.warning("No experience badge found")
            experience = ""
        # badge-bookings
        try:
            bookings = profile.find_element(By.CLASS_NAME, 'badge-bookings').text
        except NoSuchElementException:
            self.logger.warning("No bookings badge found")
            bookings = ""
        # badge-references
        try:
            references = profile.find_element(By.CLASS_NAME, 'badge-references').text
        except NoSuchElementException:
            self.logger.warning("No references badge found")
            references = ""
        # reviews
        try:
            reviews = profile.find_element(By.CLASS_NAME, 'stars').get_attribute('title')
        except NoSuchElementException:
            reviews = 0
        favorised_count = profile.find_element(By.CLASS_NAME, 'favorited-count').text
        salary = profile.find_element(By.CLASS_NAME, 'rate').text
        url = profile.find_element(By.CSS_SELECTOR, 'a.stretched-link').get_attribute('href')
        match = re.search(r'/babysitter/[^/]+/([^/]+)/', url)
        id = match.group(1) if match else url
        return [self.current_plz, scraping_date.strftime('%Y-%m-%d'), id, name, job_type, location, experience, bookings, favorised_count, reviews, references, salary, url]

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
    
class Jobs(Babysits):
    def __init__(self, username="", password="", logger=None):
        super().__init__(username, password, logger)

        self.website = "https://www.babysits.ch/babysitting/"
        self.type = PlatformType.JOB
        self.attributes = ["PLZ", "Scraping date", "ID", "Name", "Type", "Location", "Number of kids", "Age of kids", "Last online", "Last online (delta in days)", "Favorised count", "URL", "Additionals"]

    def get_profile_data(self, profile, driver):
        try:
            url = profile.find_element(By.CSS_SELECTOR, 'a.stretched-link').get_attribute('href')
            match = re.search(r'/babysitting/[^/]+/([^/]+)/', url)
            id = match.group(1) if match else ""
        except NoSuchElementException:
            self.logger.exception("Error while getting profile URL/ID")
            return []
        try:
            d1 = date.today()
            name = profile.find_element(By.CLASS_NAME, 'name').text
            job_type_location = profile.find_element(By.CLASS_NAME, 'city').text
            job_type, location = job_type_location.split(' in ')
            additionals = profile.find_elements(By.CSS_SELECTOR, 'div.additionals > div')
            additional_details = [a.text.strip() for a in additionals]
            number_kids = ""
            age_kids = ""
            activity = ""
            additional_details = ""
            if len(additionals) >= 3:
                number_kids = additionals[0].text
                age_kids = additionals[1].text
                activity = additionals[2].get_attribute("title")
                d2 = datetime.strptime(activity, "%d.%m.%y").date()
                last_online_delta = (d1 - d2).days
                if len(additionals) > 3:
                    additional_details = [a.text for a in additionals[3:]]
            favorised_count = profile.find_element(By.CLASS_NAME, 'favorited-count').text
            return [self.current_plz, d1.strftime('%Y-%m-%d'), id, name, job_type, location, number_kids, age_kids, d2.strftime('%Y-%m-%d'), last_online_delta, favorised_count, url, additional_details]
        except NoSuchElementException:
            self.logger.exception(f"Error while scraping profile data for ID {id}")
            # re_list = list(range(30)) + [url, additional_details]
            # re_list[0] = self.current_plz
            # re_list[2] = id
            # re_list[27] = url
            # return re_list
            return [self.current_plz, d1, id]
    
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
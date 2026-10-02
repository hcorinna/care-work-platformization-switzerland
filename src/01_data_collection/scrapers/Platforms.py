from abc import ABC, abstractmethod

import json

import logging
from pathlib import Path

class Platforms(ABC):
    def __init__(self, username="", password="", logger=None):
        self.username = username
        self.password = password
        self.name = ""
        self.type = None
        self.category = None
        self.loginpage = ""
        self.website = ""
        self.filename = ""
        self.attributes = []
        self.pagination = 1
        self.requires_login = False
        self.requires_plz_search = False
        self.requires_distance_sorting = False
        self.requires_plz_name = False
        self.logger = logger or logging.getLogger(__name__)

    def initialise_platform_credentials(self):
        credentials_path = Path(__file__).resolve().parents[3] / 'credentials.json'
        with credentials_path.open('r', encoding='utf-8') as file:
            credentials = json.load(file)
        platform_credentials = credentials[self.name.name]

        if "username" in platform_credentials:
            self.username = platform_credentials["username"]
        else:
            self.username = platform_credentials["email"]
        self.password = platform_credentials["password"]

    def get_name(self):
        return self.name
    
    def get_filename(self):
        return self.name.value + "_" + self.type.value + (("_" + self.category.value) if self.category else "")
    
    def get_type(self):
        return self.type

    def get_category(self):
        return self.category

    def is_plz_search_required(self):
        return self.requires_plz_search

    def is_logged_in(self, driver):
        pass

    def fill_in_log_in(self, driver):
        pass

    def login(self, driver):
        if self.requires_login:
            driver.get(self.loginpage)
            if not self.is_logged_in(driver):
                self.fill_in_log_in(driver)

    def navigate_to_plz(self, driver, plz, name=""):
        pass

    def sort_by_distance(self, driver):
        pass

    @abstractmethod
    def load_more_profiles(self, driver):
        pass

    @abstractmethod
    def find_profiles(self, driver):
        pass

    @abstractmethod
    def get_profile_data(self, profile, driver):
        pass
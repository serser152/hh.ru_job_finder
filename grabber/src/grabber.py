#!/usr/bin/env python
# coding: utf-8
"""
Grabbers:
    HHGrabber - class for hh.ru
    ZPGrabber - class for zarplata.ru
"""

from time import sleep
from abc import ABC, abstractmethod
from tqdm import tqdm
import selenium.webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

#######################################
#           Login utils               #
#######################################

class GrabberException(Exception):
    """ Something happened """


class Grabber (ABC):
    """ Base class for job site grabber """
    driver = None
    site = None
    login = None
    password = None


    def __init__(self, site, login, password):
        """
        Constructor
        Create driver, login to site
        """
        self.site = site
        self.login = login
        self.password = password
        self.create_driver()
        self.login_to_site()

    def create_driver(self, eager=True):
        """ Create selenium driver """
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')
        options.add_argument('--start-maximized')
        if eager:
            options.page_load_strategy = 'eager'

        self.driver = selenium.webdriver.Firefox(options=options)


    def __del__(self):
        """ Destructor. Quit driver """
        if self.driver:
            self.driver.quit()


    @abstractmethod
    def login_to_site(self):
        """
        login to site
        """


    @abstractmethod
    def make_search_request(self, search_request):
        """ Make search request to site """


    @abstractmethod
    def get_page_count(self):
        """ Get page count """

    @abstractmethod
    def get_pages_vacancies(self, page, skip_click=False):
        """ Get vacancies from page """


    def get_vacancies(self, search_request):
        """ Get vacancies from site """
        self.make_search_request(search_request)
        all_vacancies = []
        pages = self.get_page_count()
        if pages > 1:
            for i in tqdm(list(range(1,pages + 1))):
                all_vacancies.extend(self.get_pages_vacancies(i))
        else:
            all_vacancies = self.get_pages_vacancies(1, skip_click = True)
        return all_vacancies


    @abstractmethod
    def get_vacancy_description(self, vacancy_id: int) -> dict:
        """ Get vacancy description """


    def get_vacancies_descriptions(self, vacancy_ids: list) -> list:
        """ Get vacancies list descriptions """
        result = []
        for vacancy_id in tqdm(vacancy_ids):
            result.append(self.get_vacancy_description(vacancy_id))
        return result


    @abstractmethod
    def respond_to_vacancy(self, vacancy_id: int, cover_letter: str):
        """Respond to vacancy (vacancy_id) with cover_letter"""


#######################################
#           Selenium utils           #
#######################################


def find_by_qa(driver, qa_txt):
    '''find element by qa attribute'''
    return driver.find_elements(By.CSS_SELECTOR, f'[data-qa="{qa_txt}"]')


def find_by_qa2(driver, txt):
    '''find element by qa attribute'''
    try:
        elems = find_by_qa(driver, txt)
        if len(elems) > 0:
            return elems[0].text
        print('no elements found')
        return None
    except NoSuchElementException:
        return None

def find_n_click(driver, txt):
    '''Find the button with text txt and click on it'''
    res = driver.find_elements(By.TAG_NAME, 'button')

    for r in res:
        if txt == r.text:
            r.click()
            driver.implicitly_wait(1)
            break

#######################################
#          HH.ru Grabber              #
#######################################


class HHGrabber(Grabber):
    """ Grabber for hh.ru """

    def __init__(self, login, password):
        """Initialize HHGrabber"""
        if not self.site:
            self.site = 'hh.ru'

        super().__init__(self.site, login, password)


    def login_to_site(self):
        """ Login to site """
        if self.login and self.password:
            if self.driver:
                self.driver.set_page_load_timeout(20)
                self.driver.get(f'https://{self.site}')
                sleep(3)

                # accept cookie and accept city
                find_n_click(self.driver, 'Понятно')
                find_n_click(self.driver, 'Да, верно')

                self.driver.get(f'https://{self.site}/account/login?'
                'role=applicant&backurl=%2F&hhtmFrom=main')
                sleep(2)

                # enter via password
                find_n_click(self.driver, 'Войти')
                sleep(2)

                # enter phone
                res = self.driver.find_elements(By.TAG_NAME, 'input')
                res[4].send_keys(self.login)
                sleep(1)
                find_n_click(self.driver, 'Войти с паролем')
                sleep(2)

                #enter pass
                res = self.driver.find_elements(By.TAG_NAME,'input')
                res[1].send_keys(self.password)
                self.driver.implicitly_wait(10)
                sleep(1)

                find_n_click(self.driver, 'Войти')
                sleep(3)

    def make_search_request(self, search_request):
        """ Make search request to site """
        if self.driver:
            if search_request:
                res = self.driver.find_elements(By.TAG_NAME, 'input')
                for r in res:
                    if r.get_attribute('data-qa') == 'search-input':
                        r.send_keys(search_request)
                        break
                find_n_click(self.driver, 'Найти')
                sleep(2)

    def get_page_count(self) -> int:
        """ Get page count """
        try:
            ii = self.driver.find_element(By.TAG_NAME, 'nav').find_elements(By.TAG_NAME, 'li')
            pages = [iii.text for iii in ii]
            last_page = int(pages[-2])
            return last_page + 1
        except NoSuchElementException:
            return 1


    def __parse_card(self, r):
        """ parse job card in main list"""
        res = r.find_elements(By.TAG_NAME, 'div')
        vac_id = None
        status = None
        for t in res:
            if t.get_attribute('class').startswith('vacancy-card--'):
                vac_id = t.get_property('id')
            if t.get_attribute('class').startswith('vacancy-card-footer'):
                status = t.text

        title = r.find_element(By.CSS_SELECTOR,'[data-qa="serp-item__title-text"]').text

        # simplify status
        if status.startswith('Вы откликнулись'):
            status = 'Отклик'
        elif status.startswith('Откликнуться'):
            status = 'Откликнуться'
        elif status.startswith('Вам отказали'):
            status = 'Отказ'

        d = {
            'vac_id': vac_id,
            'title': title,
            'status': status,
            'site': self.site,
            'link': f'https://{self.site}/vacancy/{vac_id}'
        }

        return d


    def get_pages_vacancies(self, page, skip_click=False) -> list:
        """ Get vacancies from page """
        print(f'loading page {page}')
        if self.driver:
            # go to page
            if not skip_click:
                ii = self.driver.find_element(By.TAG_NAME, 'nav').find_elements(By.TAG_NAME, 'li')
                pages = ii
                p = None
                for p in pages:
                    if p.text == str(page):
                        break
                p.click()
                sleep(3)
            vacancies = find_by_qa(self.driver, "vacancy-serp__vacancy")
            print(f'found {len(vacancies)} div tags')
            new_data = []
            for v in tqdm(vacancies):
                new_data.append(self.__parse_card(v))
            return new_data
        return []

    def get_vacancy_description(self, vacancy_id: int) -> dict:
        """parse vacancy details description page"""
        print(f'loadin vacancy {vacancy_id}')
        self.driver.get(f'https://{self.site}/vacancy/{vacancy_id}')
        sleep(3)
        d = {
            'vac_id': vacancy_id,
            'vac_title': find_by_qa2(self.driver, 'vacancy-title'),
            'vac_company': find_by_qa2(self.driver, 'vacancy-company-name'),
            'vac_salary': find_by_qa2(self.driver, 'vacancy-salary'),
            'vac_exp': find_by_qa2(self.driver, 'work-experience-text'),
            'vac_emp': find_by_qa2(self.driver, 'common-employment-text'),
            'vac_hiring_format': find_by_qa2(self.driver, 'vacancy-hiring-formats'),
            'vac_working_hours': find_by_qa2(self.driver, 'working-hours-text'),
            'vac_work_format': find_by_qa2(self.driver, 'work-formats-text'),
            'vac_descr': find_by_qa2(self.driver, 'vacancy-description')
        }
        # remove prefixes
        if d['vac_exp']:
            d['vac_exp'] = d['vac_exp'].replace('Опыт работы: ','')
        if d['vac_hiring_format']:
            d['vac_hiring_format'] = d['vac_hiring_format'].replace('Оформление: ','')
        if d['vac_work_format']:
            d['vac_work_format'] = d['vac_work_format'].replace('Формат работы: ','')

        print(d)
        return d

    def respond_to_vacancy(self, vacancy_id: int, cover_letter: str):
        """ Respond to vacancy with cover letter """
        self.driver.get(f'https://{self.site}/vacancy/{vacancy_id}')
        sleep(2)

        r = find_by_qa2(self.driver, 'vacancy-response-link-top')
        r.click()
        sleep(2)

class ZPGrabber(HHGrabber):
    """ Grabber for zarplata.ru (same as hh.ru but with different site) """
    def __init__(self, login, password):
        self.site = 'zarplata.ru'
        super().__init__(login, password)

    def get_vacancy_description(self, vacancy_id: int) -> dict:
        """parse vacancy details description page"""

        print(f'loadin vacancy {vacancy_id}')

        self.driver.get(f'https://{self.site}/vacancy/{vacancy_id}')
        sleep(3)

        d = {
            'vac_id': vacancy_id,
            'vac_title': find_by_qa2(self.driver, 'vacancy-title'),
            'vac_company': self.driver.find_element(By.CLASS_NAME, 'vacancy-company-details').text,
            'vac_salary': find_by_qa2(self.driver, 'vacancy-salary'),
            'vac_exp': find_by_qa2(self.driver, 'work-experience-text'),
            'vac_emp': find_by_qa2(self.driver, 'common-employment-text'),
            'vac_hiring_format': find_by_qa2(self.driver, 'vacancy-hiring-formats'),
            'vac_working_hours': find_by_qa2(self.driver, 'working-hours-text'),
            'vac_work_format': find_by_qa2(self.driver, 'work-formats-text'),
            'vac_descr': find_by_qa2(self.driver, 'vacancy-description')
        }
        # remove prefixes
        if d['vac_exp']:
            d['vac_exp'] = d['vac_exp'].replace('Опыт работы: ','')
        if d['vac_hiring_format']:
            d['vac_hiring_format'] = d['vac_hiring_format'].replace('Оформление: ','')
        if d['vac_work_format']:
            d['vac_work_format'] = d['vac_work_format'].replace('Формат работы: ','')

        # check if scrapping failed
        if d['vac_title'] == None:
            raise GrabberException()

        print(d)

        return d


class GrabberFactory:
    """
    Factory for grabbers
    """

    def __init__(self):
        """constructor"""

    @staticmethod
    def create_grabber(site, login, password) -> Grabber:
        """
        create grabber based on site value
        acceptable values: 'hh.ru', 'zarplata.ru'
        """
        if site == 'hh.ru':
            return HHGrabber(login, password)
        if site == 'zarplata.ru':
            return ZPGrabber(login, password)
        raise ValueError(f"Unknown site: {site}")


    def get_supported_grabbers(self):
        """
        get list of supported grubbers
        """
        return ['hh.ru', 'zarplata.ru']

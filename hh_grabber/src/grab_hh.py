#!/usr/bin/env python
# coding: utf-8
'''
Grab hh.ru data modules

def get_vacancies(phone, password, request)
def get_descriptions(phone, password, vacancy_ids)
def accept_vacancy(phone, password, vacancy_ids)
'''

from time import sleep
import datetime
import pandas as pd
from tqdm import tqdm
import selenium.webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

#######################################
#           Login utils               #
#######################################

def find_n_click(driver, txt):
    '''Find the button with text txt and click on it'''
    res = driver.find_elements(By.TAG_NAME, 'button')

    for r in res:
        if txt == r.text:
            r.click()
            driver.implicitly_wait(1)
            break


def login(phone='9200123456', password='123456', eager=True):
    '''login to hh.ru using phone and password'''
    print('Login to hh')

    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    options.add_argument('--start-maximized')
    if eager:
        options.page_load_strategy = 'eager'

    driver = selenium.webdriver.Firefox(options=options)

    driver.set_page_load_timeout(20)
    driver.get('https://nn.hh.ru')
    sleep(3)

    # accept cookie and accept city
    find_n_click(driver, 'Понятно')
    find_n_click(driver, 'Да, верно')

    driver.get('https://nn.hh.ru/account/login?role=applicant&backurl=%2F&hhtmFrom=main')
    sleep(2)

    # enter via password
    find_n_click(driver, 'Войти')
    sleep(2)
    # enter phone
    res = driver.find_elements(By.TAG_NAME, 'input')
    res[4].send_keys(phone)
    sleep(1)

    find_n_click(driver, 'Войти с паролем')
    sleep(2)
    #enter pass
    res= driver.find_elements(By.TAG_NAME,'input')
    res[1].send_keys(password)
    driver.implicitly_wait(10)
    sleep(1)

    find_n_click(driver, 'Войти')
    sleep(3)
    return driver

def send_find_request(driver, txt):
    '''Send find request'''
    res = driver.find_elements(By.TAG_NAME, 'input')
    for r in res:
        if r.get_attribute('data-qa') == 'search-input':
            r.send_keys(txt)
            break
    find_n_click(driver, 'Найти')

########################################
# # parsing functions                 #
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


def parse_card(r):
    ''' parse job card. Click and parse details'''
    res = r.find_elements(By.TAG_NAME, 'div')
    vac_id = None
    tags = None
    company = None
    status = None

    title = r.find_element(By.CSS_SELECTOR,'[data-qa="serp-item__title-text"]').text
    res=r.find_elements(By.TAG_NAME,'div')
    for t in res:
        if t.get_attribute('class').startswith('vacancy-card--'):
            vac_id = t.get_property('id')
        if t.get_attribute('class').startswith('compensation-labels'):
            tags = t.text
        if t.get_attribute('class').startswith('company-name'):
            company = t.text
        if t.get_attribute('class').startswith('vacancy-card-footer'):
            status = t.text
    d = {
        'vac_id': vac_id,
        'title': title,
        'tags': tags,
        'company': company,
        'status': status,
        'link': f'https://hh.ru/vacancy/{vac_id}'
    }
    sleep(1)
    return d


def get_last_page(driver):
    '''get the last page number of search results'''
    try:
        ii = driver.find_element(By.TAG_NAME, 'nav').find_elements(By.TAG_NAME, 'li')
        pages = [iii.text for iii in ii]
        last_page = int(pages[-2])
        return last_page + 1
    except NoSuchElementException:
        return 1


def parse_page_content(driver):
    '''parsing vacancy card from search results'''
    res = find_by_qa(driver, "vacancy-serp__vacancy")
    print(f'found {len(res)} div tags')
    new_data = []
    for r in tqdm(res):
        new_data.append(parse_card(r))
    return new_data


def parse_page(driver, n=1, skip_click=False):
    '''Parsing page of search results'''
    if not skip_click:
        ii = driver.find_element(By.TAG_NAME, 'nav').find_elements(By.TAG_NAME, 'li')
        pages = ii
        p = None
        for p in pages:
            if p.text == str(n):
                break
        p.click()
        sleep(3)
    new_data = parse_page_content(driver)
    return new_data


def get_description(driver, vac_id):
    '''parse vacancy details description page'''
    print(f'loadin vacancy {vac_id}')
    driver.get(f'https://nn.hh.ru/vacancy/{vac_id}')
    sleep(3)
    d = {
        'vac_id': vac_id,
        'vac_title': find_by_qa2(driver, 'vacancy-title'),
        'vac_salary': find_by_qa2(driver, 'vacancy-salary'),
        'vac_exp': find_by_qa2(driver, 'work-expirience-text'),
        'vac_emp': find_by_qa2(driver, 'common-employment-text'),
        'vac_hiring_format': find_by_qa2(driver, 'vacancy-hiring-format'),
        'vac_working_hours': find_by_qa2(driver, 'working-hours-text'),
        'vac_work_format': find_by_qa2(driver, 'work-formats-text'),
        'vac_descr': find_by_qa2(driver, 'vacancy-description')
    }
    print(d)
    return d


def get_descriptions_by_ids(driver, vac_ids):
    '''get vacancy details for all vacancy ids'''
    descrs = []
    for i in tqdm(vac_ids):
        print(f'Loading description for vacancy {i}')
        descrs.append(get_description(driver, i))
    return descrs


def grep_results(driver):
    '''parsing all search results (all pages, all cards)'''

    print('Grep results')
    driver.switch_to.window(driver.window_handles[0])

    data = []
    last_page = get_last_page(driver)
    print(f'total {last_page} pages')
    for i in tqdm(range(0, last_page)):
        new_data = parse_page(driver, i + 1, last_page == 1)
        data += new_data
    return data


##########################
# respond to vacancy    #
##########################

def click_by_id(driver, vac_id):
    '''
    click to respond on a vacancy.
    vid - vacancy id
    '''
    driver.get(f'https://hh.ru/vacancy/{vac_id}')
    sleep(2)

    r = find_by_qa2(driver, 'vacancy-response-link-top')
    r.click()
    sleep(2)


############################
# process parsed data     #
############################

def process_results(data_res):
    '''process parsed data'''
    df = pd.DataFrame(data_res)
    df['dt'] = datetime.datetime.now()

    df.loc[df['status'].str.startswith('Откликнуться'), 'status'] = 'Откликнуться'
    df.loc[df['status'].str.startswith('Вам отказали'), 'status'] = 'Вам отказали'
    df.loc[df['status'].str.startswith('Вы откликнулись'), 'status'] = 'Вы откликнулись'
    df.loc[df['status'].str.startswith('Вас пригласили'), 'status'] = 'Вас пригласили'

    def parse_tags(x):
        l = x['tags'].split('\n')
        x['expirience'] = None
        x['money'] = None
        x['remote'] = None
        for i in l:
            if i.lower().find('опыт') >= 0:
                x['expirience'] = i
            if i.lower().find('за месяц') >= 0:
                x['money'] = i
            if i.lower().find('удалённо') >= 0:
                x['remote'] = i
        return x

    df2 = df.apply(parse_tags, axis=1)
    df2.drop(columns=['tags'], inplace=True)
    df2['site'] = 'hh.ru'
    return df2


################################
#   Functions for external use #
################################


def get_vacancies(phone, password, request):
    ''' get vacancies for request'''
    try:
        driver = login(phone, password)
        send_find_request(driver, request)
        data_res = grep_results(driver)
        df = process_results(data_res)
        driver.quit()
    except NoSuchElementException as e:
        print(e)
        driver.quit()
        df = None
    return df


def get_descriptions(phone, password, vacancy_ids):
    ''' get vacancy details for all vacancy ids'''
    try:
        driver = login(phone, password)
        df = pd.DataFrame(get_descriptions_by_ids(driver, vacancy_ids))
        df['site']='hh.ru'
        driver.quit()
    except NoSuchElementException as e:
        print(e)
        driver.quit()
        df = None
    return df


def accept_vacancy(phone, password, vacancy_ids):
    ''' click reply vacancy by vacancy id and request'''
    try:
        driver = login(phone, password)
        for vacancy_id in vacancy_ids:
            click_by_id(driver, vacancy_id)
    except NoSuchElementException as e:
        print(e)
    driver.quit()

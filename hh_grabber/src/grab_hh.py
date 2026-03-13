#!/usr/bin/env python
# coding: utf-8

# In[5]:


import selenium.webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from time import sleep
import datetime
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import pandas as pd

# Login utils
driver = None

def find_n_click(txt):
    '''Find the button with text txt and click on it'''
    res= driver.find_elements(By.TAG_NAME,'button')

    for r in res:
        if txt == r.text:
            r.click()
            driver.implicitly_wait(1)
            break

def login(phone='9200123456', password='123456'):
    '''login to hh.ru using phone and password'''

    global driver
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    #options.add_argument('--headless')
    options.add_argument('--start-maximized')

    driver = selenium.webdriver.Chrome(options=options)

    driver.get('https://nn.hh.ru')

    #accept cookie and accept NN
    find_n_click('Понятно')
    find_n_click('Да, верно')

    driver.get('https://nn.hh.ru/account/login?role=applicant&backurl=%2F&hhtmFrom=main')
    sleep(2)

    # enter via password
    find_n_click('Войти')

    # enter phone
    res= driver.find_elements(By.TAG_NAME,'input')
    res[4].send_keys(phone)
    sleep(1)


    find_n_click('Войти с паролем')

    #enter pass
    res= driver.find_elements(By.TAG_NAME,'input')
    res[1].send_keys(password)
    driver.implicitly_wait(10)
    sleep(1)

    find_n_click('Войти')

    sleep(3)


# In[7]:


def send_find_request(txt):
    res= driver.find_elements(By.TAG_NAME,'input')
    for r in res:
        if r.get_attribute('data-qa') == 'search-input':
            r.send_keys(txt)
            break
    find_n_click('Найти')


# # parsing functions

# In[88]:


def find_by_qa(qa_txt):
    return driver.find_elements(By.CSS_SELECTOR,f'[data-qa="{qa_txt}"]')
def find_by_qa2(txt):
    try:
        return find_by_qa(txt)[0].text
    except:
        return None





def get_description():
    '''parse vacancy details description page'''

    #print('switch tab')
    original_window=driver.current_window_handle

    for w in driver.window_handles:
        if w != original_window:
            driver.switch_to.window(w)
            break
    #print('parsing desc')
    sleep(1)
    d = {
        'vac_title': find_by_qa2('vacancy-title'),
        'vac_salary': find_by_qa2('vacancy-salary'),
        'vac_exp': find_by_qa2('work-expirience-text'),
        'vac_emp': find_by_qa2('common-employment-text'),
        'vac_hiring_format': find_by_qa2('vacancy-hiring-format'),
        'vac_working_hours': find_by_qa2('working-hours-text'),
        'vac_work_format': find_by_qa2('work-formats-text'),
        'vac_descr': find_by_qa2('vacancy-description')
    }

    #print('switch back')
    driver.close()

    driver.switch_to.window(original_window)
    return d

def parse_card(r):
    ''' parse job card. Click and parse details'''
    title = r.find_element(By.TAG_NAME,'h2').text
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
        'description': ''
    }
    sleep(1)
    try:
        r2 = r.find_element(By.TAG_NAME,'h2')
        r2.click()
        #driver.execute_script("arguments[0].click();", r2)
        wait = WebDriverWait(driver,2)
        wait.until(EC.number_of_windows_to_be(2))
        d['description'] = get_description()
    except Exception as e:
        print('error parsing description:', e)
    return d

def get_last_page():
    '''get the last page number of search results'''
    try:
        ii=driver.find_element(By.TAG_NAME,'nav').find_elements(By.TAG_NAME,'li')
        pages=[iii.text for iii in ii]
        last_page=int(pages[-2])
        return last_page + 1
    except:
        return 1

# parsing pages and grab vacancies data

def parse_page_content():
    '''parsing vacancy card from search results'''
    global data
    res = find_by_qa("vacancy-serp__vacancy")
    print(f'found {len(res)} div tags')
    for r in tqdm(res):
        data.append(parse_card(r))


def parse_page(n=1, skip_click=False):
    '''Parsing page of search results'''
    if not skip_click:
        ii=driver.find_element(By.TAG_NAME,'nav').find_elements(By.TAG_NAME,'li')
        pages=[iii for iii in ii]
        for p in pages:
            if p.text == str(n):
                break
        #sleep(1)
        p.click()
        #driver.execute_script("arguments[0].click();", p)
        sleep(2)
    parse_page_content()


data=[]

def grep_results():
    '''parsing all search results (all pages, all cards)'''
    global data
    driver.switch_to.window(driver.window_handles[0])

    data=[]
    last_page = get_last_page()
    print(f'total {last_page} pages')
    for i in tqdm(range(0,last_page)):
        parse_page(i+1, last_page==1)
    return data



# find n click on vacancy

def click_card_if_id(r,vid):
    res=r.find_elements(By.TAG_NAME,'div')
    for t in res:
        if t.get_attribute('class').startswith('vacancy-card--'):
            vac_id = t.get_property('id')
    print('vac_id = ', vac_id)
    if str(vac_id) == str(vid):
        print('Card found')
        for t in res:
            if t.get_attribute('class').startswith('vacancy-card-footer'):
                res2 = t.find_element(By.TAG_NAME,'a')
                print(res2.text)
                res2.click()
                sleep(2)
                print('click')
                return True # card found
    return False # continue search

def find_n_click_cards_on_page(vid):
    '''parsing vacancy card from search results'''
    global data
    res = find_by_qa("vacancy-serp__vacancy")
    for r in tqdm(res):
        if click_card_if_id(r, vid):
            return True # found card
    print('not found on page')
    return False # continue search


def click_by_id_on_page(n, skip_click, vid):
    '''
    click to respond on a vacancy.
    vid - vacancy id
    '''
    '''Parsing page of search results'''
    print('find page ',n)
    if not skip_click:
        ii=driver.find_element(By.TAG_NAME,'nav').find_elements(By.TAG_NAME,'li')
        pages=[iii for iii in ii]
        for p in pages:
            if p.text == str(n):
                break
        p.click()
        sleep(2)
    return find_n_click_cards_on_page(vid)


data=[]

def click_by_id(vid):
    '''
    click to respond on a vacancy.
    vid - vacancy id
    '''
    global data
    driver.switch_to.window(driver.window_handles[0])

    last_page = get_last_page()
    print(f'total {last_page} pages')
    for i in tqdm(range(0,last_page)):
        if click_by_id_on_page(i+1, last_page==1, vid):
            return True
    return False


# process parsed data

def process_results(data, req='ds'):
    df = pd.DataFrame(data)
    df['dt']=datetime.datetime.now()

    df.loc[df['status'].str.startswith('Откликнуться'),'status']='Откликнуться'
    df.loc[df['status'].str.startswith('Вам отказали'),'status']='Вам отказали'
    df.loc[df['status'].str.startswith('Вы откликнулись'),'status']='Вы откликнулись'
    df.loc[df['status'].str.startswith('Вас пригласили'),'status']='Вас пригласили'



    def parse_tags(x):
        l=x['tags'].split('\n')

        x['expirience']=None
        x['money']=None 
        x['remote']=None
        for i in l:
            if i.lower().find('опыт')>=0:
                x['expirience'] = i
            if i.lower().find('за месяц')>=0:
                x['money']=i
            if i.lower().find('удалённо')>=0:
                x['remote']=i
        return x


    df2=df.apply(parse_tags,axis=1)


    df2.drop(columns=['tags'], inplace=True)

    if df2[df2['description'].isna()].shape[0]/df2.shape[0] > 0.05:
#        raise Exception('Failed scraping description. Errors rate > 5%')
        print('Failed scraping description. Errors rate > 5%')

    df22=pd.json_normalize(df2['description'])
    df3 = df2.join(df22)
    df3.drop('description',axis=1, inplace=True)
    return df3
def save2pg(pg_connection,data):
    #con='postgresql://postgres:postgres@localhost:5433/public'
    df3.to_sql(f'hh_{req}', pg_connection, if_exists='append', index=False)

def get_vacancies(phone, password, request):
    print('login')
    login(phone, password)
    print('searching')
    send_find_request(request)
    print('collecting results')
    data=grep_results()
    df = process_results(data, 'ds')
    print(df)
    print('exit')
    driver.quit()
    return df


def accept_vacancy(phone, password, request, vacancy_id):
    ''' click reply vacancy by vacancy id and request'''
    print('login')
    login(phone, password)
    print('searching')
    send_find_request(request)
    print('find and click vacancy')
    res = click_by_id(vacancy_id)
    driver.quit()
    return res



#!/usr/bin/env python
# coding: utf-8
"""Шаблон для задач celery"""
import json
from time import sleep
from io import StringIO
import psycopg2
import pandas as pd
import requests
from celery import Celery
import sqlalchemy


class ScrapingException(Exception):
    """ Scraping exception"""
    def __init__(self, msg):
        self.msg = msg
        super().__init__(self.msg)


CON = 'postgresql://postgres:postgres@postgres:5432/public'
app = Celery('tasks',
    backend='redis://redis:6379/0',
    broker='amqp://admin:secure_password@rabbitmq//')
#app = Celery('tasks',
#    backend='redis://localhost:6380/0',
#    broker='amqp://admin:secure_password@localhost:5673//')
#CON = 'postgresql://postgres:postgres@localhost:5433/public'


def get_active_searches():
    """get active searches"""
    df = pd.read_sql('select * from searches',CON)
    return df

def update_db_df(edited_df):
    """update db"""
    edited_df.to_sql('searches', con=CON, index=False, if_exists='replace')


def get_last_data():
    """get last data """
    df2 = pd.read_sql('''select * from hh_ds_last_values''', con=CON)
    return df2

def get_empty_descriptions_data():
    """get last data without parsed skills"""
    df2 = pd.read_sql('''select h2.* from hh_ds_last_values h1
join vacancy_descriptions h2 on h1.vac_id = h2.vac_id
where h2.vac_id not in (select distinct vac_id from vacancy_skills)
and h2.vac_descr is not null
''', con=CON)
    return df2

def del_last_data():
    """del last data grabbed"""
    conn = psycopg2.connect(CON)
    cur = conn.cursor()
    cur.execute('''
    delete from hh_ds
     WHERE dt = (( SELECT max(hd.dt) AS max
           FROM hh_ds hd));''')
    conn.commit()
    conn.close()


def init_db():
    """init db"""
    conn = psycopg2.connect(CON)
    cur = conn.cursor()
    with open('db_dump.sql',encoding='utf-8') as f:
        sql = f.read()
    cur.execute(sql)
    conn.commit()
    conn.close()


def check_db():
    '''check database and initialize if required'''
    try:
        get_active_searches()
    except sqlalchemy.exc.NoSuchTableError:
        init_db()


def grab_hh_new_vac_desc(phone, password):
    """
    grab new vacancies description
    """
    phone = str(phone)
    df2 = pd.read_sql('''
    select vac_id from hh_ds_last_values 
    where vac_id not in (select vac_id from vacancy_descriptions)''',
    con=CON)

    vac_ids = df2.vac_id.to_list()
    jsn={
        "phone": phone,
        "password": password,
        "vacancy_ids": vac_ids
    }
    res = requests.post('http://hh_grabber:8000/get_vacancy_descriptions',
                    json=jsn, timeout=2400)

    max_try = 5
    while not res.ok:
        if max_try == 0:
            raise ScrapingException('Request vac desriptions: API max retries reached')
        #wait 1 min
        sleep(60)
        # request again
        res = requests.post('http://hh_grabber:8000/get_vacancy_descriptions',
                        json=jsn, timeout=2400)
        max_try -= 1


    d=res.json()
    df = pd.DataFrame(json.loads(d))

    df.to_sql('vacancy_descriptions',con=CON, if_exists='append', index=False)


def grab_hh(phone, password, request):
    """grab hh"""
    phone = str(phone)
    print('first try')
    print(f''' phone = "{phone}", "{password}", "{request}"''')
    res = requests.post('http://hh_grabber:8000/find_vacancies',
                        json={
                          "phone": phone,
                          "password": password,
                          "request": request
                        }, timeout=2400)

    max_try = 5

    while not res.ok:
        if max_try == 0:
            raise ScrapingException('API max retries reached')
        #wait 1 min
        sleep(60)
        # request again
        res = requests.post('http://hh_grabber:8000/find_vacancies',
                        json={
                        "phone": phone,
                        "password": password,
                        "request": request
                        }, timeout=2400)
        max_try -= 1

    d = res.json()
    df = pd.DataFrame(json.loads(d))
    df['dt'] = pd.to_datetime(df.dt, unit='ms')

    df.to_sql('hh_ds', con=CON, if_exists='append', index=False)
    grab_hh_new_vac_desc(phone, password)



def grab_zp_new_vac_desc(phone, password):
    """
    grab zarplata.ru new vacancies description
    """
    phone = str(phone)
    df2 = pd.read_sql('''select vac_id from hh_ds_last_values
    where vac_id not in (select vac_id from vacancy_descriptions where site = 'zarplata.ru')
    and site = 'zarplata.ru' 
    ''', con=CON)

    vac_ids = df2.vac_id.to_list()

    res = requests.post('http://zarplata_grabber:8000/get_vacancy_descriptions',
                    json={
                      "phone": phone,
                      "password": password,
                      "vacancy_ids": vac_ids
                    }, timeout=2400)

    max_try = 5
    while not res.ok:
        if max_try == 0:
            raise ScrapingException('Request vac desriptions: API max retries reached')
        #wait 1 min
        sleep(60)
        # request again
        res = requests.post('http://zarplata_grabber:8000/get_vacancy_descriptions',
                        json={
                          "phone": phone,
                          "password": password,
                          "vacancy_ids": vac_ids
                        }, timeout=2400)
        max_try -= 1


    d=res.json()
    df = pd.DataFrame(json.loads(d))
    df.to_sql('vacancy_descriptions',con=CON, if_exists='append', index=False)

def grab_zp(phone, password, request):
    """
    grab zarplata.ru vacancies
    """
    phone=str(phone)
    res = requests.post('http://zarplata_grabber:8000/find_vacancies',
                        json={
                          "phone": phone,

                            "password": password,
                          "request": request
                        }, timeout=2400)

    max_try = 5

    while not res.ok:
        if max_try == 0:
            raise ScrapingException('API max retries reached')
        #wait 1 min
        sleep(60)
        # request again
        res = requests.post('http://zarplata_grabber:8000/find_vacancies',
                        json={
                          "phone": phone,

                            "password": password,
                          "request": request
                        }, timeout=2400)
        max_try -= 1

    d=res.json()
    df = pd.DataFrame(json.loads(d))
    df['dt']=pd.to_datetime(df.dt, unit='ms')

    df.to_sql('hh_ds',con=CON, if_exists='append',index=False)

    grab_zp_new_vac_desc(phone, password)

@app.task(bind=True)
def grab(self, df):
    '''grab vacancies using sources from dataframe df'''
    df2=pd.read_json(StringIO(df))
    print('grab job started')
    self.update_state(state='PROGRESS', meta={'done': 0})
    for i,row in df2.iterrows():
        # check if enabled
        if not row.enabled:
            continue
        if row.site == 'hh.ru':
            print('grab hh', row.request)
            grab_hh(row.phone, row.password, row.request)
        elif row.site == 'zarplata.ru':
            print('grab zp', row.request)
            grab_zp(row.phone, row.password, row.request)

        self.update_state(state='PROGRESS', meta={'done': 100.0*i/len(df2)})
    return 'DONE'
    #self.update_state(state='SUCCESS', meta={'done': 100.0 * i / len(df2)})


@app.task(bind=True)
def grab_description(self, df):
    '''grab vacancies using sources from dataframe df'''
    df2=pd.read_json(StringIO(df))
    print('grab job started')
    self.update_state(state='PROGRESS', meta={'done': 0})
    for i,row in df2.iterrows():
        # check if enabled
        if not row.enabled:
            continue
        if row.site == 'hh.ru':
            print('grab hh new desc', row.request)
            grab_hh_new_vac_desc(row.phone, row.password)
        elif row.site == 'zarplata.ru':
            print('grab zp new desc', row.request)
            grab_zp_new_vac_desc(row.phone, row.password)

        self.update_state(state='PROGRESS', meta={'done': int(100.0*i/len(df2))})
    return 'DONE'
    #self.update_state(state='SUCCESS', meta={'done': 100.0 * i / len(df2)})

@app.task(bind=True)
def grab2(self,df):
    """grab vacancies test task"""
    df2=pd.read_json(StringIO(df))
    print(df2)
    self.update_state(state='PROGRESS', meta={'done': 0})
    sleep(10)
    self.update_state(state='PROGRESS', meta={'done': 25})
    sleep(10)
    self.update_state(state='PROGRESS', meta={'done': 50})
    sleep(10)
    self.update_state(state='PROGRESS', meta={'done': 75})
    sleep(10)
    self.update_state(state='PROGRESS', meta={'done': 100})
    return [{'request': 123}]


@app.task(bind=True)
def process_description(self,df):
    """parse vacancies description task"""
    print('Task:parsing_descriptions ',df)
    df2=pd.read_json(StringIO(df))
    self.update_state(state='PROGRESS', meta={'done': 0})
    for i,row in df2.iterrows():
        print(i,row)
        res = requests.post('http://description_analyzer:8000/parse_descriptions',
                        json={
                          "desc": row.vac_descr,
                        }, timeout=100)
        d = res.json()
        df = pd.DataFrame(json.loads(d))
        df['vac_id'] = row.vac_id

        df.to_sql('vacancy_skills', con=CON, if_exists='append', index=False)
        self.update_state(state='PROGRESS', meta={'done': int(100.0*i/df2.shape[0])})

    return 'DONE'
